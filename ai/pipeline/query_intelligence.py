# pipeline/query_intelligence.py
"""Query Intelligence Layer: Validation, Augmentation, Analysis, Planning.

This module handles:
1. Query validation (sanity checks)
2. Query augmentation (rephrasing, expansion, synonyms)
3. Query summarization
4. Keyword extraction
5. Multi-class semantic classification
6. Query routing based on semantic classes
"""

from models import Ticket
from typing import Dict, List, Tuple, Optional
import json
import os
import re
from agno.agent import Agent
from agno.models.mistral import MistralChat
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

_mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
if _mistral_key:
    os.environ["MISTRALAI_API_KEY"] = _mistral_key

MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")

# Semantic class definitions
SEMANTIC_CLASSES = {
    "technique": {
        "keywords": ["error", "bug", "crash", "erreur", "panne", "configuration", "api", "système"],
        "description": "Technical issues, bugs, system errors"
    },
    "facturation": {
        "keywords": ["facture", "invoice", "paiement", "payment", "subscription", "billing", "coût", "prix"],
        "description": "Billing, invoicing, payment, pricing"
    },
    "authentification": {
        "keywords": ["login", "password", "accès", "access", "auth", "motdepasse", "connexion", "compte"],
        "description": "Authentication, access, login issues"
    },
    "autre": {
        "keywords": ["autre", "autre chose", "divers", "misc"],
        "description": "Other issues"
    }
}


def _create_augmentation_agent() -> Agent:
    """Create agent for query augmentation and expansion."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.5)
    
    instructions = """You are a query augmentation expert. Your task is to:
1. Rephrase the query in clearer terms
2. Expand with synonyms and related concepts
3. Identify implicit context or assumptions

Return JSON:
{
    "original": "original query",
    "rephrased": "clearer version",
    "expansion": ["related term 1", "related term 2", ...],
    "synonyms": ["synonym1", "synonym2", ...],
    "implicit_context": "inferred context or assumptions"
}"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="QueryAugmentationAgent"
    )
    return agent


def _create_multiclass_classifier_agent() -> Agent:
    """Create agent for multi-class semantic classification."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.4)
    
    instructions = """You are a semantic classification expert. Classify the ticket against ALL relevant semantic classes:

SEMANTIC CLASSES:
1. technique: Technical issues, bugs, system errors, configuration problems
2. facturation: Billing, invoices, payments, subscriptions, pricing
3. authentification: Authentication, access control, login, passwords
4. autre: All other issues not fitting above

For each class, provide:
- Relevance score (0.0-1.0): How well the ticket matches this class
- Confidence (0.0-1.0): How certain you are about this classification

Return JSON:
{
    "primary_class": "class with highest score",
    "primary_score": 0.0-1.0,
    "class_scores": {
        "technique": {"score": 0.0-1.0, "confidence": 0.0-1.0},
        "facturation": {"score": 0.0-1.0, "confidence": 0.0-1.0},
        "authentification": {"score": 0.0-1.0, "confidence": 0.0-1.0},
        "autre": {"score": 0.0-1.0, "confidence": 0.0-1.0}
    },
    "reasoning": "explanation of classification"
}"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="MulticlassClassifier"
    )
    return agent


