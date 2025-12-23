#!/usr/bin/env python3
"""
Batch Evaluation Script - TEAM 3
Process multiple question files and generate combined results
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

AI_DIR = Path(__file__).parent


class BatchEvaluator:
    """Process multiple question files in batch."""
    
    def __init__(self, team_name: str = "TEAM 3"):
        self.team_name = team_name
        self.results = []
    
    def process_batch(self, input_files: List[str]) -> Dict[str, Any]:
        """
        Process multiple question files.
        
        Args:
            input_files: List of input JSON file paths
            
        Returns:
            Combined results dictionary
        """
        logger.info(f"Processing {len(input_files)} files in batch...")
        
        for input_file in input_files:
            logger.info(f"\nProcessing: {input_file}")
            
            try:
                # Import dynamically to avoid circular imports
                from ai.Evaluation_Systeme.evaluation_script import EvaluationPipeline
                
                pipeline = EvaluationPipeline(self.team_name)
                results = pipeline.process_questions_file(input_file)
                
                self.results.append({
                    "source_file": input_file,
                    "timestamp": datetime.now().isoformat(),
                    "answers": results["Answers"]
                })
                
                logger.info(f"✓ Processed {len(results['Answers'])} answers from {input_file}")
                
            except Exception as e:
                logger.error(f"✗ Failed to process {input_file}: {e}")
        
        return self._compile_results()
    
    def _compile_results(self) -> Dict[str, Any]:
        """Compile all results into single output."""
        all_answers = []
        
        for batch in self.results:
            all_answers.extend(batch["answers"])
        
        return {
            "Team": self.team_name,
            "BatchInfo": {
                "total_files": len(self.results),
                "total_questions": len(all_answers),
                "processed_at": datetime.now().isoformat()
            },
            "Answers": all_answers
        }
    
    def save_results(self, output_file: str = None) -> str:
        """Save compiled results to file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"batch_results_TEAM3_{timestamp}.json"
        
        output_path = AI_DIR / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self._compile_results(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ Batch results saved to: {output_path}")
        return str(output_path)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python batch_evaluation.py <file1.json> [file2.json] [file3.json] ...")
        print("\nExample:")
        print("  python batch_evaluation.py questions_team3.json my_questions.json")
        sys.exit(1)
    
    input_files = sys.argv[1:]
    output_file = None
    
    # Check for --output flag
    if "--output" in input_files:
        idx = input_files.index("--output")
        output_file = input_files[idx + 1]
        input_files = input_files[:idx] + input_files[idx+2:]
    
    logger.info("="*60)
    logger.info("TEAM 3 - Batch Evaluation Pipeline")
    logger.info("="*60)
    
    evaluator = BatchEvaluator(team_name="TEAM 3")
    evaluator.process_batch(input_files)
    
    output_path = evaluator.save_results(output_file)
    
    # Print summary
    results = evaluator._compile_results()
    logger.info("="*60)
    logger.info("Batch Processing Summary:")
    logger.info(f"  Files processed: {results['BatchInfo']['total_files']}")
    logger.info(f"  Total questions: {results['BatchInfo']['total_questions']}")
    logger.info(f"  Results saved to: {output_path}")
    logger.info("="*60)
    
    print("\n" + json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
