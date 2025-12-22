"""
Agent 5: Response Composer
Génère la réponse finale au client
"""

from models.schemas import Ticket, AgentResponse
from utils.llm_client import llm_client
from typing import Dict
from loguru import logger

class ResponseComposerAgent:
    """Génère des réponses structurées et professionnelles"""
    
    def compose(
        self, 
        ticket: Ticket,
        kb_context: str,
        analysis: Dict
    ) -> AgentResponse:
        """Génère la réponse finale"""
        
        prompt = f"""Tu es un agent de support client professionnel. 

Génère une réponse complète et structurée pour ce ticket:

TICKET:
Client: {ticket.client_name}
Sujet: {ticket.subject}
Description: {ticket.description}

ANALYSE:
Catégorie: {ticket.category}
Résumé: {analysis.get('summary', 'N/A')}
Mots-clés: {', '.join(ticket.keywords)}

CONTEXTE DE LA BASE DE CONNAISSANCES:
{kb_context}

Structure ta réponse ainsi:
1. Salutation personnalisée
2. Reformulation claire du problème
3. Solution détaillée avec étapes concrètes
4. Recommandations ou actions à suivre
5. Formule de politesse et signature

Ton: professionnel mais chaleureux
Longueur: 150-300 mots
Langue: français

Ne mentionne JAMAIS que tu utilises une base de connaissances ou que tu es une IA."""

        try:
            messages = [
                {"role": "system", "content": "Tu es un expert en support client."},
                {"role": "user", "content": prompt}
            ]
            
            response = llm_client.generate(messages, temperature=0.7)
            
            logger.info(f"Response composed for ticket {ticket.id}")
            
            return AgentResponse(
                success=True,
                data={'response': response},
                confidence=0.85
            )
            
        except Exception as e:
            logger.error(f"Response composition error for ticket {ticket.id}: {e}")
            return AgentResponse(
                success=False,
                error=f"Erreur lors de la génération de réponse: {str(e)}"
            )

response_composer_agent = ResponseComposerAgent()

