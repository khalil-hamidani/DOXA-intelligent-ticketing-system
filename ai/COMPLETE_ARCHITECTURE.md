# Complete System Architecture & Flow

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TICKET PROCESSING SYSTEM                         │
│                    (10-Step Workflow)                               │
└─────────────────────────────────────────────────────────────────────┘

CLIENT INTERFACE
    │
    ├─ Submit Ticket (subject + description)
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 0: VALIDATION                                [Agent Validator] │
├─────────────────────────────────────────────────────────────────────┤
│ • Check ticket has sufficient context                               │
│ • Extract keywords for exploitability analysis                      │
│ • Validate format and content                                       │
│ Output: {"valid": bool, "reasons": List}                            │
└─────────────────────────────────────────────────────────────────────┘
    │
    ├─ INVALID? → Reject, ask for more details
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: SCORING & PRIORITISATION               [Agent Scorer]      │
├─────────────────────────────────────────────────────────────────────┤
│ • Score: 0-100 based on:                                            │
│   - Urgency (CRITICAL, URGENT keywords)                             │
│   - Recurrence (repeated mentions)                                  │
│   - Business Impact (production, customers, revenue)                │
│ Output: {"score": int, "priority": str}                             │
│ Storage: ticket.priority_score = score                              │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: QUERY ANALYSIS & CLASSIFICATION                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ AGENT A: Query Analysis                   [query_analyzer.py] │ │
│ ├────────────────────────────────────────────────────────────────┤ │
│ │ • Reformulate problem (standardize language)                  │ │
│ │ • Extract keywords for semantic search                        │ │
│ │ • Identify entities (dates, locations, systems)              │ │
│ │ Output: {"summary": str, "keywords": List, "entities": List} │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                            │                                        │
│                            ▼                                        │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ AGENT B: Classification                   [classifier.py]     │ │
│ ├────────────────────────────────────────────────────────────────┤ │
│ │ • Classify into category:                                     │ │
│ │   - "technique" (technical issues)                            │ │
│ │   - "facturation" (billing issues)                            │ │
│ │   - "authentification" (access issues)                        │ │
│ │   - "autre" (other)                                           │ │
│ │ • Determine treatment type (standard/priority/escalation)    │ │
│ │ Output: {"category": str, "treatment_type": str}              │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: SOLUTION FINDING (RAG PIPELINE)       [solution_finder.py] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Keywords + Entities from Step 2                                    │
│           │                                                          │
│           ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ RAG PIPELINE ORCHESTRATION         [pipeline/orchestrator]   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│           │                                                          │
│           ├─ Query Intelligence  [pipeline/query_intelligence.py]  │
│           │  └─ Enrich query with semantics                        │
│           │                                                         │
│           ├─ Retrieval          [pipeline/retrieval.py]            │
│           │  └─ Search KB (Chroma/Pinecone) → Top 10 docs         │
│           │                                                         │
│           ├─ Ranking            [pipeline/ranking.py]              │
│           │  └─ Re-rank by relevance → Top 3-5 docs               │
│           │                                                         │
│           ├─ Context Building   [pipeline/context.py]              │
│           │  └─ Build context from snippets                        │
│           │                                                         │
│           └─ Answer Generation  [pipeline/answer.py]               │
│              └─ Generate solution from context                     │
│                                                                      │
│  Output: {                                                           │
│    "solution_text": str,           # Generated answer               │
│    "snippets": List,               # Source documents               │
│    "confidence": float (0-1.0)     # RAG confidence                │
│  }                                                                   │
│  Storage:                                                            │
│    ticket.solution_text = solution_text                             │
│    ticket.snippets = snippets                                       │
│    ticket.solution_confidence = confidence                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: EVALUATION & CONFIDENCE              [Agent Evaluator]      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Confidence Calculation (4-factor weighted):                        │
│                                                                      │
│    confidence = (                                                   │
│      rag_conf × 0.40 +           # RAG pipeline confidence         │
│      priority_conf × 0.30 +       # Priority score (0-100→0.2-0.8)│
│      category_bonus × 0.20 +      # Category clarity (+0.1 each)  │
│      priority_adj × 0.10          # Priority adjustment (+/- 0.1) │
│    ) clamped to [0.0, 1.0]                                         │
│                                                                      │
│  Escalation Trigger Detection:                                     │
│    ✗ Low Confidence: confidence < 0.60 (60%)                       │
│    ✗ Sensitive Data: Email, Phone, CC, SSN, Passport detected     │
│    ✗ Negative Sentiment: Angry tone + confidence < 0.75            │
│                                                                      │
│  Output: {                                                           │
│    "confidence": float (0-1.0),                                     │
│    "escalate": bool,                                                │
│    "reasons": List,                                                 │
│    "sensitive": bool,                                               │
│    "negative_sentiment": bool,                                      │
│    "escalation_reason": str or None                                 │
│  }                                                                   │
│  Storage:                                                            │
│    ticket.confidence = confidence                                   │
│    ticket.sensitive = bool                                          │
│    ticket.negative_sentiment = bool                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ├─ Escalation Decision
    │
    ├────────────────────────────────────────────────────────┐
    │                                                        │
    │ Escalate (Low Conf OR Sensitive)  │ Respond (High Conf)
    │                                    │
    ▼                                    ▼
