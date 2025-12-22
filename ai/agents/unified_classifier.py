"""
Unified Semantic Classifier

Consolidates multiple classification systems into a single semantic taxonomy
with confidence scores per class.

SEMANTIC TAXONOMY:
- Primary Category (technique, facturation, authentification, autre)
- Severity Level (low, medium, high, critical)
- Treatment Type (standard, priority, escalation, urgent)
- Required Skills (array of specialist skills)

Provides multi-dimensional confidence scores for better decision making.
"""

from models import Ticket
from typing import Dict, List, Tuple, Optional
import json
import os
from agno.agent import Agent
from agno.models.mistral import MistralChat
from dotenv import load_dotenv, find_dotenv
from dataclasses import dataclass
import re

load_dotenv(find_dotenv())

# Load API key
_mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
if _mistral_key:
    os.environ["MISTRALAI_API_KEY"] = _mistral_key

MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")

# Unified semantic taxonomy
SEMANTIC_CATEGORIES = {
    "technique": {
        "description": "Technical issues (bugs, errors, crashes, system problems)",
        "keywords": ["error", "bug", "crash", "fail", "not working", "erreur", "panne", "système"],
        "sub_categories": ["bug", "system_issue", "performance", "compatibility"]
    },
    "facturation": {
        "description": "Billing/payment issues (invoices, pricing, charges, subscriptions)",
        "keywords": ["invoice", "payment", "billing", "price", "charge", "facturation", "paiement"],
        "sub_categories": ["invoice", "payment_issue", "pricing_question", "refund"]
    },
    "authentification": {
        "description": "Access/login issues (password reset, account access, permissions)",
        "keywords": ["login", "password", "access", "auth", "account", "connexion", "mot de passe"],
        "sub_categories": ["login_issue", "password_reset", "permissions", "account_access"]
    },
    "feature_request": {
        "description": "Feature requests and enhancement suggestions",
        "keywords": ["request", "feature", "enhancement", "would like", "could you add"],
        "sub_categories": ["new_feature", "enhancement", "improvement"]
    },
    "autre": {
        "description": "Other issues not fitting above categories",
        "keywords": [],
        "sub_categories": []
    }
}

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]
TREATMENT_TYPES = ["standard", "priority", "escalation", "urgent"]


@dataclass
class ClassificationResult:
    """Unified classification result with multi-dimensional confidence."""
    
    primary_category: str  # Main semantic category
    confidence_category: float  # Confidence in primary category (0.0-1.0)
    
    severity: str  # Severity level (low/medium/high/critical)
    confidence_severity: float  # Confidence in severity (0.0-1.0)
    
    treatment_type: str  # Treatment type (standard/priority/escalation/urgent)
    confidence_treatment: float  # Confidence in treatment (0.0-1.0)
    
    required_skills: List[str]  # Specialist skills needed
    confidence_skills: float  # Confidence in skill requirements (0.0-1.0)
    
    reasoning: str  # Explanation for classification
    
    # Additional metadata
    sub_category: Optional[str] = None
    alternative_categories: Optional[List[Tuple[str, float]]] = None  # Ranked alternatives
    
    def overall_confidence(self) -> float:
        """Calculate weighted overall confidence score."""
        # Weight: category (40%), severity (25%), treatment (20%), skills (15%)
        return (
            self.confidence_category * 0.40 +
            self.confidence_severity * 0.25 +
            self.confidence_treatment * 0.20 +
            self.confidence_skills * 0.15
        )


def _create_unified_classifier_agent() -> Agent:
    """Create LLM agent for unified semantic classification."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.3)
    
    instructions = """You are a master ticket classifier. Your task is to perform unified semantic classification:

CATEGORIES (with examples):
1. technique: bugs, errors, crashes, system failures, performance issues
2. facturation: invoices, payments, billing disputes, pricing questions
3. authentification: login failures, password issues, account access, permissions
4. feature_request: new feature suggestions, enhancements, improvements
5. autre: anything else

For each ticket, provide:
1. Primary category with confidence (0.0-1.0)
2. Severity level (low/medium/high/critical) with confidence
3. Treatment type (standard/priority/escalation/urgent) with confidence
4. Required skills (technical, billing, account management, management)
5. Sub-category (more specific classification)
6. Alternative categories (ranked by likelihood)
7. Clear reasoning

Return JSON:
{
    "primary_category": "technique|facturation|authentification|feature_request|autre",
    "confidence_category": 0.0-1.0,
    "sub_category": "more specific type",
    "alternative_categories": [
        {"category": "facturation", "confidence": 0.15},
        {"category": "autre", "confidence": 0.05}
    ],
    "severity": "low|medium|high|critical",
    "confidence_severity": 0.0-1.0,
    "treatment_type": "standard|priority|escalation|urgent",
    "confidence_treatment": 0.0-1.0,
    "required_skills": ["skill1", "skill2"],
    "confidence_skills": 0.0-1.0,
    "reasoning": "detailed explanation"
}"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="UnifiedClassifier"
    )
    return agent


