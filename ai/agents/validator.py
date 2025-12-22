"""
Agent 0: Validation initiale
Vérifie que le ticket contient les éléments nécessaires
"""

from models.schemas import Ticket, AgentResponse
from loguru import logger
import re

class ValidatorAgent:
    """Valide la qualité et complétude d'un ticket"""
    
    MIN_DESCRIPTION_LENGTH = 20
    MIN_SUBJECT_LENGTH = 5
    
    def validate(self, ticket: Ticket) -> AgentResponse:
        """Valide un ticket"""
        errors = []
        
        # Vérifier le sujet
        if not ticket.subject or len(ticket.subject) < self.MIN_SUBJECT_LENGTH:
            errors.append(f"Le sujet doit contenir au moins {self.MIN_SUBJECT_LENGTH} caractères")
        
        # Vérifier la description
        if not ticket.description or len(ticket.description) < self.MIN_DESCRIPTION_LENGTH:
            errors.append(f"La description doit contenir au moins {self.MIN_DESCRIPTION_LENGTH} caractères")
        
        # Vérifier l'email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, ticket.email):
            errors.append("Format d'email invalide")
        
        # Vérifier présence de mots exploitables
        if len(ticket.description.split()) < 5:
            errors.append("La description est trop courte pour être traitée")
        
        if errors:
            logger.warning(f"Ticket {ticket.id} validation failed: {errors}")
            return AgentResponse(
                success=False,
                error="; ".join(errors),
                confidence=0.0
            )
        
        logger.info(f"Ticket {ticket.id} validated successfully")
        return AgentResponse(
            success=True,
            confidence=1.0
        )

validator_agent = ValidatorAgent()