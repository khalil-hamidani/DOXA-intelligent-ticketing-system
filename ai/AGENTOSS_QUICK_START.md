# 🚀 AgentOS Quick Reference

## Start Server (ONE COMMAND)

```powershell
cd C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai
python agentoss_server.py
```

**Server URL**: `http://0.0.0.0:7777`

---

## Test Server is Running

```powershell
# Test health endpoint
curl http://localhost:7777/health

# Or in PowerShell
Invoke-WebRequest http://localhost:7777/health
```

---

## Connect to os.agno.com

1. Go to: https://os.agno.com/settings/servers
2. Click "Add Server"
3. Enter:
   - **Name**: DOXA Intelligent Ticketing System
   - **URL**: `http://<YOUR_IP>:7777`
   - **Type**: AgentOS

4. Save and wait for "Active" status

---

## What's Running

✅ **AgentOS Server** on port 7777  
✅ **Mistral LLM** integration (mistral-small-latest)  
✅ **4 AI Agents**: Validator, Scorer, Query Analyzer, Classifier  
✅ **FastAPI** with Uvicorn ASGI server  
✅ **Tavily Search** tools enabled  

---

## Available Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health check |
| GET | `/health` | AgentOS health |
| POST | `/process-ticket` | Process support ticket |
| POST | `/agent/chat` | Chat with agent |

---

## Stop Server

```powershell
Press Ctrl+C in the terminal
```

---

## Get Your IP Address

```powershell
# Windows
ipconfig

# Look for IPv4 Address (e.g., 192.168.1.100)
# Then use: http://192.168.1.100:7777
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Port 7777 in use | `netstat -ano \| findstr :7777` then kill process |
| API key error | Check `.env` file has `MISTRAL_API_KEY` |
| Server crashes | Check logs, verify internet connection |
| os.agno.com not connecting | Verify firewall allows port 7777 |

---

## API Key

Your Mistral API key is already configured:
```
MISTRAL_API_KEY=jhP09mKu30IaiOqzopwG0jdujcgQZbtg
```
(stored in `.env` file)

---

## Full Documentation

See [AGENTOSS_SETUP.md](AGENTOSS_SETUP.md) for detailed setup guide.
