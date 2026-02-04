# Planner MCP Server Upgrade Guide

## Version 2.0 - New Features

### Added Capabilities
1. **get_task_details** - Retrieve complete task information including:
   - Full description
   - Checklist items
   - References/attachments
   - Bucket name
   - Assignee information
   - Created/due/start dates
   - Priority level
   - Completion percentage

2. **update_task** - Modify existing tasks:
   - Update title
   - Change completion percentage
   - Modify description
   - Adjust due dates

3. **Enhanced create_task** - Improved task creation with:
   - Description support
   - Due date setting
   - User assignment

## Installation Instructions

### Step 1: Locate Your Current MCP Server

Your Planner MCP server is registered in Claude Desktop's configuration. 

**Windows Path:**
```
C:\Users\tasms\AppData\Roaming\Claude\claude_desktop_config.json
```

Open this file to find the current server location.

### Step 2: Backup Current Server

```bash
# Navigate to your MCP server directory (example)
cd C:\path\to\your\mcp\servers\planner

# Backup the current version
copy server.py server.py.backup
```

### Step 3: Install Upgraded Server

Option A - Replace existing file:
```bash
# Copy the upgraded server to your MCP directory
copy planner_mcp_upgraded.py C:\path\to\your\mcp\servers\planner\server.py
```

Option B - Run as separate server (recommended for testing):
```bash
# Keep both versions and test the new one first
copy planner_mcp_upgraded.py C:\path\to\your\mcp\servers\planner\server_v2.py
```

### Step 4: Update Claude Desktop Config

Edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "planner": {
      "command": "python",
      "args": [
        "C:\\path\\to\\your\\mcp\\servers\\planner\\server_v2.py"
      ],
      "env": {
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_TENANT_ID": "common",
        "PLANNER_PLAN_ID": "your-plan-id",
        "PLANNER_GROUP_ID": "your-group-id"
      }
    }
  }
}
```

### Step 5: Restart Claude Desktop

Close and reopen Claude Desktop to load the upgraded server.

### Step 6: Test New Functionality

Test the new `get_task_details` function:

```
Retrieve all details for task ID: CfZuItAUdUKOl_LCgsb1i2UAK1rq
```

## Troubleshooting

### Authentication Issues

If you get authentication errors:

1. Delete token cache:
```bash
del %USERPROFILE%\.planner_mcp_token_cache.json
```

2. Restart Claude Desktop - you'll be prompted to authenticate again

### Missing Dependencies

Install required packages:
```bash
pip install msal httpx mcp
```

### Server Not Showing Up

1. Check Claude Desktop logs:
```
C:\Users\tasms\AppData\Roaming\Claude\logs\mcp.log
```

2. Verify config file JSON syntax is valid

3. Ensure Python path is correct in config

## Verification Checklist

- [ ] Backup of original server created
- [ ] Upgraded server file in correct location
- [ ] claude_desktop_config.json updated
- [ ] Claude Desktop restarted
- [ ] Authentication completed (if prompted)
- [ ] list_tasks works
- [ ] get_task_details works with test task ID
- [ ] No errors in MCP logs

## Rollback Procedure

If you need to revert to the previous version:

```bash
# Restore backup
copy server.py.backup server.py

# Or update config to point to backup
# Edit claude_desktop_config.json and change:
"args": ["C:\\path\\to\\server.py.backup"]
```

Restart Claude Desktop.

## New Tool Usage Examples

### Get Task Details
```python
# In Claude conversation:
"Get full details for task CfZuItAUdUKOl_LCgsb1i2UAK1rq"
```

### Update Task
```python
# Mark task 50% complete with new description
"Update task CfZuItAUdUKOl_LCgsb1i2UAK1rq to 50% complete and add description: Research completed for agent persona framework"
```

### Create Task with Details
```python
# Create fully specified task
"Create a task titled 'Deploy Orchestrator v1' in Digital Teammates bucket with description 'Build and test first Orchestrator prototype' due January 31, 2026"
```

## Support

If you encounter issues:

1. Check server logs: `~/.planner_mcp.log`
2. Verify Graph API permissions in Azure AD
3. Test authentication with: `python server_v2.py` (should show device code prompt)

## Next Steps

Once verified working:
1. Test get_task_details on your R&D task
2. Update 2-3 tasks to verify write operations
3. Create a new test task
4. If all works, remove backup and old version
