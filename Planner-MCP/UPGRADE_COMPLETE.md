# Planner MCP Server v2.0 Upgrade - COMPLETED

## ✅ Upgrade Status: SUCCESSFUL

**Date:** January 29, 2026  
**Version:** 2.0  
**Location:** `c:\Users\tasms\my-new-project\Charter & Stone Operations Tools\Planner-MCP\`

---

## 📋 Completed Steps

### ✅ 1. Workspace Setup
- [x] Identified current Planner-MCP directory
- [x] Located existing server.py
- [x] Created backup: `server.py.backup`

### ✅ 2. Installation
- [x] Copied upgraded server to `server.py`
- [x] Updated `requirements.txt` to v2.0 specifications
- [x] Installed/upgraded all Python dependencies
- [x] Verified imports work correctly

### ✅ 3. Configuration
- [x] Retrieved Plan ID: `y9DwHD-ObEGDHvjmhIFtW2UAAnJj`
- [x] Retrieved Group ID: `y9DwHD-ObEGDHvjmhIFtW2UAAnJj`
- [x] Updated `.env` file with required IDs
- [x] Verified all environment variables are set

### ✅ 4. Documentation
- [x] Copied `UPGRADE_GUIDE.md` to workspace
- [x] Copied `QUICK_REFERENCE.md` to workspace
- [x] Created `test_upgrade.py` for validation

---

## 🔧 Configuration Summary

**Environment Variables Set:**
```
AZURE_TENANT_ID=a7704ac7-417c-49ec-b214-18a1636bd1cd
AZURE_CLIENT_ID=b8c66910-f314-4a6d-a7ca-da4ac50101dd
PLANNER_PLAN_ID=y9DwHD-ObEGDHvjmhIFtW2UAAnJj
PLANNER_GROUP_ID=y9DwHD-ObEGDHvjmhIFtW2UAAnJj
M365_GROUP_NAME=Charter & Stone
PLANNER_PLAN_NAME=Launch Operations
```

**Plan Details:**
- **Plan Name:** Launch Operations
- **Group:** Charter & Stone
- **Buckets Available:**
  - Watchdog Inbox
  - Sandbox/Parking Lot
  - Operations Blueprint
  - Digital Teammates Org Chart (R&D)
  - Branding & Assets
  - Strategy & Intel
  - Financial Infrastructure
  - Legal & Structure

---

## 🎯 Next Steps for You

### Step 1: Update Claude Desktop Config

You need to update your Claude Desktop configuration to use the upgraded server.

**File Location:**  
`C:\Users\tasms\AppData\Roaming\Claude\claude_desktop_config.json`

**Add or update the "planner" section:**

```json
{
  "mcpServers": {
    "planner": {
      "command": "C:\\Users\\tasms\\my-new-project\\Charter & Stone Operations Tools\\Planner-MCP\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\tasms\\my-new-project\\Charter & Stone Operations Tools\\Planner-MCP\\server.py"
      ],
      "env": {
        "AZURE_CLIENT_ID": "b8c66910-f314-4a6d-a7ca-da4ac50101dd",
        "AZURE_TENANT_ID": "a7704ac7-417c-49ec-b214-18a1636bd1cd",
        "PLANNER_PLAN_ID": "y9DwHD-ObEGDHvjmhIFtW2UAAnJj",
        "PLANNER_GROUP_ID": "y9DwHD-ObEGDHvjmhIFtW2UAAnJj"
      }
    }
  }
}
```

### Step 2: Restart Claude Desktop

1. **Close** Claude Desktop completely (check system tray)
2. **Reopen** Claude Desktop
3. The upgraded Planner MCP server will load automatically

### Step 3: Test the New Features

Once Claude Desktop restarts, test the new capabilities:

#### Test 1: List Tasks
```
List all incomplete tasks in the Launch Operations plan
```

#### Test 2: Get Task Details (NEW!)
```
Get full details for the R&D personas task
```

#### Test 3: Create Task with Description (ENHANCED!)
```
Create a task titled "Test v2.0 Upgrade" in Strategy & Intel bucket with description "Verifying the upgraded MCP server works correctly" due February 1, 2026
```

#### Test 4: Update Task (NEW!)
```
Update the test task to 50% complete
```

---

## 🎉 New Features Available

### 1. **get_task_details**
- Retrieve complete task information including:
  - Full description text
  - Checklist items and status
  - Bucket name (not just ID)
  - All assignment details
  - References/attachments

### 2. **update_task**
- Modify existing tasks:
  - Update title
  - Change completion percentage (0-100)
  - Modify description
  - Adjust due dates

### 3. **Enhanced create_task**
- Create tasks with full metadata:
  - Set description on creation
  - Assign to users by email
  - Set due dates
  - Specify bucket

---

## 🐛 Troubleshooting

### If authentication fails:

```bash
# Navigate to MCP directory
cd "C:\Users\tasms\my-new-project\Charter & Stone Operations Tools\Planner-MCP"

# Delete token cache
rm ~/.planner_mcp_token_cache.json

# Or on Windows:
del %USERPROFILE%\.planner_mcp_token_cache.json
```

Then restart Claude Desktop - you'll see a device code prompt.

### If server doesn't load:

Check Claude Desktop logs:
```
C:\Users\tasms\AppData\Roaming\Claude\logs\mcp*.log
```

Look for errors related to the planner server.

### Run Manual Test:

```bash
cd "C:\Users\tasms\my-new-project\Charter & Stone Operations Tools\Planner-MCP"
venv\Scripts\python.exe test_upgrade.py
```

This will test all new features and verify everything works.

---

## 📚 Documentation

- **Full Guide:** [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Test Suite:** [test_upgrade.py](test_upgrade.py)
- **Server Logs:** `~/.planner_mcp.log`

---

## 🔄 Rollback Instructions

If you need to revert to the old version:

```bash
cd "C:\Users\tasms\my-new-project\Charter & Stone Operations Tools\Planner-MCP"
cp server.py.backup server.py
```

Then restart Claude Desktop.

---

## ✨ What Changed

### Files Modified:
- ✅ `server.py` - Replaced with v2.0
- ✅ `requirements.txt` - Updated dependencies
- ✅ `.env` - Added PLANNER_PLAN_ID and PLANNER_GROUP_ID

### Files Added:
- ✅ `server.py.backup` - Backup of original
- ✅ `UPGRADE_GUIDE.md` - Detailed instructions
- ✅ `QUICK_REFERENCE.md` - Feature reference
- ✅ `test_upgrade.py` - Validation suite

### Files Unchanged:
- ✅ `get_plan_id.py` - Still works for reference
- ✅ `auth_setup.py` - Authentication helper
- ✅ Other project files (watchdog, orchestrator, etc.)

---

## 🎯 Ready to Use!

Your Planner MCP Server v2.0 is fully installed and configured. 

**To complete the upgrade:**
1. Update `claude_desktop_config.json` (see Step 1 above)
2. Restart Claude Desktop
3. Test the new features!

**Questions or Issues?**
- Check server logs: `~/.planner_mcp.log`
- Review documentation in workspace
- Run test suite: `venv\Scripts\python.exe test_upgrade.py`

---

**Upgrade completed by:** GitHub Copilot  
**Date:** January 29, 2026  
**Status:** ✅ READY FOR USE
