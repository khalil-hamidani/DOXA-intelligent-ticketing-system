# AgentOS Server Setup & os.agno.com Connection Guide

## ✅ Server Status - ACTIVE

**AgentOS Server is running successfully on port 7777!**

```
Status: HEALTHY
Service: DOXA Ticketing
Port: 7777
Integration: os.agno.com Control Plane
Ready: True
```

**Verified:** Server responding to health checks

## 📋 Quick Start

### 1. Start the AgentOS Server

```powershell
cd C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai
python agentoss_server_v2.py
```

The server will start immediately on port 7777.

### 2. Verify Server is Running

Test the health endpoint:
```bash
curl http://localhost:7777/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "DOXA Ticketing",
  "ready": true
}
```

## 🔗 os.agno.com Connection Steps

### Step 1: Get Your Server Address

Determine your public IP or hostname:

**Option A: Local Network (Windows)**
```powershell
ipconfig
# Look for "IPv4 Address" under your active network connection
# Example: 192.168.1.100:7777
```

**Option B: Cloud/VPS**
```bash
echo $HOSTNAME
# Or use: hostname -I
```

### Step 2: Register Server in os.agno.com

1. Go to: https://os.agno.com/settings/servers
2. Click **"Add New Server"** or **"Register Server"**
3. Enter the following details:

   | Field | Value |
   |-------|-------|
   | **Server Name** | DOXA Intelligent Ticketing System |
   | **Server URL** | `http://<YOUR_IP>:7777` |
   | **Server Type** | AgentOS |
   | **Description** | AI-Powered Support Ticket Management |

   **Example:**
   ```
   http://192.168.1.100:7777
   ```

### Step 3: Configure Server Settings (in os.agno.com)

- **Enable webhooks** (optional)
- **Set polling interval** to 10-30 seconds
- **Enable monitoring** for performance tracking

## 📡 Available API Endpoints

Once connected, os.agno.com can access these endpoints:

### Health & Status

```http
GET /
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "DOXA Intelligent Ticketing System",
  "port": 7777,
  "integration": "os.agno.com",
  "agents": ["Validator", "Scorer", "Query Analyzer", "Classifier"]
}
```

### Process Ticket

```http
POST /process-ticket
Content-Type: application/json

{
  "client_name": "John Doe",
  "email": "john@example.com",
  "subject": "Login Issue",
  "description": "Cannot login to my account"
}
```

Response:
```json
{
  "status": "success",
  "ticket_id": "uuid",
  "validation": {
    "valid": true,
    "confidence": 0.95,
    "reasons": ["Clear subject", "Detailed description"]
  },
  "score": {
    "score": 75,
    "priority": "high"
  },
  "analysis": {
    "summary": "User unable to authenticate",
    "keywords": ["authentication", "access", "login"],
    "category": "authentication"
  },
  "classification": {
    "category": "authentification",
    "treatment_type": "priority",
    "severity": "high"
  }
}
```

### Agent Chat

```http
POST /agent/chat?message=Can%20you%20help%20with%20a%20billing%20issue
```

Response:
```json
{
  "status": "success",
  "agent_response": "I'm here to help with your billing issue..."
}
```

## 🤖 What's Included

### 4 Specialized AI Agents

1. **Validator Agent**
   - Checks ticket clarity and completeness
   - Provides confidence score
   - Identifies missing information

2. **Scorer Agent**
   - Assigns priority score (0-100)
   - Categorizes as low/medium/high priority
   - Provides reasoning for score

3. **Query Analyzer Agent**
   - Reformulates problem statements
   - Extracts keywords and topics
   - Suggests category
   - Provides detailed analysis

4. **Classifier Agent**
   - Detailed categorization
   - Maps to support categories:
     - `technical` - Technical issues
     - `facturation` - Billing/Invoice issues
     - `authentification` - Auth/Login issues
     - `autre` - Other issues
   - Provides treatment recommendation
   - Assigns severity level

