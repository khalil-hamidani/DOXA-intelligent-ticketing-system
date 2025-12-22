"""
Agent 4: Evaluator & Decider
Évalue la confiance et décide d'escalader ou non
"""

from models.schemas import Ticket, AgentResponse, EscalationContext
from utils.llm_client import llm_client
from config.settings import settings
from typing import Dict
from loguru import logger
import re

class EvaluatorAgent:
    """Évalue la qualité de la solution et décide d'escalader"""
    
    def evaluate(
        self, 
        ticket: Ticket, 
        kb_results: Dict,
        proposed_solution: str
    ) -> AgentResponse:
        """Évalue la confiance et détecte les cas problématiques"""
        
        # 1. Calculer le score de confiance
        confidence_score = self._calculate_confidence(ticket, kb_results, proposed_solution)
        
        # 2. Détecter émotions négatives
        negative_emotion = self._detect_negative_emotion(ticket)
        
        # 3. Détecter données sensibles
        sensitive_data = self._detect_sensitive_data(ticket)
        
        # 4. Détecter cas non standard
        non_standard = self._is_non_standard(ticket, kb_results)
        
        # Décision d'escalade
        should_escalate = (
            confidence_score < settings.confidence_threshold or
            negative_emotion['detected'] or
            sensitive_data['detected'] or
            non_standard
        )
        
        escalation_reasons = []
        if confidence_score < settings.confidence_threshold:
            escalation_reasons.append(f"Confiance trop faible ({confidence_score:.2f})")
        if negative_emotion['detected']:
            escalation_reasons.append(f"Émotion négative détectée: {negative_emotion['type']}")
        if sensitive_data['detected']:
            escalation_reasons.append(f"Données sensibles: {', '.join(sensitive_data['types'])}")
        if non_standard:
            escalation_reasons.append("Cas non standard")
        
        # Générer contexte d'escalade si nécessaire
        escalation_context = None
        if should_escalate:
            escalation_context = self._generate_escalation_context(
                ticket, 
                escalation_reasons,
                kb_results,
                proposed_solution
            )
        
        logger.info(
            f"Ticket {ticket.id} evaluated: confidence={confidence_score:.2f}, "
            f"escalate={should_escalate}"
        )
        
        return AgentResponse(
            success=True,
            data={
                'confidence_score': confidence_score,
                'should_escalate': should_escalate,
                'escalation_reasons': escalation_reasons,
                'negative_emotion': negative_emotion,
                'sensitive_data': sensitive_data,
                'non_standard': non_standard,
                'escalation_context': escalation_context
            },
            confidence=confidence_score
        )
    
    def _calculate_confidence(
        self, 
        ticket: Ticket, 
        kb_results: Dict,
        proposed_solution: str
    ) -> float:
        """Calcule un score de confiance composite"""
        
        scores = []
        
        # 1. Confiance de la KB (basée sur distance moyenne)
        if kb_results.get('documents'):
            avg_distance = sum(d['distance'] for d in kb_results['documents']) / len(kb_results['documents'])
            kb_confidence = 1 - avg_distance
            scores.append(kb_confidence * 0.4)  # 40% du poids
        
        # 2. Clarté de la solution (longueur et structure)
        solution_confidence = min(len(proposed_solution) / 500, 1.0)  # Solutions plus longues = mieux
        scores.append(solution_confidence * 0.2)  # 20% du poids
        
        # 3. Match keywords ticket <-> KB
        if ticket.keywords and kb_results.get('documents'):
            kb_text = ' '.join([d['text'].lower() for d in kb_results['documents']])
            keyword_match = sum(1 for kw in ticket.keywords if kw.lower() in kb_text) / len(ticket.keywords)
            scores.append(keyword_match * 0.4)  # 40% du poids
        
        return sum(scores) if scores else 0.3  # Score par défaut si rien à évaluer
    
    def _detect_negative_emotion(self, ticket: Ticket) -> Dict:
        """Détecte les émotions négatives fortes"""
        text = (ticket.subject + " " + ticket.description).lower()
        
        emotion_patterns = {
            'colère': ['furieux', 'inacceptable', 'scandaleux', 'honte', 'inadmissible'],
            'frustration': ['exaspéré', 'las', 'fatigué', 'énième fois', 'ras-le-bol'],
            'urgence': ['désespéré', 'catastrophe', 'vital', 'crucial']
        }
        
        for emotion_type, keywords in emotion_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    return {
                        'detected': True,
                        'type': emotion_type,
                        'keyword': keyword
                    }
        
        return {'detected': False}
    
    def _detect_sensitive_data(self, ticket: Ticket) -> Dict:
        """Détecte mentions de données sensibles"""
        text = ticket.subject + " " + ticket.description
        
        sensitive_types = []
        
        # Numéros de carte bancaire (pattern simplifié)
        if re.search(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', text):
            sensitive_types.append('carte_bancaire')
        
        # Mots-clés sensibles
        if any(word in text.lower() for word in ['mot de passe', 'password', 'mdp']):
            sensitive_types.append('credentials')
        
        if any(word in text.lower() for word in ['juridique', 'avocat', 'tribunal', 'plainte']):
            sensitive_types.append('legal')
        
        return {
            'detected': len(sensitive_types) > 0,
            'types': sensitive_types
        }
    
    def _is_non_standard(self, ticket: Ticket, kb_results: Dict) -> bool:
        """Détecte si le cas est non standard"""
        
        # Si très peu de résultats KB pertinents
        if not kb_results.get('documents') or len(kb_results['documents']) < 2:
            return True
        
        # Si tous les documents KB ont une distance > 0.7 (peu similaires)
        if all(d['distance'] > 0.7 for d in kb_results['documents']):
            return True
        
        return False
    
    def _generate_escalation_context(
        self,
        ticket: Ticket,
        reasons: list,
        kb_results: Dict,
        proposed_solution: str
    ) -> EscalationContext:
        """Génère un contexte complet pour l'escalade"""
        
        # Analyser ce qui manque dans la KB
        kb_gaps = []
        if not kb_results.get('documents'):
            kb_gaps.append("Aucun document pertinent trouvé dans la KB")
        elif all(d['distance'] > 0.7 for d in kb_results['documents']):
            kb_gaps.append("Documents KB peu similaires au problème")
        
        return EscalationContext(
            ticket_id=ticket.id,
            reason="; ".join(reasons),
            agent_analysis=f"Catégorie: {ticket.category}, Score priorité: {ticket.priority_score}",
            suggested_solution=proposed_solution if proposed_solution else None,
            kb_gaps_identified=kb_gaps
        )

evaluator_agent = EvaluatorAgent()

