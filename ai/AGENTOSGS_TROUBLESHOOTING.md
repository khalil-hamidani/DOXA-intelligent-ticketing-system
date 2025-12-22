# 🔧 AgentOS Troubleshooting Guide - "Connected but not Active" Fix

**Status**: Connected but not active on os.agno.com  
**Issue**: AgentOS can't initialize properly despite backend running

---

## STEP 1: Check Environment Variables ✓

### 1.1 Verify .env file exists
```powershell
Test-Path C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai\.env
```
**Expected**: `True`

### 1.2 Check .env content
```powershell
Get-Content C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai\.env
```
**Expected output:**
```
MISTRAL_API_KEY=jhP09mKu30IaiOqzopwG0jdujcgQZbtg
TAVILY_API_KEY=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
```

### 1.3 Test if Python can read the variables
```powershell
cd C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'MISTRAL_API_KEY: {os.getenv(\"MISTRAL_API_KEY\")}'); print(f'TAVILY_API_KEY: {os.getenv(\"TAVILY_API_KEY\")}')"
```
**Expected**: Both keys should print (not None or blank)

### ❌ If keys are not loading:
1. Check if python-dotenv is installed:
   ```powershell
   pip list | Select-String python-dotenv
   ```
2. If not installed:
   ```powershell
   pip install python-dotenv
   ```

---

## STEP 2: Verify Backend is Running ✓

### 2.1 Check if server is listening on port 8000
```powershell
netstat -ano | Select-String ":8000"
```
**Expected**: Shows a LISTENING process on port 8000

### 2.2 Test the health endpoint
```powershell
curl http://127.0.0.1:8000/
```
**Expected response:**
```json
{
  "status": "online",
  "service": "AI Ticketing System",
  "version": "1.0.0"
}
```

### 2.3 Check Swagger documentation (visual test)
Open in browser:
```
http://127.0.0.1:8000/docs
```
**Expected**: Swagger UI loads with all endpoints listed

### ❌ If server not responding:
1. Check if process is running:
   ```powershell
   Get-Process | Select-String python
   ```
2. If not running, start it:
   ```powershell
   cd C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## STEP 3: Test API Endpoints ✓

### 3.1 Test health check
```powershell
curl http://127.0.0.1:8000/
```

### 3.2 Test agent configuration endpoint (if exists)
```powershell
curl http://127.0.0.1:8000/config
```

### 3.3 Test with a sample ticket
```powershell
curl -X POST http://127.0.0.1:8000/tickets `
  -H "Content-Type: application/json" `
  -d '{
    "client_name": "Test User",
    "email": "test@example.com",
    "subject": "Test",
    "description": "Testing API"
  }'
```
**Expected**: Returns ticket object with processing results

### ❌ If endpoints not responding:
1. Check for import errors in main.py:
   ```powershell
   python main.py
   ```
   (This will show any import issues without starting the server)

2. Check logs (if available):
   ```powershell
   Get-Content -Tail 50 logs/app.log
   ```

---

## STEP 4: AgentOS Connectivity Check ✓

### 4.1 Verify CORS is configured correctly
Check that **os.agno.com** is in allowed origins. Edit `ai/main.py` line ~27:

```python
allow_origins=[
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://os.agno.com",    # ← Must be here
    "http://os.agno.com",     # ← And this
]
```

### 4.2 Test CORS from command line
```powershell
curl -X OPTIONS http://127.0.0.1:8000/ `
  -H "Origin: https://os.agno.com" `
  -H "Access-Control-Request-Method: POST" `
  -v
```

**Look for in response headers:**
```
Access-Control-Allow-Origin: https://os.agno.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: *
```

### 4.3 Check if AgentOS configuration is correct
**In os.agno.com**, look for Agent configuration that points to:
- Backend URL: `http://127.0.0.1:8000` (or your IP: `http://10.0.31.135:8000`)
- API Key: Should match MISTRAL_API_KEY from .env

### ❌ If CORS headers missing:
Server restart required for changes to take effect:
```powershell
# Kill existing process
Stop-Process -Name python -Force

# Wait 2 seconds
Start-Sleep -Seconds 2

# Restart server
cd C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## STEP 5: Apply Fixes 🔧

### Issue A: Backend running but os.agno.com can't reach it

**Problem**: Server is on 127.0.0.1 (localhost only)

**Solution**: Change to 0.0.0.0 (all interfaces)

```powershell
# Stop server
Stop-Process -Name python -Force

