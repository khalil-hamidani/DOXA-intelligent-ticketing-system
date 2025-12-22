# agents/query_analyzer.py
"""Query Analyzer using Agno Team with enhanced entity extraction and reformulation validation.

Components:
- Agent A: Reformulation & keyword extraction with entity extraction
- Agent B: Ticket classification (category, treatment type)
- Reformulation Validator: Validates reformulation against original (min 0.85 similarity)
- Entity Extractor: Extracts domain entities (error codes, product versions, customer types)
"""

from models import Ticket
from typing import Dict, List, Optional
import json
import os
import re
from agno.agent import Agent
from agno.models.mistral import MistralChat
from agno.team import Team
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Load API key
_mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
if _mistral_key:
    os.environ["MISTRALAI_API_KEY"] = _mistral_key

MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")

# Reformulation validation settings
REFORMULATION_SIMILARITY_THRESHOLD = 0.85

# Entity pattern definitions
ENTITY_PATTERNS = {
    "error_code": r'\b(?:ERR|ERROR|CODE|E\d{3,5})\b',  # ERR_*, ERROR_*, CODE*, E123
    "product_version": r'\bv\d+\.\d+(?:\.\d+)?\b|\bversion\s+\d+\.\d+',  # v1.0, version 2.3
    "customer_type": r'\b(?:enterprise|premium|basic|starter|free|trial|paid)\b',
    "component": r'\b(?:API|database|server|client|backend|frontend|auth|payment|billing)\b',
    "os_platform": r'\b(?:Windows|macOS|Linux|iOS|Android|Chrome|Firefox|Safari|Edge)\b',
}


def _create_reformulation_agent() -> Agent:
    """Agent A: Reformulate ticket and extract keywords with domain entities."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.4)
    
    instructions = """You are a ticket analysis expert. Your task is to:
1. Summarize the main issue in one sentence (concise)
2. Reformulate the problem clearly, preserving all key details
3. Extract 5-8 key technical/business terms
4. Identify domain entities:
   - Error codes (e.g., ERR_123, ERROR_TIMEOUT)
   - Product/software versions (e.g., v2.1.3)
   - Customer account types (enterprise, premium, free)
   - System components (API, database, auth)
   - OS/platforms (Windows, iOS, Chrome)

Reformulation should be clearer than original while maintaining accuracy.

Return JSON:
{
    "summary": "one-line summary of the issue",
    "reformulation": "clear and concise problem statement",
    "keywords": ["keyword1", "keyword2", ...],
    "entities": {
        "error_codes": ["ERR_123", ...],
        "product_versions": ["v2.1", ...],
        "customer_type": "enterprise|premium|basic|free",
        "components": ["API", "database"],
        "platforms": ["Windows", "Chrome"]
    },
    "reformulation_notes": "brief explanation of changes"
}"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="ReformulationAgent"
    )
    return agent


def _create_classification_agent() -> Agent:
    """Agent B: Classify ticket type and suggest treatment."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.3)
    
    instructions = """You are a ticket classification expert. Categorize the issue into ONE of:
- technique: Technical/system issues, errors, bugs, crashes
- facturation: Billing, invoicing, payment, subscription
- authentification: Login, access, password, auth errors
- autre: Other issues not fitting above

Also suggest treatment priority and action type.

Return JSON:
{
    "category": "technique|facturation|authentification|autre",
    "expected_treatment": "standard|urgent|escalation",
    "treatment_action": "brief action description",
    "confidence": 0.0-1.0
}"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="ClassificationAgent"
    )
    return agent