class QueryValidator:
    """Query validation with configurable rules."""
    
    def __init__(self, min_subject_length: int = 5, min_description_length: int = 20):
        self.min_subject_length = min_subject_length
        self.min_description_length = min_description_length
    
    def validate(self, ticket: Ticket) -> Dict:
        """Validate query with sanity checks.
        
        Returns: {"valid": bool, "reasons": List[str], "signals": Dict}
        """
        reasons = []
        signals = {}
        
        # Subject checks
        if not ticket.subject or len(ticket.subject.strip()) < self.min_subject_length:
            reasons.append(f"Subject too short (min {self.min_subject_length} chars)")
            signals["empty_subject"] = True
        
        # Description checks
        if not ticket.description or len(ticket.description.strip()) < self.min_description_length:
            reasons.append(f"Description too short (min {self.min_description_length} chars)")
            signals["empty_description"] = True
        
        # Low-signal detection (e.g., only whitespace or URLs)
        desc_text = (ticket.description or "").strip()
        if desc_text and re.match(r"^https?://", desc_text):
            reasons.append("Description is only a URL (needs context)")
            signals["low_signal"] = True
        
        # Excessive capitalization (spam indicator)
        if desc_text and len(desc_text) > 20:
            caps_ratio = sum(1 for c in desc_text if c.isupper()) / len(desc_text)
            if caps_ratio > 0.5:
                signals["spam_indicator"] = True
        
        valid = len(reasons) == 0
        return {"valid": valid, "reasons": reasons, "signals": signals}


class QueryAugmenter:
    """Query augmentation: rephrasing, expansion, synonyms."""
    
    def augment(self, ticket: Ticket) -> Dict:
        """Augment query with rephrasing and expansion.
        
        Returns: {"rephrased": str, "expansion": List[str], "synonyms": List[str], "implicit_context": str}
        """
        agent = _create_augmentation_agent()
        
        prompt = f"""Augment and expand this ticket:
Subject: {ticket.subject}
Description: {ticket.description}

Provide rephrasing, expansion, synonyms, and inferred context."""
        
        try:
            response = agent.run(prompt)
            response_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                return {
                    "rephrased": result.get("rephrased", ticket.description),
                    "expansion": result.get("expansion", []),
                    "synonyms": result.get("synonyms", []),
                    "implicit_context": result.get("implicit_context", "")
                }
        except Exception as e:
            print(f"Query augmentation error: {e}")
        
        # Fallback: simple expansion based on keywords
        return {
            "rephrased": ticket.description,
            "expansion": ticket.keywords or [],
            "synonyms": [],
            "implicit_context": ""
        }


class MulticlassClassifier:
    """Multi-class semantic classification with per-class scoring."""
    
    def __init__(self, threshold: float = 0.3):
        """Initialize with relevance threshold.
        
        Args:
            threshold: Minimum score to include a class as relevant
        """
        self.threshold = threshold
    
    def classify(self, ticket: Ticket) -> Dict:
        """Classify ticket against all semantic classes.
        
        Returns: {
            "primary_class": str,
            "primary_score": float,
            "relevant_classes": List[str],  # All classes above threshold
            "class_scores": {class: {score, confidence}},
            "routing": str  # Route suggestion
        }
        """
        agent = _create_multiclass_classifier_agent()
        
        prompt = f"""Classify this ticket:
Subject: {ticket.subject}
Description: {ticket.description}
Keywords: {', '.join(ticket.keywords or [])}

Provide multi-class scores for all semantic classes."""
        
        try:
            response = agent.run(prompt)
            response_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                class_scores = result.get("class_scores", {})
                relevant = [cls for cls, info in class_scores.items() 
                           if info.get("score", 0) >= self.threshold]
                
                primary = result.get("primary_class", "autre")
                primary_score = result.get("primary_score", 0.5)
                
                # Route based on primary class and score
                routing = self._compute_routing(primary, primary_score, relevant)
                
                return {
                    "primary_class": primary,
                    "primary_score": primary_score,
                    "relevant_classes": relevant,
                    "class_scores": class_scores,
                    "routing": routing,
                    "reasoning": result.get("reasoning", "")
                }
        except Exception as e:
            print(f"Multi-class classification error: {e}")
        
        # Fallback: heuristic classification
        return self._fallback_multiclass_classify(ticket)
    
    def _compute_routing(self, primary: str, score: float, relevant: List[str]) -> str:
        """Compute routing strategy based on classification.
        
        Returns routing suggestion: "vector_search" | "kb_lookup" | "escalate"
        """
        if primary == "technique" and score > 0.8:
            return "vector_search"
        elif primary == "facturation":
            return "kb_lookup"  # Billing handled by templates
        elif primary == "authentification":
            return "kb_lookup"  # Auth handled by templates
        elif len(relevant) >= 2:
            return "vector_search"  # Ambiguous, use semantic retrieval
        else:
            return "vector_search"  # Default to semantic search
    
    def _fallback_multiclass_classify(self, ticket: Ticket) -> Dict:
        """Fallback heuristic multi-class classification."""
        kws = set((ticket.keywords or []))
        text_lower = (ticket.description or "").lower()
        
        scores = {}
        for cls_name, cls_info in SEMANTIC_CLASSES.items():
            keyword_matches = sum(1 for kw in cls_info["keywords"] if kw in text_lower)
            score = min(1.0, keyword_matches / max(1, len(cls_info["keywords"])))
            scores[cls_name] = {"score": score, "confidence": score * 0.7}
        
        primary = max(scores, key=lambda x: scores[x]["score"])
        primary_score = scores[primary]["score"]
        relevant = [cls for cls, info in scores.items() if info["score"] >= self.threshold]
        
        return {
            "primary_class": primary,
            "primary_score": primary_score,
            "relevant_classes": relevant,
            "class_scores": scores,
            "routing": self._compute_routing(primary, primary_score, relevant),
            "reasoning": "Fallback heuristic classification"
        }


