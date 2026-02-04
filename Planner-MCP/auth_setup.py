#!/usr/bin/env python3
"""
Charter & Stone Planner MCP - Authentication Setup

This script performs a one-time Device Code Flow authentication to generate
and cache the token needed by the MCP server.

Run this once before starting the server.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import msal

# Load environment variables
load_dotenv()

# Configuration (matches server.py)
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "a7704ac7-417c-49ec-b214-18a1636bd1cd")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "b8c66910-f314-4a6d-a7ca-da4ac50101dd")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
SCOPES = ["Tasks.ReadWrite", "Group.Read.All", "User.Read"]

# Token cache location (must match server.py)
TOKEN_CACHE_PATH = Path.home() / ".charterstone" / "token_cache.json"


def setup_authentication():
    """Perform Device Code Flow authentication and save token cache."""
    print("\n" + "="*70)
    print("Charter & Stone Planner MCP - Authentication Setup")
    print("="*70 + "\n")
    
    # Initialize token cache
    token_cache = msal.SerializableTokenCache()
    
    # Load existing cache if it exists
    if TOKEN_CACHE_PATH.exists():
        print(f"Loading existing token cache from {TOKEN_CACHE_PATH}")
        token_cache.deserialize(TOKEN_CACHE_PATH.read_text())
    
    # Create MSAL app
    app = msal.PublicClientApplication(
        AZURE_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{AZURE_TENANT_ID}",
        token_cache=token_cache
    )
    
    # Check if we already have a valid token
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(
            scopes=[f"https://graph.microsoft.com/{s}" for s in SCOPES],
            account=accounts[0]
        )
        if result and "access_token" in result:
            print("✓ Valid cached token found!")
            print(f"  Expires: {result.get('expires_in')} seconds")
            return True
    
    print("No valid cached token found. Starting Device Code Flow...\n")
    
    # Initiate device flow
    flow = app.initiate_device_flow(
        scopes=[f"https://graph.microsoft.com/{s}" for s in SCOPES]
    )
    
    if "user_code" not in flow:
        error_desc = flow.get('error_description', 'Unknown error')
        print(f"✗ Failed to create device flow: {error_desc}")
        if "client_secret" in error_desc.lower():
            print("\n⚠️  IMPORTANT: Your Azure app may need a client secret.")
            print("   Set AZURE_CLIENT_SECRET in a .env file or as an environment variable.")
        return False
    
    # Display instructions
    print("="*70)
    print("AUTHENTICATION REQUIRED")
    print("="*70)
    print(f"\n1. Go to: {flow['verification_uri']}")
    print(f"2. Enter code: {flow['user_code']}\n")
    print("Waiting for you to complete authentication...")
    print("(This typically takes 2-5 minutes)")
    print("="*70 + "\n")
    
    # Wait for user to authenticate
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" not in result:
        error_desc = result.get('error_description', 'Unknown error')
        print(f"✗ Authentication failed: {error_desc}")
        return False
    
    # Save token cache to disk
    TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE_PATH.write_text(token_cache.serialize())
    
    print("✓ Authentication successful!")
    print(f"✓ Token cache saved to: {TOKEN_CACHE_PATH}\n")
    
    return True


if __name__ == "__main__":
    success = setup_authentication()
    sys.exit(0 if success else 1)
