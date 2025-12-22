# Deployment Guide - Agno Agents v1.0

## Pre-Deployment Checklist

- [ ] All 4 agents refactored and tested
- [ ] Test suite passes: `python ai/tests/test_agents.py`
- [ ] Demo runs successfully: `python ai/demo_agents.py`
- [ ] API key configured in `ai/.env`
- [ ] Documentation reviewed
- [ ] Backward compatibility verified
- [ ] Fallback behavior tested

---

## Step 1: Verify Environment Setup

### Check Python Version
```bash
python --version
# Should be 3.8+ (tested with 3.10+)
```

### Verify Dependencies
```bash
pip list | grep -E "agno|mistral|pydantic"
# Should show:
# agno 2.3.19
# mistral-sdk 0.x.x
# pydantic 2.x.x
# python-dotenv x.x.x
```

### Check API Key
```bash
cat ai/.env | grep MISTRAL_API_KEY
# Should show: MISTRAL_API_KEY=sk-xxxxx
```

---

## Step 2: Run Verification Tests

### Test 1: Agent Tests
```bash
cd ai/
python tests/test_agents.py

# Expected Output:
# ✓ Validator tests completed
# ✓ Scorer tests completed
# ✓ Query Analyzer tests completed
# ✓ Classifier tests completed
# ✓ ALL AGENT TESTS COMPLETED
```

### Test 2: Demo Script
```bash
python demo_agents.py

# Expected Output:
# Shows 3 real-world examples
# Demonstrates full pipeline
# ~30-60 second execution
```

### Test 3: Quick Integration
```bash
python -c "
from models import Ticket
from agents.orchestrator import process_ticket

ticket = Ticket(
    id='deploy_test',
    client_name='Test',
    email='test@example.com',
    subject='Test ticket',
    description='This is a test ticket to verify deployment'
)

result = process_ticket(ticket)
assert result['status'] in ['answered', 'escalated', 'invalid']
print('✓ Integration test passed')
"
```

---

## Step 3: Production Environment Setup

### Create Production .env
```bash
# ai/.env (ENSURE THIS IS GITIGNORED)
MISTRAL_API_KEY=sk-prod-your-api-key-here
MISTRAL_MODEL_ID=mistral-small-latest
ENABLE_AGENT_LOGGING=false
LOG_LLM_RESPONSES=false
```

### Verify .gitignore
```bash
# Check that ai/.env is ignored
grep "ai/.env" .gitignore
# Should output: ai/.env
```

### Set Permissions (Linux/Mac)
```bash
chmod 600 ai/.env
chmod 644 ai/*.py
chmod 755 ai/
```

---

## Step 4: Deployment Strategies

### Option A: Direct Deployment (Simple)
**Best for**: Small-to-medium deployments, development environments

```bash
# 1. Copy files to production server
scp -r ai/ user@prod-server:/app/

# 2. Verify setup
ssh user@prod-server "cd /app && python ai/tests/test_agents.py"

# 3. Start application
ssh user@prod-server "cd /app && python ai/main.py"
```

### Option B: Docker Deployment (Recommended)
**Best for**: Scalable, containerized deployments

```dockerfile
# Dockerfile (update existing)
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

# Copy agents and configuration
COPY ai/ ./ai/
COPY ai/.env ./ai/.env

# Run tests before starting
RUN python ai/tests/test_agents.py

# Start application
CMD ["python", "ai/main.py"]
```

Build and run:
```bash
docker build -t doxa-agents:1.0 .
docker run -e MISTRAL_API_KEY=$MISTRAL_API_KEY doxa-agents:1.0
```

### Option C: Docker Compose (Full Stack)
**Best for**: Complete application deployment

Update `docker-compose.yml`:
```yaml
version: '3.8'
services:
  ai:
    build: ./ai
    environment:
      MISTRAL_API_KEY: ${MISTRAL_API_KEY}
      MISTRAL_MODEL_ID: mistral-small-latest
    ports:
      - "8000:8000"
    volumes:
      - ./ai:/app/ai
    command: python ai/main.py

  backend:
    build: ./backend
    # ... existing configuration

  frontend:
    build: ./frontend
    # ... existing configuration
```

Run:
```bash
export MISTRAL_API_KEY=sk-your-api-key
docker-compose up -d
```

---

## Step 5: Health Checks

