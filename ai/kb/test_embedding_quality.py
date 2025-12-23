#!/usr/bin/env python3
"""
TEAM 3 - KB Embedding Quality & Validation Tests
Tests de similarité, validation des chunks, et métriques de qualité
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from kb.retriever import ChromaRetriever
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available - will create mock tests")


class ChunkValidator:
    """Validates chunk quality metrics"""
    
    def __init__(self, min_size: int = 100, max_size: int = 1000, overlap_ratio: float = 0.1):
        self.min_size = min_size
        self.max_size = max_size
        self.overlap_ratio = overlap_ratio
        self.results = {
            "chunks_analyzed": 0,
            "valid_chunks": 0,
            "invalid_chunks": 0,
            "issues": []
        }
    
    def validate_chunk_size(self, chunk: str) -> Tuple[bool, str]:
        """Validate chunk is within size boundaries"""
        size = len(chunk)
        
        if size < self.min_size:
            return False, f"Chunk too small ({size} < {self.min_size})"
        if size > self.max_size:
            return False, f"Chunk too large ({size} > {self.max_size})"
        
        return True, "OK"
    
    def validate_chunk_cohesion(self, chunk: str) -> Tuple[bool, str]:
        """Check if chunk has coherent content (not fragmented)"""
        lines = chunk.strip().split('\n')
        
        # Check minimum lines
        if len(lines) < 2:
            return False, "Chunk too fragmented (< 2 lines)"
        
        # Check average line length (coherence indicator)
        avg_line_len = sum(len(l) for l in lines) / len(lines)
        if avg_line_len < 10:
            return False, f"Lines too short (avg {avg_line_len:.1f} chars)"
        
        return True, "OK"
    
    def validate_chunks_batch(self, chunks: List[str]) -> Dict:
        """Validate multiple chunks"""
        self.results["chunks_analyzed"] = len(chunks)
        
        for i, chunk in enumerate(chunks):
            valid_size, msg_size = self.validate_chunk_size(chunk)
            valid_cohesion, msg_cohesion = self.validate_chunk_cohesion(chunk)
            
            if valid_size and valid_cohesion:
                self.results["valid_chunks"] += 1
            else:
                self.results["invalid_chunks"] += 1
                issue = {
                    "chunk_id": i,
                    "size_check": msg_size,
                    "cohesion_check": msg_cohesion
                }
                self.results["issues"].append(issue)
        
        self.results["validity_rate"] = (
            self.results["valid_chunks"] / len(chunks) * 100 
            if chunks else 0
        )
        
        return self.results


class EmbeddingQualityMetrics:
    """Compute embedding quality metrics"""
    
    def __init__(self):
        self.metrics = {
            "embedding_dimensionality": 0,
            "mean_norm": 0.0,
            "std_norm": 0.0,
            "mean_sparsity": 0.0,
            "coverage": 0.0
        }
    
    def compute_metrics(self, embeddings: List[List[float]]) -> Dict:
        """Compute quality metrics for embeddings"""
        if not embeddings or not embeddings[0]:
            return self.metrics
        
        import statistics
        
        # Dimensionality
        self.metrics["embedding_dimensionality"] = len(embeddings[0])
        
        # Norms - fix: properly iterate through embeddings
        norms = []
        for emb in embeddings:
            if isinstance(emb, (list, tuple)):
                norm = sum(x**2 for x in emb)**0.5
            else:
                norm = sum(emb)**0.5
            norms.append(norm)
        
        self.metrics["mean_norm"] = round(statistics.mean(norms), 3) if norms else 0.0
        self.metrics["std_norm"] = round(statistics.stdev(norms), 3) if len(norms) > 1 else 0.0
        
        # Sparsity (percentage of zeros)
        sparsities = []
        for emb in embeddings:
            zero_count = sum(1 for x in emb if abs(x) < 1e-6)
            sparsity = zero_count / len(emb) * 100
            sparsities.append(sparsity)
        
        self.metrics["mean_sparsity"] = statistics.mean(sparsities) if sparsities else 0
        
        # Coverage (non-zero dimensions)
        non_zero_dims = set()
        for emb in embeddings:
            for i, val in enumerate(emb):
                if abs(val) >= 1e-6:
                    non_zero_dims.add(i)
        
        self.metrics["coverage"] = len(non_zero_dims) / self.metrics["embedding_dimensionality"] * 100
        
        return self.metrics


class SimilarityTestSuite:
    """Test similarity scores on KB dataset"""
    
    def __init__(self, retriever=None):
        self.retriever = retriever
        self.test_cases = []
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "similarity_scores": [],
            "mean_similarity": 0.0,
            "median_similarity": 0.0,
            "min_similarity": 0.0,
            "max_similarity": 0.0,
            "above_threshold_80": 0,
            "coverage_80_percent": 0.0
        }
    
    def add_test_case(self, query: str, expected_docs: List[str], min_similarity: float = 0.8):
        """Add a test case"""
        self.test_cases.append({
            "query": query,
            "expected_docs": expected_docs,
            "min_similarity": min_similarity
        })
    
    def _mock_retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """Mock retrieval if Chroma not available"""
        # Compute simple lexical similarity
        query_words = set(query.lower().split())
        
        results = []
        for doc in self.test_cases[0]["expected_docs"] if self.test_cases else []:
            doc_words = set(doc.lower().split())
            
            # Jaccard similarity
            if query_words or doc_words:
                similarity = len(query_words & doc_words) / len(query_words | doc_words)
            else:
                similarity = 0.0
            
            results.append({
                "content": doc,
                "score": round(similarity, 3)
            })
        
        return sorted(results, key=lambda x: x["score"], reverse=True)[:k]
    
    def run_tests(self) -> Dict:
        """Execute all test cases"""
        if not self.test_cases:
            logger.warning("No test cases defined")
            return self.results
        
        logger.info(f"Running {len(self.test_cases)} similarity tests...")
        
        for i, test_case in enumerate(self.test_cases):
            self.results["tests_run"] += 1
            query = test_case["query"]
            expected_docs = test_case["expected_docs"]
            min_similarity = test_case["min_similarity"]
            
            # Retrieve
            if self.retriever and CHROMA_AVAILABLE:
                retrieved = self.retriever.retrieve(query, k=5)
            else:
                retrieved = self._mock_retrieve(query, k=5)
            
            if not retrieved:
                self.results["tests_failed"] += 1
                logger.warning(f"Test {i+1}: No results retrieved")
                continue
            
            # Check similarity
            top_score = retrieved[0]["score"]
            self.results["similarity_scores"].append(top_score)
            
            if top_score >= min_similarity:
                self.results["tests_passed"] += 1
                logger.info(f"Test {i+1}: PASS (similarity={top_score:.3f})")
            else:
                self.results["tests_failed"] += 1
                logger.warning(f"Test {i+1}: FAIL (similarity={top_score:.3f} < {min_similarity})")
        
        # Compute statistics
        if self.results["similarity_scores"]:
            import statistics
            
            scores = self.results["similarity_scores"]
            self.results["mean_similarity"] = round(statistics.mean(scores), 3)
            self.results["median_similarity"] = round(statistics.median(scores), 3)
            self.results["min_similarity"] = round(min(scores), 3)
            self.results["max_similarity"] = round(max(scores), 3)
            
            # Count above threshold
            above_80 = sum(1 for s in scores if s >= 0.8)
            self.results["above_threshold_80"] = above_80
            self.results["coverage_80_percent"] = round(above_80 / len(scores) * 100, 1)
        
        return self.results


def create_test_dataset() -> List[Dict]:
    """Create sample KB test dataset"""
    return [
        {
            "id": "kb_001",
            "content": "Pour les problèmes de connexion, essayez de réinitialiser votre mot de passe depuis la page de connexion. Si vous avez oublié votre email, contactez le support.",
            "category": "authentification"
        },
        {
            "id": "kb_002",
            "content": "Les tarifs dépendent de votre plan d'abonnement. Plan Basic: 99€/mois, Plan Pro: 299€/mois, Plan Enterprise: prix personnalisé.",
            "category": "facturation"
        },
        {
            "id": "kb_003",
            "content": "Pour configurer SSO, accédez à Admin > Sécurité > Single Sign-On. Nous supportons SAML 2.0 et OAuth 2.0. Consultez la documentation pour les détails.",
            "category": "technique"
        },
        {
            "id": "kb_004",
            "content": "Exporter vos données: Allez à Paramètres > Export. Sélectionnez le format (CSV, JSON, Excel). Les données seront prêtes en quelques minutes.",
            "category": "données"
        },
        {
            "id": "kb_005",
            "content": "Configuration d'une équipe par projet: Projet > Ajouter une équipe > Assigner des membres avec rôles (Admin, Manager, Contributor). Les permissions peuvent être ajustées par rôle.",
            "category": "gestion"
        },
        {
            "id": "kb_006",
            "content": "Problèmes de performance: Vérifiez votre connexion internet. Réduisez le nombre de filtres actifs. Contactez le support si le problème persiste.",
            "category": "technique"
        },
        {
            "id": "kb_007",
            "content": "Facturation et paiement: Vous pouvez modifier votre plan à tout moment. Les changements prennent effet au prochain cycle de facturation.",
            "category": "facturation"
        },
        {
            "id": "kb_008",
            "content": "Détection de données sensibles: Ne partagez jamais vos cartes bancaires, emails ou numéros de téléphone dans les tickets. Utilisez des channels sécurisés.",
            "category": "sécurité"
        },
        {
            "id": "kb_009",
            "content": "Intégrations disponibles: Slack, Microsoft Teams, Zapier, Webhooks personnalisés. Consultez le marketplace pour plus d'intégrations.",
            "category": "intégrations"
        },
        {
            "id": "kb_010",
            "content": "Support client: Disponible 24/7 via chat, email, et téléphone. Temps de réponse moyen: < 2 heures pour les tickets prioritaires.",
            "category": "support"
        }
    ]


def run_all_tests() -> Dict:
    """Run complete test suite"""
    
    logger.info("="*80)
    logger.info("TEAM 3 - KB EMBEDDING QUALITY VALIDATION")
    logger.info("="*80)
    
    all_results = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "chunk_validation": {},
        "embedding_quality": {},
        "similarity_tests": {},
        "summary": {}
    }
    
    # ===== TEST 1: CHUNK VALIDATION =====
    logger.info("\n[TEST 1] Chunk Validation...")
    
    chunks_to_validate = [
        "This is a valid chunk with sufficient content about important topics and technical information.",
        "Short chunk",
        "A very long chunk that contains extensive information about many different topics and subtopics that might be too much for a single chunk to handle effectively in a vector database context.",
    ]
    
    chunk_validator = ChunkValidator(min_size=50, max_size=500)
    validation_results = chunk_validator.validate_chunks_batch(chunks_to_validate)
    
    all_results["chunk_validation"] = {
        "status": "PASS" if validation_results["validity_rate"] >= 80 else "FAIL",
        "valid_chunks": validation_results["valid_chunks"],
        "total_chunks": validation_results["chunks_analyzed"],
        "validity_rate_percent": validation_results["validity_rate"],
        "issues": validation_results["issues"]
    }
    
    logger.info(f"Chunk Validation: {validation_results['valid_chunks']}/{validation_results['chunks_analyzed']} valid ({validation_results['validity_rate']:.1f}%)")
    
    # ===== TEST 2: EMBEDDING QUALITY =====
    logger.info("\n[TEST 2] Embedding Quality Metrics...")
    
    # Mock embeddings (384-dim like all-MiniLM-L6-v2)
    mock_embeddings = [
        [0.1, 0.2, -0.15] + [0.0]*381,  # Some non-zero values
        [0.05, -0.1, 0.2] + [0.0]*381,
        [0.15, 0.1, 0.0] + [0.0]*381,
    ]
    
    emb_metrics = EmbeddingQualityMetrics()
    embedding_quality = emb_metrics.compute_metrics(mock_embeddings)
    
    all_results["embedding_quality"] = {
        "dimensionality": embedding_quality["embedding_dimensionality"],
        "mean_norm": embedding_quality["mean_norm"],
        "std_norm": embedding_quality["std_norm"],
        "mean_sparsity_percent": embedding_quality["mean_sparsity"],
        "coverage_percent": embedding_quality["coverage"],
        "status": "HEALTHY" if 0.95 <= embedding_quality["coverage"] <= 100 else "WARNING"
    }
    
    logger.info(f"Embedding Quality: dim={embedding_quality['embedding_dimensionality']}, coverage={embedding_quality['coverage']:.1f}%")
    
    # ===== TEST 3: SIMILARITY TESTS =====
    logger.info("\n[TEST 3] Similarity Threshold Tests...")
    
    kb_dataset = create_test_dataset()
    
    # Create test cases
    test_queries = [
        ("Comment réinitialiser mon mot de passe?", [doc["content"] for doc in kb_dataset if doc["category"] == "authentification"]),
        ("Quels sont les tarifs?", [doc["content"] for doc in kb_dataset if doc["category"] == "facturation"]),
        ("Comment exporter les données?", [doc["content"] for doc in kb_dataset if doc["category"] == "données"]),
        ("Configurer SSO", [doc["content"] for doc in kb_dataset if doc["category"] == "technique"]),
        ("Équipe par projet", [doc["content"] for doc in kb_dataset if doc["category"] == "gestion"]),
    ]
    
    similarity_suite = SimilarityTestSuite(retriever=None)
    
    for query, expected_docs in test_queries:
        similarity_suite.add_test_case(query, expected_docs, min_similarity=0.8)
    
    similarity_results = similarity_suite.run_tests()
    
    all_results["similarity_tests"] = {
        "tests_run": similarity_results["tests_run"],
        "tests_passed": similarity_results["tests_passed"],
        "tests_failed": similarity_results["tests_failed"],
        "pass_rate_percent": round(similarity_results["tests_passed"] / max(1, similarity_results["tests_run"]) * 100, 1),
        "mean_similarity": similarity_results["mean_similarity"],
        "median_similarity": similarity_results["median_similarity"],
        "min_similarity": similarity_results["min_similarity"],
        "max_similarity": similarity_results["max_similarity"],
        "above_threshold_80_count": similarity_results["above_threshold_80"],
        "coverage_80_percent": similarity_results["coverage_80_percent"],
        "status": "PASS" if similarity_results["coverage_80_percent"] >= 80 else "FAIL"
    }
    
    logger.info(f"Similarity Tests: {similarity_results['tests_passed']}/{similarity_results['tests_run']} passed, Coverage >0.8: {similarity_results['coverage_80_percent']:.1f}%")
    
    # ===== SUMMARY =====
    logger.info("\n[SUMMARY]")
    all_results["summary"] = {
        "chunk_validation_status": all_results["chunk_validation"]["status"],
        "embedding_quality_status": all_results["embedding_quality"]["status"],
        "similarity_test_status": all_results["similarity_tests"]["status"],
        "overall_status": "PASS" if all([
            all_results["chunk_validation"]["status"] == "PASS",
            all_results["embedding_quality"]["status"] == "HEALTHY",
            all_results["similarity_tests"]["status"] == "PASS"
        ]) else "FAIL",
        "improvements_needed": []
    }
    
    # Add improvement suggestions
    if all_results["chunk_validation"]["status"] != "PASS":
        all_results["summary"]["improvements_needed"].append(
            "Chunk validation: Adjust min/max sizes or improve chunking strategy"
        )
    
    if all_results["embedding_quality"]["status"] != "HEALTHY":
        all_results["summary"]["improvements_needed"].append(
            "Embedding quality: Low coverage suggests embedding model issues"
        )
    
    if all_results["similarity_tests"]["status"] != "PASS":
        all_results["summary"]["improvements_needed"].append(
            f"Similarity tests: Only {all_results['similarity_tests']['coverage_80_percent']:.1f}% above threshold, need better retrieval"
        )
    
    # Save results
    output_file = "KB_EMBEDDING_VALIDATION_RESULTS.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\nResults saved to: {output_file}")
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info(f"OVERALL STATUS: {all_results['summary']['overall_status']}")
    logger.info("="*80 + "\n")
    
    return all_results


if __name__ == "__main__":
    results = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["summary"]["overall_status"] == "PASS" else 1)
