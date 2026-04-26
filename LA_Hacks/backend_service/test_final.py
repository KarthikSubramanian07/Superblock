import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUDIENCE = os.getenv("AUTH0_AUDIENCE")

def get_token():
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": AUDIENCE,
        "grant_type": "client_credentials"
    }
    headers = {'content-type': "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get("access_token")

token = get_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
response = requests.post("http://127.0.0.1:8000/agents/orchestrate/live", json={"h3_index": "8929a1d6bd7ffff"}, headers=headers)
print(json.dumps(response.json(), indent=2))