class QueryPlanner:
    """Query planning: routes and strategies based on classification."""
    
    def plan(self, ticket: Ticket, classification: Dict) -> Dict:
        """Generate query plan with retrieval strategy.
        
        Returns: {
            "primary_route": str,
            "fallback_routes": List[str],
            "search_query": str,
            "search_params": {k: v},
            "expected_output_type": str
        }
        """
        primary_route = classification.get("routing", "vector_search")
        primary_class = classification.get("primary_class", "autre")
        relevant_classes = classification.get("relevant_classes", [primary_class])
        
        # Build search query from augmented terms
        search_query = f"{ticket.summary or ticket.subject}"
        if ticket.keywords:
            search_query += " " + " ".join(ticket.keywords[:5])
        
        # Determine fallback routes
        if primary_route == "vector_search":
            fallback = ["kb_lookup"]
        else:
            fallback = ["vector_search"]
        
        # Set search parameters based on classification
        search_params = {
            "semantic_classes": relevant_classes,
            "top_k": 5,
            "similarity_threshold": 0.4,
            "filter_by_category": primary_class
        }
        
        # Expected output: contextualized solution or escalation
        expected_output_type = "contextualized_solution" if primary_class != "autre" else "escalation"
        
        return {
            "primary_route": primary_route,
            "fallback_routes": fallback,
            "search_query": search_query,
            "search_params": search_params,
            "expected_output_type": expected_output_type,
            "routing_reason": f"Primary class: {primary_class} (score: {classification.get('primary_score', 0):.2f})"
        }


def process_query_intelligence(ticket: Ticket, augment: bool = True) -> Dict:
    """Run full query intelligence pipeline.
    
    Returns: {
        "validation": {...},
        "augmentation": {...},
        "summary": str,
        "keywords": List[str],
        "classification": {...},
        "plan": {...}
    }
    """
    # Step 1: Validate
    validator = QueryValidator()
    validation = validator.validate(ticket)
    
    result = {
        "validation": validation,
        "augmentation": {},
        "summary": ticket.summary or ticket.subject,
        "keywords": ticket.keywords or [],
        "classification": {},
        "plan": {}
    }
    
    if not validation.get("valid"):
        return result
    
    # Step 2: Augment (optional)
    if augment:
        augmenter = QueryAugmenter()
        result["augmentation"] = augmenter.augment(ticket)
    
    # Step 3: Multi-class classification
    classifier = MulticlassClassifier(threshold=0.3)
    result["classification"] = classifier.classify(ticket)
    
    # Step 4: Query planning
    planner = QueryPlanner()
    result["plan"] = planner.plan(ticket, result["classification"])
    
    return result
