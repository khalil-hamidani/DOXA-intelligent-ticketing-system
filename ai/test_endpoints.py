#!/usr/bin/env python
"""
Quick test of AgentOS backend endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("🔍 AgentOS Backend Endpoint Testing")
print("=" * 60)

# Test 1: Root endpoint
print("\n1️⃣  Testing GET /")
try:
    r = requests.get(f"{BASE_URL}/")
    print(f"   Status: {r.status_code}")
    print(f"   Response: {json.dumps(r.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Health endpoint
print("\n2️⃣  Testing GET /health")
try:
    r = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {r.status_code}")
    print(f"   Response: {json.dumps(r.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Swagger docs
print("\n3️⃣  Testing GET /docs")
try:
    r = requests.get(f"{BASE_URL}/docs")
    print(f"   Status: {r.status_code}")
    print(f"   Response: Swagger UI loaded" if r.status_code == 200 else "   Failed to load")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Create ticket
print("\n4️⃣  Testing POST /tickets")
try:
    ticket_data = {
        "client_name": "Test User",
        "email": "test@example.com",
        "subject": "Test Ticket",
        "description": "This is a test ticket"
    }
    r = requests.post(f"{BASE_URL}/tickets", json=ticket_data)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        response = r.json()
        print(f"   ✓ Ticket ID: {response.get('ticket_id')}")
        print(f"   ✓ Status: {response.get('result', {}).get('status')}")
    else:
        print(f"   Response: {r.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: CORS preflight
print("\n5️⃣  Testing OPTIONS / (CORS preflight)")
try:
    r = requests.options(
        f"{BASE_URL}/",
        headers={
            "Origin": "https://os.agno.com",
            "Access-Control-Request-Method": "POST"
        }
    )
    print(f"   Status: {r.status_code}")
    cors_header = r.headers.get("access-control-allow-origin", "NOT SET")
    print(f"   CORS Header: {cors_header}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ Test complete!")
print("=" * 60)
