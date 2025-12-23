"""
Query Planner: Orchestrates semantic analysis pipeline

The QueryPlanner orchestrates the full semantic analysis workflow:
1. Validation → Ensures ticket quality
2. Analysis → Reformulation & entity extraction
3. Classification → Multi-dimensional semantic classification
4. Planning → Determine resolution path and next steps

This module coordinates all query augmentation steps to produce a comprehensive
ticket analysis plan that drives downstream processing.
"""

from models import Ticket
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

from agents.validator import validate_ticket
from agents.query_analyzer import analyze_and_reformulate
from agents.unified_classifier import classify_unified, ClassificationResult

logger = logging.getLogger(__name__)


@dataclass
class QueryPlan:
    """Complete query analysis and planning result."""
    
    # Validation results
    is_valid: bool
    validation_errors: List[str]
    validation_confidence: float
    
    # Analysis results
    summary: str
    reformulation: str
    keywords: List[str]
    entities: List[str]
    
    # Classification results
    classification: ClassificationResult
    
    # Planning results (derived from above)
    resolution_path: str  # e.g., "kb_retrieval", "escalation", "fallback"
    estimated_resolution_time: str  # e.g., "immediate", "1-2 hours", "1-2 days"
    priority_level: str  # "low", "normal", "high", "critical"
    next_steps: List[str]
    
    # Metadata
    analysis_confidence: float  # Overall confidence in analysis plan
    reasoning: str  # Why this plan was chosen
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["classification"] = {
            "primary_category": self.classification.primary_category,
            "confidence_category": self.classification.confidence_category,
            "severity": self.classification.severity,
            "confidence_severity": self.classification.confidence_severity,
            "treatment_type": self.classification.treatment_type,
            "confidence_treatment": self.classification.confidence_treatment,
            "required_skills": self.classification.required_skills,
            "confidence_skills": self.classification.confidence_skills,
            "overall_confidence": self.classification.overall_confidence(),
            "reasoning": self.classification.reasoning
        }
        return result


class QueryPlanner:
    """
    Orchestrates semantic analysis and planning for ticket resolution.
    
    Workflow:
    1. Validation: Check ticket quality/completeness
    2. Analysis: Reformulate query, extract entities
    3. Classification: Multi-dimensional semantic classification
    4. Planning: Determine resolution path and next steps
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize QueryPlanner.
        
        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.INFO)
    
    def plan_ticket_resolution(self, ticket: Ticket) -> QueryPlan:
        """
        Create comprehensive resolution plan for a ticket.
        
        Args:
            ticket: Ticket object to analyze
            
        Returns:
            QueryPlan with full analysis and next steps
        """
        self._log("Starting query planning...")
        
        # STEP 1: VALIDATION
        self._log("Step 1: Validating ticket...")
        validation_result = validate_ticket(ticket)
        
        is_valid = validation_result.get("valid", False)
        validation_errors = validation_result.get("reasons", [])
        validation_confidence = validation_result.get("confidence", 0.5)
        
        if not is_valid:
            self._log(f"  ✗ Validation failed: {', '.join(validation_errors)}")
            return self._create_rejection_plan(
                ticket, validation_errors, validation_confidence
            )
        
        self._log(f"  ✓ Validation passed (confidence: {validation_confidence:.1%})")
        
        # STEP 2: ANALYSIS
        self._log("Step 2: Analyzing and reformulating query...")
        analysis_result = analyze_and_reformulate(ticket)
        
        summary = analysis_result.get("summary", ticket.subject)
        reformulation = analysis_result.get("reformulation", ticket.description)
        keywords = analysis_result.get("keywords", [])
        entities = analysis_result.get("entities", [])
        
        self._log(f"  ✓ Analysis complete: {len(keywords)} keywords, {len(entities)} entities")
        
        # STEP 3: CLASSIFICATION
        self._log("Step 3: Classifying ticket...")
        classification = classify_unified(ticket)
        
        self._log(
            f"  ✓ Classification: {classification.primary_category} "
            f"(conf={classification.confidence_category:.1%}), "
            f"severity={classification.severity}, "
            f"treatment={classification.treatment_type}"
        )
        
        # STEP 4: PLANNING
        self._log("Step 4: Creating resolution plan...")
        plan = self._create_resolution_plan(
            ticket=ticket,
            is_valid=is_valid,
            validation_confidence=validation_confidence,
            validation_errors=validation_errors,
            summary=summary,
            reformulation=reformulation,
            keywords=keywords,
            entities=entities,
            classification=classification
        )
        
        self._log(f"  ✓ Plan created: path={plan.resolution_path}, priority={plan.priority_level}")
        
        return plan
    
    def _create_resolution_plan(
        self,
        ticket: Ticket,
        is_valid: bool,
        validation_confidence: float,
        validation_errors: List[str],
        summary: str,
        reformulation: str,
        keywords: List[str],
        entities: List[str],
        classification: ClassificationResult
    ) -> QueryPlan:
        """
        Create detailed resolution plan based on analysis.
        
        Decision logic:
        - High confidence KB path (category + severity <= medium): KB retrieval
        - Medium confidence: KB + escalation ready
        - Low confidence: Escalation path
        - Special cases: Fallback paths
        """
        
        overall_conf = classification.overall_confidence()
        
        # Determine resolution path
        resolution_path = "kb_retrieval"  # default
        estimated_time = "immediate (if KB match) or 1-2 hours"
        priority_level = "normal"
        next_steps = []
        
        # High confidence path: Use KB retrieval
        if overall_conf >= 0.75 and classification.severity in ["low", "medium"]:
            resolution_path = "kb_retrieval"
            estimated_time = "immediate (if KB match) or 1-2 hours"
            priority_level = "normal"
            next_steps = [
                f"Search KB for '{classification.primary_category}' solutions",
                "Retrieve top-k documents by semantic similarity",
                "Rank solutions by relevance and completeness",
                "Generate contextual response from top match"
            ]
        
        # Medium confidence: KB with escalation readiness
        elif overall_conf >= 0.60:
            resolution_path = "kb_with_escalation_ready"
            estimated_time = "1-2 hours (escalate if KB fails)"
            priority_level = "normal"
            next_steps = [
                f"Attempt KB retrieval for '{classification.primary_category}'",
                "Escalate to human support if confidence < 0.50",
                f"Skills needed: {', '.join(classification.required_skills)}"
            ]
        
        # Low confidence: Escalation path
        elif overall_conf < 0.60 or classification.treatment_type == "escalation":
            resolution_path = "escalation"
            estimated_time = "2-4 hours (human review)"
            priority_level = "high"
            next_steps = [
                f"Route to specialist team: {', '.join(classification.required_skills)}",
                f"Escalation reason: Low classification confidence ({overall_conf:.1%})",
                "Provide analysis context to support team",
                "Enable KB gap detection for future improvement"
            ]
        
        # Critical/urgent: Immediate escalation
        if classification.severity == "critical" or classification.treatment_type == "urgent":
            resolution_path = "urgent_escalation"
            estimated_time = "immediate escalation"
            priority_level = "critical"
            next_steps = [
                f"URGENT: {summary}",
                f"Route to: {', '.join(classification.required_skills)}",
                "Send immediate acknowledgement to customer",
                "Trigger escalation notifications"
            ]
        
        # Feature request: Different path
        if classification.primary_category == "feature_request":
            resolution_path = "feature_queue"
            estimated_time = "Backlog (not immediate resolution)"
            priority_level = "low"
            next_steps = [
                "Add to product feature request queue",
                "Route to product management team",
                "Notify customer of submission"
            ]
        
        # Calculate analysis confidence
        analysis_confidence = (
            (validation_confidence * 0.2) +
            (overall_conf * 0.8)
        )
        
        reasoning = f"""