┌───────────────────────────────┐  ┌──────────────────────────┐
│ STEP 7: ESCALATION            │  │ STEP 5: RESPONSE         │
│ [escalation_manager.py]       │  │ COMPOSITION              │
├───────────────────────────────┤  │ [response_composer.py]   │
│ • Route to human agent        │  ├──────────────────────────┤
│ • Create escalation record    │  │ • Thank client           │
│ • Send notification email     │  │ • Explain problem        │
│ • Store context               │  │ • Provide solution       │
│ • Set status: "escalated"     │  │ • List action steps      │
│                               │  │ • Invite follow-up       │
│                               │  │ • Set status: "answered" │
└───────────────────────────────┘  └──────────────────────────┘
    │                                    │
    │                                    ▼
    │                          ┌──────────────────────────┐
    │                          │ STEP 6: SEND TO CLIENT   │
    │                          │ & COLLECT FEEDBACK       │
    │                          ├──────────────────────────┤
    │                          │ • Send response email    │
    │                          │ • Request satisfaction   │
    │                          │   feedback               │
    │                          │ • Set status: "waiting"  │
    │                          └──────────────────────────┘
    │                                    │
    │                                    ▼
    │                          ┌──────────────────────────┐
    │                          │ CLIENT FEEDBACK RECEIVED │
    │                          └──────────────────────────┘
    │                                    │
    │                          ┌─────────┴──────────┐
    │                          │                    │
    │                   YES: Satisfied         NO: Not Satisfied
    │                          │                    │
    │                          ▼                    ▼
    │                  [CLOSE TICKET]      ┌───────────────────┐
    │                      ✓               │ Attempts < 2?     │
    │                                       └───────────────────┘
    │                                           │         │
    │                                      YES │         │ NO
    │                                          ▼         ▼
    │                                    [RETRY]    [ESCALATE]
    │                                      │            │
    │                    ┌─────────────────┘            │
    │                    │                              │
    │                    ▼                              │
    │            [Go back to Step 2]                    │
    │            with clarification                     │
    │                    │                              │
    │                    └──────────────────────────────┤
    │                                                   │
    └───────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 8: POST-ANALYSIS                   [feedback_handler.py]      │
├─────────────────────────────────────────────────────────────────────┤
│ • Log escalation reason                                             │
│ • Store client feedback                                             │
│ • Record resolution outcome                                         │
│ • Mark ticket as closed or escalated                                │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 9: CONTINUOUS IMPROVEMENT              [continuous_improvement]
├─────────────────────────────────────────────────────────────────────┤
│ Analyze all escalations (daily/weekly batch):                       │
│                                                                      │
│ • KB Gaps Analysis:                                                 │
│   - Find escalations with "no solution found"                       │
│   - Flag categories with high escalation rates                      │
│   - Create KB update requests for data prep team                    │
│                                                                      │
│ • Hallucination Detection:                                          │
│   - Find escalations with "wrong solution provided"                 │
│   - Flag documents causing false positives                          │
│   - Remove or improve those KB entries                              │
│                                                                      │
│ • Pattern Recognition:                                              │
│   - Identify recurring issues                                       │
│   - Find categories needing training                                │
│   - Detect seasonal/trending problems                               │
│                                                                      │
│ Output: KB Improvement Recommendations                              │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 10: METRICS & REPORTING                     [orchestrator]     │
├─────────────────────────────────────────────────────────────────────┤
│ Generate daily/weekly reports:                                      │
│                                                                      │
│ • Volume Metrics:                                                   │
│   - Total tickets processed                                         │
│   - Resolved vs Escalated rate                                      │
│   - Distribution by category                                        │
│                                                                      │
│ • Quality Metrics:                                                  │
│   - Average confidence score                                        │
│   - Escalation rate by category                                     │
│   - Retry rate & reasons                                            │
│                                                                      │
│ • Performance Metrics:                                              │
│   - Average response time                                           │
│   - Processing time by step                                         │
│   - System bottlenecks                                              │
│                                                                      │
│ • AI Health:                                                        │
│   - Confidence distribution                                         │
│   - Hallucination rate                                              │
│   - KB coverage gaps                                                │
│                                                                      │
│ Output: Dashboard data + Reports for leadership & data prep team    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Relationships

