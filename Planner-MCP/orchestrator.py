import os
import json
import re
import time
import requests
import msal
from pathlib import Path
from dotenv import load_dotenv
import sys
import io

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import your existing tool
from irs_scraper import scrape_990

# Load environment variables
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# 1. CREDENTIALS
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")

# 2. PLANNER CONFIG
PLAN_ID = "y9DwHD-ObEGDHvjmhIFtW2UAAnJj" # Launch Operations
SOURCE_BUCKET_ID = "_KJDX4pHKkuO7bxKv98R5WUAJVxe"   # Watchdog Inbox
DEST_BUCKET_ID = "QDeSpyXMUUaBLf2cJIi84WUALZr_"   # Strategy & Intel

# 3. STORAGE
TOKEN_CACHE_PATH = Path.home() / ".charterstone" / "token_cache.json"

# =============================================================================
# AUTHENTICATION (Standardized)
# =============================================================================

class GraphAuthenticator:
    def __init__(self):
        self._token_cache = msal.SerializableTokenCache()
        self._load_token_cache()
        self._app = msal.PublicClientApplication(
            AZURE_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{AZURE_TENANT_ID}",
            token_cache=self._token_cache
        )
    
    def _load_token_cache(self):
        if TOKEN_CACHE_PATH.exists():
            self._token_cache.deserialize(TOKEN_CACHE_PATH.read_text())
            
    def _save_token_cache(self):
        TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE_PATH.write_text(self._token_cache.serialize())
    
    def get_access_token(self):
        accounts = self._app.get_accounts()
        scopes = ["Tasks.ReadWrite", "Group.Read.All", "User.Read"]
        if accounts:
            result = self._app.acquire_token_silent(scopes=scopes, account=accounts[0])
            if result and "access_token" in result:
                self._save_token_cache()
                return result["access_token"]
        print("❌ Auth Error: No cached token found. Run server.py or watchdog.py first.")
        return None

_auth = GraphAuthenticator()

def get_graph_headers():
    token = _auth.get_access_token()
    if token:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return None

# =============================================================================
# DATA CLEANING MAPS
# =============================================================================

ABBREVIATIONS = {
    "WVU": "West Virginia University",
    "UW": "University of Washington",
    "UT": "University of Texas",
    "LSU": "Louisiana State University",
    "UNC": "University of North Carolina",
    "UVA": "University of Virginia",
    "USC": "University of Southern California",
    "NYU": "New York University",
    "MSU": "Michigan State University",
    "A&M": "Texas A&M University",
    "UCONN": "University of Connecticut",
    "UMASS": "University of Massachusetts",
    "NAU": "Northern Arizona University",
    "ASU": "Arizona State University"
}

# =============================================================================
# AUTHENTICATION
# =============================================================================

class GraphAuthenticator:
    def __init__(self):
        self._token_cache = msal.SerializableTokenCache()
        self._load_token_cache()
        self._app = msal.PublicClientApplication(
            AZURE_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{AZURE_TENANT_ID}",
            token_cache=self._token_cache
        )
    
    def _load_token_cache(self):
        if TOKEN_CACHE_PATH.exists():
            self._token_cache.deserialize(TOKEN_CACHE_PATH.read_text())
            
    def _save_token_cache(self):
        TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE_PATH.write_text(self._token_cache.serialize())
    
    def get_access_token(self):
        accounts = self._app.get_accounts()
        scopes = ["Tasks.ReadWrite", "Group.Read.All", "User.Read"]
        if accounts:
            result = self._app.acquire_token_silent(scopes=scopes, account=accounts[0])
            if result and "access_token" in result:
                self._save_token_cache()
                return result["access_token"]
        print("❌ Auth Error: No cached token found. Run server.py or watchdog.py first.")
        return None

_auth = GraphAuthenticator()

def get_graph_headers():
    token = _auth.get_access_token()
    if token:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return None

# =============================================================================
# WORKFLOW LOGIC
# =============================================================================

def clean_org_name(task_title):
    # Remove tags and cleanup
    name = re.sub(r"\[.*?\]\s*", "", task_title)
    name = name.replace("...", "").strip()
    
    # Check abbreviations
    first_word = name.split(" ")[0].upper().replace(":", "").replace(",", "")
    if first_word in ABBREVIATIONS:
        return ABBREVIATIONS[first_word]
    
    return name

def process_tasks():
    headers = get_graph_headers()
    if not headers: return

    print("🌉 Orchestrator: Checking the Bridge...")
    
    # 0. Get My ID (For Assignment)
    try:
        me_res = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        my_id = me_res.json().get('id')
    except:
        print("⚠️ Could not fetch user ID. Tasks will be unassigned.")
        my_id = None

    # 1. Get Tasks from Source Bucket
    url = f"https://graph.microsoft.com/v1.0/planner/buckets/{SOURCE_BUCKET_ID}/tasks"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to list tasks: {response.text}")
        return

    tasks = response.json().get('value', [])
    print(f"📋 Found {len(tasks)} tasks in Inbox.")

    for task in tasks:
        task_id = task['id']
        title = task['title']
        print(f"⚙️ Processing: {title}")

        # 2. Extract Name & Run Research
        org_name = clean_org_name(title)
        print(f"   🔎 Researching: '{org_name}'")
        
        # Default notes if scraper fails
        notes = "Automated Research: Analysis pending."
        
        try:
            # CALL THE DEEP DIVE TOOL
            data = scrape_990(org_name)
            
            if not data or not data.ein:
                print("   ⚠️ No 990 found. Moving without data.")
                notes = "Automated Research: No IRS 990 data found matching this name."
            else:
                print(f"   ✅ Data Found: Rev ${data.total_revenue:,}")
                notes = (
                    f"🤖 Automated Deep Dive:\n"
                    f"Organization: {data.organization_name}\n"
                    f"Tax Year: {data.tax_year}\n"
                    f"Revenue: ${data.total_revenue:,}\n"
                    f"Net Assets: ${data.net_assets:,}\n"
                    f"Link: {data.pdf_url}"
                )

            # 3. Update Task (Notes)
            details_res = requests.get(f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}/details", headers=headers)
            etag = details_res.json()['@odata.etag']
            existing_desc = details_res.json().get('description', "")
            
            requests.patch(
                f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}/details",
                headers={"Authorization": headers["Authorization"], "Content-Type": "application/json", "If-Match": etag},
                json={"description": f"{existing_desc}\n\n{notes}", "previewType": "description"}
            )

            # 4. Move & Assign
            task_res = requests.get(f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}", headers=headers)
            task_etag = task_res.json()['@odata.etag']
            
            payload = {"bucketId": DEST_BUCKET_ID}
            
            # Add assignment if ID was found
            if my_id:
                payload["assignments"] = {
                    my_id: {"@odata.type": "#microsoft.graph.plannerAssignment", "orderHint": " !"}
                }

            requests.patch(
                f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}",
                headers={"Authorization": headers["Authorization"], "Content-Type": "application/json", "If-Match": task_etag},
                json=payload
            )
            
            print(f"   🚀 Moved to Strategy Bucket (Assigned to You)")

        except Exception as e:
            print(f"   ❌ Error processing task: {e}")

if __name__ == "__main__":
    process_tasks()
