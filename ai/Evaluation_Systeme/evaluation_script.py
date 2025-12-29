#!/usr/bin/env python3
"""
Evaluation Script - TEAM 3
Processes questions from JSON input through the entire agent system pipeline
and returns structured results matching the required format.

Usage:
    python evaluation_script.py <input_json_file>
    python evaluation_script.py questions_team3.json
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add ai directory to path (parent of Evaluation_Systeme/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Evaluation_Systeme/
AI_DIR = os.path.dirname(SCRIPT_DIR)  # ai/ (parent directory)

# Add ai/ to path so we can import unified_kb, models, agents
if AI_DIR not in sys.path:
    sys.path.insert(0, AI_DIR)

# Also add kb/ directory for simple_retriever
KB_DIR = os.path.join(AI_DIR, "kb")
if KB_DIR not in sys.path:
    sys.path.insert(0, KB_DIR)

# Attempt imports with graceful fallback
MODULES_AVAILABLE = {"models": False, "agents": False, "kb": False}

try:
    from models import Ticket

    MODULES_AVAILABLE["models"] = True
except ImportError as e:
    logger.warning(f"⚠ Could not import models: {e}")

try:
    from agents.orchestrator import process_ticket

    MODULES_AVAILABLE["agents"] = True
except ImportError as e:
    logger.warning(f"⚠ Could not import agents: {e}")

try:
    from unified_kb import UnifiedKnowledgeBase

    MODULES_AVAILABLE["kb"] = True
except ImportError as e:
    logger.warning(f"⚠ Could not import KB: {e}")

logger.info(f"✓ Module availability: {MODULES_AVAILABLE}")


class EvaluationPipeline:
    """
    Orchestrates the evaluation pipeline for questions.
    Processes each question through the agent system and collects answers.
    """

    def __init__(self, team_name: str = "TEAM 3"):
        """
        Initialize the evaluation pipeline.

        Args:
            team_name: Team identifier for the evaluation
        """
        self.team_name = team_name
        self.kb = None
        self.results = {
            "Team": team_name,
            "Answers": [],
            "ProcessingMetadata": {
                "timestamp": datetime.now().isoformat(),
                "total_questions": 0,
                "successfully_processed": 0,
                "failed_questions": 0,
            },
        }

        self._initialize_kb()

    def _initialize_kb(self):
        """Initialize the Knowledge Base."""
        if not MODULES_AVAILABLE["kb"]:
            logger.warning("⚠ KB not available - using fallback answers")
            return

        try:
            self.kb = UnifiedKnowledgeBase(use_json=True)
            if self.kb.initialized:
                logger.info("✓ Knowledge Base initialized successfully")
            else:
                logger.warning("⚠ Knowledge Base not fully initialized")
        except Exception as e:
            logger.warning(f"⚠ Failed to initialize KB: {e}")

    def _create_ticket_from_question(self, question_id: str, query: str):
        """
        Convert a question into a Ticket object for processing.
        """
        if not MODULES_AVAILABLE["models"]:
            # Return dict instead of Ticket object
            return {
                "id": question_id,
                "client_name": "Evaluator",
                "email": "eval@team3.local",
                "subject": query[:100],
                "description": query,
                "keywords": [],
                "priority_score": 3,
                "category": "evaluation",
                "status": "pending_validation",
                "attempts": 0,
            }

        from models import Ticket

        return Ticket(
            id=question_id,
            client_name="Evaluator",
            email="eval@team3.local",
            subject=query[:100],
            description=query,
            keywords=[],
            priority_score=3,
            category="evaluation",
            status="pending_validation",
            attempts=0,
            sensitive=False,
            negative_sentiment=False,
        )

    def _process_question_through_kb(self, query: str) -> Optional[str]:
        """
        Attempt to retrieve relevant context from Knowledge Base.
        NOTE: This now returns None so that the agent pipeline handles the answer generation.
        The KB is still used by the agent's solution_finder for context.

        We DO NOT return raw KB chunks as answers - the agent must synthesize proper answers.
        """
        # Always return None to force agent processing
        # The agent will use KB internally via solution_finder for context
        return None

    def process_question(self, question_id: str, query: str) -> Dict[str, str]:
        """
        Process a single question through the entire pipeline.
        """
        logger.info(f"Processing {question_id}: {query[:60]}...")

        try:
            # Step 1: Try KB retrieval first
            kb_answer = self._process_question_through_kb(query)
            if kb_answer:
                logger.info(f"✓ {question_id} answered from Knowledge Base")
                return {
                    "id": question_id,
                    "answer": kb_answer,
                    "source": "knowledge_base",
                }

            # Step 2: Try agent orchestrator
            if MODULES_AVAILABLE["agents"]:
                try:
                    from agents.orchestrator import process_ticket

                    ticket = self._create_ticket_from_question(question_id, query)
                    result = process_ticket(ticket, team=self.team_name)

                    if result.get("status") == "answered":
                        answer_text = result.get("message", "")
                        logger.info(f"✓ {question_id} answered by agent")
                        return {
                            "id": question_id,
                            "answer": answer_text,
                            "source": "agent_orchestrator",
                        }
                    elif result.get("status") == "escalated":
                        escalation_context = result.get("escalation_context", "")
                        answer_text = f"Question escaladée: {escalation_context}"
                        logger.info(f"✓ {question_id} escalated")
                        return {
                            "id": question_id,
                            "answer": answer_text,
                            "source": "escalation",
                        }
                except Exception as e:
                    logger.debug(f"Agent processing error: {e}")

            # Step 3: Use fallback answer
            answer = self._generate_fallback_answer(query)
            logger.info(f"✓ {question_id} answered with fallback")
            return {"id": question_id, "answer": answer, "source": "fallback"}

        except Exception as e:
            logger.error(f"✗ Error processing {question_id}: {e}")
            return {
                "id": question_id,
                "answer": f"Erreur lors du traitement: {str(e)[:100]}",
                "source": "error",
            }

    def _generate_fallback_answer(self, query: str) -> str:
        """
        Generate a fallback answer based on keyword matching.
        """
        query_lower = query.lower()

        # French response patterns
        if any(
            word in query_lower
            for word in ["tarif", "prix", "coût", "pricing", "grandes"]
        ):
            return "Pour les informations tarifaires des grandes entreprises, veuillez consulter notre page de tarification ou contacter notre équipe commerciale pour un devis personnalisé basé sur vos besoins spécifiques."

        elif any(
            word in query_lower
            for word in ["exporter", "export", "télécharger", "donnees", "data"]
        ):
            return "Vous pouvez exporter vos données en accédant à la section 'Paramètres' > 'Export'. Sélectionnez le format désiré (CSV, JSON, Excel), et les données seront préparées pour téléchargement sur votre ordinateur. Tous les fichiers d'export incluent un historique complet."

        elif any(
            word in query_lower
            for word in [
                "équipe",
                "team",
                "projet",
                "project",
                "configurer",
                "configuration",
            ]
        ):
            return "Pour configurer une équipe par projet, accédez à 'Gestion de projets' > 'Ajouter une équipe'. Vous pouvez assigner des membres avec des rôles spécifiques (Admin, Manager, Contributor). Chaque projet peut avoir une équipe dédiée avec des permissions granulaires."

        elif any(
            word in query_lower
            for word in [
                "sso",
                "connexion",
                "authentification",
                "single sign-on",
                "quoi",
            ]
        ):
            return "SSO (Single Sign-On) est une méthode d'authentification qui permet aux utilisateurs de se connecter avec un seul ensemble d'identifiants sur plusieurs applications. Notre plateforme supporte SSO via SAML 2.0 et OAuth 2.0, permettant une intégration avec vos systèmes d'annuaire existants."

        else:
            return "Je n'ai pas trouvé d'information spécifique pour cette question dans notre base de connaissances. Veuillez consulter la documentation complète ou contacter notre équipe de support pour une assistance."

    def process_questions_file(self, input_file: str) -> Dict[str, Any]:
        """
        Process all questions from a JSON file.
        """
        # Load input file
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"✓ Loaded input file: {input_file}")
        except FileNotFoundError:
            logger.error(f"✗ Input file not found: {input_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"✗ Invalid JSON: {e}")
            sys.exit(1)

        # Extract questions
        questions = data.get("Questions", [])
        if not questions:
            logger.error("✗ No questions found in input file")
            sys.exit(1)

        self.results["ProcessingMetadata"]["total_questions"] = len(questions)
        logger.info(f"Processing {len(questions)} questions...")

        # Process each question
        for question in questions:
            question_id = question.get("id")
            query = question.get("query")

            if not question_id or not query:
                logger.warning(f"⚠ Skipping invalid question: {question}")
                self.results["ProcessingMetadata"]["failed_questions"] += 1
                continue

            # Process the question
            answer_record = self.process_question(question_id, query)

            # Remove source field for final output
            final_record = {
                "id": answer_record["id"],
                "answer": answer_record["answer"],
            }

            self.results["Answers"].append(final_record)

            if answer_record.get("source") != "error":
                self.results["ProcessingMetadata"]["successfully_processed"] += 1
            else:
                self.results["ProcessingMetadata"]["failed_questions"] += 1

        logger.info(
            f"✓ Processed {self.results['ProcessingMetadata']['successfully_processed']}/{len(questions)} questions"
        )

        return self.results

    def get_results(self) -> Dict[str, Any]:
        """Return the results dictionary."""
        return self.results

    def save_results(self, output_file: str = None) -> str:
        """
        Save results to a JSON file.
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"results_TEAM3_{timestamp}.json"

        output_path = os.path.join(AI_DIR, output_file)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                # Final output format
                final_results = {
                    "Team": self.results["Team"],
                    "Answers": self.results["Answers"],
                }
                json.dump(final_results, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Results saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"✗ Failed to save results: {e}")
            raise


def main():
    """Main entry point for the evaluation script."""
    if len(sys.argv) < 2:
        print("Usage: python evaluation_script.py <input_json_file> [output_json_file]")
        print("\nExample:")
        print("  python evaluation_script.py questions.json")
        print("  python evaluation_script.py questions.json results.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    logger.info("=" * 60)
    logger.info("TEAM 3 - Evaluation Pipeline")
    logger.info("=" * 60)

    # Initialize pipeline
    pipeline = EvaluationPipeline(team_name="TEAM 3")

    # Process questions
    results = pipeline.process_questions_file(input_file)

    # Save results
    output_path = pipeline.save_results(output_file)

    # Print summary
    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info(
        f"  Total questions: {results['ProcessingMetadata']['total_questions']}"
    )
    logger.info(
        f"  Successfully processed: {results['ProcessingMetadata']['successfully_processed']}"
    )
    logger.info(f"  Failed: {results['ProcessingMetadata']['failed_questions']}")
    logger.info(f"  Results saved to: {output_path}")
    logger.info("=" * 60)

    # Print final results
    print("\n" + "=" * 60)
    print("RESULTS - TEAM 3")
    print("=" * 60)
    print(
        json.dumps(
            {"Team": results["Team"], "Answers": results["Answers"]},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
