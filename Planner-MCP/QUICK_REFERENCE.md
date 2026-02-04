# Planner MCP v2.0 - Quick Reference Card

## New Features Summary

### 1. get_task_details
**Purpose:** Retrieve complete information about a specific task

**What You Get:**
- Full description text
- Checklist items and their status
- Bucket name (not just ID)
- Assigned users
- All dates (created, start, due)
- Priority level
- References/attachments
- ETags for updates

**Usage:**
```
"Get full details for task ID: CfZuItAUdUKOl_LCgsb1i2UAK1rq"
"Show me everything about the R&D personas task"
"Retrieve details for task CfZuItAUdUKOl_LCgsb1i2UAK1rq"
```

**Output Format:**
```
Title: R&D: Conversational Agent Interfaces (Personas)
Bucket: Digital Teammates Org Chart (R&D)
Status: 25% complete
Description: [Full description text here]
Checklist: 4 items
Assigned To: aaron@charterandstone.com
```

---

### 2. update_task
**Purpose:** Modify existing task properties

**What You Can Update:**
- Title
- Completion percentage (0-100)
- Description
- Due date

**Usage:**
```
"Update task CfZuItAUdUKOl_LCgsb1i2UAK1rq to 75% complete"
"Change the description of task [ID] to: [new description]"
"Set due date for task [ID] to January 31, 2026"
"Mark task [ID] as 100% complete"
```

**Examples:**
```
Update task CfZuItAUdUKOl_LCgsb1i2UAK1rq:
- percent_complete: 50
- description: "Phase 1 research completed. Moving to prototype development."

Set task CfZuItAUdUKOl_LCgsb1i2UAK1rq due date to 2026-02-15T00:00:00Z
```

---

### 3. Enhanced create_task
**Purpose:** Create tasks with full metadata from the start

**New Parameters:**
- description (multi-line text)
- due_date (ISO 8601 format)
- assigned_to (email address)

**Usage:**
```
"Create a task titled 'Deploy Orchestrator' in Digital Teammates bucket with description 'Build automated workflow coordinator' due February 1, 2026"

"Add task 'Research competitor pricing' to Strategy & Intel bucket, assigned to aaron@charterandstone.com, due next Friday"
```

**Old vs New:**
```
OLD (v1.0):
  Create task → Manually add description in Planner UI → Manually set due date

NEW (v2.0):
  Create task with all details in one operation
```

---

## Typical Workflows

### Workflow 1: Deep Dive on a Task
```
1. List incomplete tasks
2. Get details for specific task ID
3. Review description and checklist
4. Update progress percentage
5. Add notes to description
```

### Workflow 2: Sprint Planning
```
1. Create new task with full specification
2. Assign to team member
3. Set due date for sprint end
4. Track progress with get_task_details
5. Update completion as work progresses
```

### Workflow 3: Task Audit
```
1. List all tasks
2. For each task: get_task_details
3. Check if description exists
4. Check if assigned
5. Check if due date set
6. Generate completeness report
```

---

## Integration with Your Workflow

### Digital Teammates Use Case
```python
# Orchestrator checks task status
task_details = get_task_details("CfZuItAUdUKOl_LCgsb1i2UAK1rq")

# Reads description to understand requirements
requirements = task_details['description']

# Updates progress as it works
update_task(
    task_id="CfZuItAUdUKOl_LCgsb1i2UAK1rq",
    percent_complete=75,
    description=f"{requirements}\n\nSTATUS: Agent completed research phase."
)
```

### Watchdog Integration
```python
# Watchdog finds new opportunity
create_task(
    title="[🔴 DISTRESS] New Target: University XYZ",
    bucket_name="Strategy & Intel",
    description=f"""
    Institution: University XYZ
    Signal: Budget crisis, 50 staff layoffs
    Source: Inside Higher Ed
    Financial Data: [IRS 990 summary]
    Recommended Action: Immediate outreach
    """,
    due_date="2026-02-01T00:00:00Z"
)
```

---

## Technical Notes

### Date Format
Always use ISO 8601: `YYYY-MM-DDTHH:MM:SSZ`
Example: `2026-01-31T17:00:00Z`

### Task IDs
IDs are long alphanumeric strings from Microsoft Graph:
`CfZuItAUdUKOl_LCgsb1i2UAK1rq`

### ETags
Automatically handled by the server. Used for:
- Preventing concurrent update conflicts
- Ensuring you're updating the latest version

### Authentication
- Token cached for ~90 days
- Automatic refresh when expired
- Device code flow for initial auth

---

## Comparison: v1.0 vs v2.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| List tasks | ✓ | ✓ |
| Get task details | ✗ | ✓ NEW |
| Create basic task | ✓ | ✓ |
| Create with description | ✗ | ✓ ENHANCED |
| Update task | ✗ | ✓ NEW |
| Assign on creation | ✗ | ✓ ENHANCED |
| Set due date on creation | ✗ | ✓ ENHANCED |
| Read descriptions | ✗ | ✓ NEW |
| Read checklists | ✗ | ✓ NEW |
| Get bucket names | ✗ | ✓ NEW |

---

## Troubleshooting Quick Fixes

**"Task not found"**
- Verify task ID is correct (check for typos)
- Task may be completed (only shows incomplete tasks)

**"Unauthorized"**
- Delete token cache: `~/.planner_mcp_token_cache.json`
- Restart Claude Desktop
- Re-authenticate when prompted

**"Update failed"**
- Task may have been updated by another user
- Server automatically retries with fresh ETag
- If persists, check Graph API permissions

---

## Performance Notes

**Latency:**
- list_tasks: ~500ms
- get_task_details: ~1000ms (2 API calls)
- create_task: ~800ms
- update_task: ~1200ms (requires fetching ETag first)

**Rate Limits:**
- Microsoft Graph throttles at ~2000 requests/minute
- Not an issue for normal use
- Relevant for bulk operations

---

## Next Steps After Upgrade

1. ✓ Test `get_task_details` on existing task
2. ✓ Test `update_task` on test task
3. ✓ Test `create_task` with description
4. [ ] Update Operations Manual with new capabilities
5. [ ] Update Digital Teammates to use new features
6. [ ] Build Orchestrator using enhanced task management

---

## Support & Documentation

- Full upgrade guide: `UPGRADE_GUIDE.md`
- Test suite: `test_upgrade.py`
- Server logs: `~/.planner_mcp.log`
- Graph API docs: https://docs.microsoft.com/en-us/graph/api/resources/planner-overview

**Version:** 2.0  
**Release Date:** January 29, 2026  
**Maintainer:** Charter & Stone Engineering
