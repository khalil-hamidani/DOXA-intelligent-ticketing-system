"""
Configuration for Agno agents.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables
env_path = find_dotenv(os.path.join(Path(__file__).parent.parent, '.env'))
load_dotenv(env_path)

# ============================================================================
# LLM Configuration
# ============================================================================

# Mistral API
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY")
MISTRAL_MODEL_ID = os.environ.get("MISTRAL_MODEL_ID", "mistral-small-latest")

# Alternative models
# "mistral-small-latest": Fastest, ~$0.00014/1K tokens
# "mistral-medium-latest": Balanced
# "mistral-large-latest": Most capable, ~$0.00024/1K tokens

# Tavily API (optional, for search tools)
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY") or os.environ.get("TVLY_API_KEY")

# ============================================================================
# Agent Configuration
# ============================================================================

# Temperature values for different agents
# Lower = more consistent/deterministic
# Higher = more creative/varied
AGENT_TEMPERATURE = {
    "validator": 0.3,      # Strict validation
    "scorer": 0.3,         # Consistent scoring
    "reformulator": 0.4,   # Some flexibility in reformulation
    "classifier": 0.3,     # Consistent classification
}

# Timeout settings
AGENT_RUN_TIMEOUT = 10  # seconds
LLM_API_TIMEOUT = 5     # seconds

# Retry logic
MAX_RETRIES = 1
RETRY_DELAY = 1  # seconds

# ============================================================================
# Output Validation
# ============================================================================

# Categories
VALID_CATEGORIES = ["technique", "facturation", "authentification", "autre"]

# Priority levels
VALID_PRIORITIES = ["low", "medium", "high"]

# Treatment types
VALID_TREATMENT_TYPES = ["standard", "priority", "escalation", "urgent"]

# Severity levels
VALID_SEVERITY_LEVELS = ["low", "medium", "high"]

# Score ranges
MIN_SCORE = 0
MAX_SCORE = 100
LOW_PRIORITY_THRESHOLD = 35
HIGH_PRIORITY_THRESHOLD = 70

# ============================================================================
# Logging
# ============================================================================

ENABLE_AGENT_LOGGING = os.environ.get("ENABLE_AGENT_LOGGING", "false").lower() == "true"
LOG_LLM_RESPONSES = os.environ.get("LOG_LLM_RESPONSES", "false").lower() == "true"

# ============================================================================
# API Setup
# ============================================================================

def setup_api_keys():
    """Ensure API keys are set in environment."""
    if MISTRAL_API_KEY:
        os.environ["MISTRALAI_API_KEY"] = MISTRAL_API_KEY
    
    if TAVILY_API_KEY:
        os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

# Call on import
setup_api_keys()
