#!/usr/bin/env python3
"""
AgentOS Server for DOXA Intelligent Ticketing System
Integrates 4 AI Agents (Validator, Scorer, Query Analyzer, Classifier) with Mistral LLM
Runs on port 7777 for os.agno.com Control Plane connection
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent
from agno.tools.tavily import TavilyTools
from agno.models.mistral import MistralChat
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import our custom agents and utilities
from agents.config import MISTRAL_API_KEY, TAVILY_API_KEY, MISTRAL_MODEL_ID
from agents.orchestrator import process_ticket
from models import Ticket, Feedback

# Verify API keys
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found in environment")

logger.info("✓ API Keys loaded successfully")
logger.info(f"✓ Mistral API Key: {MISTRAL_API_KEY[:10]}...")


# ============================================================================
# DOXA Intelligent Ticketing Agent
# ============================================================================
def create_ticketing_agent():
    """Create the main ticketing agent that processes support tickets"""
    return Agent(
        name="DOXA Ticketing System",
        role="Intelligent Support Ticket Processor",
        model=MistralChat(
            id=MISTRAL_MODEL_ID,
            api_key=MISTRAL_API_KEY,
        ),
        tools=[TavilyTools()] if TAVILY_API_KEY else [],
        description="""
        I am DOXA's intelligent ticketing system powered by Mistral LLM.
        
        I process support tickets through 4 specialized AI agents:
        1. **Validator**: Checks ticket clarity and completeness
        2. **Scorer**: Assigns priority scores (0-100)
        3. **Query Analyzer**: Reformulates and analyzes problems
        4. **Classifier**: Categorizes tickets (technical/billing/auth/other)
        
        I can:
        - Analyze incoming support tickets
        - Provide intelligent routing and prioritization
        - Suggest solutions based on knowledge base
        - Track ticket status and metrics
        - Generate feedback for continuous improvement
        """,
        instructions="""
        You are DOXA's intelligent ticketing system. When processing tickets:
        
        1. **Validate** the ticket for clarity and completeness
        2. **Score** the priority based on urgency and impact
        3. **Analyze** the query and reformulate it for clarity
        4. **Classify** the ticket into appropriate categories
        5. **Suggest** solutions from knowledge base
        6. **Route** to appropriate team based on classification
        
        Always provide:
        - Confidence scores for your assessments
        - Clear reasoning for decisions
        - Suggested next steps
        - Knowledge base references when applicable
        
        Be professional, helpful, and thorough in your analysis.
        """,
        markdown=True,
        add_datetime_to_context=True,
    )


# ============================================================================
# Create Agent Instances
# ============================================================================
logger.info("🤖 Creating DOXA Ticketing Agent...")
ticketing_agent = create_ticketing_agent()
logger.info("✓ Agent created successfully")


# ============================================================================
# Playground Setup (Optional - for testing in browser)
# ============================================================================
def create_fastapi_app():
    """Create FastAPI app for AgentOS integration"""
    app = FastAPI(
        title="DOXA Intelligent Ticketing System",
        description="AI-Powered Support Ticket Management with AgentOS",
        version="1.0.0"
    )
    
    @app.get("/")
    async def root():
        """Root endpoint - health check"""
        return {
            "status": "healthy",
            "service": "DOXA Intelligent Ticketing System",
            "port": 7777,
            "integration": "os.agno.com",
            "agents": ["Validator", "Scorer", "Query Analyzer", "Classifier"]
        }
    
    @app.get("/health")
    async def health():
        """Health endpoint for AgentOS"""
        return {
            "status": "healthy",
            "service": "DOXA Ticketing",
            "ready": True
        }
    
    @app.post("/process-ticket")
    async def process_ticket_endpoint(ticket: Ticket):
        """Process a support ticket through all AI agents"""
        try:
            result = await process_ticket(ticket)
            return {
                "status": "success",
                "ticket_id": result.get("id"),
                "validation": result.get("validation"),
                "score": result.get("score"),
                "analysis": result.get("analysis"),
                "classification": result.get("classification")
            }
        except Exception as e:
            logger.error(f"Error processing ticket: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @app.post("/agent/chat")
    async def agent_chat(message: str):
        """Chat with the ticketing agent"""
        try:
            response = ticketing_agent.run(message)
            return {
                "status": "success",
                "agent_response": response
            }
        except Exception as e:
            logger.error(f"Agent error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    return app


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DOXA AgentOS Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=7777, help="Server port")
    parser.add_argument("--playground", action="store_true", help="Enable playground UI")
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("[AGENTOSS SERVER] DOXA INTELLIGENT TICKETING SYSTEM")
    print("="*70)
    print(f"[INFO] Host: {args.host}")
    print(f"[INFO] Port: {args.port}")
    print(f"[INFO] Playground: {'Enabled' if args.playground else 'Disabled'}")
    print(f"[INFO] Connection: os.agno.com Control Plane")
    print("="*70 + "\n")
    
    if args.playground:
        logger.info("Starting with FastAPI interface...")
        app = create_fastapi_app()
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info",
        )
    else:
        logger.info("Starting AgentOS server for os.agno.com...")
        app = create_fastapi_app()
        logger.info(f"Server running on http://{args.host}:{args.port}")
        logger.info("Register this server in os.agno.com Control Plane at:")
        logger.info("  https://os.agno.com/settings/servers")
        logger.info("Available endpoints:")
        logger.info("  GET / - Health check")
        logger.info("  GET /health - AgentOS health check")
        logger.info("  POST /process-ticket - Process support ticket")
        logger.info("  POST /agent/chat - Chat with DOXA agent")
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info",
        )