def analyze_and_reformulate(ticket: Ticket) -> Dict:
    """Agent A: Summarize, reformulate and extract keywords.
    
    Returns dict with `summary`, `reformulation`, `keywords`, `entities`.
    """
    agent = _create_reformulation_agent()
    
    prompt = f"""Analyze and reformulate this support ticket:
Subject: {ticket.subject}
Description: {ticket.description}

Provide summary, clear reformulation, and extract key terms."""
    
    try:
        response = agent.run(prompt)
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            ticket.summary = result.get("summary", "")
            ticket.reformulation = result.get("reformulation", "")
            ticket.keywords = result.get("keywords", [])
            
            return {
                "summary": ticket.summary,
                "reformulation": ticket.reformulation,
                "keywords": ticket.keywords,
                "entities": result.get("entities", [])
            }
    except Exception as e:
        print(f"Reformulation Agent error: {e}")
    
    # Fallback heuristic
    import re
    text = ticket.description.strip()
    sentences = re.split(r'[\.\n]', text)
    summary = sentences[0].strip() if sentences and sentences[0].strip() else text[:100]
    
    words = [w for w in re.findall(r"\w+", text.lower()) if len(w) > 3]
    keywords: List[str] = list(dict.fromkeys(words))[:8]
    
    ticket.summary = summary
    ticket.reformulation = ticket.subject + " - " + summary
    ticket.keywords = keywords
    
    return {
        "summary": summary,
        "reformulation": summary,
        "keywords": keywords,
        "entities": []
    }


def classify_ticket(ticket: Ticket) -> Dict:
    """Agent B: Classify ticket into category and expected treatment type.
    
    Returns dict with `category` and `expected_treatment`.
    """
    agent = _create_classification_agent()
    
    prompt = f"""Classify this support ticket:
Subject: {ticket.subject}
Description: {ticket.description}
Summary: {ticket.summary or 'N/A'}
Keywords: {', '.join(ticket.keywords or [])}

Determine the category (technique/facturation/authentification/autre) and treatment approach."""
    
    try:
        response = agent.run(prompt)
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            ticket.category = result.get("category", "autre")
            
            return {
                "category": ticket.category,
                "expected_treatment": result.get("expected_treatment", "standard"),
                "treatment_action": result.get("treatment_action", "")
            }
    except Exception as e:
        print(f"Classification Agent error: {e}")
    
    # Fallback heuristic classification
    kws = set((ticket.keywords or []))
    cat = "autre"
    
    if any(w in kws for w in ("facturation", "invoice", "payment", "paiement", "billing")):
        cat = "facturation"
    elif any(w in kws for w in ("error", "bug", "erreur", "panne", "crash", "technique")):
        cat = "technique"
    elif any(w in kws for w in ("accès", "login", "auth", "motdepasse", "password", "authentification")):
        cat = "authentification"
    
    ticket.category = cat
    return {"category": cat, "expected_treatment": "standard", "treatment_action": ""}


def extract_entities(ticket: Ticket, analysis_result: Dict) -> Dict:
    """
    Extract domain entities from ticket using pattern matching and LLM results.
    
    Identifies:
    - Error codes (ERR_*, ERROR_*, E123)
    - Product/software versions (v1.0, version 2.3)
    - Customer account types (enterprise, premium, free)
    - System components (API, database, server)
    - OS/platforms (Windows, macOS, iOS, Chrome)
    
    Args:
        ticket: Ticket object
        analysis_result: Result from analyze_and_reformulate()
        
    Returns:
        Dict with extracted entities by type
    """
    text = (ticket.subject or "") + " " + (ticket.description or "")
    
    # Get entities from LLM if available
    llm_entities = {}
    if "entities" in analysis_result and isinstance(analysis_result["entities"], dict):
        llm_entities = analysis_result["entities"]
    
    # Pattern-based entity extraction (fallback)
    extracted_entities = {
        "error_codes": [],
        "product_versions": [],
        "customer_type": [],
        "components": [],
        "platforms": []
    }
    
    # Extract error codes
    error_codes = re.findall(ENTITY_PATTERNS["error_code"], text, re.IGNORECASE)
    extracted_entities["error_codes"] = list(set(error_codes))
    
    # Extract product versions
    product_versions = re.findall(ENTITY_PATTERNS["product_version"], text, re.IGNORECASE)
    extracted_entities["product_versions"] = list(set(product_versions))
    
    # Extract customer type
    customer_types = re.findall(ENTITY_PATTERNS["customer_type"], text, re.IGNORECASE)
    extracted_entities["customer_type"] = list(set(customer_types))
    
    # Extract components
    components = re.findall(ENTITY_PATTERNS["component"], text, re.IGNORECASE)
    extracted_entities["components"] = list(set(components))
    
    # Extract OS/platforms
    platforms = re.findall(ENTITY_PATTERNS["os_platform"], text, re.IGNORECASE)
    extracted_entities["platforms"] = list(set(platforms))
    
    # Merge with LLM results (LLM takes precedence)
    if llm_entities:
        for key in extracted_entities:
            if key in llm_entities and llm_entities[key]:
                llm_val = llm_entities[key]
                if isinstance(llm_val, list):
                    extracted_entities[key] = list(set(extracted_entities[key] + llm_val))
                else:
                    extracted_entities[key] = list(set(extracted_entities[key] + [str(llm_val)]))
    
    return extracted_entities


