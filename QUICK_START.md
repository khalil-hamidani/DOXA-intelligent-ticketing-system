# Quick Start Guide: Agno Agents

## Setup (5 minutes)

### 1. Ensure API Key
```bash
# In ai/.env
MISTRAL_API_KEY=sk-your_key_here
```

### 2. Check Dependencies
```bash
pip list | grep -E "agno|mistral|pydantic"
# Should show: agno, mistral-sdk, pydantic
```

### 3. Verify Import Path
```bash
cd ai/
python -c "from agents.validator import validate_ticket; print('✓ Imports OK')"
```

## Running Agents

### Option 1: Test Suite (Recommended)
```bash
cd ai/
python tests/test_agents.py
```
- Runs 4+ tests per agent
- Validates output signatures
- Tests fallback behavior
- Takes ~10-30 seconds

### Option 2: Interactive Demo
```bash
cd ai/
python demo_agents.py
```
- Shows 3 real-world examples
- Displays LLM output
- Demonstrates full pipeline
- Takes ~15-30 seconds

### Option 3: Programmatic
```python
from models import Ticket
from agents.validator import validate_ticket

ticket = Ticket(
    id="t1",
    client_name="Test",
    email="test@example.com",
    subject="Help with login",
    description="I cannot log in to my account after password reset"
)

result = validate_ticket(ticket)
print(f"Valid: {result['valid']}")
print(f"Reasons: {result['reasons']}")
print(f"Confidence: {result['confidence']}")
```

## Agent Examples

### Validator
```python
from agents.validator import validate_ticket

result = validate_ticket(ticket)
# → {"valid": True, "reasons": [], "confidence": 0.95}
```

### Scorer
```python
from agents.scorer import score_ticket

result = score_ticket(ticket)
# → {"score": 75, "priority": "high", "reasoning": "..."}
```

### Query Analyzer
```python
from agents.query_analyzer import analyze_and_reformulate, classify_ticket

# Agent A
reform = analyze_and_reformulate(ticket)
# → {"summary": "...", "reformulation": "...", "keywords": [...]}

# Agent B
classif = classify_ticket(ticket)
# → {"category": "technique", "expected_treatment": "standard", ...}
```

### Classifier
```python
from agents.classifier import classify_ticket_model

result = classify_ticket_model(ticket)
# → {
#     "category": "technique",
#     "treatment_type": "urgent",
#     "severity": "high",
#     "confidence": 0.92,
#     "required_skills": ["database", "devops"]
# }
```

### Full Pipeline
```python
from agents.orchestrator import process_ticket

result = process_ticket(ticket)
# → {"status": "answered", "message": "...", "ticket": Ticket}
```

## Troubleshooting

### Issue: "MISTRAL_API_KEY not found"
**Solution**:
```bash
# Create/update ai/.env
echo "MISTRAL_API_KEY=sk-your_key" > ai/.env
```

### Issue: "Agent.run() timeout"
**Solution**: Agents automatically fallback to heuristics after ~5 seconds. Check:
- Network connectivity
- API key validity
- Mistral service status

### Issue: "ModuleNotFoundError: No module named 'agno'"
**Solution**:
```bash
pip install agno mistral-sdk
python -m pip install --upgrade agno
```

### Issue: "JSON parsing error in response"
**Solution**: Check agent logs - should fallback to heuristics. If not:
- Verify LLM temperature (should be 0.3-0.4)
- Check response format in agent instructions

## Performance Tips

### Speed Up Processing
```python
# Option 1: Use faster model
MODEL_ID = "mistral-small-latest"  # Fastest

# Option 2: Parallel processing (future)
# Process multiple tickets in parallel

# Option 3: Cache results
# Store reformulations for duplicate tickets
```

### Reduce Costs
```python
# Use cheaper model tier
# Batch similar tickets
# Cache common analyses
```

## Common Scenarios

### Scenario 1: Validate + Score a Ticket
```python
from models import Ticket
from agents.validator import validate_ticket
from agents.scorer import score_ticket

ticket = Ticket(...)
if validate_ticket(ticket)["valid"]:
    result = score_ticket(ticket)
    print(f"Score: {result['score']}/100")
```

### Scenario 2: Full Analysis Pipeline
```python
from agents.orchestrator import process_ticket

result = process_ticket(ticket)
if result["status"] == "answered":
    print(f"Response: {result['message']}")
elif result["status"] == "escalated":
    print(f"Escalated: {result['escalation_context']}")
else:
    print(f"Invalid: {result['reasons']}")
```

### Scenario 3: Classification Only
```python
from agents.classifier import classify_ticket_model
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate

# Prepare ticket
score_ticket(ticket)
analyze_and_reformulate(ticket)

# Classify
classification = classify_ticket_model(ticket)
print(f"Category: {classification['category']}")
print(f"Treatment: {classification['treatment_type']}")
print(f"Skills needed: {classification['required_skills']}")
```

## Output Reference

### Validator Output
```python
{
    "valid": True,              # bool
    "reasons": [],              # List[str] (empty if valid)
    "confidence": 0.95          # float (0-1)
}
```

### Scorer Output
```python
{
    "score": 75,                # int (0-100)
    "priority": "high",         # str: low|medium|high
    "reasoning": "..."          # str (LLM reasoning)
}
```

### Query Analyzer (Agent A) Output
```python
{
    "summary": "...",           # str (one-liner)
    "reformulation": "...",     # str (problem statement)
    "keywords": [...],          # List[str]
    "entities": [...]           # List[str]
}
```

### Query Analyzer (Agent B) Output
```python
{
    "category": "technique",    # str: technique|facturation|authentification|autre
    "expected_treatment": "...",# str
    "treatment_action": "..."   # str
}
```

### Classifier Output
```python
{
    "category": "technique",    # str
    "treatment_type": "urgent", # str: standard|priority|escalation|urgent
    "severity": "high",         # str: low|medium|high
    "reasoning": "...",         # str
    "confidence": 0.92,         # float (0-1)
    "required_skills": [...]    # List[str]
}
```

## Next Steps

1. **Test your setup**
   ```bash
   python ai/tests/test_agents.py
   ```

2. **Run the demo**
   ```bash
   python ai/demo_agents.py
   ```

3. **Integrate into your app**
   ```python
   from agents.orchestrator import process_ticket
   result = process_ticket(ticket)
   ```

4. **Monitor performance**
   - Track token usage
   - Monitor LLM latency
   - Check fallback rates

5. **Customize as needed**
   - Edit agent instructions
   - Adjust temperature/model
   - Add custom tools

## Support Resources

- 📖 **Full Documentation**: `ai/agents/README_AGENTS.md`
- 📝 **Refactoring Details**: `REFACTORING_SUMMARY.md`
- 🧪 **Test Suite**: `ai/tests/test_agents.py`
- 🎬 **Demo Script**: `ai/demo_agents.py`
- 🔗 **Agno Docs**: https://docs.agno.ai
- 🔗 **Mistral Docs**: https://docs.mistral.ai

## Summary

✅ **4 Agno agents refactored with LLM power**
✅ **Backward compatible with existing pipeline**
✅ **Graceful fallbacks for resilience**
✅ **Comprehensive testing & documentation**

You're ready to go! 🚀
