import os
import sys
import json
import requests
import feedparser
import msal
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# 1. CREDENTIALS (Load from .env - Same as server.py)
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

# 2. PLANNER CONFIG
PLANNER_BUCKET_ID = "_KJDX4pHKkuO7bxKv98R5WUAJVxe" # Watchdog Inbox
PLAN_ID = "y9DwHD-ObEGDHvjmhIFtW2UAAnJj" # Launch Operations

# 3. STORAGE
HISTORY_FILE = "watchdog_history.json"
TOKEN_CACHE_PATH = Path.home() / ".charterstone" / "token_cache.json"

# 4. FEEDS (THE "DEEP DIVE" STRATEGY)
FEEDS = [
    # 🔴 DISTRESS (Turnaround Targets)
    "https://news.google.com/rss/search?q=university+president+resigns+OR+financial+exigency+OR+faculty+vote+no+confidence+OR+budget+deficit+layoffs&hl=en-US&gl=US&ceid=US:en",
    
    # 🟢 FORECAST: STRATEGIC PLANNING (The "Pre-RFP" Signal)
    # Looks for Boards approving plans, launching task forces, or master planning.
    "https://news.google.com/rss/search?q=university+board+of+regents+approves+%22strategic+plan%22+OR+%22master+plan%22+OR+%22enrollment+strategic+plan%22&hl=en-US&gl=US&ceid=US:en",

    # 🟡 FORECAST: BUDGET & FINANCE (The Money Trail)
    # Looks for budget presentations, deficits, or new fiscal year priorities.
    "https://news.google.com/rss/search?q=university+%22FY26+budget%22+presentation+OR+%22capital+improvement+plan%22+approved+OR+%22enrollment+management%22+budget&hl=en-US&gl=US&ceid=US:en",
    
    # Industry News
    "https://www.highereddive.com/feeds/news"
]

# 🔴 DISTRESS KEYWORDS
DISTRESS_KEYWORDS = [
    "resigns", "stepping down", "deficit", "budget cuts", "layoffs", 
    "restructuring", "closure", "merger", "vote of no confidence", 
    "financial exigency", "probation"
]

# 🟢 OPPORTUNITY KEYWORDS (Updated with "Forecast" Terms)
OPPORTUNITY_KEYWORDS = [
    # Explicit Procurement
    "request for proposal", "rfp", "request for qualifications", "rfq", 
    "feasibility study", 
    
    # The "Forecast" Signals (6 Months Out)
    "strategic plan approved", "master plan approved", "capital campaign launch",
    "enrollment task force", "presidential search committee", 
    "board of trustees meeting", "budget presentation", "strategic initiative",
    "consultant search", "audit findings"
]

# =============================================================================
# AUTHENTICATION (The Shared Brain)
# =============================================================================

class GraphAuthenticator:
    """Handles Microsoft Graph API authentication via Device Code Flow (Shared with server.py)."""
    
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
        
        # 1. Try Silent (Cache)
        if accounts:
            result = self._app.acquire_token_silent(scopes=scopes, account=accounts[0])
            if result and "access_token" in result:
                self._save_token_cache()
                return result["access_token"]
        
        # 2. Device Code Flow (Interactive)
        # Note: Since server.py likely already logged you in, this rarely hits.
        flow = self._app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            print("❌ Failed to create device flow")
            return None
            
        print(f"\n⚠️ AUTH REQUIRED: {flow['message']}")
        result = self._app.acquire_token_by_device_flow(flow)
        
        if "access_token" in result:
            self._save_token_cache()
            return result["access_token"]
        else:
            print(f"❌ Auth Failed: {result.get('error_description')}")
            return None

# Initialize Auth
_auth = GraphAuthenticator()

def get_graph_headers():
    token = _auth.get_access_token()
    if token:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return None

# =============================================================================
# CORE LOGIC
# =============================================================================

def analyze_signal(title):
    title_lower = title.lower()
    for word in DISTRESS_KEYWORDS:
        if word in title_lower: return "🔴 DISTRESS", word, 1
    for word in OPPORTUNITY_KEYWORDS:
        if word in title_lower: return "🟢 FORECAST", word, 3
    return None, None, None

def send_teams_alert(signal_type, title, article_url, matched_keyword):
    if not TEAMS_WEBHOOK_URL: return
    # Color Coding: Red (Distress), Green (Forecast/Opportunity)
    color = "Attention" if signal_type == "🔴 DISTRESS" else "Good"
    
    card = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "body": [
                    {"type": "TextBlock", "text": f"{signal_type} SIGNAL", "weight": "Bolder", "size": "Large", "color": color},
                    {"type": "TextBlock", "text": f"**Trigger:** {matched_keyword.upper()}", "isSubtle": True},
                    {"type": "TextBlock", "text": title, "wrap": True},
                    {"type": "FactSet", "facts": [{"title": "Strategy", "value": "Turnaround" if signal_type == "🔴 DISTRESS" else "BizDev Forecast"}]}
                ],
                "actions": [{"type": "Action.OpenUrl", "title": "Read Intel", "url": article_url}],
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "version": "1.2"
            }
        }]
    }
    requests.post(TEAMS_WEBHOOK_URL, json=card)

def create_planner_task(signal_type, title, article_url, keyword, priority):
    headers = get_graph_headers()
    if not headers: 
        print("❌ Failed to get headers for task creation")
        return

    task_payload = {
        "planId": PLAN_ID,
        "bucketId": PLANNER_BUCKET_ID,
        "title": f"[{signal_type}] {title[:50]}...", 
        "priority": priority,
        "dueDateTime": datetime.now().isoformat() + "Z"
    }
    
    response = requests.post("https://graph.microsoft.com/v1.0/planner/tasks", headers=headers, json=task_payload)
    if response.status_code == 201:
        print(f"✅ Task Created: {title[:30]}...")
        task_data = response.json()
        task_id = task_data['id']
        
        # Add description
        details_get = requests.get(f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}/details", headers=headers)
        if details_get.status_code == 200:
            etag = details_get.json()['@odata.etag']
            headers['If-Match'] = etag
            requests.patch(
                f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}/details",
                headers=headers,
                json={"description": f"Triggered by Watchdog V2.2.\nType: {signal_type}\nKeyword: {keyword}\nSource: {article_url}", "previewType": "description"}
            )
    else:
        print(f"❌ Task Creation Failed: {response.text}")

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f: return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f: json.dump(history, f)

def scan_feeds():
    history = load_history()
    print(f"🔎 Watchdog V2.2 scanning for Strategic Forecasts...")
    
    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            
            if link in history: continue

            signal_type, keyword, priority = analyze_signal(title)
            
            if signal_type:
                print(f"🎯 {signal_type} FOUND: {title}")
                send_teams_alert(signal_type, title, link, keyword)
                create_planner_task(signal_type, title, link, keyword, priority)
                
                history.append(link)
                save_history(history)

if __name__ == "__main__":
    scan_feeds()