### Test Agent Availability
```bash
python -c "
from agents.validator import validate_ticket
from agents.scorer import score_ticket
from agents.query_analyzer import analyze_and_reformulate, classify_ticket
from agents.classifier import classify_ticket_model
print('✓ All agents imported successfully')
"
```

### Test API Key
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv('ai/.env')
api_key = os.environ.get('MISTRAL_API_KEY')
if api_key and api_key.startswith('sk-'):
    print(f'✓ API key configured: {api_key[:10]}...')
else:
    print('✗ API key not configured')
"
```

### Test LLM Connection
```bash
python -c "
from agents.config import setup_api_keys
from agno.models.mistral import MistralChat

setup_api_keys()
try:
    model = MistralChat(id='mistral-small-latest')
    print('✓ LLM connection successful')
except Exception as e:
    print(f'✗ LLM connection failed: {e}')
"
```

---

## Step 6: Monitoring & Logging

### Enable Logging (Optional)
```bash
# Update ai/.env
ENABLE_AGENT_LOGGING=true
LOG_LLM_RESPONSES=true
```

### Monitor Token Usage
```python
# In your application
from agents.config import AGENT_TEMPERATURE

def log_token_usage(agent_name, tokens_used):
    """Log token usage for cost tracking"""
    cost = tokens_used * 0.00014 / 1000  # mistral-small-latest rate
    print(f"Agent: {agent_name}, Tokens: {tokens_used}, Cost: ${cost:.4f}")
```

### Set Up Alerts
```bash
# Monitor for:
# - API timeouts (>5 seconds)
# - Fallback usage (should be <5%)
# - Cost per ticket (should be ~$0.08-0.11)
# - Accuracy metrics (track human corrections)
```

---

## Step 7: Rollback Plan

### Quick Rollback (If Issues Occur)
```bash
# Option 1: Use git
git revert <commit_hash>

# Option 2: Disable LLM (use fallback heuristics)
# Agents automatically fallback if LLM is unavailable
# Just stop the Mistral API calls

# Option 3: Restore previous version
cp ai/agents/validator.py.backup ai/agents/validator.py
cp ai/agents/scorer.py.backup ai/agents/scorer.py
# etc.
```

### Verification After Rollback
```bash
python ai/tests/test_agents.py
# Should still pass with fallback heuristics
```

---

## Step 8: Production Validation

### Run Full Test Suite
```bash
python ai/tests/test_agents.py 2>&1 | tee deployment.log
# Verify all tests pass
# Save log for records
```

### Monitor First 24 Hours
- ✓ Track accuracy metrics
- ✓ Monitor LLM API calls
- ✓ Check for errors in logs
- ✓ Verify fallback behavior
- ✓ Measure latency

### Example Metrics to Track
```python
{
    "total_tickets": 150,
    "valid_tickets": 145,
    "escalated_tickets": 8,
    "average_latency": "7.3s",
    "fallback_rate": "0.2%",
    "tokens_used": 85000,
    "estimated_cost": "$11.90",
    "accuracy_improvement": "+45%"
}
```

---

## Step 9: Documentation & Handoff

### Ensure Team Access
- [ ] All developers have API key
- [ ] Documentation is accessible
- [ ] Test suite can be run by anyone
- [ ] Monitoring dashboards are set up
- [ ] Runbooks are documented

### Share Knowledge
1. Walk through [QUICK_START.md](./QUICK_START.md)
2. Demo [ai/demo_agents.py](./ai/demo_agents.py)
3. Review [ARCHITECTURE.md](./ARCHITECTURE.md)
4. Discuss monitoring strategy
5. Plan for future enhancements

### Create Runbooks
```bash
# Runbook: ai_agents_troubleshooting.md
# Include:
# - Common issues & solutions
# - How to check logs
# - How to enable/disable features
# - How to escalate problems
# - Contact information
```

---

## Step 10: Post-Deployment Monitoring

### Daily Checklist
- [ ] Application is running
- [ ] No errors in logs
- [ ] API latency is acceptable
- [ ] Fallback rate is low (<5%)
- [ ] Cost is within budget

### Weekly Review
- [ ] Accuracy metrics
- [ ] Token usage trends
- [ ] Cost analysis
- [ ] User feedback
- [ ] Performance metrics

### Monthly Review
- [ ] Accuracy improvements
- [ ] ROI analysis
- [ ] Scaling requirements
- [ ] Model optimization opportunities
- [ ] Feature requests

---

## Common Issues & Solutions

### Issue: "MISTRAL_API_KEY not found"
```bash
# Solution:
echo "MISTRAL_API_KEY=sk-your-key" > ai/.env
# Restart application
```

### Issue: "Agent timeout after 5 seconds"
```bash
# Normal behavior - should fallback to heuristics
# Check network connectivity
# Verify API key is valid
# Check Mistral API status
```

### Issue: "JSON parsing error"
```bash
# Normal for some responses - handled gracefully
# Agents fallback to heuristic output
# Check LLM response format if persistent
```

### Issue: "High costs (>$0.20/ticket)"
```bash
# Use cheaper model: mistral-small-latest (default)
# Optimize prompts to reduce tokens
# Cache repeated queries
# Batch process tickets
```

### Issue: "Low accuracy"
```bash
# Check agent instructions
# Verify temperature settings (0.3-0.4)
# Test with different ticket types
# Review fallback vs LLM accuracy
```

---

## Performance Tuning

### Optimize Temperature (Accuracy vs Variety)
```python
# config.py
AGENT_TEMPERATURE = {
    "validator": 0.1,      # Very strict
    "scorer": 0.2,         # Consistent
    "reformulator": 0.3,   # Balanced
    "classifier": 0.2,     # Strict
}
```

### Optimize Timeouts
```python
# config.py
AGENT_RUN_TIMEOUT = 5   # seconds (was 10)
LLM_API_TIMEOUT = 3     # seconds (was 5)
```

### Cache Results
```python
# Implement in your application
cache = {}

