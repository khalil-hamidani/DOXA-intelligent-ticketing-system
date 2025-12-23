# pipeline/answer.py
"""Answer Generation: LLM-based response generation with augmented context.

This module handles:
1. LLM-based answer generation
2. Context-aware response composition
3. Confidence scoring
4. Response validation
"""

from typing import Dict, Optional
from models import Ticket
import json
import os
from agno.agent import Agent
from agno.models.mistral import MistralChat
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

_mistral_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
if _mistral_key:
    os.environ["MISTRALAI_API_KEY"] = _mistral_key

MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")


def _create_answer_agent() -> Agent:
    """Create agent for answer generation."""
    mistral_model = MistralChat(id=MODEL_ID, temperature=0.3)
    
    instructions = """You are a support specialist generating answers based on retrieved knowledge.

Your task:
1. Read the ticket and retrieved context carefully
2. Generate a clear, actionable solution or response
3. If the context doesn't contain relevant information, suggest escalation
4. Always be professional and respectful
5. Include next steps or validation instructions when relevant

Return JSON:
{
    "answer": "detailed response",
    "confidence": 0.0-1.0,
    "is_escalation_recommended": bool,
    "escalation_reason": "reason if escalation recommended",
    "suggested_actions": ["action 1", "action 2", ...],
    "follow_up_required": bool
}"""
    
    agent = Agent(
        model=mistral_model,
        instructions=instructions,
        name="AnswerGenerationAgent"
    )
    return agent


class AnswerGenerator:
    """LLM-based answer generation with context."""
    
    def __init__(self, use_context: bool = True):
        """Initialize answer generator.
        
        Args:
            use_context: Whether to use augmented context
        """
        self.use_context = use_context
    
    def generate(
        self,
        ticket: Ticket,
        context_prompt: Optional[str] = None
    ) -> Dict:
        """Generate answer based on ticket and context.
        
        Args:
            ticket: Ticket object
            context_prompt: Optional pre-built context prompt
            
        Returns:
            {
                "answer": str,
                "confidence": float,
                "is_escalation_recommended": bool,
                "suggested_actions": List[str],
                "source": "llm" | "fallback"
            }
        """
        agent = _create_answer_agent()
        
        # Build prompt
        if context_prompt:
            prompt = context_prompt
        else:
            prompt = self._build_prompt(ticket)
        
        try:
            response = agent.run(prompt)
            response_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                return {
                    "answer": result.get("answer", "Unable to generate answer"),
                    "confidence": result.get("confidence", 0.5),
                    "is_escalation_recommended": result.get("is_escalation_recommended", False),
                    "escalation_reason": result.get("escalation_reason", ""),
                    "suggested_actions": result.get("suggested_actions", []),
                    "follow_up_required": result.get("follow_up_required", False),
                    "source": "llm"
                }
        except Exception as e:
            print(f"Answer generation error: {e}")
        
        # Fallback
        return self._fallback_answer(ticket)
    
    def _build_prompt(self, ticket: Ticket) -> str:
        """Build prompt from ticket alone."""
        return f"""Generate a support answer for this ticket:

Subject: {ticket.subject}
Category: {ticket.category or 'unclassified'}
Description: {ticket.description}
Keywords: {', '.join(ticket.keywords or [])}
Summary: {ticket.summary or 'N/A'}

Provide a helpful response based on the ticket information."""
    
    def _fallback_answer(self, ticket: Ticket) -> Dict:
        """Fallback answer generation."""
        category = ticket.category or "autre"
        
        answers = {
            "technique": "Thank you for reporting this technical issue. Please provide the following information for troubleshooting: 1) System version, 2) Steps to reproduce, 3) Error messages or logs. We'll investigate further and get back to you.",
            "facturation": "Thank you for your billing inquiry. Please provide your invoice number or transaction ID. Our billing team will review your request and respond within 24 hours.",
            "authentification": "For account access issues, please try resetting your password. If the issue persists, contact our support team with your account details.",
            "autre": "Thank you for contacting us. We've received your request and will review it shortly."
        }
        
        return {
            "answer": answers.get(category, answers["autre"]),
            "confidence": 0.3,
            "is_escalation_recommended": True,
            "escalation_reason": "Unable to generate LLM-based answer, fallback template used",
            "suggested_actions": ["Contact support team"],
            "follow_up_required": True,
            "source": "fallback"
        }