### Agent Dependencies

```
Ticket Input
    │
    ├─→ validator.py        [Step 0: Validation]
    │      Output: valid (bool)
    │
    ├─→ scorer.py           [Step 1: Scoring]
    │      Input: ticket + priority indicators
    │      Output: priority_score (0-100)
    │
    ├─→ query_analyzer.py   [Step 2A: Analysis]
    │      Input: ticket description + priority
    │      Output: keywords, summary, entities
    │
    ├─→ classifier.py       [Step 2B: Classification]
    │      Input: summary + keywords
    │      Output: category, treatment_type
    │
    ├─→ solution_finder.py  [Step 3: RAG]
    │      Input: keywords + category
    │      │
    │      ├─→ pipeline/query_intelligence.py   [Enrich]
    │      ├─→ pipeline/retrieval.py            [Search]
    │      ├─→ pipeline/ranking.py              [Rank]
    │      ├─→ pipeline/context.py              [Build Context]
    │      └─→ pipeline/answer.py               [Generate Answer]
    │      │
    │      Output: solution_text, snippets, confidence
    │
    ├─→ evaluator.py        [Step 4: Evaluation]
    │      Input: solution_text, snippets, priority
    │      Output: confidence, escalate (bool)
    │
    ├─→ response_composer.py [Step 5: Response]
    │      Input: solution_text, confidence
    │      Output: response message
    │
    ├─→ feedback_handler.py  [Step 6: Feedback]
    │      Input: client feedback
    │      Output: action (close/retry/escalate)
    │
    ├─→ escalation_manager.py [Step 7: Escalation]
    │      Input: ticket + escalation reason
    │      Output: escalation_id, notification sent
    │
    └─→ continuous_improvement.py [Step 9: CI]
           Input: escalation logs (batch)
           Output: KB gap recommendations
```

---

## Data Flow Example

### Example: "Cannot Login" Ticket

```
INPUT TICKET:
{
  "id": "T12345",
  "client_name": "John Doe",
  "email": "john@example.com",
  "subject": "Cannot login after browser update",
  "description": "I tried to log in after updating Chrome but get
                  'Invalid credentials' error. Password is correct."
}

STEP 0: VALIDATION
↓
{
  "valid": true,
  "reasons": ["Description > 50 chars", "Keywords found: login, credentials"]
}

STEP 1: SCORING
↓
{
  "score": 45,
  "priority": "medium",
  "reasoning": "User is blocked but not critical"
}
→ ticket.priority_score = 45

STEP 2A: ANALYSIS
↓
{
  "summary": "Cannot login after browser update",
  "keywords": ["login", "credentials", "browser", "Chrome", "error"],
  "entities": ["Chrome", "Browser"],
  "reformulation": "User experiencing authentication failure post-browser update"
}

STEP 2B: CLASSIFICATION
↓
{
  "category": "authentification",
  "treatment_type": "standard",
  "severity": "normal",
  "confidence": 0.92
}
→ ticket.category = "authentification"

STEP 3: SOLUTION FINDING
Query RAG with: "login browser update credentials cache"
↓
Found 3 documents:
  • "Browser Cache & Login" (similarity: 0.85)
  • "Clear Browser Cache Guide" (similarity: 0.78)
  • "Password Reset Procedure" (similarity: 0.71)
↓
{
  "solution_text": "Try clearing browser cache and cookies...",
  "snippets": [
    {"text": "...", "similarity": 0.85},
    {"text": "...", "similarity": 0.78},
    {"text": "...", "similarity": 0.71}
  ],
  "confidence": 0.78
}
→ ticket.solution_text = "..."
→ ticket.snippets = [...]
→ ticket.solution_confidence = 0.78

STEP 4: EVALUATION
RAG conf = (0.78*0.7 + 3*0.1) = 0.69
Priority conf = 45/100 = 0.45
Category bonus = 0.2
Priority adj = 0 (medium)
confidence = (0.69*0.4 + 0.45*0.3 + 0.2*0.2 + 0*0.1) = 0.551
↓
No sensitive data, no negative tone
Escalate? 0.55 < 0.60 → YES, escalate
↓
{
  "confidence": 0.55,
  "escalate": true,
  "reasons": ["Confidence insuffisante (55% < 60%)"],
  "sensitive": false,
  "negative_sentiment": false,
  "escalation_reason": "Confidence insuffisante (55% < 60%)"
}
→ ticket.status = "escalated"

STEP 7: ESCALATION
↓
{
  "escalation_id": "ESC_12345",
  "notification_sent": true,
  "human_agent_assigned": "support_team_1"
}

STEP 8: POST-ANALYSIS
→ Store: escalation reason = "Low confidence"
→ Store: category = "authentification"

STEP 9: CONTINUOUS IMPROVEMENT (weekly)
→ Analyze: Found authentication issues with login after browser update
→ Action: "Create KB doc about browser cache & login"

RESULT: Ticket escalated to human for review
Human can apply their expertise and potentially improve KB
```