### LLM Backend

- **Model**: Mistral Small Latest (fast & efficient)
- **API**: Mistral AI (mistralai==2.3.19)
- **Temperature**: Optimized per agent (0.3-0.4)
- **Timeout**: 10 seconds per request
- **Fallback**: Heuristic-based scoring if API fails

### Search Integration

- **Tavily Search Tools**: Optional knowledge retrieval
- **API Key**: Already configured in .env

## 🚀 Advanced Features

### Custom Configuration

Edit `ai/agents/config.py` to customize:

```python
# Temperature values
AGENT_TEMPERATURE = {
    "validator": 0.3,      # Strict validation
    "scorer": 0.3,         # Consistent scoring
    "reformulator": 0.4,   # Some flexibility
    "classifier": 0.3,     # Consistent classification
}

# Timeouts
AGENT_RUN_TIMEOUT = 10      # seconds
LLM_API_TIMEOUT = 5         # seconds
```

### Enable Debug Mode

Start server with debug logging:

```powershell
python agentoss_server.py --debug
```

### Run with Custom Port

```powershell
python agentoss_server.py --port 8080
```

## 🔒 Security Considerations

1. **API Key Management**
   - Mistral API key stored in `.env` file
   - Never commit `.env` to git
   - Rotate keys regularly

2. **Network Access**
   - Restrict access to trusted networks only
   - Use firewall rules to limit port 7777 access
   - Consider using VPN for remote access

3. **CORS Configuration**
   - Currently allows all origins
   - Update [agentoss_server.py](agentoss_server.py) to restrict origins if needed

## 📊 Monitoring & Logs

### View Server Logs

```powershell
# Windows - already displayed in terminal
# For persistent logging, redirect output:

python agentoss_server.py > server.log 2>&1
```

### Monitor Performance

os.agno.com provides built-in monitoring:
- Request/response times
- Agent processing times
- Error rates
- Ticket throughput

## 🐛 Troubleshooting

### Server Won't Start

```powershell
# Check if port 7777 is in use
netstat -ano | findstr :7777

# Kill process using port 7777
taskkill /PID <process_id> /F

# Try different port
python agentoss_server.py --port 8888
```

### os.agno.com Shows "Connected but Not Active"

1. Verify server is running: `curl http://localhost:7777/health`
2. Check firewall allows port 7777
3. Verify network connectivity
4. Check server logs for errors
5. Restart the server

### API Key Issues

```powershell
# Verify API key is loaded
python -c "from agents.config import MISTRAL_API_KEY; print(f'Key loaded: {bool(MISTRAL_API_KEY)}')"

# Check .env file exists
Test-Path .\.env
```

### Slow Processing

1. Check internet connection to Mistral API
2. Monitor CPU/memory usage
3. Consider upgrading to faster Mistral model: `mistral-large-latest`
4. Increase timeout values in `config.py`

## 📚 Architecture Overview

```
os.agno.com (Control Plane)
        ↓
    Polling/Webhooks
        ↓
AgentOS Server (Port 7777)
    ├─ FastAPI
    ├─ Uvicorn ASGI
    └─ Agno Agent Framework
        ├─ Mistral LLM
        └─ 4 Specialized Agents
            ├─ Validator
            ├─ Scorer
            ├─ Query Analyzer
            └─ Classifier
```

## 🔄 Next Steps

1. ✅ Start AgentOS server on port 7777
2. ✅ Test endpoints locally
3. 📍 Register server in os.agno.com
4. 📍 Submit test tickets via os.agno.com dashboard
5. 📍 Monitor performance and optimize

## 📞 Support

For issues or questions:
1. Check server logs for error messages
2. Test endpoints directly with curl/Postman
3. Verify Mistral API key and connectivity
4. Review os.agno.com documentation

---

**Status**: ✅ Ready for production  
**Last Updated**: 2025-12-22  
**AgentOS Version**: 2.3.19  
**Mistral API**: mistral-small-latest