class ContextAwareAnswerGenerator:
    """Answer generation with integrated context optimization."""
    
    def __init__(self, answer_generator: Optional[AnswerGenerator] = None):
        """Initialize context-aware generator.
        
        Args:
            answer_generator: AnswerGenerator instance
        """
        self.answer_generator = answer_generator or AnswerGenerator()
    
    def generate_with_context(
        self,
        ticket: Ticket,
        context_result: Dict
    ) -> Dict:
        """Generate answer with optimized context.
        
        Args:
            ticket: Ticket object
            context_result: Result from ContextOptimizer
            
        Returns:
            {
                "answer_generation": {...},
                "context_info": {...},
                "final_response": str
            }
        """
        from pipeline.context import ContextBuilder
        
        # Build context prompt
        context_prompt = ContextBuilder.build_prompt_context(ticket, context_result)
        
        # Generate answer
        answer_result = self.answer_generator.generate(ticket, context_prompt)
        
        # Format final response
        final_response = self._format_response(ticket, answer_result, context_result)
        
        return {
            "answer_generation": answer_result,
            "context_info": {
                "selected_documents": len(context_result.get("selected_documents", [])),
                "context_tokens": context_result.get("token_estimate", 0),
                "optimization_efficiency": context_result.get("optimization_info", {}).get("efficiency", 0)
            },
            "final_response": final_response,
            "escalation_recommended": answer_result.get("is_escalation_recommended", False)
        }
    
    @staticmethod
    def _format_response(
        ticket: Ticket,
        answer_result: Dict,
        context_result: Dict
    ) -> str:
        """Format final response for client."""
        answer = answer_result.get("answer", "")
        confidence = answer_result.get("confidence", 0)
        actions = answer_result.get("suggested_actions", [])
        
        response = f"""Dear {ticket.client_name},

Thank you for contacting us regarding: {ticket.subject}

RESPONSE:
{answer}

SUGGESTED STEPS:
"""
        
        if actions:
            for i, action in enumerate(actions, 1):
                response += f"{i}. {action}\n"
        else:
            response += "Please follow the guidance above.\n"
        
        response += f"""
CONFIDENCE LEVEL: {int(confidence * 100)}%

If this resolves your issue, please confirm. If not, feel free to reply with additional details.

Best regards,
Support Team"""
        
        return response


class ResponseValidator:
    """Validates generated responses."""
    
    def __init__(self, min_confidence: float = 0.5):
        """Initialize validator.
        
        Args:
            min_confidence: Minimum acceptable confidence
        """
        self.min_confidence = min_confidence
    
    def validate(self, answer_result: Dict) -> Dict:
        """Validate generated answer.
        
        Args:
            answer_result: Answer generation result
            
        Returns:
            {
                "valid": bool,
                "issues": List[str],
                "recommendations": List[str]
            }
        """
        issues = []
        recommendations = []
        
        # Check answer presence
        answer = answer_result.get("answer", "").strip()
        if not answer or len(answer) < 50:
            issues.append("Answer too short or empty")
            recommendations.append("Request longer, more detailed response")
        
        # Check confidence
        confidence = answer_result.get("confidence", 0)
        if confidence < self.min_confidence:
            issues.append(f"Confidence below threshold ({confidence:.2%} < {self.min_confidence:.2%})")
            recommendations.append("Consider escalation")
        
        # Check for escalation recommendation
        if answer_result.get("is_escalation_recommended", False):
            recommendations.append(f"Escalation recommended: {answer_result.get('escalation_reason', '')}")
        
        # Check actions
        actions = answer_result.get("suggested_actions", [])
        if not actions:
            recommendations.append("Consider adding suggested actions")
        
        valid = len(issues) == 0 and confidence >= self.min_confidence
        
        return {
            "valid": valid,
            "issues": issues,
            "recommendations": recommendations,
            "confidence": confidence
        }
