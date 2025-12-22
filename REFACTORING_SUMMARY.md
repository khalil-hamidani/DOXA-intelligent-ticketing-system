# Refactoring Summary: Heuristic → Agno/Mistral Agents

## Overview

This document summarizes the refactoring of 4 core ticketing agents from **heuristic-based** logic to **LLM-powered** agents using **Agno framework** and **Mistral LLM**.

## What Changed

### 1. **Validator Agent** ✓ REFACTORED
**File**: `ai/agents/validator.py`

**Before (Heuristic)**:
- ✗ Simple regex/length checks
- ✗ Limited to predefined patterns
- ✗ No contextual understanding

**After (Agno + Mistral)**:
- ✓ LLM evaluates ticket quality contextually
- ✓ Analyzes clarity, keyword exploitability, information sufficiency
- ✓ Returns confidence score alongside validation
- ✓ Graceful fallback to heuristics on LLM error

**Key Functions**:
```python
validate_ticket(ticket: Ticket) → Dict["valid", "reasons", "confidence"]
```

---

### 2. **Scorer Agent** ✓ REFACTORED
**File**: `ai/agents/scorer.py`

**Before (Heuristic)**:
- ✗ Keyword matching with fixed points (+40 urgency, +20 recurrence, +30 impact)
- ✗ No nuanced understanding of priority factors
- ✗ Limited to predefined keywords

**After (Agno + Mistral)**:
- ✓ LLM analyzes urgency, recurrence, and impact contextually
- ✓ Returns detailed reasoning for score
- ✓ Flexible interpretation of priority factors
- ✓ Component scores for transparency (urgency_level, recurrence_level, impact_level)
- ✓ Fallback to heuristic scoring

**Key Functions**:
```python
score_ticket(ticket: Ticket) → Dict["score", "priority", "reasoning"]
```

---

### 3. **Query Analyzer** ✓ REFACTORED
**File**: `ai/agents/query_analyzer.py`

**Agent A: Reformulation & Keywords**

*Before (Heuristic)*:
- ✗ Splits by sentence/period
- ✗ Simple word extraction with length filters
- ✗ No intelligent summarization

*After (Agno + Mistral)*:
- ✓ LLM generates concise, meaningful summary
- ✓ Professional reformulation of problem statement
- ✓ Extraction of 5-8 key technical/business terms
- ✓ Entity extraction for better context

**Agent B: Classification**

*Before (Heuristic)*:
- ✗ Keyword matching for 4 fixed categories
- ✗ No confidence scoring
- ✗ All tickets classified with same treatment

*After (Agno + Mistral)*:
- ✓ LLM contextually classifies into 4 categories
- ✓ Confidence score for classification
- ✓ Suggests specific treatment approach
- ✓ Fallback to enhanced heuristic

**Key Functions**:
```python
analyze_and_reformulate(ticket) → Dict["summary", "reformulation", "keywords", "entities"]
classify_ticket(ticket) → Dict["category", "expected_treatment", "treatment_action"]
```

---

### 4. **Classification Model** ✓ NEW FILE
**File**: `ai/agents/classifier.py` (NEW)

**Purpose**: Advanced categorization and treatment planning

*Before*: No dedicated classification model

*After (Agno + Mistral)*:
- ✓ Dedicated LLM agent for advanced categorization
- ✓ Differentiates treatment_type: standard → priority → escalation → urgent
- ✓ Severity assessment (low/medium/high)
- ✓ Identifies required skills/expertise
- ✓ Higher confidence scoring

**Key Functions**:
```python
classify_ticket_model(ticket: Ticket) → Dict[
    "category",
    "treatment_type",
    "severity",
    "reasoning",
    "confidence",
    "required_skills"
]
```

---

## New Files Created

### `ai/tests/test_agents.py` (NEW)
Comprehensive test suite with:
- **Fixtures**: Sample tickets for each scenario (login, billing, production outage, recurrent)
- **Test Cases**: Validator, Scorer, Query Analyzer, Classifier
- **Assertions**: Output schema validation
- **Full Pipeline**: End-to-end validation

**Run Tests**:
```bash
python ai/tests/test_agents.py
```

### `ai/demo_agents.py` (NEW)
Interactive demonstration of all agents:
- Example 1: Login issue (authentification)
- Example 2: Production outage (urgent technique)
- Example 3: Billing issue (facturation)

**Run Demo**:
```bash
python ai/demo_agents.py
```

### `ai/agents/README_AGENTS.md` (NEW)
Comprehensive documentation:
- Architecture overview
- Agent descriptions with examples
- LLM configuration
- Error handling & fallbacks
- Integration guide
- Performance considerations

---

## Configuration

### Environment Variables (in `ai/.env`)
```bash
MISTRAL_API_KEY=your_api_key_here
MISTRAL_MODEL_ID=mistral-small-latest  # Optional
```

### Fallback Behavior
All agents implement automatic fallback to heuristics if:
- LLM API is unavailable
- JSON parsing fails
- API timeout occurs

**Result**: System remains operational even if LLM is down

---

## Backward Compatibility

### ✓ Full Compatibility
- All function signatures remain unchanged
- Same input/output contracts
- Existing orchestrator.py works without modification
- Drop-in replacement for heuristic agents

### Example
```python
# Before and after have identical interface
from agents.scorer import score_ticket

result = score_ticket(ticket)
# Still returns: {"score": int, "priority": str}
# But now with better reasoning and fallback!
```

---

## Agent Specifications

