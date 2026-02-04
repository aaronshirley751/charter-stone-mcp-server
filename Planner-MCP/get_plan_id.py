import os
import msal
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load your existing credentials
load_dotenv()

CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
TOKEN_CACHE_PATH = Path.home() / ".charterstone" / "token_cache.json"

# Debug: Check if credentials are loaded
if not all([CLIENT_ID, TENANT_ID]):
    print("❌ Missing credentials in .env file!")
    print(f"   CLIENT_ID: {'✓' if CLIENT_ID else '✗'}")
    print(f"   TENANT_ID: {'✓' if TENANT_ID else '✗'}")
    exit(1)

SCOPES = ["Tasks.ReadWrite", "Group.Read.All", "User.Read"]

def get_access_token():
    """Get access token using device code flow (same as server.py)."""
    cache = msal.SerializableTokenCache()
    
    # Load existing cache if available
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(open(TOKEN_CACHE_PATH, "r").read())
    
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=authority,
        token_cache=cache
    )
    
    # Try to get token from cache first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]
    
    # If no cached token, use device code flow
    print("\n🔐 Authentication required...")
    flow = app.initiate_device_flow(scopes=SCOPES)
    
    if "user_code" not in flow:
        raise Exception("Failed to create device flow")
    
    print(flow["message"])
    
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        # Save token cache
        TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_CACHE_PATH, "w") as f:
            f.write(cache.serialize())
        
        print("✅ Authentication successful!\n")
        return result["access_token"]
    else:
        print(f"❌ Authentication failed: {result.get('error_description', 'Unknown error')}")
        return None

def list_plans():
    token = get_access_token()
    if not token:
        print("❌ Failed to acquire token. Check your .env file.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔎 Scanning for Plans...")
    response = requests.get("https://graph.microsoft.com/v1.0/groups", headers=headers)
    
    if response.status_code == 200:
        groups = response.json().get('value', [])
        for group in groups:
            # Check for plans in this group
            plan_res = requests.get(f"https://graph.microsoft.com/v1.0/groups/{group['id']}/planner/plans", headers=headers)
            if plan_res.status_code == 200:
                plans = plan_res.json().get('value', [])
                for plan in plans:
                    print(f"✅ FOUND PLAN: {plan['title']}")
                    print(f"   ID: {plan['id']}")
                    print(f"   Group: {group['displayName']}")
                    
                    # Fetch buckets for this plan
                    bucket_res = requests.get(f"https://graph.microsoft.com/v1.0/planner/plans/{plan['id']}/buckets", headers=headers)
                    if bucket_res.status_code == 200:
                        buckets = bucket_res.json().get('value', [])
                        if buckets:
                            print(f"   Buckets:")
                            for bucket in buckets:
                                print(f"      - {bucket['name']}: {bucket['id']}")
                    
                    print("-" * 50)
    else:
        print(f"Error listing groups: {response.status_code} - {response.text}")

if __name__ == "__main__":
    list_plans()