def classify_unified(ticket: Ticket) -> ClassificationResult:
    """
    Perform unified semantic classification on a ticket.
    
    Args:
        ticket: Ticket object with subject, description, keywords
    
    Returns:
        ClassificationResult with multi-dimensional confidence scores
    """
    agent = _create_unified_classifier_agent()
    
    # Prepare context
    prompt = f"""Classify this support ticket using unified semantic taxonomy:

SUBJECT: {ticket.subject}
DESCRIPTION: {ticket.description}
KEYWORDS: {', '.join(ticket.keywords or [])}
PRIORITY SCORE: {ticket.priority_score or 'N/A'}
CLIENT: {ticket.client_name}

Perform comprehensive unified classification."""
    
    try:
        response = agent.run(prompt)
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # Parse alternative categories
            alt_cats = None
            if "alternative_categories" in result and result["alternative_categories"]:
                alt_cats = [
                    (cat["category"], float(cat.get("confidence", 0)))
                    for cat in result["alternative_categories"]
                ]
            
            classification = ClassificationResult(
                primary_category=result.get("primary_category", "autre"),
                confidence_category=float(result.get("confidence_category", 0.5)),
                severity=result.get("severity", "medium"),
                confidence_severity=float(result.get("confidence_severity", 0.5)),
                treatment_type=result.get("treatment_type", "standard"),
                confidence_treatment=float(result.get("confidence_treatment", 0.5)),
                required_skills=result.get("required_skills", []),
                confidence_skills=float(result.get("confidence_skills", 0.5)),
                reasoning=result.get("reasoning", ""),
                sub_category=result.get("sub_category"),
                alternative_categories=alt_cats
            )
            
            # Update ticket with primary category
            ticket.category = classification.primary_category
            
            return classification
            
    except json.JSONDecodeError as e:
        print(f"JSON parse error in unified classifier: {e}")
    except Exception as e:
        print(f"Unified classifier LLM error: {e}")
    
    # FALLBACK HEURISTIC CLASSIFICATION
    return _classify_heuristic(ticket)


def _classify_heuristic(ticket: Ticket) -> ClassificationResult:
    """
    Fallback heuristic classification when LLM fails.
    
    Uses keyword matching and pattern detection.
    """
    text = (ticket.description or "" + " " + ticket.subject or "").lower()
    keywords = set([k.lower() for k in (ticket.keywords or [])])
    
    # Score each category
    category_scores = {}
    for category, config in SEMANTIC_CATEGORIES.items():
        score = 0.0
        matches = 0
        for keyword in config["keywords"]:
            if keyword in text or keyword in keywords:
                score += 0.3
                matches += 1
        
        # Boost score if multiple matches
        if matches > 1:
            score *= (1 + matches * 0.1)
        
        category_scores[category] = min(score, 1.0)
    
    # Determine primary category
    primary_category = max(category_scores, key=category_scores.get)
    confidence_category = category_scores[primary_category]
    
    # Determine severity based on keywords
    severity = "medium"
    confidence_severity = 0.6
    if any(w in text for w in ["critical", "urgent", "emergency", "critical issue", "down", "broken"]):
        severity = "critical"
        confidence_severity = 0.8
    elif any(w in text for w in ["high", "important", "asap", "quickly"]):
        severity = "high"
        confidence_severity = 0.7
    elif any(w in text for w in ["low", "minor", "small", "trivial"]):
        severity = "low"
        confidence_severity = 0.7
    
    # Determine treatment type
    treatment_type = "standard"
    confidence_treatment = 0.6
    priority_score = ticket.priority_score or 0
    
    if priority_score >= 80 or severity == "critical":
        treatment_type = "urgent"
        confidence_treatment = 0.8
    elif priority_score >= 60 or severity == "high":
        treatment_type = "priority"
        confidence_treatment = 0.7
    elif any(w in text for w in ["escalate", "manager", "supervisor", "specialist"]):
        treatment_type = "escalation"
        confidence_treatment = 0.7
    
    # Determine required skills
    required_skills = []
    confidence_skills = 0.5
    
    if primary_category == "technique":
        required_skills = ["technical_support", "debugging"]
        confidence_skills = 0.8
    elif primary_category == "facturation":
        required_skills = ["billing", "financial_knowledge"]
        confidence_skills = 0.8
    elif primary_category == "authentification":
        required_skills = ["account_management", "security"]
        confidence_skills = 0.7
    elif primary_category == "feature_request":
        required_skills = ["product_management", "development"]
        confidence_skills = 0.6
    
    # Alternative categories (sorted by score)
    sorted_categories = sorted(
        [(cat, score) for cat, score in category_scores.items() if cat != primary_category],
        key=lambda x: x[1],
        reverse=True
    )
    alternative_categories = sorted_categories[:2] if sorted_categories else None
    
    ticket.category = primary_category
    
    return ClassificationResult(
        primary_category=primary_category,
        confidence_category=confidence_category,
        severity=severity,
        confidence_severity=confidence_severity,
        treatment_type=treatment_type,
        confidence_treatment=confidence_treatment,
        required_skills=required_skills,
        confidence_skills=confidence_skills,
        reasoning=f"Heuristic classification: {primary_category} (severity={severity}, treatment={treatment_type})",
        alternative_categories=alternative_categories
    )


def get_classification_explanation(result: ClassificationResult) -> str:
    """
    Generate human-readable explanation of classification.
    
    Args:
        result: ClassificationResult object
        
    Returns:
        Human-readable explanation string
    """
    overall = result.overall_confidence()
    
    explanation = f"""
CLASSIFICATION SUMMARY:
- Category: {result.primary_category} (confidence: {result.confidence_category:.1%})
- Severity: {result.severity} (confidence: {result.confidence_severity:.1%})
- Treatment: {result.treatment_type} (confidence: {result.confidence_treatment:.1%})
- Skills Needed: {', '.join(result.required_skills) if result.required_skills else 'General support'}
- Overall Confidence: {overall:.1%}

REASONING:
{result.reasoning}

ALTERNATIVES:
"""
    if result.alternative_categories:
        for alt_cat, alt_conf in result.alternative_categories:
            explanation += f"\n- {alt_cat}: {alt_conf:.1%}"
    else:
        explanation += "\nNone"
    
    return explanation
