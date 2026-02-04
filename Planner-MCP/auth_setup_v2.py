#!/usr/bin/env python3
"""
Planner MCP Server v2.0 - Authentication Setup
Performs device code authentication and caches the token
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import msal

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TENANT_ID = os.getenv("AZURE_TENANT_ID", "common")

SCOPES = [
    "Tasks.ReadWrite",
    "Group.Read.All",
    "User.Read"
]

TOKEN_CACHE_FILE = Path.home() / ".planner_mcp_token_cache.json"

print("\n" + "="*70)
print(" Planner MCP Server v2.0 - Authentication Setup")
print("="*70)

# Verify we have the required credentials
if not CLIENT_ID:
    print("\n❌ ERROR: AZURE_CLIENT_ID not found in environment")
    print("   Make sure .env file is in the current directory")
    sys.exit(1)

print(f"\n✅ CLIENT_ID: {CLIENT_ID[:20]}...")
print(f"✅ TENANT_ID: {TENANT_ID}")
print(f"📁 Token cache: {TOKEN_CACHE_FILE}")

# Create token cache
token_cache = msal.SerializableTokenCache()

if TOKEN_CACHE_FILE.exists():
    print(f"\n✅ Existing token cache found")
    with open(TOKEN_CACHE_FILE, "r") as f:
        token_cache.deserialize(f.read())

# Create MSAL app
app = msal.PublicClientApplication(
    CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    token_cache=token_cache
)

# Try to get token from cache first
print("\n🔎 Checking for cached token...")
accounts = app.get_accounts()

if accounts:
    print(f"✅ Found {len(accounts)} cached account(s)")
    result = app.acquire_token_silent(SCOPES, account=accounts[0])
    if result and "access_token" in result:
        print("✅ Valid cached token found - authentication complete!")
        print("\n" + "="*70)
        print(" ✨ MCP Server is ready to use!")
        print("="*70)
        print("\nYou can now:")
        print("  1. Close this window")
        print("  2. Restart Claude Desktop")
        print("  3. Start using the Planner MCP Server v2.0")
        print("\n" + "="*70 + "\n")
        sys.exit(0)

# Need interactive authentication
print("\n🔐 No valid cached token - starting interactive authentication...\n")

# Initiate device code flow
flow = app.initiate_device_flow(scopes=SCOPES)

if "user_code" not in flow:
    print("❌ Failed to create device flow")
    print(flow)
    sys.exit(1)

print("="*70)
print(" MICROSOFT AUTHENTICATION REQUIRED")
print("="*70)
print("\n" + flow["message"])
print("\n" + "="*70)
print("\nWaiting for authentication...")

# Poll for token
result = app.acquire_token_by_device_flow(flow)

if "access_token" not in result:
    print("\n❌ Authentication failed!")
    print(result.get("error_description", "Unknown error"))
    sys.exit(1)

# Save token cache
print("\n✅ Authentication successful!")
print("💾 Saving token cache...")

TOKEN_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(TOKEN_CACHE_FILE, "w") as f:
    f.write(token_cache.serialize())

print(f"✅ Token cached at: {TOKEN_CACHE_FILE}")

print("\n" + "="*70)
print(" ✨ MCP Server is ready to use!")
print("="*70)
print("\nYou can now:")
print("  1. Close this window")
print("  2. Restart Claude Desktop")
print("  3. Start using the Planner MCP Server v2.0")
print("\n" + "="*70 + "\n")
