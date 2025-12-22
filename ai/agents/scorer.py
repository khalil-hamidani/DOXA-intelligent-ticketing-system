"""
Agent 1: Scoring & Priorisation
Calcule un score de priorité basé sur urgence, récurrence et impact
"""

from models.schemas import Ticket, AgentResponse
from typing import Dict
from loguru import logger

class ScorerAgent:
    """Calcule le score de priorité d'un ticket"""
    
    # Mots-clés d'urgence avec pondération
    URGENCY_KEYWORDS = {
        'urgent': 50,
        'critique': 45,
        'bloquant': 40,
        'immédiat': 35,
        'grave': 30,
        'important': 20
    }
    
    # Mots-clés de récurrence
    RECURRENCE_KEYWORDS = {
        'toujours': 30,
        'systématique': 25,
        'chaque fois': 25,
        'répété': 20,
        'encore': 15,
        'plusieurs fois': 20
    }
    
    # Impact business
    BUSINESS_KEYWORDS = {
        'client': 25,
        'production': 30,
        'vente': 20,
        'perte': 25,
        'bloqué': 20
    }
    
    def score(self, ticket: Ticket) -> AgentResponse:
        """Calcule le score de priorité"""
        text = (ticket.subject + " " + ticket.description).lower()
        score = 0
        breakdown = {
            'urgency': 0,
            'recurrence': 0,
            'business_impact': 0
        }
        
        # Score d'urgence
        for keyword, points in self.URGENCY_KEYWORDS.items():
            if keyword in text:
                breakdown['urgency'] += points
                score += points
        
        # Score de récurrence
        for keyword, points in self.RECURRENCE_KEYWORDS.items():
            if keyword in text:
                breakdown['recurrence'] += points
                score += points
        
        # Impact business
        for keyword, points in self.BUSINESS_KEYWORDS.items():
            if keyword in text:
                breakdown['business_impact'] += points
                score += points
        
        # Normaliser le score (0-100)
        max_possible = 150  # Score maximum théorique
        normalized_score = min(int((score / max_possible) * 100), 100)
        
        ticket.priority_score = normalized_score
        
        logger.info(f"Ticket {ticket.id} scored: {normalized_score} (breakdown: {breakdown})")
        
        return AgentResponse(
            success=True,
            data={
                'score': normalized_score,
                'breakdown': breakdown
            },
            confidence=0.85
        )

scorer_agent = ScorerAgent()