def _compute_embedding_similarity(text1: str, text2: str) -> float:
    """
    Compute cosine similarity between two texts using embeddings.
    
    Uses sentence_transformers for embedding generation.
    
    Args:
        text1: Original text
        text2: Reformulated text
        
    Returns:
        Similarity score (0.0-1.0)
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings1 = model.encode(text1, convert_to_tensor=False)
        embeddings2 = model.encode(text2, convert_to_tensor=False)
        
        # Compute cosine similarity
        similarity = np.dot(embeddings1, embeddings2) / (
            np.linalg.norm(embeddings1) * np.linalg.norm(embeddings2)
        )
        
        return float(similarity)
    except Exception as e:
        print(f"Embedding similarity computation failed: {e}")
        return 0.5  # Neutral fallback


def validate_reformulation(
    original: str,
    reformulation: str,
    threshold: float = REFORMULATION_SIMILARITY_THRESHOLD
) -> Dict:
    """
    Validate that reformulation preserves meaning of original.
    
    Uses embedding similarity to ensure reformulated query maintains fidelity.
    
    Args:
        original: Original query text
        reformulation: Reformulated query text
        threshold: Minimum similarity threshold (default 0.85)
        
    Returns:
        Dict with:
        - is_valid: bool (True if similarity >= threshold)
        - similarity: float (0.0-1.0)
        - confidence: float confidence in validation
        - feedback: str validation feedback
    """
    if not original or not reformulation:
        return {
            "is_valid": False,
            "similarity": 0.0,
            "confidence": 1.0,
            "feedback": "Original or reformulation is empty"
        }
    
    similarity = _compute_embedding_similarity(original, reformulation)
    is_valid = similarity >= threshold
    
    feedback = ""
    if is_valid:
        feedback = f"Reformulation preserves meaning well (similarity: {similarity:.2%})"
    else:
        feedback = f"Reformulation may have drifted from original (similarity: {similarity:.2%}, threshold: {threshold:.2%})"
    
    return {
        "is_valid": is_valid,
        "similarity": similarity,
        "confidence": min(similarity / threshold, 1.0),  # Confidence = how close to threshold
        "feedback": feedback
    }


def analyze_and_reformulate_with_validation(ticket: Ticket) -> Dict:
    """
    Enhanced analysis and reformulation with entity extraction and validation.
    
    Performs:
    1. Analysis & reformulation using LLM
    2. Entity extraction (patterns + LLM)
    3. Reformulation validation (embedding similarity)
    
    Args:
        ticket: Ticket to analyze
        
    Returns:
        Dict with: summary, reformulation, keywords, entities, 
                   reformulation_validation, analysis_confidence
    """
    # Step 1: Base analysis
    analysis_result = analyze_and_reformulate(ticket)
    
    # Step 2: Enhanced entity extraction
    entities = extract_entities(ticket, analysis_result)
    
    # Step 3: Reformulation validation
    original_text = ticket.subject + " " + ticket.description
    reformulation_text = analysis_result.get("reformulation", ticket.description)
    reformulation_validation = validate_reformulation(original_text, reformulation_text)
    
    # Combine results
    result = {
        "summary": analysis_result.get("summary", ""),
        "reformulation": analysis_result.get("reformulation", ""),
        "keywords": analysis_result.get("keywords", []),
        "entities": entities,
        "reformulation_validation": reformulation_validation,
        "analysis_confidence": 1.0 if reformulation_validation["is_valid"] else 0.6
    }
    
    return result

