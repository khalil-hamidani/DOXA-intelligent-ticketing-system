"""
Agent 2: Query Analyzer (A+B)
Agent A: Analyse & Reformulation
Agent B: Classification
"""

from models.schemas import Ticket, TicketCategory, AgentResponse
from utils.llm_client import llm_client
from typing import List, Dict
from loguru import logger
import json

class QueryAnalyzerAgent:
    """Analyse et classifie les tickets"""
    
    def analyze(self, ticket: Ticket) -> AgentResponse:
        """Analyse complète: reformulation + classification"""
        
        # Agent A: Analyse & Reformulation
        analysis_result = self._analyze_and_reformulate(ticket)
        
        if not analysis_result['success']:
            return AgentResponse(success=False, error="Analysis failed")
        
        # Agent B: Classification
        classification_result = self._classify(ticket, analysis_result)
        
        if not classification_result['success']:
            return AgentResponse(success=False, error="Classification failed")
        
        # Mettre à jour le ticket
        ticket.keywords = analysis_result['keywords']
        ticket.category = classification_result['category']
        
        return AgentResponse(
            success=True,
            data={
                'summary': analysis_result['summary'],
                'reformulated': analysis_result['reformulated'],
                'keywords': analysis_result['keywords'],
                'category': classification_result['category'],
                'entities': analysis_result.get('entities', [])
            },
            confidence=0.88
        )
    
    def _analyze_and_reformulate(self, ticket: Ticket) -> Dict:
        """Agent A: Extrait keywords, entités et reformule"""
        
        prompt = f"""Analyse ce ticket de support et extrait les informations clés.

Ticket:
Sujet: {ticket.subject}
Description: {ticket.description}

Fournis une réponse JSON avec:
- summary: résumé en 1-2 phrases
- reformulated: reformulation claire du problème
- keywords: liste de 5-10 mots-clés pertinents
- entities: entités importantes (noms, produits, numéros, etc.)

Réponds UNIQUEMENT en JSON."""

        try:
            messages = [
                {"role": "system", "content": "Tu es un expert en analyse de tickets support. Réponds toujours en JSON valide."},
                {"role": "user", "content": prompt}
            ]
            
            response = llm_client.generate(messages, temperature=0.3, json_mode=True)
            result = llm_client.extract_json(response)
            
            result['success'] = True
            logger.info(f"Ticket {ticket.id} analyzed: {len(result.get('keywords', []))} keywords extracted")
            return result
            
        except Exception as e:
            logger.error(f"Analysis error for ticket {ticket.id}: {e}")
            return {'success': False}
    
    def _classify(self, ticket: Ticket, analysis: Dict) -> Dict:
        """Agent B: Classifie le ticket"""
        
        categories_desc = {
            'technique': "Problèmes techniques, erreurs, bugs logiciels",
            'facturation': "Questions de paiement, factures, tarification",
            'bug': "Bugs confirmés nécessitant correction",
            'feature_request': "Demandes de nouvelles fonctionnalités",
            'autre': "Autres demandes"
        }
        
        prompt = f"""Classifie ce ticket dans UNE de ces catégories:

{json.dumps(categories_desc, indent=2, ensure_ascii=False)}

Informations du ticket:
- Sujet: {ticket.subject}
- Description: {ticket.description}
- Keywords: {', '.join(analysis.get('keywords', []))}

Fournis un JSON avec:
- category: la catégorie choisie (exactement comme ci-dessus)
- confidence: ton niveau de confiance (0-1)
- reasoning: explication courte de ton choix

Réponds UNIQUEMENT en JSON."""

        try:
            messages = [
                {"role": "system", "content": "Tu es un expert en classification de tickets. Réponds toujours en JSON valide."},
                {"role": "user", "content": prompt}
            ]
            
            response = llm_client.generate(messages, temperature=0.2, json_mode=True)
            result = llm_client.extract_json(response)
            
            # Valider la catégorie
            if result.get('category') not in categories_desc:
                result['category'] = 'autre'
            
            result['success'] = True
            logger.info(f"Ticket {ticket.id} classified as: {result.get('category')}")
            return result
            
        except Exception as e:
            logger.error(f"Classification error for ticket {ticket.id}: {e}")
            return {'success': False, 'category': 'autre'}

query_analyzer_agent = QueryAnalyzerAgent()

