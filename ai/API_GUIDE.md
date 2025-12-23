# 🔗 API Integration Guide

## Server Status
✅ **Running on**: http://127.0.0.1:8000  
✅ **CORS Configured for**: os.ogno.com (+ localhost)

---

## API Endpoints

### 1. Health Check
```bash
GET http://127.0.0.1:8000/
```
**Response:**
```json
{
  "status": "online",
  "service": "AI Ticketing System",
  "version": "1.0.0"
}
```

### 2. Create Ticket
```bash
POST http://127.0.0.1:8000/tickets
Content-Type: application/json

{
  "client_name": "John Doe",
  "email": "john@example.com",
  "subject": "Cannot login",
  "description": "I cannot log into my account after password reset"
}
```

**Response:**
```json
{
  "ticket_id": "uuid-here",
  "result": {
    "status": "answered",
    "message": "...",
    "ticket": {...}
  }
}
```

### 3. Get Ticket
```bash
GET http://127.0.0.1:8000/tickets/{ticket_id}
```

### 4. Submit Feedback
```bash
POST http://127.0.0.1:8000/tickets/{ticket_id}/feedback
Content-Type: application/json

{
  "satisfied": true,
  "reason": "Issue was resolved quickly"
}
```

---

## Interactive API Documentation

**Swagger UI** (test endpoints in browser):
```
http://127.0.0.1:8000/docs
```

**ReDoc** (read-only documentation):
```
http://127.0.0.1:8000/redoc
```

---

## CORS Configuration

**Currently Allowed Origins:**
- `http://127.0.0.1:8000` (local testing)
- `http://localhost:8000` (local testing)
- `http://localhost:3000` (frontend dev)
- `https://os.ogno.com` (production)
- `http://os.ogno.com` (production)

**To add more domains**, edit `ai/main.py` line ~26:
```python
allow_origins=[
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://os.ogno.com",
    # Add more here
]
```

---

## Testing from os.ogno.com

### Using fetch() in JavaScript
```javascript
const response = await fetch('http://127.0.0.1:8000/tickets', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    client_name: 'Test User',
    email: 'test@example.com',
    subject: 'Test Ticket',
    description: 'This is a test'
  })
});

const data = await response.json();
console.log(data);
```

### Using cURL (from terminal)
```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "client_name":"Test User",
    "email":"test@example.com",
    "subject":"Test Ticket",
    "description":"This is a test"
  }'
```

### Using Python
```python
import requests

response = requests.post(
    'http://127.0.0.1:8000/tickets',
    json={
        'client_name': 'Test User',
        'email': 'test@example.com',
        'subject': 'Test Ticket',
        'description': 'This is a test'
    }
)

print(response.json())
```

---

## What Happens When You Create a Ticket

```
POST /tickets
    ↓
[1] Validator Agent - Checks if ticket is clear
    ↓
[2] Scorer Agent - Assigns priority (0-100)
    ↓
[3] Query Analyzer - Reformulates + analyzes
    ↓
[4] Classifier Agent - Categorizes (tech/billing/auth/other)
    ↓
[5] Solution Finder - Searches knowledge base
    ↓
[6] Evaluator - Decides to escalate or respond
    ↓
[7] Response Composer - Creates response
    ↓
Returns enriched ticket + response
```

---

## Response Format

All ticket responses include:
```json
{
  "ticket_id": "uuid",
  "status": "answered|escalated|invalid",
  "message": "Response to user",
  "ticket": {
    "id": "uuid",
    "client_name": "John",
    "email": "john@example.com",
    "subject": "...",
    "description": "...",
    "priority_score": 30,
    "category": "authentification",
    "status": "answered",
    "summary": "User cannot log in",
    "confidence": 0.95
  }
}
```

---

## Troubleshooting

**CORS Error?**
- Make sure os.ogno.com is in `allow_origins` list
- Check that you're using http:// or https:// correctly
- Clear browser cache

**Server not responding?**
- Check server is running: `http://127.0.0.1:8000/`
- Check firewall allows port 8000
- Restart server if needed

**Agent errors?**
- Check MISTRAL_API_KEY is set in `ai/.env`
- Check agents work: `python demo_agents.py`

---

## Integration Checklist

- [ ] Server running on port 8000
- [ ] CORS configured for os.ogno.com
- [ ] Health check working: `GET /`
- [ ] Can create ticket: `POST /tickets`
- [ ] Response includes all fields
- [ ] Tests passing: `pytest tests/test_agents.py`
- [ ] Demo working: `python demo_agents.py`

---

## Next Steps

1. **Test locally**: Use http://127.0.0.1:8000/docs
2. **Test from os.ogno.com**: Send request to your IP
3. **Update firewall**: Allow external traffic to port 8000
4. **Add authentication**: (Optional) Add API keys/tokens
5. **Database**: Replace in-memory tickets_db with real DB

---

**Server is ready!** 🚀
