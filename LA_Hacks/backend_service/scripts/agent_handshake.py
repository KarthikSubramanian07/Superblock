import os
import requests
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUDIENCE = os.getenv("AUTH0_AUDIENCE")

def get_agent_token():
    """Performs the Auth0 Machine-to-Machine handshake to get a JWT."""
    print(f"🔒 Authenticating agent with Auth0 ({AUTH0_DOMAIN})...")
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": AUDIENCE,
        "grant_type": "client_credentials"
    }
    headers = {'content-type': "application/json"}
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.text}")
        return None
    
    token = response.json().get("access_token")
    print("✅ Agent Identity Verified. JWT acquired.")
    return token

def call_protected_orchestrate(token):
    """Calls the Superblock orchestrate endpoint using the Auth0 token."""
    print("\n📡 Calling Superblock Orchestrator with secure identity...")
    url = "http://127.0.0.1:8000/agents/orchestrate"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json={}, headers=headers)
    if response.status_code == 200:
        print("🎉 Success! Orchestrator accepted the agent's identity.")
        print(f"Response: {response.json().get('selected_h3_index')}")
    else:
        print(f"❌ Rejected: {response.status_code} - {response.text}")

if __name__ == "__main__":
    token = get_agent_token()
    if token:
        call_protected_orchestrate(token)
