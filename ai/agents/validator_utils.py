"""
Validation utilities for agent outputs.
"""

import json
from typing import Dict, Any, List
from .config import (
    VALID_CATEGORIES,
    VALID_PRIORITIES,
    VALID_TREATMENT_TYPES,
    VALID_SEVERITY_LEVELS,
    MIN_SCORE,
    MAX_SCORE,
)


# ============================================================================
# JSON Parsing
# ============================================================================

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract JSON object from text response.
    
    Args:
        text: Response text that may contain JSON
        
    Returns:
        Parsed JSON dict or empty dict if not found
    """
    try:
        # Find first { and last }
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        
        if json_start == -1 or json_end <= json_start:
            return {}
        
        json_str = text[json_start:json_end]
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return {}


# ============================================================================
# Validator Output
# ============================================================================

def validate_validator_output(result: Dict[str, Any]) -> bool:
    """Validate validator agent output schema.
    
    Args:
        result: Output dict from validator
        
    Returns:
        True if valid schema
    """
    required = ["valid", "reasons"]
    
    if not isinstance(result, dict):
        return False
    
    if not all(k in result for k in required):
        return False
    
    if not isinstance(result["valid"], bool):
        return False
    
    if not isinstance(result.get("reasons", []), list):
        return False
    
    return True


def normalize_validator_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize validator output to ensure correct types."""
    normalized = {
        "valid": bool(result.get("valid", False)),
        "reasons": list(result.get("reasons", [])),
        "confidence": float(result.get("confidence", 0.5))
    }
    normalized["confidence"] = max(0.0, min(1.0, normalized["confidence"]))
    return normalized


# ============================================================================
# Scorer Output
# ============================================================================

def validate_scorer_output(result: Dict[str, Any]) -> bool:
    """Validate scorer agent output schema."""
    required = ["score", "priority"]
    
    if not isinstance(result, dict):
        return False
    
    if not all(k in result for k in required):
        return False
    
    if not isinstance(result["score"], (int, float)):
        return False
    
    if result["priority"] not in VALID_PRIORITIES:
        return False
    
    if not (MIN_SCORE <= result["score"] <= MAX_SCORE):
        return False
    
    return True


def normalize_scorer_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize scorer output to ensure correct types."""
    score = int(result.get("score", 50))
    score = max(MIN_SCORE, min(MAX_SCORE, score))
    
    priority = result.get("priority", "medium")
    if priority not in VALID_PRIORITIES:
        # Infer from score
        if score >= 70:
            priority = "high"
        elif score >= 35:
            priority = "medium"
        else:
            priority = "low"
    
    normalized = {
        "score": score,
        "priority": priority,
        "reasoning": str(result.get("reasoning", ""))
    }
    return normalized


# ============================================================================
# Query Analyzer Output
# ============================================================================

def validate_reformulation_output(result: Dict[str, Any]) -> bool:
    """Validate query analyzer (Agent A) output schema."""
    required = ["summary", "reformulation", "keywords"]
    
    if not isinstance(result, dict):
        return False
    
    if not all(k in result for k in required):
        return False
    
    if not isinstance(result["summary"], str):
        return False
    
    if not isinstance(result["reformulation"], str):
        return False
    
    if not isinstance(result.get("keywords", []), list):
        return False
    
    return True


def normalize_reformulation_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize reformulation output."""
    normalized = {
        "summary": str(result.get("summary", ""))[:500],
        "reformulation": str(result.get("reformulation", ""))[:1000],
        "keywords": list(result.get("keywords", []))[:10],
        "entities": list(result.get("entities", []))[:10]
    }
    return normalized


def validate_classification_output(result: Dict[str, Any]) -> bool:
    """Validate query analyzer (Agent B) output schema."""
    required = ["category"]
    
    if not isinstance(result, dict):
        return False
    
    if not all(k in result for k in required):
        return False
    
    if result["category"] not in VALID_CATEGORIES:
        return False
    
    return True


def normalize_classification_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize classification output."""
    category = result.get("category", "autre")
    if category not in VALID_CATEGORIES:
        category = "autre"
    
    normalized = {
        "category": category,
        "expected_treatment": str(result.get("expected_treatment", "standard")),
        "treatment_action": str(result.get("treatment_action", ""))[:500]
    }
    return normalized


# ============================================================================
# Classifier Model Output
# ============================================================================

def validate_classifier_output(result: Dict[str, Any]) -> bool:
    """Validate classifier model output schema."""
    required = ["category", "treatment_type", "severity"]
    
    if not isinstance(result, dict):
        return False
    
    if not all(k in result for k in required):
        return False
    
    if result["category"] not in VALID_CATEGORIES:
        return False
    
    if result["treatment_type"] not in VALID_TREATMENT_TYPES:
        return False
    
    if result["severity"] not in VALID_SEVERITY_LEVELS:
        return False
    
    return True


def normalize_classifier_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize classifier output."""
    # Ensure valid values
    category = result.get("category", "autre")
    if category not in VALID_CATEGORIES:
        category = "autre"
    
    treatment_type = result.get("treatment_type", "standard")
    if treatment_type not in VALID_TREATMENT_TYPES:
        treatment_type = "standard"
    
    severity = result.get("severity", "medium")
    if severity not in VALID_SEVERITY_LEVELS:
        severity = "medium"
    
    confidence = float(result.get("confidence", 0.7))
    confidence = max(0.0, min(1.0, confidence))
    
    normalized = {
        "category": category,
        "treatment_type": treatment_type,
        "severity": severity,
        "reasoning": str(result.get("reasoning", ""))[:500],
        "confidence": confidence,
        "required_skills": list(result.get("required_skills", []))[:10]
    }
    return normalized


# ============================================================================
# Integration
# ============================================================================

def validate_and_normalize_output(
    agent_name: str,
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate and normalize output based on agent type.
    
    Args:
        agent_name: Name of agent (validator, scorer, reformulator, classifier, etc.)
        result: Raw output dict
        
    Returns:
        Normalized output dict
    """
    if agent_name == "validator":
        if validate_validator_output(result):
            return normalize_validator_output(result)
    elif agent_name == "scorer":
        if validate_scorer_output(result):
            return normalize_scorer_output(result)
    elif agent_name == "reformulator":
        if validate_reformulation_output(result):
            return normalize_reformulation_output(result)
    elif agent_name == "classifier":
        if validate_classification_output(result):
            return normalize_classification_output(result)
    elif agent_name == "classifier_model":
        if validate_classifier_output(result):
            return normalize_classifier_output(result)
    
    # Default: return empty normalized for agent type
    return result

MISTRAL_API_KEY=jhP09mKu30IaiOqzopwG0jdujcgQZbtg