---

## Test Coverage Mapping

```
orchestrator.py
├── process_ticket()        [Tested via test_full_workflow]
├── process_feedback()      [Tested via test_feedback_handler]
└── get_ticket_status()     [Tested implicitly]

validator.py
├── validate_ticket()       [test_validator: 3 cases]
└── _extract_keywords()     [Implicitly tested]

scorer.py
├── score_ticket()          [test_scorer: 3 cases]
├── _calculate_urgency()    [Implicitly tested]
├── _calculate_recurrence() [Implicitly tested]
└── _calculate_impact()     [Implicitly tested]

query_analyzer.py
├── analyze_and_reformulate() [test_query_analyzer: 3 cases]
├── _reformulate()          [Implicitly tested]
├── _extract_keywords()     [Implicitly tested]
└── _extract_entities()     [Implicitly tested]

classifier.py
├── classify_ticket_model() [test_classifier: 4 cases]
├── _determine_category()   [Implicitly tested]
└── _determine_treatment()  [Implicitly tested]

solution_finder.py
├── find_solution()         [test_solution_finder: 2 cases]
├── _query_kb()             [Implicitly tested]
└── _generate_response()    [Implicitly tested]

evaluator.py
├── evaluate()              [test_evaluator: 3 cases]
├── _calculate_rag_conf()   [Implicitly tested]
├── _contains_sensitive()   [Implicitly tested]
└── _detect_negative()      [Implicitly tested]

response_composer.py
├── compose_response()      [test_response_composer: 2 cases]

feedback_handler.py
├── handle_feedback()       [test_feedback_handler: 3 cases]

escalation_manager.py
├── escalate_ticket()       [test_escalation_manager: 2 cases]

continuous_improvment.py
├── analyze_improvements()  [test_continuous_improvement: 3 cases]
```

---

## Configuration & Thresholds

### Confidence Scoring
```python
CONFIDENCE_THRESHOLD = 0.60      # 60% - escalate if lower
RAG_WEIGHT = 0.40                # 40% of confidence
PRIORITY_WEIGHT = 0.30           # 30% of confidence
CATEGORY_WEIGHT = 0.20           # 20% of confidence
ADJUSTMENT_WEIGHT = 0.10         # 10% of confidence
```

### Retry Policy
```python
MAX_ATTEMPTS = 2                 # Maximum retry attempts
RETRY_TRIGGER = "unsatisfied"    # Feedback condition
ESCALATION_TRIGGER = "max_attempts_exceeded"  # Final condition
```

### Sensitive Data Patterns
```python
EMAIL = r"\b[\w.-]+@[\w.-]+\.[a-z]{2,}\b"
PHONE = r"\b\d{9,15}\b"
CREDIT_CARD = r"\b4[0-9]{12}(?:[0-9]{3})?\b"
SSN = r"\b\d{3}-\d{2}-\d{4}\b"
PASSPORT = r"\b[A-Z]{2}\d{6,9}\b"
```

### Priority Scoring
```python
Urgency Words:        +30 points (URGENT, CRITICAL, DOWN, etc.)
Recurrence Signals:   +20 points (recurring, again, frequently)
Impact Keywords:      +25 points (production, customers, revenue)
Category Default:     +10 points (other factors)
```

---

## System Status & Health Checks

### Healthy Ticket Processing
```
Validation ✓ → Scoring ✓ → Analysis ✓ → Classification ✓ → 
RAG ✓ → Evaluation ✓ → Response ✓ → Client Satisfied ✓
Confidence: 65-95% (resolved at first attempt)
Escalation Rate: 0-15%
Retry Rate: 0-5%
```

### Degraded Mode
```
Example: Low KB Coverage
- Solution Finding returns fallback text
- Confidence drops to 45-55%
- More tickets escalated
- Action: Data prep team adds KB docs
```

### System Down (Fallback)
```
RAG Pipeline Unavailable
→ Use heuristic-only solution
→ Lower confidence automatically
→ Higher escalation rate
→ All tickets still processed
```

---

This architecture ensures:
✅ Comprehensive ticket processing
✅ Multiple decision points and safeguards
✅ Clear escalation paths
✅ Continuous improvement loop
✅ Full audit trail
✅ Scalable to high volume
