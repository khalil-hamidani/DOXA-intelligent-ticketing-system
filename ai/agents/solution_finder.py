import os
from models import Ticket
from typing import Dict, List, Tuple, Optional
import re
import logging
import json

logger = logging.getLogger(__name__)

KB_ENTRIES: List[Tuple[str, str, str]] = [
    ("kb_fact_1", "facturation", "Pour les questions de facturation, contactez le service financier ou consultez la FAQ facturation."),
    ("kb_tech_1", "technique", "Pour les bugs connus, vérifiez la configuration et redémarrez le service. Si le problème persiste, fournissez les logs."),
    ("kb_auth_1", "authentification", "Pour les problèmes d'accès, réinitialisez votre mot de passe depuis la page de connexion."),
    ("kb_general_1", "autre", "Merci de préciser votre demande pour que nous puissions vous aider efficacement.")
]

# Try to import Chroma retriever (optional)
ChromaRetriever = None
try:
    from kb.retriever import ChromaRetriever
except Exception:
    try:
        from ai.kb.retriever import ChromaRetriever
    except Exception:
        ChromaRetriever = None
else:
    ChromaRetriever = ChromaRetriever

NEGATIVE_WORDS = ["insatisfait", "mécontent", "furieux", "en colère", "pas satisfait", "impossible"]

# Useful regexes
EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.[a-z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{6,12}")
CC_RE = re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b")
IBAN_RE = re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4,30}\b", re.I)
CVV_RE = re.compile(r"\b\d{3,4}\b")

def _lexical_score(entry_text: str, keywords: List[str]) -> float:
    text = entry_text.lower()
    score = 0
    for kw in keywords:
        if kw.lower() in text:
            score += 1
    # normalized lexical score (0..1)
    return min(1.0, score / max(1, len(keywords)))

def _normalize_scores(candidates: List[Dict]) -> List[Dict]:
    if not candidates:
        return candidates
    max_raw = max(c.get("raw_score", 0.0) for c in candidates) or 1.0
    for c in candidates:
        c["score"] = round(min(1.0, c.get("raw_score", 0.0) / max_raw), 3)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates

def find_solution(ticket, top_n: int = 3, team: Optional[str] = None) -> Dict:
    """
    Retrieve top-N KB entries and snippets based on ticket keywords and category.
    Prefer semantic retrieval via Chroma if available; fallback to lexical in-memory KB.
    Returns dict {"results": [ {id, category, text, score, snippet}], "solution_text": str }
    """
    keywords = ticket.keywords or []
    candidates = []

    # Attempt semantic retrieval if Chroma retriever is available and DB exists
    if ChromaRetriever is not None:
        try:
            base_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "kb"))
            chroma_dir = os.path.join(base_dir, "chroma_db")
            if os.path.exists(chroma_dir):
                retriever = ChromaRetriever(persist_dir=chroma_dir)
                docs = retriever.retrieve(" ".join(keywords) if keywords else (ticket.summary or ticket.subject or ""), k=top_n, threshold=0.0)
                for d in docs:
                    meta = d.get("meta", {}) or {}
                    content = d.get("content", "")
                    sim = float(d.get("score", 0.0))
                    candidates.append({
                        "id": meta.get("id") or meta.get("source", "kb") + "_" + str(meta.get("chunk_id", 0)),
                        "category": meta.get("category", "kb"),
                        "text": content,
                        "snippet": content[:200],
                        "raw_score": sim
                    })
        except Exception:
            # fallthrough to lexical below
            candidates = []

    # Fallback / supplementary lexical scoring
    if not candidates:
        for eid, cat, text in KB_ENTRIES:
            raw = 0.2 if (ticket.category and cat == ticket.category) else 0.05
            raw += _lexical_score(text, keywords)
            candidates.append({
                "id": eid,
                "category": cat,
                "text": text,
                "snippet": text[:200],
                "raw_score": raw
            })

    # Normalize scores to 0..1
    candidates = _normalize_scores(candidates)
    results = candidates[:top_n]

    # attach snippets to ticket for evaluator use
    ticket.snippets = [r["snippet"] for r in results]
    solution_text = results[0]["text"] if results else "Aucune solution trouvée dans la KB."
    return {"results": results, "solution_text": solution_text}

def _contains_sensitive(text: str) -> bool:
    if not text:
        return False
    if EMAIL_RE.search(text):
        return True
    if CC_RE.search(text):
        return True
    if IBAN_RE.search(text):
        return True
    if PHONE_RE.search(text):
        return True
    return False

def _mask_pii(text: str) -> str:
    if not text:
        return text
    masked = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    masked = CC_RE.sub("[REDACTED_CC]", masked)
    masked = IBAN_RE.sub("[REDACTED_IBAN]", masked)
    masked = PHONE_RE.sub("[REDACTED_PHONE]", masked)
    # optionally mask CVV-like standalone 3-4 digits near CC context is risky — skip broad CVV masking
    return masked

def evaluate(ticket: Ticket) -> Dict:
    """Evaluate the proposed solution and compute confidence and escalation decision.

    Returns dict: {"confidence": float, "escalate": bool, "reasons": [...], "sensitive": bool, "escalation_context": str}
    """
    reasons: List[str] = []
    priority = (ticket.priority_score or 0)

    base_conf = min(0.9, max(0.2, priority / 120))
    snippet_bonus = 0.0
    if ticket.snippets:
        snippet_bonus = 0.2

    confidence = base_conf + snippet_bonus
    confidence = min(1.0, confidence)

    text = (ticket.description or "").lower()
    negative = any(w in text for w in NEGATIVE_WORDS)
    if negative:
        reasons.append("Ton négatif détecté")
        confidence -= 0.15

    sensitive = _contains_sensitive(ticket.description)
    if sensitive:
        reasons.append("Données sensibles détectées")
        # mask description for storage / further processing
        try:
            ticket.description_masked = _mask_pii(ticket.description)
        except Exception:
            ticket.description_masked = "[MASKING_ERROR]"
        # log structured audit event
        trace_id = getattr(ticket, "trace_id", None)
        audit = {
            "event": "pii_detected",
            "ticket_id": getattr(ticket, "id", None),
            "trace_id": trace_id,
            "reasons": reasons
        }
        logger.info(json.dumps(audit))

    confidence = max(0.0, min(1.0, confidence))

    escalate = False
    escalation_context = None
    if confidence < 0.6:
        escalate = True
        reasons.append("Confiance insuffisante (<60%)")

    if sensitive:
        escalate = True

    if escalate:
        escalation_context = f"Ticket {getattr(ticket,'id',None)} - categorie={getattr(ticket,'category',None)} - score={priority} - snippets={ticket.snippets} - raisons={reasons}"

    ticket.confidence = confidence
    ticket.sensitive = sensitive
    ticket.escalation_context = escalation_context

    return {"confidence": confidence, "escalate": escalate, "reasons": reasons, "sensitive": sensitive, "escalation_context": escalation_context}