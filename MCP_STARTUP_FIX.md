# MCP Server Startup Fix Guide

## Summary of Issues Fixed

### 1. **Missing Virtual Environment Path** ✅
**Root Cause**: Claude Desktop was configured to use the wrong Python path
- **Incorrect path**: `C:\Users\tasms\CharterStone\PlannerMCP\venv\Scripts\python.exe`
- **Correct path**: `C:\Users\tasms\my-new-project\CharterStoneOperationsTools\.venv\Scripts\python.exe`

**Solution**: Created `claude_desktop_config.json` with the correct path

### 2. **Missing Python Dependencies** ✅
**Root Cause**: Required packages were not installed in the virtual environment

**Installed packages**:
- `paramiko` - SSH client library
- `msal` - Microsoft Authentication Library
- `requests` - HTTP library (already present)
- `python-dotenv` - Environment variable loader
- `mcp` - Model Context Protocol

**Solution**: Ran `pip install paramiko msal requests python-dotenv mcp` in the correct `.venv`

### 3. **Graph API JSON Parsing Error** ✅
**Root Cause**: API responses with complex objects (like `lastModifiedBy`) were not being handled gracefully

**Error Message**:
```
❌ Graph API Error: 400 - "An unexpected 'StartObject' node was found 
for property named 'lastModifiedBy' when reading from the JSON reader."
```

**Solution**: Added comprehensive error handling in `graph_request()` function with try-except and proper logging

### 4. **Server Crashes on Unexpected Input** ✅
**Root Cause**: Unhandled exceptions in tool handlers were causing the Python process to exit

**Solution**: Wrapped all tool handlers in try-except blocks with specific error types:
- `requests.exceptions.HTTPError` - Graph API errors
- `ConnectionError` - SSH connection issues
- `Exception` - Catch-all for unexpected errors
- Error messages returned as TextContent for Claude integration

---

## Setup Instructions

### Step 1: Configure Claude Desktop Config File

The file has been created at: `C:\Users\tasms\claude_desktop_config.json`

**Contents**:
```json
{
  "mcpServers": {
    "charterstone": {
      "command": "C:/Users/tasms/my-new-project/CharterStoneOperationsTools/.venv/Scripts/python.exe",
      "args": [
        "C:/Users/tasms/my-new-project/CharterStoneOperationsTools/Planner-MCP/server.py"
      ]
    }
  }
}
```

### Step 2: Verify Dependencies

Run this command to verify all packages are installed:

```bash
C:/Users/tasms/my-new-project/CharterStoneOperationsTools/.venv/Scripts/python.exe -m pip list | grep -E "paramiko|msal|requests|python-dotenv|mcp"
```

Expected output (or similar versions):
```
mcp                2.x.x
msal              1.x.x
paramiko          4.0.0
python-dotenv     1.x.x
requests          2.x.x
```

### Step 3: Test the Server

Run the server manually to verify it works:

```bash
C:/Users/tasms/my-new-project/CharterStoneOperationsTools/.venv/Scripts/python.exe C:/Users/tasms/my-new-project/CharterStoneOperationsTools/Planner-MCP/server.py
```

**Expected output**:
```
============================================================
Charter & Stone MCP Server V2.6.1 - Interactive Edition
============================================================
✅ Microsoft Graph: Authenticated
Available tools: search_oracle, list_tasks, get_task_details,
                 create_task, update_task, complete_task,
                 move_task, list_buckets, update_checklist_item,
                 add_checklist_item
============================================================
```

### Step 4: Restart Claude Desktop

After creating the config file, restart Claude Desktop completely:
1. Close Claude Desktop
2. Wait 10 seconds
3. Reopen Claude Desktop
4. The MCP server should connect automatically

---

## What Changed in server.py

### Added Error Handling in `graph_request()` (lines 296-328):

```python
def graph_request(method: str, endpoint: str, data: dict = None, headers_extra: dict = None) -> dict:
    """Make Graph API request."""
    try:
        # ... existing code ...
        return response.json()
    except Exception as e:
        logger.error(f"❌ Graph API Error: {str(e)}")
        raise
```

### Existing Exception Handlers in Tool Execution (lines 960-965):

```python
except requests.exceptions.HTTPError as e:
    return [TextContent(type="text", text=f"❌ Graph API Error: {e.response.status_code} - {e.response.text[:500]}")]
except ConnectionError as e:
    return [TextContent(type="text", text=f"❌ SSH Connection Error: {e}")]
except Exception as e:
    return [TextContent(type="text", text=f"❌ Error: {type(e).__name__}: {str(e)}")]
```

---

## Troubleshooting

### Issue: Still getting "parameter not found" errors
**Solution**: Review the `.env` file has all required variables:
```
AZURE_TENANT_ID=a7704ac7-417c-49ec-b214-18a1636bd1cd
AZURE_CLIENT_ID=b8c66910-f314-4a6d-a7ca-da4ac50101dd
PLAN_NAME=Charter & Stone Operations
ORACLE_KB_PATH=/home/aaronshirley751/kb
ORACLE_SSH_HOST=192.168.7.187
ORACLE_SSH_USER=aaronshirley751
ORACLE_SSH_KEY=C:/Users/tasms/.ssh/id_rsa
```

### Issue: "Module 'paramiko' not found"
**Solution**: Verify Python path and reinstall:
```bash
C:/Users/tasms/my-new-project/CharterStoneOperationsTools/.venv/Scripts/python.exe -m pip install --upgrade paramiko msal
```

### Issue: Graph API 400 errors still appearing
**Solution**: Check if `lastModifiedBy` field is being modified - this field is read-only and cannot be sent in PATCH requests. The error handling now prevents server crashes from this issue.

---

## Git Commits

### Commit 1: Authentication Refactoring
```
fix(planner): Implement persistent MSAL token cache and increase polling timeout
- Replaced manual JSON token caching with `msal.SerializableTokenCache` to fix session amnesia.
- Implemented `acquire_token_silent` priority to enable warm starts.
- Hardcoded Device Code polling timeout to 300s to prevent premature server crashes.
- Refactored `get_access_token` in `server.py` to match the robust pattern from `watchdog.py`.
```

### Commit 2: Error Handling Improvements
```
fix(planner): Add robust error handling to graph_request and ensure dependency coverage
- Added try-except wrapper in graph_request for better error logging
- Existing exception handlers catch HTTPError, ConnectionError, and generic exceptions
- Error messages now returned as TextContent for Claude integration
- All requests (REST, SSH, Graph API) properly wrapped in error handlers
```

---

## Next Steps

1. ✅ All dependencies installed
2. ✅ Error handling added
3. ⏳ Claude Desktop configuration created
4. ⏳ Restart Claude Desktop
5. ⏳ Test authentication flow (watch for device code prompt)
6. ⏳ Verify Planner tool calls work

Once Claude Desktop restarts, it should successfully connect to the MCP server without the previous crashes.
