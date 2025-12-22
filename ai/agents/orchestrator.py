"""
Orchestrateur global - Cerveau du système
Coordonne tous les agents et gère le workflow
"""

from models.schemas import Ticket, Feedback, TicketStatus, AgentResponse
from agents.validator import validator_agent
from agents.scorer import scorer_agent
from agents.query_analyzer import query_analyzer_agent
from agents.solution_finder import solution_finder_agent
from agents.evaluator import evaluator_agent
from agents.response_composer import response_composer_agent
from config.settings import settings
from loguru import logger
from typing import Dict, Optional
import uuid
from datetime import datetime

class Orchestrator:
    """Orchestre le workflow complet de traitement des tickets"""
    
    def __init__(self):
        self.max_attempts = settings.max_retry_attempts
    
    def process_ticket(self, ticket: Ticket) -> Dict:
        """Point d'entrée principal - traite un ticket de A à Z"""
        
        logger.info(f"🎫 Starting processing for ticket {ticket.id}")
        
        # Étape 0: Validation
        validation_result = validator_agent.validate(ticket)
        if not validation_result.success:
            return self._handle_validation_failure(ticket, validation_result)
        
        ticket.status = TicketStatus.VALIDATED
        
        # Étape 1: Scoring
        scoring_result = scorer_agent.score(ticket)
        logger.info(f"📊 Ticket {ticket.id} priority score: {ticket.priority_score}")
        
        # Workflow principal avec retry
        while ticket.attempts < self.max_attempts:
            ticket.attempts += 1
            logger.info(f"🔄 Attempt {ticket.attempts}/{self.max_attempts} for ticket {ticket.id}")
            
            # Étape 2: Analyse & Classification
            ticket.status = TicketStatus.ANALYZING
            analysis_result = query_analyzer_agent.analyze(ticket)
            
            if not analysis_result.success:
                logger.error(f"❌ Analysis failed for ticket {ticket.id}")
                continue
            
            # Étape 3: Recherche solution (RAG)
            solution_result = solution_finder_agent.find_solution(ticket)
            
            if not solution_result.success:
                logger.warning(f"⚠️ No solution found in KB for ticket {ticket.id}")
                return self._handle_escalation(ticket, "Aucune solution dans la KB")
            
            # Étape 4: Composer la réponse
            response_result = response_composer_agent.compose(
                ticket,
                solution_result.data['context'],
                analysis_result.data
            )
            
            if not response_result.success:
                logger.error(f"❌ Response composition failed for ticket {ticket.id}")
                continue
            
            # Étape 5: Évaluation & Décision
            evaluation_result = evaluator_agent.evaluate(
                ticket,
                solution_result.data,
                response_result.data['response']
            )
            
            # Décision d'escalade
            if evaluation_result.data['should_escalate']:
                logger.warning(
                    f"🚨 Escalation triggered for ticket {ticket.id}: "
                    f"{evaluation_result.data['escalation_reasons']}"
                )
                return self._handle_escalation(
                    ticket, 
                    evaluation_result.data['escalation_reasons'],
                    evaluation_result.data.get('escalation_context')
                )
            
            # ✅ Solution trouvée avec confiance suffisante
            ticket.status = TicketStatus.SOLVED
            ticket.confidence_score = evaluation_result.confidence
            
            return {
                'success': True,
                'ticket_id': ticket.id,
                'status': ticket.status.value,
                'response': response_result.data['response'],
                'confidence': evaluation_result.confidence,
                'attempts': ticket.attempts,
                'analysis': analysis_result.data,
                'escalated': False
            }
        
        # Max attempts atteints
        logger.error(f"❌ Max attempts reached for ticket {ticket.id}")
        return self._handle_escalation(ticket, f"Maximum de tentatives atteint ({self.max_attempts})")
    
    def handle_feedback(self, ticket: Ticket, feedback: Feedback) -> Dict:
        """Gère le feedback client et relance le workflow si nécessaire"""
        
        logger.info(f"📬 Feedback received for ticket {ticket.id}: satisfied={feedback.satisfied}")
        
        if feedback.satisfied:
            # Client satisfait - clôturer
            ticket.status = TicketStatus.CLOSED
            return {
                'success': True,
                'ticket_id': ticket.id,
                'status': 'closed',
                'message': 'Ticket clôturé avec succès'
            }
        
        else:
            # Client insatisfait - retry si possible
            if ticket.attempts >= self.max_attempts:
                logger.warning(f"⚠️ Max retries reached, escalating ticket {ticket.id}")
                return self._handle_escalation(
                    ticket, 
                    "Client insatisfait après maximum de tentatives"
                )
            
            # Ajouter la clarification au contexte
            ticket.description += f"\n\nClarification client: {feedback.reason}"
            ticket.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'feedback',
                'satisfied': False,
                'reason': feedback.reason
            })
            
            # Relancer le workflow
            logger.info(f"🔄 Reprocessing ticket {ticket.id} with clarification")
            return self.process_ticket(ticket)
    
    def _handle_validation_failure(self, ticket: Ticket, result: AgentResponse) -> Dict:
        """Gère l'échec de validation"""
        return {
            'success': False,
            'ticket_id': ticket.id,
            'status': 'rejected',
            'error': result.error,
            'message': 'Veuillez compléter le formulaire avec les informations manquantes'
        }
    
    def _handle_escalation(
        self, 
        ticket: Ticket, 
        reason: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Gère l'escalade vers un humain"""
        
        ticket.status = TicketStatus.ESCALATED
        ticket.escalated = True
        ticket.escalation_reason = reason
        
        return {
            'success': True,
            'ticket_id': ticket.id,
            'status': 'escalated',
            'escalated': True,
            'reason': reason,
            'context': context,
            'message': 'Ticket escaladé vers un agent humain',
            'priority_score': ticket.priority_score
        }

# Instance globale
orchestrator = Orchestrator()