# Restart with 0.0.0.0
cd C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then use your actual IP when configuring os.agno.com:
- If os.agno.com is **local**: `http://10.0.31.135:8000`
- If os.agno.com is **remote**: Use your public IP or reverse proxy

---

### Issue B: API keys not loading

**Problem**: MISTRAL_API_KEY or TAVILY_API_KEY shows as None

**Solution**: 

1. Verify .env exists in correct location:
   ```powershell
   C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai\.env
   ```

2. Add explicit path to main.py if needed (line ~1):
   ```python
   from dotenv import load_dotenv
   import os
   
   load_dotenv(dotenv_path='ai/.env')  # Explicit path
   ```

3. Restart server after changes

---

### Issue C: "Connected but not active" on os.agno.com

**Problem**: AgentOS can reach backend but can't initialize

**Possible causes & fixes:**

#### Fix C1: Check API key is valid
```powershell
python -c "
from agents.config import setup_api_keys
try:
    setup_api_keys()
    print('✓ API keys loaded successfully')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

#### Fix C2: Check agents can initialize
```powershell
cd ai
python -m pytest tests/test_agents.py -v
```
**Expected**: All 4 tests PASS

#### Fix C3: Run demo to verify agents work
```powershell
cd ai
python demo_agents.py
```
**Expected**: Shows 3 scenarios processing successfully

#### Fix C4: Verify endpoints exist
Check if os.agno.com is calling the right endpoint. Common endpoints:
```
GET  /                      # Health check
GET  /docs                  # Swagger UI
POST /tickets               # Create ticket
GET  /tickets/{id}          # Get ticket
POST /tickets/{id}/feedback # Feedback
```

If os.agno.com expects different endpoints, add them to main.py

---

## STEP 6: Verification Checklist ✅

After applying fixes, run these checks:

```powershell
# 1. Environment variables loaded?
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('MISTRAL_API_KEY:', 'SET' if os.getenv('MISTRAL_API_KEY') else 'NOT SET')"

# 2. Server running?
netstat -ano | Select-String ":8000"

# 3. Health check works?
curl http://127.0.0.1:8000/

# 4. Agents work?
cd ai && python demo_agents.py

# 5. Tests pass?
python -m pytest tests/test_agents.py -v

# 6. Can create ticket?
curl -X POST http://127.0.0.1:8000/tickets -H "Content-Type: application/json" -d '{"client_name":"Test","email":"t@t.com","subject":"T","description":"T"}'
```

**All should return success/valid responses** ✓

---

## STEP 7: Configure os.agno.com Correctly

Once everything is verified locally:

1. **Note your IP address:**
   ```powershell
   ipconfig | Select-String "IPv4"
   ```
   Copy: `10.0.31.135` or `192.168.56.1`

2. **In os.agno.com, configure the backend:**
   - Backend URL: `http://10.0.31.135:8000` (or your IP)
   - API Key: `jhP09mKu30IaiOqzopwG0jdujcgQZbtg`
   - Port: `8000`

3. **Test connection in os.agno.com:**
   - Should show "Connected and Active" ✓

4. **If still showing "Connected but not active":**
   - Check browser console for errors (F12)
   - Verify API endpoint URLs in os.agno.com config
   - Check that POST /tickets works with test data

---

## Common Issues & Quick Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Server won't start | Port 8000 in use | `netstat -ano \| Select-String ":8000"` then `taskkill /PID <PID>` |
| Import errors | Missing packages | `pip install -r ai/requirements.txt` |
| Keys not loading | .env not found | Move .env to `ai/` directory |
| CORS errors | os.agno.com not in allow_origins | Update main.py line 26-33 |
| Agents failing | API key invalid | Test with: `python demo_agents.py` |
| Can't reach from os.agno.com | Server on 127.0.0.1 | Restart with `0.0.0.0` host |

---

## Need More Help?

**Test locally first:**
```powershell
cd C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Then test: http://127.0.0.1:8000/docs
```

**If backend works but os.agno.com shows "connected but not active":**
- The issue is in AgentOS configuration, not the backend
- Check that AgentOS is pointing to correct IP + port
- Verify API calls are going to POST /tickets (not GET)
- Check browser console (F12) for actual error messages

---

## Quick Start Command

**Start server immediately with all correct settings:**
```powershell
cd C:\Users\hp\OneDrive\Bureau\TC\doxa-intelligent-ticketing\ai
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Then test:**
- http://127.0.0.1:8000/ (health check)
- http://127.0.0.1:8000/docs (Swagger UI)
- os.agno.com (should now show "Connected and Active")

---

**Report back with the output from any failing step and I'll help further!** 🚀
