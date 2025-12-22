"""
Agent 3: Solution Finder (RAG)
Recherche dans la KB et assemble le contexte
"""

from models.schemas import Ticket, AgentResponse
from kb.kb_manager import kb_manager
from typing import List, Dict
from loguru import logger

class SolutionFinderAgent:
    """Recherche des solutions via RAG sur la KB"""
    
    def find_solution(self, ticket: Ticket, n_results: int = 5) -> AgentResponse:
        """Recherche les documents pertinents dans la KB"""
        
        # Construire une query optimale
        search_query = self._build_search_query(ticket)
        
        # Rechercher dans la KB
        results = kb_manager.search(
            query=search_query,
            n_results=n_results,
            category_filter=ticket.category.value if ticket.category else None
        )
        
        if not results:
            logger.warning(f"No KB results found for ticket {ticket.id}")
            return AgentResponse(
                success=False,
                error="Aucune solution trouvée dans la base de connaissances",
                confidence=0.0
            )
        
        # Assembler le contexte
        context = self._assemble_context(results)
        
        # Calculer confiance moyenne
        avg_confidence = sum(1 - r['distance'] for r in results) / len(results)
        
        logger.info(f"Found {len(results)} relevant documents for ticket {ticket.id}")
        
        return AgentResponse(
            success=True,
            data={
                'documents': results,
                'context': context,
                'num_results': len(results)
            },
            confidence=avg_confidence
        )
    
    def _build_search_query(self, ticket: Ticket) -> str:
        """Construit une query optimale pour la recherche"""
        query_parts = [ticket.subject]
        
        if ticket.keywords:
            query_parts.extend(ticket.keywords[:5])  # Top 5 keywords
        
        # Ajouter des extraits de la description
        desc_words = ticket.description.split()[:50]  # Premiers 50 mots
        query_parts.append(' '.join(desc_words))
        
        return ' '.join(query_parts)
    
    def _assemble_context(self, results: List[Dict]) -> str:
        """Assemble les documents en contexte structuré"""
        context_parts = []
        
        for i, doc in enumerate(results, 1):
            context_parts.append(f"[Document {i}]")
            context_parts.append(doc['text'])
            context_parts.append("")  # Ligne vide
        
        return '\n'.join(context_parts)

solution_finder_agent = SolutionFinderAgent()