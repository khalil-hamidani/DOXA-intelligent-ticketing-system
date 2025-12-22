# agents/evaluator.py
"""
Evaluator Agent - Step 4: Evaluation & Confidence

Responsibilities:
  - Calculate confidence score (0-1.0) based on:
    * RAG pipeline confidence (from snippets/similarity)
    * Priority score (urgency + impact)
    * LLM assessment of solution quality
  - Detect escalation triggers:
    * Low confidence (<60%)
    * Sensitive data (PII)
    * Negative/angry sentiment
  - Provide escalation context (reason + details)

Output:
  {"confidence": float, "escalate": bool, "reasons": List,
   "sensitive": bool, "negative_sentiment": bool, "escalation_reason": str}
"""

from models import Ticket
from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Sensitive data patterns
SENSITIVE_PATTERNS = {
    "email": r"\b[\w.-]+@[\w.-]+\.[a-z]{2,}\b",
    "phone": r"\b\d{9,15}\b",
    "credit_card": r"\b(?:4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}|5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}|3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5})\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "passport": r"\b[A-Z]{2}\d{6,9}\b"
}

NEGATIVE_WORDS = [
    "insatisfait", "mécontent", "furieux", "en colère", "pas satisfait",
    "impossible", "ne fonctionne pas", "erreur", "bug", "cassé",
    "inutile", "nul", "mauvais", "pire", "jamais", "awful", "terrible",
    "frustrated", "angry", "hate", "useless", "broken"
]

CONFIDENCE_THRESHOLD = 0.60  # 60%


def _contains_sensitive_data(text: Optional[str]) -> tuple[bool, List[str]]:
    """
    Detect PII/sensitive data in text.
    
    Returns:
        (contains_sensitive: bool, detected_types: List[str])
    """
    if not text:
        return False, []
    
    detected_types = []
    text_lower = text.lower()
    
    for data_type, pattern in SENSITIVE_PATTERNS.items():
        if re.search(pattern, text):
            detected_types.append(data_type)
    
    return len(detected_types) > 0, detected_types


def _detect_negative_sentiment(text: Optional[str]) -> tuple[bool, List[str]]:
    """
    Detect negative/angry sentiment in text.
    
    Returns:
        (has_negative: bool, detected_words: List[str])
    """
    if not text:
        return False, []
    
    text_lower = text.lower()
    detected_words = [word for word in NEGATIVE_WORDS if word in text_lower]
    
    return len(detected_words) > 0, detected_words


def _calculate_rag_confidence(ticket: Ticket) -> float:
    """
    Calculate confidence from RAG pipeline results.
    
    Factors:
      - Number & quality of snippets
      - Similarity scores of snippets
      - Solution text clarity
    """
    if not hasattr(ticket, 'snippets') or not ticket.snippets:
        return 0.0
    
    # Average similarity score (handle both dict and string snippets)
    similarities = []
    for s in ticket.snippets:
        if isinstance(s, dict):
            similarities.append(s.get("similarity", 0.0))
        else:
            # String snippet - estimate similarity from length
            similarities.append(min(1.0, len(str(s)) / 500))
    
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
    
    # Snippet count bonus (more relevant docs = higher confidence)
    snippet_count = min(len(ticket.snippets), 5)  # Cap at 5
    snippet_bonus = snippet_count * 0.1  # Up to 0.5
    
    rag_conf = (avg_similarity * 0.7) + snippet_bonus  # 70% similarity, 30% count
    rag_conf = min(1.0, rag_conf)
    
    return rag_conf


def _calculate_priority_confidence(ticket: Ticket) -> float:
    """
    Calculate confidence adjustment based on priority.
    
    Logic:
      - Low priority (0-30): Normal processing, confidence neutral
      - Medium priority (30-70): Standard confidence boost
      - High priority (70-100): May indicate urgent issue needing escalation
    """
    priority = getattr(ticket, 'priority_score', 50) or 50
    
    if priority < 30:
        return -0.1  # Low priority, slight penalty (less urgency = less confidence)
    elif priority < 70:
        return 0.0   # Medium priority, neutral
    else:
        return 0.05  # High priority, slight boost (more urgent = more scrutiny)


