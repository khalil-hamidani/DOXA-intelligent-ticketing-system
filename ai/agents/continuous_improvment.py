"""
Continuous Improvement Agent - Step 9: Continuous Improvement

Responsibilities:
  - Analyze escalations to find patterns
  - Identify KB gaps (questions with no good answers)
  - Detect hallucinations (wrong answers)
  - Recommend KB updates

Output:
  {"patterns": List, "kb_gaps": List, "hallucinations": List, ...}
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def analyze_improvements(escalations: List[Dict]) -> Dict:
    """
    Analyze escalations to identify improvement opportunities.
    
    Step 9: Continuous Improvement
    
    Args:
        escalations: List of escalation records with reason, category, etc.
    
    Returns:
        {
            "patterns": List[str],
            "kb_gaps": List[Dict],
            "hallucinations": List[Dict],
            "recommendations": List[str],
            "kb_gaps_count": int,
            "hallucination_count": int
        }
    """
    logger.info(f"Analyzing {len(escalations)} escalations for improvements")
    
    patterns = []
    kb_gaps = []
    hallucinations = []
    recommendations = []
    
    # ====================================================================
    # PATTERN DETECTION
    # ====================================================================
    
    category_counts = {}
    reason_counts = {}
    
    for esc in escalations:
        category = esc.get("category", "autre")
        reason = esc.get("reason", "unknown")
        
        category_counts[category] = category_counts.get(category, 0) + 1
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    # Find categories with high escalation rates
    for category, count in category_counts.items():
        if count >= 3:  # 3+ escalations in same category
            pattern = f"{category.capitalize()}: {count} escalations (high rate)"
            patterns.append(pattern)
            recommendations.append(f"Review {category} KB content - {count} escalations detected")
            logger.warning(f"Pattern detected: {pattern}")
    
    # ====================================================================
    # KB GAP DETECTION
    # ====================================================================
    
    for esc in escalations:
        reason = esc.get("reason", "")
        
        # Check for "no solution found" patterns
        if "no solution" in reason.lower() or "kb gap" in reason.lower():
            kb_gap = {
                "ticket_id": esc.get("ticket_id"),
                "category": esc.get("category"),
                "reason": reason,
                "human_resolution": esc.get("human_resolution", "Unknown")
            }
            kb_gaps.append(kb_gap)
            logger.warning(f"KB gap identified: {esc.get('ticket_id')}")
    
    # ====================================================================
    # HALLUCINATION DETECTION
    # ====================================================================
    
    for esc in escalations:
        reason = esc.get("reason", "")
        
        # Check for "wrong answer" or "hallucination" patterns
        if "wrong" in reason.lower() or "hallucination" in reason.lower() or "incorrect" in reason.lower():
            hallucination = {
                "ticket_id": esc.get("ticket_id"),
                "category": esc.get("category"),
                "reason": reason,
                "human_resolution": esc.get("human_resolution", "Unknown")
            }
            hallucinations.append(hallucination)
            logger.error(f"Hallucination detected: {esc.get('ticket_id')}")
    
    # ====================================================================
    # RECOMMENDATIONS
    # ====================================================================
    
    if kb_gaps:
        recommendations.append(f"Create KB entries for {len(kb_gaps)} identified gaps")
    
    if hallucinations:
        recommendations.append(f"Review {len(hallucinations)} hallucinated answers in KB")
    
    if patterns:
        recommendations.append("Prioritize high-escalation categories for KB improvement")
    
    # ====================================================================
    # RESULT
    # ====================================================================
    
    result = {
        "patterns": patterns,
        "kb_gaps": kb_gaps,
        "hallucinations": hallucinations,
        "kb_gaps_count": len(kb_gaps),
        "hallucination_count": len(hallucinations),
        "total_escalations_analyzed": len(escalations),
        "recommendations": recommendations
    }
    
    logger.info(f"Analysis complete: {len(patterns)} patterns, {len(kb_gaps)} gaps, {len(hallucinations)} hallucinations")
    
    return result


def generate_improvement_report(analysis: Dict) -> str:
    """
    Generate a human-readable improvement report.
    """
    report = "📊 CONTINUOUS IMPROVEMENT ANALYSIS REPORT\n"
    report += "=" * 50 + "\n\n"
    
    report += f"Total Escalations Analyzed: {analysis.get('total_escalations_analyzed', 0)}\n\n"
    
    if analysis.get('patterns'):
        report += "🔍 PATTERNS DETECTED:\n"
        for pattern in analysis['patterns']:
            report += f"  • {pattern}\n"
        report += "\n"
    
    if analysis.get('kb_gaps'):
        report += f"⚠️ KB GAPS ({analysis.get('kb_gaps_count', 0)}):\n"
        for gap in analysis['kb_gaps'][:5]:  # Show first 5
            report += f"  • {gap.get('ticket_id')}: {gap.get('reason')}\n"
        report += "\n"
    
    if analysis.get('hallucinations'):
        report += f"🚨 HALLUCINATIONS ({analysis.get('hallucination_count', 0)}):\n"
        for hall in analysis['hallucinations'][:5]:  # Show first 5
            report += f"  • {hall.get('ticket_id')}: {hall.get('reason')}\n"
        report += "\n"
    
    if analysis.get('recommendations'):
        report += "✅ RECOMMENDATIONS:\n"
        for rec in analysis['recommendations']:
            report += f"  • {rec}\n"
    
    return report
