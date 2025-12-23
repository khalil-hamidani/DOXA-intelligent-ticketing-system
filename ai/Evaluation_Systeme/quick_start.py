#!/usr/bin/env python3
"""
Quick Start Script for TEAM 3 Evaluation
Demonstrates how to use the evaluation pipeline with your own questions
"""

import json
import subprocess
import sys
from pathlib import Path

def create_custom_questions(output_file: str = "my_questions.json"):
    """Create a custom questions file with new questions."""
    questions = {
        "Questions": [
            {
                "id": "Q001",
                "query": "votre question 1 ici"
            },
            {
                "id": "Q002",
                "query": "votre question 2 ici"
            },
            {
                "id": "Q003",
                "query": "votre question 3 ici"
            }
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Created {output_file}")
    return output_file

def run_evaluation(input_file: str):
    """Run the evaluation script."""
    cmd = [sys.executable, "evaluation_script.py", input_file]
    
    print(f"\n{'='*60}")
    print("Running TEAM 3 Evaluation Pipeline")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    return result.returncode == 0

def main():
    """Main entry point."""
    ai_dir = Path(__file__).parent
    
    print("\n" + "="*60)
    print("TEAM 3 - Evaluation System Quick Start")
    print("="*60 + "\n")
    
    # Check if evaluation_script exists
    script_path = ai_dir / "evaluation_script.py"
    if not script_path.exists():
        print("✗ evaluation_script.py not found!")
        sys.exit(1)
    
    print("Choose an option:")
    print("1. Run with existing questions_team3.json")
    print("2. Create new questions file")
    print("3. View existing results")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        # Run with existing questions
        questions_file = ai_dir / "questions_team3.json"
        if questions_file.exists():
            success = run_evaluation(str(questions_file))
            if success:
                print("\n✓ Evaluation completed successfully!")
        else:
            print(f"✗ {questions_file} not found!")
    
    elif choice == "2":
        # Create new questions
        custom_file = input("Enter filename for your questions (default: my_questions.json): ").strip()
        if not custom_file:
            custom_file = "my_questions.json"
        
        # Add .json if not present
        if not custom_file.endswith('.json'):
            custom_file += '.json'
        
        create_custom_questions(ai_dir / custom_file)
        
        # Ask if user wants to run evaluation
        if input("\nRun evaluation now? (y/n): ").strip().lower() == 'y':
            success = run_evaluation(custom_file)
            if success:
                print("\n✓ Evaluation completed successfully!")
    
    elif choice == "3":
        # List existing results
        results_files = list(ai_dir.glob("results_TEAM3_*.json"))
        if results_files:
            print("\nExisting results:")
            for i, f in enumerate(sorted(results_files, reverse=True), 1):
                print(f"  {i}. {f.name}")
            
            selection = input("\nSelect file to view (number): ").strip()
            try:
                selected = sorted(results_files, reverse=True)[int(selection)-1]
                with open(selected, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"\n{selected.name}:")
                    print(json.dumps(data, ensure_ascii=False, indent=2))
            except (ValueError, IndexError):
                print("Invalid selection")
        else:
            print("No results files found")
    
    print("\n" + "="*60)
    print("For more information, see EVALUATION_SCRIPT_README.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
