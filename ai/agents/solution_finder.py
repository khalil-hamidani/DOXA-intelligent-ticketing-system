import os
from models import Ticket
from typing import Dict, List, Tuple, Optional
import re
import logging
import json

logger = logging.getLogger(__name__)

# Try to load environment variables
try:
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())
except ImportError:
    pass

# LLM for answer generation
_answer_agent = None


def _get_answer_agent():
    """Get or create the LLM agent for answer generation."""
    global _answer_agent
    if _answer_agent is not None:
        return _answer_agent

    try:
        from agno.agent import Agent
        from agno.models.mistral import MistralChat

        _mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get(
            "MISTRALAI_API_KEY"
        )
        if _mistral_key:
            os.environ["MISTRALAI_API_KEY"] = _mistral_key

        MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")
        mistral_model = MistralChat(id=MODEL_ID, temperature=0.3)

        instructions = """You are a helpful customer support assistant for Doxa, a SaaS project management platform.
Your task is to answer user questions based ONLY on the provided knowledge base context.

Rules:
1. Answer in the SAME LANGUAGE as the question (French if question is in French)
2. Be concise and direct - answer the specific question asked
3. If the context doesn't contain relevant information, say so honestly
4. Do NOT make up information not in the context
5. Format your answer clearly, using bullet points if listing multiple items
6. If the question is completely unrelated to Doxa or project management, politely indicate that"""

        _answer_agent = Agent(
            model=mistral_model, instructions=instructions, name="AnswerAgent"
        )
        return _answer_agent
    except Exception as e:
        logger.warning(f"Could not create answer agent: {e}")
        return None


def generate_answer_from_context(question: str, kb_context: List[str]) -> Optional[str]:
    """Use LLM to generate a proper answer based on KB context.

    Args:
        question: The user's question
        kb_context: List of relevant KB snippets

    Returns:
        Generated answer string or None if failed
    """
    agent = _get_answer_agent()
    if not agent:
        return None

    context_text = "\n\n---\n\n".join(kb_context[:5])  # Use top 5 context chunks

    prompt = f"""Based on the following knowledge base context, answer the user's question.

KNOWLEDGE BASE CONTEXT:
{context_text}

USER QUESTION: {question}

Provide a clear, direct answer based on the context above. If the context doesn't contain relevant information for this specific question, say so."""

    try:
        response = agent.run(prompt)
        response_text = (
            str(response.content) if hasattr(response, "content") else str(response)
        )

        # Clean up the response
        response_text = response_text.strip()
        if response_text:
            return response_text
    except Exception as e:
        logger.error(f"Answer generation error: {e}")

    return None