def get_classification(ticket_key):
    if ticket_key in cache:
        return cache[ticket_key]
    result = classify_ticket_model(ticket)
    cache[ticket_key] = result
    return result
```

---

## Scaling Strategies

### Horizontal Scaling (Multiple Servers)
```bash
# Run agents on multiple servers
# Use load balancer
# Share API key across servers
# Monitor aggregate metrics
```

### Asynchronous Processing
```python
# Use async agents for better throughput
# Queue tickets for processing
# Return immediately to user
# Update status when processing completes
```

### Batch Processing
```python
# Process multiple tickets in parallel
# Reduce per-ticket overhead
# Better cost efficiency
# Aggregate results
```

---

## Final Verification

Before considering deployment complete:

```bash
# 1. All tests pass
python ai/tests/test_agents.py ✓

# 2. Demo runs successfully
python ai/demo_agents.py ✓

# 3. Integration works
python -c "from agents.orchestrator import process_ticket; print('✓')" ✓

# 4. Documentation is clear
ls -la QUICK_START.md ARCHITECTURE.md ai/agents/README_AGENTS.md ✓

# 5. Monitoring is set up
# (Application-specific)

# 6. Team is trained
# (Internal process)

# 7. Rollback plan is documented
# (In this file)
```

---

## Support & Questions

### During Deployment
- 📖 Check [QUICK_START.md](./QUICK_START.md)
- 🏗️ Review [ARCHITECTURE.md](./ARCHITECTURE.md)
- 🧪 Run tests: `python ai/tests/test_agents.py`

### After Deployment
- 📊 Monitor metrics dashboard
- 📝 Review logs
- 📞 Contact support (internal)
- 🐛 Report issues with details

### Documentation
- ✓ All docs in root directory
- ✓ Agent docs in `ai/agents/`
- ✓ Tests in `ai/tests/`
- ✓ Examples in `ai/demo_agents.py`

---

## Success Criteria

✅ **Deployment is successful when**:
1. All tests pass
2. Demo runs without errors
3. Agents respond within 5-15 seconds
4. Fallback heuristics work correctly
5. Cost is within budget ($0.08-0.11/ticket)
6. Team is trained and comfortable
7. Monitoring is active
8. Documentation is accessible

---

**Status**: 🚀 **READY FOR DEPLOYMENT**

**Expected Deployment Time**: 30-60 minutes
**Expected Testing Time**: 15-30 minutes
**Expected Stabilization**: 24-48 hours
**Expected Full Impact**: 1-2 weeks of real-world usage

---

**Last Updated**: 2024
**Version**: 1.0