Resolution path determined by:
- Validation confidence: {validation_confidence:.1%}
- Classification confidence: {overall_conf:.1%}
- Category: {classification.primary_category} (confidence: {classification.confidence_category:.1%})
- Severity: {classification.severity} (confidence: {classification.confidence_severity:.1%})
- Treatment type: {classification.treatment_type}

Decision: Use {resolution_path} approach with priority={priority_level}
        """.strip()
        
        return QueryPlan(
            is_valid=is_valid,
            validation_errors=validation_errors,
            validation_confidence=validation_confidence,
            summary=summary,
            reformulation=reformulation,
            keywords=keywords,
            entities=entities,
            classification=classification,
            resolution_path=resolution_path,
            estimated_resolution_time=estimated_time,
            priority_level=priority_level,
            next_steps=next_steps,
            analysis_confidence=analysis_confidence,
            reasoning=reasoning
        )
    
    def _create_rejection_plan(
        self,
        ticket: Ticket,
        validation_errors: List[str],
        validation_confidence: float
    ) -> QueryPlan:
        """Create rejection plan for invalid tickets."""
        
        return QueryPlan(
            is_valid=False,
            validation_errors=validation_errors,
            validation_confidence=validation_confidence,
            summary="Invalid ticket",
            reformulation="",
            keywords=[],
            entities=[],
            classification=ClassificationResult(
                primary_category="autre",
                confidence_category=0.0,
                severity="low",
                confidence_severity=0.5,
                treatment_type="standard",
                confidence_treatment=0.5,
                required_skills=[],
                confidence_skills=0.0,
                reasoning="Ticket rejected due to validation errors"
            ),
            resolution_path="rejection",
            estimated_resolution_time="immediate",
            priority_level="low",
            next_steps=[
                f"Reject ticket: {', '.join(validation_errors)}",
                "Request customer to provide missing information",
                "Explain validation requirements"
            ],
            analysis_confidence=0.0,
            reasoning=f"Validation failed: {', '.join(validation_errors)}"
        )
    
    def _log(self, message: str):
        """Log message if verbose mode enabled."""
        if self.verbose:
            logger.info(message)


# Convenience function for direct usage
def plan_ticket_resolution(ticket: Ticket, verbose: bool = True) -> QueryPlan:
    """
    Plan ticket resolution with full semantic analysis.
    
    Orchestrates: validation → analysis → classification → planning
    
    Args:
        ticket: Ticket object to analyze
        verbose: Enable detailed logging
        
    Returns:
        QueryPlan with complete analysis and next steps
    """
    planner = QueryPlanner(verbose=verbose)
    return planner.plan_ticket_resolution(ticket)
