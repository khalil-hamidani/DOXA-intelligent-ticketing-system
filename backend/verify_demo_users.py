import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"


def verify_login(email, password, role):
    print(f"Verifying login for {role} ({email})...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
        )
        if response.status_code == 200:
            print(f"✅ Login successful for {role}")
            token = response.json().get("access_token")
            if token:
                print(f"   Token received.")
                # Verify /me endpoint
                headers = {"Authorization": f"Bearer {token}"}
                me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    if user_data["role"] == role:
                        print(f"✅ Role verified: {role}")
                    else:
                        print(
                            f"❌ Role mismatch: Expected {role}, got {user_data['role']}"
                        )
                else:
                    print(f"❌ Failed to fetch user info: {me_response.status_code}")
            else:
                print("❌ No access token in response")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception during verification: {e}")


if __name__ == "__main__":
    demo_users = [
        ("admin@doxa.demo", "Admin123!", "ADMIN"),
        ("agent@doxa.demo", "Agent123!", "AGENT"),
        ("client@doxa.demo", "Client123!", "CLIENT"),
    ]

    for email, password, role in demo_users:
        verify_login(email, password, role)
        print("-" * 20)
