import requests
import sys
import uuid
import time

# Configuration
PORTS = [8000, 8001, 8002, 8003]
BASE_PATH = "/api/v1"


def find_active_port():
    """Find which port the backend is running on."""
    for port in PORTS:
        try:
            url = f"http://localhost:{port}/health"
            resp = requests.get(url, timeout=1)
            if resp.status_code == 200:
                return port
        except requests.exceptions.ConnectionError:
            continue
    return None


def run_tests():
    print("🔍 Searching for active backend server...")
    port = find_active_port()

    if not port:
        print(f"❌ Could not find running server on ports {PORTS}")
        print("   Please start the backend: uvicorn app.main:app --reload")
        sys.exit(1)

    base_url = f"http://localhost:{port}{BASE_PATH}"
    print(f"✅ Found server at http://localhost:{port}")
    print(f"🚀 Running Phase 3 Auth Tests against {base_url}...")

    # Generate unique user for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"test_user_{unique_id}@example.com"
    password = "securePassword123!"

    # ---------------------------------------------------------
    # 1. Test Registration
    # ---------------------------------------------------------
    print(f"\n[1] Testing Registration")
    print(f"    Email: {email}")
    register_url = f"{base_url}/auth/register"
    register_payload = {"email": email, "password": password}

    try:
        resp = requests.post(register_url, json=register_payload)
        if resp.status_code == 200:
            data = resp.json()
            print("    ✅ Register Success")
            print(f"       ID: {data.get('id')}, Role: {data.get('role')}")
        else:
            print(f"    ❌ Register Failed: {resp.status_code}")
            print(f"       Response: {resp.text}")
            sys.exit(1)
    except Exception as e:
        print(f"    ❌ Request Error: {e}")
        sys.exit(1)

    # ---------------------------------------------------------
    # 2. Test Login
    # ---------------------------------------------------------
    print(f"\n[2] Testing Login")
    login_url = f"{base_url}/auth/login"
    login_payload = {"email": email, "password": password}

    resp = requests.post(login_url, json=login_payload)
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("access_token")
        token_type = data.get("token_type")

        if token and token_type:
            print("    ✅ Login Success")
            print(f"       Token: {token[:15]}... (truncated)")
        else:
            print("    ❌ Login Failed: Token missing in response")
            sys.exit(1)
    else:
        print(f"    ❌ Login Failed: {resp.status_code}")
        print(f"       Response: {resp.text}")
        sys.exit(1)

    # ---------------------------------------------------------
    # 3. Test Get Me (Protected Route)
    # ---------------------------------------------------------
    print(f"\n[3] Testing /auth/me (Protected Route)")
    me_url = f"{base_url}/auth/me"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(me_url, headers=headers)
    if resp.status_code == 200:
        user_data = resp.json()
        if user_data.get("email") == email:
            print("    ✅ /auth/me Success")
            print(f"       User: {user_data.get('email')} ({user_data.get('role')})")
        else:
            print(f"    ❌ /auth/me Failed: Email mismatch")
            print(f"       Expected: {email}")
            print(f"       Got: {user_data.get('email')}")
            sys.exit(1)
    else:
        print(f"    ❌ /auth/me Failed: {resp.status_code}")
        print(f"       Response: {resp.text}")
        sys.exit(1)

    # ---------------------------------------------------------
    # 4. Test Unauthorized Access
    # ---------------------------------------------------------
    print(f"\n[4] Testing Unauthorized Access (No Token)")
    resp = requests.get(me_url)  # No headers
    if resp.status_code in [401, 403]:
        print(f"    ✅ Correctly rejected with {resp.status_code}")
    else:
        print(f"    ❌ Security Fail: Expected 401/403, got {resp.status_code}")
        sys.exit(1)

    print("\n" + "=" * 40)
    print("🎉 ALL PHASE 3 TESTS PASSED SUCCESSFULLY!")
    print("=" * 40)


if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("❌ 'requests' library not found.")
        print("   Please run: pip install requests")
        sys.exit(1)

    run_tests()
