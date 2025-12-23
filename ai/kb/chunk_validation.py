#!/usr/bin/env python3
"""
TEAM 3 - Chunk Validation and Quality Metrics
Adds validation layer to chunking process
"""

import os
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChunkQualityMetrics:
    """Metrics for chunk quality assessment"""
    chunk_id: str
    size: int
    line_count: int
    avg_line_length: float
    has_header: bool
    coherence_score: float  # 0-1
    is_valid: bool


class ChunkValidator:
    """Comprehensive chunk validation"""
    
    def __init__(self, min_size: int = 100, max_size: int = 1000, 
                 min_coherence: float = 0.5):
        self.min_size = min_size
        self.max_size = max_size
        self.min_coherence = min_coherence
        self.validation_log = []
    
    def assess_coherence(self, chunk: str) -> float:
        """
        Assess chunk coherence (0-1)
        Based on: word count uniformity, structure, etc.
        """
        lines = chunk.strip().split('\n')
        
        if not lines:
            return 0.0
        
        # Check for markdown headers (good structure indicator)
        has_header = any(line.startswith('#') for line in lines)
        header_score = 0.3 if has_header else 0.0
        
        # Check line length uniformity
        line_lengths = [len(l.strip()) for l in lines if l.strip()]
        if line_lengths:
            avg_length = sum(line_lengths) / len(line_lengths)
            min_length = min(line_lengths)
            max_length = max(line_lengths)
            
            # High variance = low coherence
            if avg_length > 0:
                variance_ratio = (max_length - min_length) / avg_length
                uniformity_score = max(0, 1 - variance_ratio * 0.1)
            else:
                uniformity_score = 0.0
        else:
            uniformity_score = 0.0
        
        # Check for meaningful content (word count)
        word_count = len(chunk.split())
        content_score = min(1.0, word_count / 50)  # 50+ words = good
        
        # Weighted average
        coherence = (header_score * 0.2 + uniformity_score * 0.4 + content_score * 0.4)
        
        return round(coherence, 2)
    
    def validate_chunk(self, chunk: str, chunk_id: str = "unknown") -> ChunkQualityMetrics:
        """Validate a single chunk"""
        
        size = len(chunk)
        lines = [l for l in chunk.split('\n') if l.strip()]
        line_count = len(lines)
        
        avg_line_len = (
            sum(len(l.strip()) for l in lines) / line_count 
            if line_count > 0 else 0
        )
        
        has_header = any(line.startswith('#') for line in lines)
        coherence = self.assess_coherence(chunk)
        
        # Validity checks
        is_valid = (
            self.min_size <= size <= self.max_size and
            coherence >= self.min_coherence and
            line_count >= 2
        )
        
        metrics = ChunkQualityMetrics(
            chunk_id=chunk_id,
            size=size,
            line_count=line_count,
            avg_line_length=round(avg_line_len, 1),
            has_header=has_header,
            coherence_score=coherence,
            is_valid=is_valid
        )
        
        # Log validation
        if not is_valid:
            reasons = []
            if size < self.min_size:
                reasons.append(f"Too small ({size} < {self.min_size})")
            if size > self.max_size:
                reasons.append(f"Too large ({size} > {self.max_size})")
            if coherence < self.min_coherence:
                reasons.append(f"Low coherence ({coherence} < {self.min_coherence})")
            if line_count < 2:
                reasons.append(f"Too few lines ({line_count})")
            
            self.validation_log.append({
                "chunk_id": chunk_id,
                "status": "INVALID",
                "reasons": reasons,
                "metrics": {
                    "size": size,
                    "coherence": coherence
                }
            })
        
        return metrics
    
    def validate_batch(self, chunks: List[str]) -> Dict:
        """Validate multiple chunks"""
        
        all_metrics = []
        valid_count = 0
        
        for i, chunk in enumerate(chunks):
            metrics = self.validate_chunk(chunk, chunk_id=f"chunk_{i:04d}")
            all_metrics.append(metrics)
            
            if metrics.is_valid:
                valid_count += 1
        
        # Compute statistics
        valid_pct = (valid_count / len(chunks) * 100) if chunks else 0
        avg_coherence = (
            sum(m.coherence_score for m in all_metrics) / len(all_metrics)
            if all_metrics else 0
        )
        
        return {
            "total_chunks": len(chunks),
            "valid_chunks": valid_count,
            "invalid_chunks": len(chunks) - valid_count,
            "validity_rate_percent": round(valid_pct, 1),
            "average_coherence": round(avg_coherence, 2),
            "all_metrics": [
                {
                    "chunk_id": m.chunk_id,
                    "size": m.size,
                    "line_count": m.line_count,
                    "avg_line_length": m.avg_line_length,
                    "has_header": m.has_header,
                    "coherence_score": m.coherence_score,
                    "is_valid": m.is_valid
                }
                for m in all_metrics
            ],
            "validation_issues": self.validation_log
        }