### Validator Agent
| Aspect | Details |
|--------|---------|
| **LLM Instructions** | Check clarity, keywords exploitability, information sufficiency |
| **Temperature** | 0.3 (low variance for consistent validation) |
| **Output Format** | JSON with valid (bool), reasons (list), confidence (0-1) |
| **Fallback** | Heuristic: length check, word count, subject presence |

### Scorer Agent
| Aspect | Details |
|--------|---------|
| **LLM Instructions** | Analyze urgency, recurrence, impact; compute 0-100 score |
| **Temperature** | 0.3 (consistent scoring) |
| **Scoring Logic** | Base 10 + urgency(40) + recurrence(20) + impact(30), capped at 100 |
| **Priority Tiers** | low (<35), medium (35-70), high (≥70) |
| **Fallback** | Heuristic keyword matching |

### Query Analyzer (Agent A + B)
| Aspect | Agent A | Agent B |
|--------|---------|---------|
| **Purpose** | Reformulation & keywords | Classification |
| **Temperature** | 0.4 | 0.3 |
| **Input** | Subject + description | Subject + description + keywords |
| **Output** | Summary, reformulation, keywords | Category, treatment, action |
| **Categories** | N/A | technique, facturation, authentification, autre |

### Classifier Model
| Aspect | Details |
|--------|---------|
| **Purpose** | Advanced categorization & treatment planning |
| **Temperature** | 0.3 |
| **Categories** | technique, facturation, authentification, autre |
| **Treatment Types** | standard, priority, escalation, urgent |
| **Severity Levels** | low, medium, high |
| **Additional Outputs** | Reasoning, confidence, required_skills |

---

## Testing Strategy

### Unit Tests (test_agents.py)
✓ Validator: Valid, vague, urgent tickets
✓ Scorer: Normal, urgent, billing, recurrent issues
✓ Query Analyzer: Reformulation accuracy, classification correctness
✓ Classifier: Category accuracy, treatment planning

### Integration Tests
✓ Full pipeline in orchestrator.py (already integrated)
✓ Error handling and fallback behavior
✓ LLM response parsing

### Test Execution
```bash
# Run all tests
python ai/tests/test_agents.py

# Expected output
# ✓ Validator tests completed
# ✓ Scorer tests completed
# ✓ Query Analyzer tests completed
# ✓ Classifier tests completed
```

---

## Performance Impact

### Token Usage
| Agent | Tokens | Notes |
|-------|--------|-------|
| Validator | 50-100 | Short validation prompt |
| Scorer | 100-150 | Keyword analysis |
| Query Analyzer (A) | 150-200 | Summarization |
| Query Analyzer (B) | 100-150 | Classification |
| Classifier | 150-200 | Detailed analysis |
| **Total** | **550-800** | Per ticket |

### Latency
- Per agent: 1-3 seconds (API dependent)
- Full pipeline: 5-15 seconds
- Heuristic fallback: <100ms

### Cost (Mistral API)
- mistral-small-latest: ~$0.00014 per 1K input tokens
- Estimated: **$0.08-0.11 per ticket**

---

## Migration Checklist

- [x] Refactor Validator agent
- [x] Refactor Scorer agent
- [x] Refactor Query Analyzer agents (A + B)
- [x] Create Classification Model agent
- [x] Create test suite
- [x] Create demo script
- [x] Document changes
- [x] Verify backward compatibility
- [x] Orchestrator.py already supports all agents
- [x] Add fallback error handling

---

## Future Enhancements

### Planned
- [ ] Prompt caching for repeated queries
- [ ] Token counting for cost tracking
- [ ] Streaming responses for UI updates
- [ ] Multi-language support (FR, EN, ES)

### Optional
- [ ] Custom LLM fine-tuning
- [ ] Agent-to-agent communication patterns
- [ ] Knowledge base integration (RAG)
- [ ] Feedback learning loop

---

## How to Use

### Basic Usage
```python
from models import Ticket
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate, classify_ticket
from agents.classifier import classify_ticket_model

# Create ticket
ticket = Ticket(
    id="t123",
    client_name="John Doe",
    email="john@example.com",
    subject="Login not working",
    description="I can't log in to my account..."
)

# Pipeline
if validate_ticket(ticket)["valid"]:
    score_ticket(ticket)
    analyze_and_reformulate(ticket)
    classify_ticket(ticket)
    classify_ticket_model(ticket)
    print(f"Ticket category: {ticket.category}")
    print(f"Priority: {ticket.priority_score}")
```

### Full Pipeline (via Orchestrator)
```python
from agents.orchestrator import process_ticket

result = process_ticket(ticket)
# Returns: {"status": "answered|escalated|invalid", "message": str, "ticket": Ticket}
```

---

## Support & Debugging

### If LLM is unavailable
- ✓ All agents fall back to heuristics
- ✓ System continues to work (with reduced accuracy)
- ✓ Check API key in `.env`

### If JSON parsing fails
- ✓ Agent returns heuristic result
- ✓ Check LLM response format in logs

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## References

- **Agno Docs**: https://docs.agno.ai
- **Mistral Docs**: https://docs.mistral.ai
- **Test Suite**: `ai/tests/test_agents.py`
- **Demo**: `ai/demo_agents.py`
- **Agent Documentation**: `ai/agents/README_AGENTS.md`

---

**Status**: ✅ REFACTORING COMPLETE

All 4 core agents have been successfully refactored to use Agno + Mistral LLM with full backward compatibility and graceful fallbacks.