def evaluate(ticket: Ticket) -> Dict:
    """
    Evaluate proposed solution and determine escalation.
    
    Step 4: Evaluation & Confidence
    
    Returns:
        {
            "confidence": float (0-1.0),
            "escalate": bool,
            "reasons": List[str],
            "sensitive": bool,
            "negative_sentiment": bool,
            "escalation_reason": str or None
        }
    """
    logger.info(f"Evaluating ticket {ticket.id}")
    
    reasons: List[str] = []
    escalation_reason: Optional[str] = None
    
    # ====================================================================
    # CONFIDENCE CALCULATION
    # ====================================================================
    
    # 1. RAG Pipeline Confidence (40% weight)
    rag_conf = _calculate_rag_confidence(ticket)
    logger.debug(f"  RAG confidence: {rag_conf:.2f}")
    
    # 2. Priority Adjustment (10% weight)
    priority_adj = _calculate_priority_confidence(ticket)
    
    # 3. Base confidence from priority score (30% weight)
    priority = getattr(ticket, 'priority_score', 50) or 50
    priority_conf = max(0.2, min(0.8, priority / 100))
    
    # 4. Category alignment bonus (20% weight)
    # If category is clear and solution text exists, boost confidence
    category_bonus = 0.0
    if hasattr(ticket, 'category') and ticket.category != "autre":
        category_bonus = 0.1
    if hasattr(ticket, 'solution_text') and ticket.solution_text:
        category_bonus += 0.1
    
    # Final confidence calculation
    confidence = (
        rag_conf * 0.40 +
        priority_conf * 0.30 +
        category_bonus * 0.20 +
        priority_adj * 0.10
    )
    confidence = max(0.0, min(1.0, confidence))
    
    logger.info(f"  Calculated confidence: {confidence:.2%}")
    
    # ====================================================================
    # ESCALATION TRIGGER DETECTION
    # ====================================================================
    
    should_escalate = False
    
    # Trigger 1: Low confidence (<60%)
    if confidence < CONFIDENCE_THRESHOLD:
        should_escalate = True
        escalation_reason = f"Confidence insuffisante ({confidence:.2%} < {CONFIDENCE_THRESHOLD:.2%})"
        reasons.append(escalation_reason)
        logger.warning(f"  ⚠️ LOW CONFIDENCE: {escalation_reason}")
    
    # Trigger 2: Sensitive data detected
    has_sensitive, sensitive_types = _contains_sensitive_data(
        getattr(ticket, 'description', '')
    )
    if has_sensitive:
        should_escalate = True
        if not escalation_reason:
            escalation_reason = f"Données sensibles détectées ({', '.join(sensitive_types)})"
        reasons.append(f"Données sensibles: {', '.join(sensitive_types)}")
        logger.warning(f"  ⚠️ SENSITIVE DATA: {sensitive_types}")
    
    # Trigger 3: Negative sentiment detected
    has_negative, negative_words = _detect_negative_sentiment(
        getattr(ticket, 'description', '')
    )
    if has_negative:
        if confidence < 0.75:  # Only escalate for low confidence + negative
            should_escalate = True
            if not escalation_reason:
                escalation_reason = f"Ton négatif + confiance insuffisante"
            reasons.append(f"Ton négatif détecté ({', '.join(negative_words[:3])})")
            logger.warning(f"  ⚠️ NEGATIVE SENTIMENT: {negative_words}")
        else:
            # Just note it if confidence is high
            reasons.append(f"Ton négatif détecté")
    
    # ====================================================================
    # PREPARE RESPONSE
    # ====================================================================
    
    result = {
        "confidence": confidence,
        "escalate": should_escalate,
        "reasons": reasons,
        "sensitive": has_sensitive,
        "negative_sentiment": has_negative,
        "escalation_reason": escalation_reason
    }
    
    # Store in ticket for later reference
    ticket.confidence = confidence
    ticket.sensitive = has_sensitive
    ticket.negative_sentiment = has_negative
    ticket.escalation_context = escalation_reason
    
    logger.info(f"  Decision: {'ESCALATE' if should_escalate else 'RESPOND'}")
    
    return result