class ChunkOverlapValidator:
    """Validates chunk overlap and continuity"""
    
    @staticmethod
    def compute_overlap(chunk1: str, chunk2: str) -> float:
        """Compute character-level overlap between consecutive chunks"""
        
        if not chunk1 or not chunk2:
            return 0.0
        
        # Find common suffix of chunk1 with prefix of chunk2
        max_overlap = min(len(chunk1), len(chunk2))
        
        for i in range(max_overlap, 0, -1):
            if chunk1[-i:] == chunk2[:i]:
                return i / max(len(chunk1), len(chunk2))
        
        return 0.0
    
    @staticmethod
    def validate_overlaps(chunks: List[str], 
                         target_overlap_pct: float = 10) -> Dict:
        """Validate overlap between consecutive chunks"""
        
        if len(chunks) < 2:
            return {"status": "insufficient_chunks", "chunks": len(chunks)}
        
        overlaps = []
        
        for i in range(len(chunks) - 1):
            overlap_ratio = ChunkOverlapValidator.compute_overlap(
                chunks[i], chunks[i+1]
            )
            overlap_pct = overlap_ratio * 100
            overlaps.append({
                "pair": (i, i+1),
                "overlap_percent": round(overlap_pct, 1),
                "valid": abs(overlap_pct - target_overlap_pct) < 5
            })
        
        # Statistics
        valid_overlaps = sum(1 for o in overlaps if o["valid"])
        
        return {
            "total_pairs": len(overlaps),
            "valid_pairs": valid_overlaps,
            "validity_rate_percent": round(valid_overlaps / len(overlaps) * 100, 1),
            "target_overlap_percent": target_overlap_pct,
            "overlaps": overlaps
        }


def generate_validation_report(chunks: List[str], 
                              output_file: str = "chunk_validation_report.json") -> Dict:
    """Generate comprehensive validation report"""
    
    report = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "summary": {
            "total_chunks": len(chunks),
            "average_size": round(sum(len(c) for c in chunks) / len(chunks), 1) if chunks else 0
        },
        "validations": {}
    }
    
    # Quality validation
    validator = ChunkValidator(min_size=100, max_size=1000, min_coherence=0.5)
    quality_results = validator.validate_batch(chunks)
    report["validations"]["quality"] = quality_results
    
    # Overlap validation
    overlap_results = ChunkOverlapValidator.validate_overlaps(chunks, target_overlap_pct=10)
    report["validations"]["overlap"] = overlap_results
    
    # Status
    quality_ok = quality_results["validity_rate_percent"] >= 80
    overlap_ok = overlap_results["validity_rate_percent"] >= 80
    
    report["overall_status"] = "PASS" if (quality_ok and overlap_ok) else "FAIL"
    
    # Recommendations
    recommendations = []
    
    if not quality_ok:
        recommendations.append(
            f"Improve chunk quality: {100 - quality_results['validity_rate_percent']:.1f}% "
            f"invalid chunks. Review size and coherence requirements."
        )
    
    if not overlap_ok:
        recommendations.append(
            f"Adjust chunk overlap: Current overlap doesn't match target {overlap_results['target_overlap_percent']}%. "
            f"Adjust chunking parameters."
        )
    
    if quality_results["average_coherence"] < 0.6:
        recommendations.append(
            f"Low coherence score ({quality_results['average_coherence']}). "
            f"Use semantic chunking instead of fixed-size chunking."
        )
    
    report["recommendations"] = recommendations
    
    # Save report
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report


if __name__ == "__main__":
    # Example usage
    sample_chunks = [
        "# Section 1\nThis is a valid chunk with sufficient content about important topics.",
        "Short",
        "# Section 2\nAnother valid chunk with good structure and meaningful content about various subjects."
    ]
    
    report = generate_validation_report(sample_chunks)
    print(json.dumps(report, ensure_ascii=False, indent=2))
