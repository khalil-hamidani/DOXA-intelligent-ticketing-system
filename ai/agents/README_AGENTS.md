# Agno-Based Intelligent Ticketing Agents

## Architecture

### 1. **Validator Agent** (`validator.py`)
**Purpose**: Validate ticket quality and completeness

- **Input**: Ticket object with subject and description
- **Output**: `{"valid": bool, "reasons": List[str], "confidence": float}`
- **LLM Task**: Evaluate ticket clarity, keyword exploitability, and information sufficiency
- **Fallback**: Heuristic validation (length, word count checks)

```python
from agents.validator import validate_ticket
result = validate_ticket(ticket)
# → {"valid": True, "reasons": [], "confidence": 0.95}
```

### 2. **Scorer Agent** (`scorer.py`)
**Purpose**: Calculate ticket priority score (0-100)

- **Input**: Ticket object
- **Output**: `{"score": int, "priority": "low|medium|high", "reasoning": str}`
- **LLM Task**: Analyze urgency, recurrence, and impact keywords; compute weighted score
- **Fallback**: Heuristic scoring based on keyword matching

```python
from agents.scorer import score_ticket
result = score_ticket(ticket)
# → {"score": 75, "priority": "high", "reasoning": "..."}
```

### 3. **Query Analyzer** (`query_analyzer.py`)
**Purpose**: Reformulate and classify ticket using two coordinated agents

#### Agent A: Reformulation & Keyword Extraction
- Summarizes the main issue
- Reformulates problem clearly
- Extracts 5-8 key technical/business terms

#### Agent B: Classification
- Categorizes ticket type: `technique | facturation | authentification | autre`
- Suggests treatment approach
- Returns confidence score

```python
from agents.query_analyzer import analyze_and_reformulate, classify_ticket

# Agent A
reform = analyze_and_reformulate(ticket)
# → {"summary": "...", "reformulation": "...", "keywords": [...], "entities": [...]}

# Agent B
classif = classify_ticket(ticket)
# → {"category": "technique", "expected_treatment": "standard", "treatment_action": "..."}
```

### 4. **Classification Model** (`classifier.py`)
**Purpose**: Advanced ticket categorization and treatment planning

- **Input**: Ticket object (after scoring and analysis)
- **Output**: `{"category", "treatment_type", "severity", "reasoning", "confidence", "required_skills"}`
- **LLM Task**: Determine category, treatment urgency, skill requirements
- **Categories**:
  - `technique`: Technical/system issues, bugs, errors
  - `facturation`: Billing, invoicing, payments
  - `authentification`: Login, access, permissions
  - `autre`: Other issues

- **Treatment Types**:
  - `standard`: Normal processing
  - `priority`: Faster handling needed
  - `escalation`: Specialist review required
  - `urgent`: Immediate action required

```python
from agents.classifier import classify_ticket_model
result = classify_ticket_model(ticket)
# → {
#     "category": "technique",
#     "treatment_type": "urgent",
#     "severity": "high",
#     "confidence": 0.92,
#     "reasoning": "Production outage detected",
#     "required_skills": ["database", "devops", "emergency_response"]
# }
```

## Pipeline Flow

```
Ticket Input
    ↓
[Validator] → Valid? No → Reject
    ↓ Yes
[Scorer] → Priority Score (0-100)
    ↓
[Query Analyzer]
    ├─ Agent A: Summarize & Extract Keywords
    └─ Agent B: Classify Type
    ↓
[Classifier] → Detailed Categorization & Treatment Plan
    ↓
[Solution Finder] → RAG-based solution retrieval
    ↓
[Evaluator] → Confidence assessment & escalation decision
    ↓
Response to Client / Escalation
```

## LLM Configuration

### Mistral Model
- **Default Model**: `mistral-small-latest`
- **Temperature**: 0.3-0.4 (lower for consistent classification)
- **API Key**: Set `MISTRAL_API_KEY` in `.env`

### Environment Setup
```bash
# In ai/.env
MISTRAL_API_KEY=your_api_key_here
MISTRAL_MODEL_ID=mistral-small-latest  # optional, defaults to mistral-small-latest
```

## Error Handling & Fallbacks

Each agent implements graceful fallbacks:

1. **LLM Call Fails**: Falls back to heuristic approach
2. **JSON Parsing Error**: Uses default/heuristic logic
3. **API Timeout**: Returns fallback result with reduced confidence

Example:
```python
try:
    # LLM-based processing
    response = agent.run(prompt)
    result = parse_json(response)
except Exception as e:
    # Fallback to heuristics
    result = heuristic_fallback(ticket)
```

## Testing

### Run Test Suite
```bash
cd ai/
python tests/test_agents.py
```

### Run Demo
```bash
cd ai/
python demo_agents.py
```

### Test Features
- Sample tickets for each category (login, billing, production outage, recurrent issues)
- Validation of output signatures
- Assertion checks for agent behavior
- Full pipeline demonstration

## Integration with Orchestrator

The `orchestrator.py` already integrates all agents seamlessly:

```python
from agents.orchestrator import process_ticket

# Full pipeline
result = process_ticket(ticket, team="support_team")
# Returns: {"status": "answered|escalated|invalid", "message": str, "ticket": Ticket}
```

## Output Schemas

### Ticket Model (Updated)
```python
class Ticket(BaseModel):
    id: str
    client_name: str
    email: str
    subject: str
    description: str
    keywords: Optional[List[str]] = []
    priority_score: Optional[int] = None  # Set by Scorer
    category: Optional[str] = None        # Set by Classifier
    status: str = "pending_validation"
    attempts: int = 0
    
    # Set by agents
    summary: Optional[str] = None              # Query Analyzer Agent A
    reformulation: Optional[str] = None        # Query Analyzer Agent A
    confidence: Optional[float] = None         # Evaluator
    escalation_context: Optional[str] = None   # Evaluator
    sensitive: Optional[bool] = False          # Evaluator
    snippets: Optional[List[str]] = []
```

## Performance Considerations

### Token Usage
- Validator: ~50-100 tokens
- Scorer: ~100-150 tokens
- Query Analyzer Agent A: ~150-200 tokens
- Query Analyzer Agent B: ~100-150 tokens
- Classifier: ~150-200 tokens

**Estimated total per ticket: 550-800 tokens**

### Latency
- Per agent: 1-3 seconds (network dependent)
- Full pipeline: 5-15 seconds

### Cost Optimization
1. Use lower-cost models like `mistral-small-latest`
2. Cache reformulations for similar tickets
3. Batch process tickets when possible

## Customization

### Modify Agent Instructions
Edit the `instructions` string in each agent's `_create_*_agent()` function to change behavior.

### Change LLM Model
```python
MODEL_ID = "mistral-large-latest"  # or any other Mistral model
```

### Add Custom Tools
```python
from agno.tools import YourTool

agent = Agent(
    model=mistral_model,
    instructions=instructions,
    tools=[YourTool()],  # Add here
    name="CustomAgent"
)
```
eof