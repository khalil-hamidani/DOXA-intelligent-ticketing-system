#!/usr/bin/env python3
"""
TEAM 3 - Grille d'Évaluation Agentic - Analyse Détaillée
Évaluation complète du système selon les 16 critères spécifiés
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple

# ==========================================
# RÉSULTATS D'ANALYSE DÉTAILLÉE
# ==========================================

ANALYSIS_RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "team": "TEAM 3",
    "evaluation_grid": "Grille d'Évaluation Agentic - Solution 1",
    "total_criteria": 16,
    "main_criteria": 12,
    "bonus_criteria": 4,
    
    "scores": {
        "main": {},
        "bonus": {},
        "summary": {}
    },
    
    "detailed_findings": {}
}

# ==========================================
# CRITÈRE 1: Extraction, Chunking et Embedding (12%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["1_extraction_chunking_embedding"] = {
    "weight": 12,
    "title": "Extraction, Chunking et Embedding",
    "expected": "Extraction contenu KB, chunking (statique/sémantique), stockage vectoriel, similarité >0.8",
    "findings": {
        "kb_structure": {
            "status": "PARTIAL",
            "details": [
                "✓ Dossier kb/ existe avec retriever.py et ingestion",
                "✓ ChromaDB Retriever implémenté (all-MiniLM-L6-v2)",
                "✓ Chunking avec MarkdownHeaderTextSplitter dans ingest_kb.py",
                "✗ MANQUE: Test de similarité >0.8 sur dataset KB",
                "✗ MANQUE: Validation des chunks (taille, overlap)",
                "✗ MANQUE: Métrique de qualité d'embedding"
            ]
        },
        "vector_store": {
            "status": "PRESENT",
            "details": [
                "✓ ChromaDB configuré avec embedding model",
                "✓ Collection 'kb_chunks' créée",
                "✗ MANQUE: Index optimization (HNSW config)",
                "✗ MANQUE: Similarity threshold testing"
            ]
        }
    },
    "score": 6,
    "max_score": 12,
    "gaps": [
        "Pas de benchmark de similarité",
        "Pas de validation de chunk quality",
        "Pas de persistence check"
    ],
    "recommendations": [
        "Implémenter test_similarity_scores() avec dataset KB de 50 docs",
        "Ajouter metrics de chunk quality (taille, cohérence)",
        "Vérifier similarité >0.8 sur 80% des queries"
    ]
}

# ==========================================
# CRITÈRE 2: Agent Query Analyzer (9%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["2_query_analyzer"] = {
    "weight": 9,
    "title": "Agent Query Analyzer",
    "expected": "Résumé <100 mots + extraction 5-10 mots-clés. Métriques: résumé, keywords",
    "findings": {
        "implementation": {
            "status": "PRESENT",
            "details": [
                "✓ query_analyzer.py avec Agent A (Reformulation)",
                "✓ Instructions pour summary et keywords",
                "✓ Mistral LLM intégré",
                "✓ Retour JSON structuré",
                "✗ MANQUE: Validation du résumé (<100 mots)",
                "✗ MANQUE: Validation keywords (5-10)",
                "✗ MANQUE: Métriques de confiance",
                "✗ MANQUE: Test de performance"
            ]
        },
        "output_format": {
            "status": "PARTIAL",
            "details": [
                "✓ JSON avec 'summary' et 'keywords'",
                "✗ Pas de word count validation",
                "✗ Pas de metrics returning",
                "✗ Pas de performance timing"
            ]
        }
    },
    "score": 5,
    "max_score": 9,
    "gaps": [
        "Pas de validation de output (word count, keyword count)",
        "Pas de métriques retournées (processing_time, confidence)",
        "Pas de fallback si extraction échoue"
    ],
    "recommendations": [
        "Ajouter validation: assert 10 < word_count(summary) <= 100",
        "Ajouter validation: assert 5 <= len(keywords) <= 10",
        "Retourner dict avec timing et confidence_score"
    ]
}

# ==========================================
# CRITÈRE 3: Agent Solution Finder (RAG) (9%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["3_solution_finder_rag"] = {
    "weight": 9,
    "title": "Agent Solution Finder (RAG)",
    "expected": "Retrieve N=5 docs + reranking. Snippets triés + scores confiance (0-1)",
    "findings": {
        "retrieval": {
            "status": "PRESENT",
            "details": [
                "✓ solution_finder.py implémenté",
                "✓ ChromaDB retrieval avec k=5 par défaut",
                "✓ Lexical scoring ajouté",
                "✓ Reranking avec _normalize_scores()",
                "✗ MANQUE: Combine retrieval + reranking (actuellement un seul)",
                "✗ MANQUE: Confiance scores explicite (0-1)",
                "✗ MANQUE: Sorting des snippets par score"
            ]
        },
        "ranking": {
            "status": "PARTIAL",
            "details": [
                "✓ _lexical_score() implémenté",
                "✓ _normalize_scores() pour normalisation",
                "✗ Pas de reranker ML (cross-encoder)",
                "✗ Pas de BM25 + semantic fusion",
                "✗ Pas de snippet extraction optimisée"
            ]
        }
    },
    "score": 5,
    "max_score": 9,
    "gaps": [
        "Hybrid retrieval non implémenté (semantic + lexical)",
        "Pas de reranker ML pour optimiser top-5",
        "Pas de snippet quality scoring",
        "Pas de diversity filtering"
    ],
    "recommendations": [
        "Implémenter hybrid retrieval: semantic(0.7) + lexical(0.3)",
        "Ajouter cross-encoder reranking sur top-10 before returning top-5",
        "Ajouter diversity scoring pour éviter redundance",
        "Retourner: [{'doc_id', 'snippet', 'score', 'confidence_pct'}]"
    ]
}

# ==========================================
# CRITÈRE 4: Agent Evaluator et Decider (9%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["4_evaluator_decider"] = {
    "weight": 9,
    "title": "Agent Evaluator et Decider",
    "expected": "Confiance <0.6 → escalade. Détection émotions négatiques. Règles configurables",
    "findings": {
        "confidence_threshold": {
            "status": "PARTIAL",
            "details": [
                "✓ evaluator.py avec base_conf + snippet_bonus",
                "✓ Détection émotions (negative_sentiment)",
                "✓ Escalade logic présente",
                "✗ MANQUE: Threshold configurable (hardcoded 0.6)",
                "✗ MANQUE: Rules engine (utilise hardcoded)",
                "✗ MANQUE: Logging des raisons"
            ]
        },
        "sentiment_detection": {
            "status": "PRESENT",
            "details": [
                "✓ NEGATIVE_WORDS list",
                "✓ Bonus/penalty système",
                "✗ Pas de NLP sentiment (utilise regex)",
                "✗ Pas de scoring nuancé (0.0-1.0)"
            ]
        }
    },
    "score": 5,
    "max_score": 9,
    "gaps": [
        "Règles hardcodées, pas configurables",
        "Pas de rules engine (ex: Drools equivalent)",
        "Sentiment detection basique (regex vs NLP)",
        "Pas de audit trail pour decisions"
    ],
    "recommendations": [
        "Créer config.json avec seuils configurables",
        "Implémenter RulesEngine class avec rule definitions",
        "Intégrer transformers sentiment model pour NLP",
        "Logger chaque decision avec trace_id et reasons"
    ]
}

# ==========================================
# CRITÈRE 5: Détection de Données Sensibles (9%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["5_sensitive_data"] = {
    "weight": 9,
    "title": "Détection de Données Sensibles",
    "expected": "Patterns: cartes, emails, phones. Escalade 100%",
    "findings": {
        "implementation": {
            "status": "PRESENT",
            "details": [
                "✓ _contains_sensitive() dans evaluator.py",
                "✓ Email pattern regex",
                "✓ Phone number detection",
                "✓ Credit card pattern (Visa 4[0-9]...)",
                "✗ MANQUE: Test coverage sur patterns",
                "✗ MANQUE: IBAN et autres formats",
                "✗ MANQUE: Document number patterns",
                "✗ MANQUE: SQL injection / command injection"
            ]
        },
        "coverage": {
            "status": "PARTIAL",
            "details": [
                "✓ Email: ✓ implémenté",
                "✓ Phone: ✓ basique",
                "✓ Card: ✓ Visa seulement",
                "✗ IBAN: manque",
                "✗ SSN: manque",
                "✗ Passport: manque"
            ]
        }
    },
    "score": 6,
    "max_score": 9,
    "gaps": [
        "Pas de test cases pour patterns",
        "Couverture incomplète (3/10 patterns)",
        "Pas de false positive rate measurement",
        "Pas de masking/redaction des données"
    ],
    "recommendations": [
        "Étendre patterns: IBAN, SSN, Passport, Driver License",
        "Créer test dataset avec 100 samples par pattern",
        "Implémenter data masking (ex: email → e***@***.com)",
        "Ajouter metrics: precision, recall, f1 score"
    ]
}

# ==========================================
# CRITÈRE 6: Agent Response Composer (9%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["6_response_composer"] = {
    "weight": 9,
    "title": "Agent Response Composer",
    "expected": "Template: remerciements + problème + solution + action. Détection langue",
    "findings": {
        "template": {
            "status": "PRESENT",
            "details": [
                "✓ response_composer.py implémenté",
                "✓ Template structure présent",
                "✓ Remerciements: 'Bonjour {name}'",
                "✓ Problème: 'Merci pour votre demande'",
                "✓ Solution proposée: incluse",
                "✓ Actions recommandées: étapes + confiance",
                "✗ MANQUE: Détection de langue",
                "✗ MANQUE: Variables de template manquent parfois"
            ]
        },
        "language_detection": {
            "status": "MISSING",
            "details": [
                "✗ Hardcoded French responses",
                "✗ Pas de langdetect integration",
                "✗ Pas de i18n support"
            ]
        }
    },
    "score": 7,
    "max_score": 9,
    "gaps": [
        "Pas de language detection (assume French)",
        "Pas de multi-language support",
        "Pas de tone adjustment (formal vs casual)",
        "Pas de template validation"
    ],
    "recommendations": [
        "Ajouter langdetect pour auto-detection",
        "Créer templates pour EN/FR/ES",
        "Implémenter tone parameter (formal/friendly)",
        "Valider que tous les placeholders sont remplis"
    ]
}

# ==========================================
# CRITÈRE 7: Qualité des Réponses IA (8%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["7_answer_quality"] = {
    "weight": 8,
    "title": "Qualité des Réponses IA",
    "expected": "Pas de hallucinations. Ton professionnel. Couvre 100% questions",
    "findings": {
        "hallucination_prevention": {
            "status": "PARTIAL",
            "details": [
                "✓ Utilisation de KB + RAG (grounded)",
                "✓ Fallback answers structurées",
                "✗ MANQUE: Validation de factualité",
                "✗ MANQUE: Citation des sources",
                "✗ MANQUE: Metrics de hallucination rate"
            ]
        },
        "tone_and_coverage": {
            "status": "PRESENT",
            "details": [
                "✓ Ton professionnel dans templates",
                "✓ Coverage: fallback génériques",
                "✗ MANQUE: Test coverage (100 questions)",
                "✗ MANQUE: Quality scoring (0-1)"
            ]
        }
    },
    "score": 5,
    "max_score": 8,
    "gaps": [
        "Pas de hallucination detection",
        "Pas de citation des sources KB",
        "Pas de factuality checking",
        "Pas de evaluation dataset (100 Q&A)"
    ],
    "recommendations": [
        "Implémenter source citation: 'D'après Doc#123'",
        "Ajouter fact checking avec entailment model",
        "Créer test set de 100 questions variées",
        "Mesurer quality_score = (no_hallucination AND source_cited AND covers_question)"
    ]
}

# ==========================================
# CRITÈRE 8: Gestion des Erreurs du Pipeline (8%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["8_error_handling"] = {
    "weight": 8,
    "title": "Gestion des Erreurs du Pipeline",
    "expected": "Fallbacks intelligents. Circuit breaker (retries 3x). Logging structuré + trace_id",
    "findings": {
        "fallback_system": {
            "status": "PARTIAL",
            "details": [
                "✓ Fallback answers dans solution_finder",
                "✓ Fallback templates dans response_composer",
                "✗ MANQUE: Centralized fallback handler",
                "✗ MANQUE: Fallback scoring/selection"
            ]
        },
        "circuit_breaker": {
            "status": "MISSING",
            "details": [
                "✗ Pas de circuit breaker implémenté",
                "✗ Pas de retry logic",
                "✗ Pas de timeout handling"
            ]
        },
        "logging": {
            "status": "BASIC",
            "details": [
                "✓ Basic logging import présent",
                "✗ MANQUE: Structured logging",
                "✗ MANQUE: trace_id propagation",
                "✗ MANQUE: Correlation IDs"
            ]
        }
    },
    "score": 3,
    "max_score": 8,
    "gaps": [
        "Pas de circuit breaker pattern",
        "Pas de retry mechanism (3x)",
        "Logging non structuré (pas de trace_id)",
        "Pas de error correlation across services"
    ],
    "recommendations": [
        "Implémenter CircuitBreaker avec states: CLOSED/OPEN/HALF_OPEN",
        "Ajouter exponential backoff retry (3x attempts)",
        "Implémenter structured logging avec trace_id",
        "Créer ErrorContext(trace_id, service, attempt, error)"
    ]
}

# ==========================================
# CRITÈRE 9: Latence du Pipeline (6%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["9_latency"] = {
    "weight": 6,
    "title": "Latence du Pipeline",
    "expected": "<10s end-to-end (<5s better)",
    "findings": {
        "current_state": {
            "status": "UNKNOWN",
            "details": [
                "✗ Pas de timing instrumentation",
                "✗ Pas de latency benchmarks",
                "✗ Pas de performance profiling"
            ]
        },
        "optimization_potential": {
            "status": "HIGH",
            "details": [
                "⚠ LLM calls (Mistral) peuvent être lentes (2-5s)",
                "⚠ ChromaDB retrieval peut prendre 1-2s",
                "⚠ Pas de parallelization"
            ]
        }
    },
    "score": 2,
    "max_score": 6,
    "gaps": [
        "Pas de timing measurement",
        "Pas de performance benchmarks",
        "Pas de parallelization (sequential vs parallel)",
        "Pas d'optimizations (caching, batching)"
    ],
    "recommendations": [
        "Ajouter @timer decorator sur tous les stages",
        "Implémenter latency_tracker avec percentiles",
        "Paralleliser KB retrieval + LLM calls",
        "Implémenter caching (LRU cache + Redis)",
        "Benchmark: target = query_analyze(1s) + retrieve(1s) + generate(2s) = 4s total"
    ]
}

# ==========================================
# CRITÈRE 10: Intégration au Backend (7%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["10_backend_integration"] = {
    "weight": 7,
    "title": "Intégration au Backend",
    "expected": "APIs cohérentes. Webhooks ou polling. Sauvegarde async. Gestion timeouts",
    "findings": {
        "api_design": {
            "status": "PARTIAL",
            "details": [
                "✓ ticket_api.py existe",
                "✓ Orchestrator methods présentes",
                "✗ MANQUE: API REST endpoints",
                "✗ MANQUE: Request/response schemas"
            ]
        },
        "async_persistence": {
            "status": "MISSING",
            "details": [
                "✗ Pas de async/await pattern",
                "✗ Pas de queue system (Celery/RQ)",
                "✗ Pas de webhook support"
            ]
        },
        "timeout_handling": {
            "status": "MISSING",
            "details": [
                "✗ Pas de timeout configuration",
                "✗ Pas de graceful degradation"
            ]
        }
    },
    "score": 3,
    "max_score": 7,
    "gaps": [
        "Pas de REST API (FastAPI/Flask)",
        "Pas de async job processing",
        "Pas de webhooks ou polling",
        "Pas de timeout handling"
    ],
    "recommendations": [
        "Créer FastAPI app avec /process-ticket endpoint",
        "Implémenter async job avec Celery/RQ",
        "Ajouter webhook notifications ou polling endpoint",
        "Configurer timeout (default 30s, configurable)",
        "Implémenter health check endpoint"
    ]
}

# ==========================================
# CRITÈRE 11: Stockage des Résultats IA (7%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["11_results_storage"] = {
    "weight": 7,
    "title": "Stockage des Résultats IA",
    "expected": "Tables: summary, keywords, rag_docs, response, confidence, escalade_reason. Index optimisés",
    "findings": {
        "database_schema": {
            "status": "MISSING",
            "details": [
                "✗ Pas de DB schema défini",
                "✗ Pas de ORM (SQLAlchemy)",
                "✗ Pas de data persistence"
            ]
        },
        "required_fields": {
            "status": "MISSING",
            "details": [
                "✗ summary: manque",
                "✗ keywords: manque",
                "✗ rag_docs: manque",
                "✗ response: manque",
                "✗ confidence: manque",
                "✗ escalade_reason: manque"
            ]
        }
    },
    "score": 1,
    "max_score": 7,
    "gaps": [
        "Aucune persistence DB",
        "Pas de schema SQL défini",
        "Pas de indexes optimisés",
        "Pas de audit trail"
    ],
    "recommendations": [
        "Créer SQLAlchemy models: AIResponse, AIMetrics",
        "Implémenter tables avec champs spécifiés",
        "Ajouter indexes sur: ticket_id, created_at, confidence",
        "Implémenter versioning et audit trail"
    ]
}

# ==========================================
# CRITÈRE 12: Prompt Engineering (7%)
# ==========================================
ANALYSIS_RESULTS["detailed_findings"]["12_prompt_engineering"] = {
    "weight": 7,
    "title": "Prompt Engineering",
    "expected": "Bon system prompt: rôle, format, contraintes",
    "findings": {
        "system_prompts": {
            "status": "PRESENT",
            "details": [
                "✓ Query Analyzer: 'ticket analysis expert'",
                "✓ Classifier: 'support ticket classifier'",
                "✓ Instructions structurées",
                "✗ MANQUE: Role definition explicite",
                "✗ MANQUE: Constraints (max length, format)",
                "✗ MANQUE: Few-shot examples",
                "✗ MANQUE: Safety guidelines"
            ]
        },
        "prompt_quality": {
            "status": "BASIC",
            "details": [
                "✓ JSON output format spécifié",
                "✗ Pas de few-shot examples",
                "✗ Pas de CoT (Chain of Thought)",
                "✗ Pas de safety constraints"
            ]
        }
    },
    "score": 4,
    "max_score": 7,
    "gaps": [
        "Prompts basiques sans few-shot",
        "Pas de Chain of Thought",
        "Pas de safety guidelines",
        "Pas de prompt versioning"
    ],
    "recommendations": [
        "Créer PromptTemplates avec role + task + constraints",
        "Ajouter 2-3 few-shot examples par prompt",
        "Implémenter CoT: 'Let me think step by step'",
        "Ajouter safety: 'Do not hallucinate, stick to KB'",
        "Version prompts avec git pour tracking"
    ]
}

# ==========================================
# BONUS CRITÈRES
# ==========================================

# CRITÈRE 13: Détection Automatique de Catégorie (6% bonus)
ANALYSIS_RESULTS["detailed_findings"]["13_auto_categorization"] = {
    "weight": 6,
    "title": "Détection Automatique de Catégorie",
    "expected": "Classification (accès, technique, commercial). Confiance score. Fallback si <0.7. Précision >85% sur 50 tickets",
    "findings": {
        "classification": {
            "status": "PARTIAL",
            "details": [
                "✓ classifier.py avec Agent",
                "✓ 4 categories: technique, facturation, authentification, autre",
                "✓ Confidence score retourné",
                "✗ MANQUE: Test sur 50 tickets",
                "✗ MANQUE: Precision measurement (>85%)"
            ]
        }
    },
    "score": 3,
    "max_score": 6,
    "gaps": [
        "Pas de test dataset",
        "Pas de precision/recall metrics",
        "Pas de confusion matrix"
    ],
    "recommendations": [
        "Créer dataset de 50 tickets labelés",
        "Implémenter classifier eval function",
        "Mesurer precision, recall, f1 par classe"
    ]
}

# CRITÈRE 14: Caching Embeddings/RAG (10% bonus)
ANALYSIS_RESULTS["detailed_findings"]["14_caching"] = {
    "weight": 10,
    "title": "Caching Embeddings/RAG",
    "expected": "Cache persistant. TTL 24h. Hit rate >70%. Invalidation KB update",
    "findings": {
        "caching": {
            "status": "MISSING",
            "details": [
                "✗ Pas de cache layer",
                "✗ Pas de persistent cache",
                "✗ Pas de TTL implementation"
            ]
        }
    },
    "score": 0,
    "max_score": 10,
    "gaps": [
        "Aucun caching implémenté"
    ],
    "recommendations": [
        "Implémenter Redis cache pour queries",
        "Cache key = hash(query + model_id)",
        "TTL = 24h, with invalidation on KB update",
        "Mesurer hit_rate, monitor performance"
    ]
}

# CRITÈRE 15: Support Multimodal KB (7% bonus)
ANALYSIS_RESULTS["detailed_findings"]["15_multimodal"] = {
    "weight": 7,
    "title": "Support Multimodal KB",
    "expected": "OCR pour PDFs/images. Retrieval cross-modal",
    "findings": {
        "multimodal": {
            "status": "MISSING",
            "details": [
                "✗ Pas d'OCR implémenté",
                "✗ Pas de multimodal embeddings",
                "✗ Pas de image handling"
            ]
        }
    },
    "score": 0,
    "max_score": 7,
    "gaps": [
        "Aucun support multimodal"
    ],
    "recommendations": [
        "Intégrer Tesseract/PyPDF2 pour OCR",
        "Utiliser CLIP ou BLIP pour image embeddings",
        "Créer unified embedding space text+image"
    ]
}

# CRITÈRE 16: Monitoring & Observabilité (2% bonus)
ANALYSIS_RESULTS["detailed_findings"]["16_monitoring"] = {
    "weight": 2,
    "title": "Monitoring & Observabilité",
    "expected": "Traces end-to-end. Métriques précision/coût. Alertes",
    "findings": {
        "monitoring": {
            "status": "MISSING",
            "details": [
                "✗ Pas de distributed tracing",
                "✗ Pas de metrics collection",
                "✗ Pas d'alerting system"
            ]
        }
    },
    "score": 0,
    "max_score": 2,
    "gaps": [
        "Aucune observabilité"
    ],
    "recommendations": [
        "Implémenter OpenTelemetry tracing",
        "Ajouter Prometheus metrics",
        "Configurer Grafana dashboards"
    ]
}

# ==========================================
# CALCUL DES SCORES
# ==========================================

def calculate_scores():
    """Calculer les scores totaux"""
    
    main_scores = []
    bonus_scores = []
    
    for i in range(1, 13):
        key = f"{i}_" + str(list(ANALYSIS_RESULTS["detailed_findings"].keys())[i-1]).split("_", 1)[1]
        if key in ANALYSIS_RESULTS["detailed_findings"]:
            score = ANALYSIS_RESULTS["detailed_findings"][key]["score"]
            max_score = ANALYSIS_RESULTS["detailed_findings"][key]["max_score"]
            weight = ANALYSIS_RESULTS["detailed_findings"][key]["weight"]
            main_scores.append((key, score, max_score, weight))
    
    for i in range(13, 17):
        key = f"{i}_" + str(list(ANALYSIS_RESULTS["detailed_findings"].keys())[i-1]).split("_", 1)[1]
        if key in ANALYSIS_RESULTS["detailed_findings"]:
            score = ANALYSIS_RESULTS["detailed_findings"][key]["score"]
            max_score = ANALYSIS_RESULTS["detailed_findings"][key]["max_score"]
            weight = ANALYSIS_RESULTS["detailed_findings"][key]["weight"]
            bonus_scores.append((key, score, max_score, weight))
    
    # Total principal
    total_main_score = sum(s[1] for s in main_scores)
    total_main_max = sum(s[2] for s in main_scores)
    total_bonus_score = sum(s[1] for s in bonus_scores)
    total_bonus_max = sum(s[2] for s in bonus_scores)
    
    return {
        "main": {
            "score": total_main_score,
            "max": total_main_max,
            "percentage": round(100 * total_main_score / total_main_max, 1)
        },
        "bonus": {
            "score": total_bonus_score,
            "max": total_bonus_max,
            "percentage": round(100 * total_bonus_score / total_bonus_max, 1) if total_bonus_max > 0 else 0
        },
        "total": {
            "score": total_main_score + total_bonus_score,
            "max": total_main_max + total_bonus_max,
            "percentage": round(100 * (total_main_score + total_bonus_score) / (total_main_max + total_bonus_max), 1)
        }
    }

ANALYSIS_RESULTS["scores"]["summary"] = calculate_scores()

# ==========================================
# EXPORT RÉSULTATS
# ==========================================

if __name__ == "__main__":
    import sys
    import io
    
    # Fix encoding for Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n" + "="*80)
    print("TEAM 3 - ANALYSE DETAILLEE GRILLE D'EVALUATION AGENTIC")
    print("="*80)
    
    # Score summary
    summary = ANALYSIS_RESULTS["scores"]["summary"]
    print(f"\n[SCORE RESUME]")
    print(f"  Principal: {summary['main']['score']}/{summary['main']['max']} ({summary['main']['percentage']}%)")
    print(f"  Bonus:     {summary['bonus']['score']}/{summary['bonus']['max']} ({summary['bonus']['percentage']}%)")
    print(f"  TOTAL:     {summary['total']['score']}/{summary['total']['max']} ({summary['total']['percentage']}%)")
    
    print(f"\n[DETAILS PAR CRITERE]\n")
    
    for i in range(1, 17):
        findings = None
        for key, data in ANALYSIS_RESULTS["detailed_findings"].items():
            if key.startswith(f"{i}_"):
                findings = data
                break
        
        if findings:
            if findings["score"] == 0:
                status = "CRITIQUE"
            elif findings["score"] <= findings["max_score"]//3:
                status = "FAIBLE"
            elif findings["score"] <= 2*findings["max_score"]//3:
                status = "PARTIEL"
            else:
                status = "BON"
            print(f"{i:2d}. {findings['title']:40s} {findings['score']:2d}/{findings['max_score']:2d} [{status}]")
    
    print("\n" + "="*80)
    print("SAUVEGARDE RESULTATS...")
    with open("TEAM3_EVALUATION_RESULTS.json", "w", encoding="utf-8") as f:
        json.dump(ANALYSIS_RESULTS, f, ensure_ascii=False, indent=2)
    print("OK - Resultats sauvegardes dans TEAM3_EVALUATION_RESULTS.json")
    print("="*80 + "\n")