KB_ENTRIES: List[Tuple[str, str, str]] = [
    # Billing / Facturation
    (
        "kb_fact_1",
        "facturation",
        "Pour les questions de facturation, contactez le service financier ou consultez la FAQ facturation dans votre espace client.",
    ),
    (
        "kb_fact_2",
        "facturation",
        "Pour un changement de forfait ou upgrade, le montant sera calculé au prorata. Connectez-vous à votre espace client > Abonnement > Changer de forfait.",
    ),
    (
        "kb_fact_3",
        "facturation",
        "Les remboursements sont traités sous 5-10 jours ouvrés. Vérifiez votre relevé bancaire après ce délai.",
    ),
    (
        "kb_fact_4",
        "billing",
        "For billing inquiries, check your invoice in the customer portal or contact our billing team.",
    ),
    (
        "kb_fact_5",
        "billing",
        "Plan upgrades are prorated. The credit for unused days will be applied to your new plan.",
    ),
    # Technical / Technique
    (
        "kb_tech_1",
        "technique",
        "Pour les bugs connus, vérifiez la configuration et redémarrez le service. Si le problème persiste, fournissez les logs.",
    ),
    (
        "kb_tech_2",
        "technique",
        "En cas d'erreur de connexion, videz le cache du navigateur et réessayez. Vérifiez également votre connexion internet.",
    ),
    (
        "kb_tech_3",
        "technical",
        "For technical issues, try clearing your browser cache, restarting the application, and checking your internet connection.",
    ),
    (
        "kb_tech_4",
        "installation",
        "Pour l'installation, téléchargez la dernière version depuis notre site et suivez le guide d'installation.",
    ),
    # Authentication / Authentification
    (
        "kb_auth_1",
        "authentification",
        "Pour les problèmes d'accès, réinitialisez votre mot de passe depuis la page de connexion.",
    ),
    (
        "kb_auth_2",
        "authentification",
        "Si vous êtes bloqué après plusieurs tentatives, attendez 15 minutes ou contactez le support.",
    ),
    (
        "kb_auth_3",
        "account",
        "For password reset, click 'Forgot Password' on the login page and follow the email instructions.",
    ),
    # Security / Sécurité
    (
        "kb_sec_1",
        "securite",
        "Pour signaler une faille de sécurité (breach), envoyez un email à security@company.com avec les détails.",
    ),
    (
        "kb_sec_2",
        "security",
        "To report a security breach, contact our security team immediately at security@company.com.",
    ),
    (
        "kb_sec_3",
        "securite",
        "Si vous suspectez une compromission de compte, changez immédiatement votre mot de passe et activez l'authentification à deux facteurs.",
    ),
    # General
    (
        "kb_general_1",
        "autre",
        "Notre équipe est disponible pour vous aider. Décrivez votre problème en détail pour une réponse plus rapide.",
    ),
    (
        "kb_general_2",
        "other",
        "Our support team is here to help. Please provide as much detail as possible about your issue.",
    ),
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

NEGATIVE_WORDS = [
    "insatisfait",
    "mécontent",
    "furieux",
    "en colère",
    "pas satisfait",
    "impossible",
]

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
            base_dir = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "kb")
            )
            chroma_dir = os.path.join(base_dir, "chroma_db")
            if os.path.exists(chroma_dir):
                retriever = ChromaRetriever(persist_dir=chroma_dir)
                docs = retriever.retrieve(
                    (
                        " ".join(keywords)
                        if keywords
                        else (ticket.summary or ticket.subject or "")
                    ),
                    k=top_n,
                    threshold=0.0,
                )
                for d in docs:
                    meta = d.get("meta", {}) or {}
                    content = d.get("content", "")
                    sim = float(d.get("score", 0.0))
                    candidates.append(
                        {
                            "id": meta.get("id")
                            or meta.get("source", "kb")
                            + "_"
                            + str(meta.get("chunk_id", 0)),
                            "category": meta.get("category", "kb"),
                            "text": content,
                            "snippet": content[:200],
                            "raw_score": sim,
                        }
                    )
        except Exception:
            # fallthrough to lexical below
            candidates = []

    # Fallback / supplementary lexical scoring
    if not candidates:
        for eid, cat, text in KB_ENTRIES:
            raw = 0.2 if (ticket.category and cat == ticket.category) else 0.05
            raw += _lexical_score(text, keywords)
            candidates.append(
                {
                    "id": eid,
                    "category": cat,
                    "text": text,
                    "snippet": text[:200],
                    "raw_score": raw,
                }
            )

    # Normalize scores to 0..1
    candidates = _normalize_scores(candidates)
    results = candidates[:top_n]

    # attach snippets to ticket for evaluator use
    ticket.snippets = [r["snippet"] for r in results]

    # Get the question from ticket
    question = ticket.subject or ticket.description or ""

    # Collect KB context texts for LLM
    kb_context = [r["text"] for r in results if r.get("text")]

    # Try to generate a proper answer using LLM
    llm_answer = generate_answer_from_context(question, kb_context)

    if llm_answer:
        solution_text = llm_answer
    else:
        # Fallback to raw KB text if LLM fails
        solution_text = (
            results[0]["text"] if results else "Aucune solution trouvee dans la KB."
        )

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
    priority = ticket.priority_score or 0

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
            "reasons": reasons,
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

    return {
        "confidence": confidence,
        "escalate": escalate,
        "reasons": reasons,
        "sensitive": sensitive,
        "escalation_context": escalation_context,
    }
