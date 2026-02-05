"""
Charter & Stone MCP Server V2.6.1 - "Interactive Edition"

Architecture V3 Compliant:
- Full Planner CRUD for interactive sessions
- SSH health checks with auto-reconnect
- Bucket-aware operations
- Checklist management (fixed Graph API validation)
- process_signals REMOVED (now handled by Power Automate)

Features:
1. Oracle Search (SSH to Pi)
2. Planner Read: list_tasks, get_task_details
3. Planner Write: create_task, update_task, complete_task, move_task
4. Checklist: update_checklist_item, add_checklist_item
"""

import os
import json
import sys
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# Check for required libraries
try:
    import paramiko
    import requests
    import msal
    from msal import SerializableTokenCache
    from dotenv import load_dotenv
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError as e:
    print(f"CRITICAL: Missing library: {e}", file=sys.stderr)
    print("Run: pip install paramiko msal requests python-dotenv mcp", file=sys.stderr)
    sys.exit(1)

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# ============================================================================
# DIAGNOSTIC LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'C:\Users\tasms\CharterStone\PlannerMCP\server_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Microsoft Graph
TENANT_ID = os.getenv("AZURE_TENANT_ID") or os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID") or os.getenv("CLIENT_ID")
TOKEN_CACHE_PATH = Path.home() / ".planner_mcp_token_cache.bin"

# Planner IDs (set these to avoid repeated lookups)
PLAN_ID = os.getenv("PLANNER_PLAN_ID")  # Optional: hardcode for speed
PLAN_NAME = os.getenv("PLANNER_PLAN_NAME", "Launch Operations")

# SSH Configuration
SSH_HOST = os.getenv("SSH_HOST", "raspberrypi.local")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")

# Oracle Configuration
ORACLE_KB_PATH = os.getenv("ORACLE_KB_PATH", "/home/aaronshirley751/charter-and-stone-automation/knowledge_base")

# ============================================================================
# SSH CLIENT WITH HEALTH CHECK
# ============================================================================

class OracleSSHClient:
    """SSH client with connection health checking and auto-reconnect."""
    
    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.last_check: Optional[datetime] = None
        self.check_interval = timedelta(seconds=30)  # Health check every 30s max
    
    def _is_connected(self) -> bool:
        """Check if SSH connection is alive."""
        if self.client is None:
            return False
        
        # Skip health check if we checked recently
        if self.last_check and datetime.now() - self.last_check < self.check_interval:
            return True
        
        try:
            transport = self.client.get_transport()
            if transport is None or not transport.is_active():
                return False
            # Lightweight health check
            transport.send_ignore()
            self.last_check = datetime.now()
            return True
        except Exception:
            return False
    
    def connect(self) -> None:
        """Connect or reconnect to Pi."""
        if self._is_connected():
            return
        
        # Clean up dead connection
        self.close()
        
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if SSH_KEY_PATH and os.path.exists(SSH_KEY_PATH):
                self.client.connect(
                    SSH_HOST, SSH_PORT, SSH_USER,
                    key_filename=SSH_KEY_PATH,
                    timeout=10,
                    banner_timeout=10
                )
            elif SSH_PASSWORD:
                self.client.connect(
                    SSH_HOST, SSH_PORT, SSH_USER,
                    password=SSH_PASSWORD,
                    timeout=10,
                    banner_timeout=10
                )
            else:
                raise ValueError("No SSH auth configured in .env (need SSH_KEY_PATH or SSH_PASSWORD)")
            
            self.last_check = datetime.now()
            print(f"✅ SSH connected to {SSH_HOST}", file=sys.stderr)
            
        except Exception as e:
            self.client = None
            raise ConnectionError(f"SSH connection failed: {e}")
    
    def close(self) -> None:
        """Clean up SSH connection."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self.last_check = None
    
    def execute(self, command: str, timeout: int = 30) -> tuple[str, str, int]:
        """Execute command with auto-reconnect on failure."""
        # First attempt
        try:
            self.connect()
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            return (stdout.read().decode('utf-8'), stderr.read().decode('utf-8'), exit_code)
        except Exception as first_error:
            # Connection might be stale - try once more with fresh connection
            print(f"⚠️ SSH command failed, reconnecting: {first_error}", file=sys.stderr)
            self.close()
            try:
                self.connect()
                stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
                exit_code = stdout.channel.recv_exit_status()
                return (stdout.read().decode('utf-8'), stderr.read().decode('utf-8'), exit_code)
            except Exception as second_error:
                raise ConnectionError(f"SSH failed after reconnect: {second_error}")

# Global SSH client
oracle_ssh = OracleSSHClient()

# ============================================================================
# MICROSOFT GRAPH AUTHENTICATION
# ============================================================================

def get_access_token() -> str:
    """Get Graph API token with persistent MSAL token cache."""
    
    # Initialize token cache
    token_cache = SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        token_cache.deserialize(TOKEN_CACHE_PATH.read_text())
    
    # Create MSAL app with token cache
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        token_cache=token_cache
    )
    
    # Try to get token from cache (silent, no user interaction)
    scopes = ["Tasks.ReadWrite", "Group.Read.All", "User.Read"]
    accounts = app.get_accounts()
    
    if accounts:
        logger.debug(f"Found {len(accounts)} cached account(s)")
        result = app.acquire_token_silent(scopes=scopes, account=accounts[0])
        if result and "access_token" in result:
            logger.info("[OK] Using cached token")
            TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            TOKEN_CACHE_PATH.write_text(token_cache.serialize())
            return result['access_token']
    
    # No valid cached token - need interactive authentication
    logger.info("[AUTH] No valid cached token - initiating device code flow")
    
    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        raise ValueError("Failed to create device flow")
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"AUTHENTICATION REQUIRED", file=sys.stderr)
    print(f"   Visit:  {flow['verification_uri']}", file=sys.stderr)
    print(f"   Code:   {flow['user_code']}", file=sys.stderr)
    print(f"   Timeout: 300 seconds", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    # Poll for token with explicit timeout
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        logger.info("[OK] Device flow authentication successful")
        TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE_PATH.write_text(token_cache.serialize())
        return result['access_token']
    else:
        error_msg = result.get('error_description', 'Unknown error')
        logger.error(f"[ERROR] Auth failed: {error_msg}")
        raise Exception(f"Auth failed: {error_msg}")


def timed_graph_call(func_name: str, method: str, url: str, **kwargs) -> requests.Response:
    """
    Wrapper to log timing and success/failure of Graph API calls

    Args:
        func_name: Name of calling function (for log correlation)
        method: HTTP method ("GET", "POST", "PATCH", "DELETE")
        url: Full Graph API URL
        **kwargs: Headers, JSON body, etc. (passed to requests)

    Returns:
        requests.Response object

    Raises:
        Re-raises any exception after logging details
    """

    start_time = time.time()

    logger.info("[GRAPH_API_START] %s - %s %s", func_name, method, url)

    try:
        response = requests.request(method, url, **kwargs)

        elapsed = time.time() - start_time

        logger.info(
            "[GRAPH_API_SUCCESS] %s - %.2fs - Status: %s",
            func_name,
            elapsed,
            response.status_code
        )

        return response

    except Exception as e:
        elapsed = time.time() - start_time

        logger.error(
            "[GRAPH_API_FAILURE] %s - %.2fs - Error: %s",
            func_name,
            elapsed,
            str(e)
        )
        logger.error("[GRAPH_API_FAILURE] Exception Type: %s", type(e).__name__)
        logger.exception("[GRAPH_API_FAILURE] Stack Trace:")

        raise


def graph_request(method: str, endpoint: str, data: dict = None, headers_extra: dict = None) -> dict:
    """Make Graph API request."""
    try:
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        if headers_extra:
            headers.update(headers_extra)

        url = f"https://graph.microsoft.com/v1.0{endpoint}"

        if method == "GET":
            response = timed_graph_call("graph_request", "GET", url, headers=headers)
        elif method == "POST":
            response = timed_graph_call("graph_request", "POST", url, headers=headers, json=data)
        elif method == "PATCH":
            response = timed_graph_call("graph_request", "PATCH", url, headers=headers, json=data)
        elif method == "DELETE":
            response = timed_graph_call("graph_request", "DELETE", url, headers=headers)
        else:
            raise ValueError(f"Unknown method: {method}")

        if response.status_code == 204:
            return {}

        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"❌ Graph API Error: {str(e)}")
        raise


# ============================================================================
# PLANNER HELPERS
# ============================================================================

_plan_cache = {}
_bucket_cache = {}

def get_plan_id() -> str:
    """Get the Plan ID, using cache or env var."""
    if PLAN_ID:
        return PLAN_ID
    
    if 'plan_id' in _plan_cache:
        return _plan_cache['plan_id']
    
    plans = graph_request("GET", "/me/planner/plans")
    for plan in plans.get('value', []):
        if plan['title'] == PLAN_NAME:
            _plan_cache['plan_id'] = plan['id']
            return plan['id']
    
    # Fallback to first plan
    if plans.get('value'):
        _plan_cache['plan_id'] = plans['value'][0]['id']
        return _plan_cache['plan_id']
    
    raise ValueError("No Planner plans found")


def get_buckets() -> dict[str, str]:
    """Get bucket name -> ID mapping."""
    if _bucket_cache:
        return _bucket_cache
    
    plan_id = get_plan_id()
    buckets = graph_request("GET", f"/planner/plans/{plan_id}/buckets")
    
    for bucket in buckets.get('value', []):
        _bucket_cache[bucket['name']] = bucket['id']
    
    return _bucket_cache


def get_bucket_id(bucket_name: str) -> str:
    """Get bucket ID by exact name."""
    buckets = get_buckets()
    
    # Exact match
    if bucket_name in buckets:
        return buckets[bucket_name]
    
    # Case-insensitive match
    for name, bid in buckets.items():
        if name.lower() == bucket_name.lower():
            return bid
    
    # Partial match (fallback)
    for name, bid in buckets.items():
        if bucket_name.lower() in name.lower():
            return bid
    
    raise ValueError(f"Bucket not found: {bucket_name}. Available: {list(buckets.keys())}")


def priority_to_int(priority: str) -> int:
    """Convert priority string to Planner integer."""
    mapping = {
        "urgent": 1,
        "important": 3,
        "medium": 5,
        "low": 9
    }
    return mapping.get(priority.lower(), 5)


def int_to_priority(value: int) -> str:
    """Convert Planner integer to priority string."""
    if value <= 1:
        return "Urgent"
    elif value <= 3:
        return "Important"
    elif value <= 5:
        return "Medium"
    else:
        return "Low"


# ============================================================================
# MCP SERVER
# ============================================================================

app = Server("charter-stone-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # === ORACLE ===
        Tool(
            name="search_oracle",
            description="Search the Charter & Stone knowledge base on Raspberry Pi.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search terms"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["signals", "docs", "prospects", "intelligence", "all"],
                        "default": "all",
                        "description": "Category to search within"
                    }
                },
                "required": ["query"]
            }
        ),
        
        # === PLANNER READ ===
        Tool(
            name="list_tasks",
            description="List Planner tasks, optionally filtered by bucket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "bucket_name": {
                        "type": "string",
                        "description": "Filter to specific bucket (e.g., 'Strategy & Intel')"
                    },
                    "include_completed": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include completed tasks"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_task_details",
            description="Get full details of a specific Planner task including description and checklist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The Planner task ID"
                    }
                },
                "required": ["task_id"]
            }
        ),
        
        # === PLANNER WRITE ===
        Tool(
            name="create_task",
            description="Create a new Planner task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title"
                    },
                    "bucket_name": {
                        "type": "string",
                        "description": "Target bucket name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Task notes/description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["urgent", "important", "medium", "low"],
                        "default": "medium"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date (ISO format: YYYY-MM-DD)"
                    }
                },
                "required": ["title", "bucket_name"]
            }
        ),
        Tool(
            name="update_task",
            description="Update an existing Planner task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["urgent", "important", "medium", "low"]
                    },
                    "due_date": {
                        "type": "string",
                        "description": "New due date (ISO format)"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description/notes"
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="complete_task",
            description="Mark a Planner task as complete.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string"
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="move_task",
            description="Move a task to a different bucket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string"
                    },
                    "bucket_name": {
                        "type": "string",
                        "description": "Target bucket name"
                    }
                },
                "required": ["task_id", "bucket_name"]
            }
        ),
        
        # === UTILITY ===
        Tool(
            name="list_buckets",
            description="List all available Planner buckets.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update_checklist_item",
            description="Check or uncheck a checklist item on a Planner task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The Planner task ID"
                    },
                    "item_title": {
                        "type": "string",
                        "description": "The checklist item title (partial match supported)"
                    },
                    "is_checked": {
                        "type": "boolean",
                        "description": "True to check, False to uncheck"
                    }
                },
                "required": ["task_id", "item_title", "is_checked"]
            }
        ),
        Tool(
            name="add_checklist_item",
            description="Add a new checklist item to a Planner task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The Planner task ID"
                    },
                    "item_title": {
                        "type": "string",
                        "description": "The checklist item text"
                    }
                },
                "required": ["task_id", "item_title"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        # =====================================================================
        # ORACLE SEARCH
        # =====================================================================
        if name == "search_oracle":
            query = arguments.get("query", "")
            category = arguments.get("category", "all")
            
            if category == "all":
                path = ORACLE_KB_PATH
            else:
                path = f"{ORACLE_KB_PATH}/{category}"
            
            # Escape single quotes in query
            safe_query = query.replace("'", "'\\''")
            cmd = f"grep -r -i -n -C 2 --color=never '{safe_query}' {path} 2>/dev/null || true"
            
            stdout, stderr, exit_code = oracle_ssh.execute(cmd)
            
            if not stdout.strip():
                return [TextContent(type="text", text=f"No results found for '{query}' in {category}.")]
            
            # Truncate if too long
            result = stdout[:4000]
            if len(stdout) > 4000:
                result += f"\n\n[... truncated, {len(stdout)} total chars]"
            
            return [TextContent(type="text", text=f"🔍 Oracle Results for '{query}':\n\n{result}")]
        
        # =====================================================================
        # LIST BUCKETS
        # =====================================================================
        elif name == "list_buckets":
            buckets = get_buckets()
            lines = ["📁 Available Buckets:", ""]
            for name, bid in buckets.items():
                lines.append(f"  • {name}")
            return [TextContent(type="text", text="\n".join(lines))]
        
        # =====================================================================
        # LIST TASKS
        # =====================================================================
        elif name == "list_tasks":
            bucket_name = arguments.get("bucket_name")
            include_completed = arguments.get("include_completed", False)
            
            plan_id = get_plan_id()
            tasks = graph_request("GET", f"/planner/plans/{plan_id}/tasks")
            
            # Filter by bucket if specified
            if bucket_name:
                bucket_id = get_bucket_id(bucket_name)
                tasks_list = [t for t in tasks.get('value', []) if t.get('bucketId') == bucket_id]
            else:
                tasks_list = tasks.get('value', [])
            
            # Filter completed
            if not include_completed:
                tasks_list = [t for t in tasks_list if t.get('percentComplete', 0) < 100]
            
            if not tasks_list:
                bucket_msg = f" in '{bucket_name}'" if bucket_name else ""
                return [TextContent(type="text", text=f"No tasks found{bucket_msg}.")]
            
            # Format output
            lines = []
            if bucket_name:
                lines.append(f"📋 Tasks in '{bucket_name}' ({len(tasks_list)} items):\n")
            else:
                lines.append(f"📋 All Tasks ({len(tasks_list)} items):\n")
            
            for task in tasks_list:
                priority = int_to_priority(task.get('priority', 5))
                status = "✅" if task.get('percentComplete', 0) >= 100 else "⬜"
                due = task.get('dueDateTime', '')[:10] if task.get('dueDateTime') else 'No due date'
                lines.append(f"{status} [{priority}] {task['title']}")
                lines.append(f"   ID: {task['id']} | Due: {due}")
                lines.append("")
            
            return [TextContent(type="text", text="\n".join(lines))]
        
        # =====================================================================
        # GET TASK DETAILS
        # =====================================================================
        elif name == "get_task_details":
            task_id = arguments.get("task_id")
            
            task = graph_request("GET", f"/planner/tasks/{task_id}")
            details = graph_request("GET", f"/planner/tasks/{task_id}/details")
            
            # Get bucket name
            buckets = get_buckets()
            bucket_name = next((n for n, bid in buckets.items() if bid == task.get('bucketId')), 'Unknown')
            
            lines = [
                f"📋 Task Details",
                f"{'='*50}",
                f"Title: {task.get('title')}",
                f"ID: {task_id}",
                f"Bucket: {bucket_name}",
                f"Priority: {int_to_priority(task.get('priority', 5))}",
                f"Progress: {task.get('percentComplete', 0)}%",
                f"Due: {task.get('dueDateTime', 'Not set')[:10] if task.get('dueDateTime') else 'Not set'}",
                f"",
                f"Description:",
                f"{details.get('description', '(No description)')[:2000]}",
            ]
            
            # Checklist
            checklist = details.get('checklist', {})
            if checklist:
                lines.append("")
                lines.append("Checklist:")
                for item_id, item in checklist.items():
                    check = "✅" if item.get('isChecked') else "⬜"
                    lines.append(f"  {check} {item.get('title')}")
            
            return [TextContent(type="text", text="\n".join(lines))]
        
        # =====================================================================
        # CREATE TASK
        # =====================================================================
        elif name == "create_task":
            title = arguments.get("title")
            bucket_name = arguments.get("bucket_name")
            description = arguments.get("description")
            priority = arguments.get("priority", "medium")
            due_date = arguments.get("due_date")
            
            plan_id = get_plan_id()
            bucket_id = get_bucket_id(bucket_name)
            
            # Create task
            task_data = {
                "planId": plan_id,
                "bucketId": bucket_id,
                "title": title,
                "priority": priority_to_int(priority)
            }
            
            if due_date:
                task_data["dueDateTime"] = f"{due_date}T00:00:00Z"
            
            new_task = graph_request("POST", "/planner/tasks", task_data)
            task_id = new_task['id']
            
            # Add description if provided
            if description:
                # Need to get etag first
                details = graph_request("GET", f"/planner/tasks/{task_id}/details")
                etag = details.get('@odata.etag')
                
                graph_request(
                    "PATCH",
                    f"/planner/tasks/{task_id}/details",
                    {"description": description},
                    {"If-Match": etag}
                )
            
            return [TextContent(type="text", text=f"✅ Task created:\n   Title: {title}\n   Bucket: {bucket_name}\n   Priority: {priority}\n   ID: {task_id}")]
        
        # =====================================================================
        # UPDATE TASK
        # =====================================================================
        elif name == "update_task":
            task_id = arguments.get("task_id")
            
            # Get current task for etag
            task = graph_request("GET", f"/planner/tasks/{task_id}")
            etag = task.get('@odata.etag')
            
            # Build update payload
            payload = {}
            if "title" in arguments:
                payload["title"] = arguments["title"]
            if "priority" in arguments:
                payload["priority"] = priority_to_int(arguments["priority"])
            if "due_date" in arguments:
                payload["dueDateTime"] = f"{arguments['due_date']}T00:00:00Z"
            
            if payload:
                graph_request("PATCH", f"/planner/tasks/{task_id}", payload, {"If-Match": etag})
            
            # Update description separately (different endpoint)
            if "description" in arguments:
                details = graph_request("GET", f"/planner/tasks/{task_id}/details")
                details_etag = details.get('@odata.etag')
                graph_request(
                    "PATCH",
                    f"/planner/tasks/{task_id}/details",
                    {"description": arguments["description"]},
                    {"If-Match": details_etag}
                )
            
            return [TextContent(type="text", text=f"✅ Task {task_id} updated.")]
        
        # =====================================================================
        # COMPLETE TASK
        # =====================================================================
        elif name == "complete_task":
            task_id = arguments.get("task_id")
            
            task = graph_request("GET", f"/planner/tasks/{task_id}")
            etag = task.get('@odata.etag')
            
            graph_request(
                "PATCH",
                f"/planner/tasks/{task_id}",
                {"percentComplete": 100},
                {"If-Match": etag}
            )
            
            return [TextContent(type="text", text=f"✅ Task marked complete: {task.get('title')}")]
        
        # =====================================================================
        # MOVE TASK
        # =====================================================================
        elif name == "move_task":
            task_id = arguments.get("task_id")
            bucket_name = arguments.get("bucket_name")
            
            bucket_id = get_bucket_id(bucket_name)
            
            task = graph_request("GET", f"/planner/tasks/{task_id}")
            etag = task.get('@odata.etag')
            
            graph_request(
                "PATCH",
                f"/planner/tasks/{task_id}",
                {"bucketId": bucket_id},
                {"If-Match": etag}
            )
            
            return [TextContent(type="text", text=f"✅ Task moved to '{bucket_name}': {task.get('title')}")]

        # =====================================================================
        # UPDATE CHECKLIST ITEM
        # =====================================================================
        elif name == "update_checklist_item":
            task_id = arguments.get("task_id")
            item_title = arguments.get("item_title")
            is_checked = arguments.get("is_checked")

            # Get current task details
            details = graph_request("GET", f"/planner/tasks/{task_id}/details")
            etag = details.get('@odata.etag')
            checklist = details.get('checklist', {})

            # Find the item (partial match)
            found_id = None
            found_title = None
            for item_id, item in checklist.items():
                if item_title.lower() in item.get('title', '').lower():
                    found_id = item_id
                    found_title = item.get('title')
                    break

            if not found_id:
                available = [item.get('title') for item in checklist.values()]
                return [TextContent(type="text", text=f"❌ Checklist item not found: '{item_title}'\n\nAvailable items:\n" + "\n".join(f"  • {t}" for t in available))]

            # Build clean checklist with only writable fields
            clean_checklist = {}
            for item_id, item in checklist.items():
                clean_checklist[item_id] = {
                    "@odata.type": "#microsoft.graph.plannerChecklistItem",
                    "title": item.get('title'),
                    "isChecked": item.get('isChecked', False)
                }

            # Update the target item
            clean_checklist[found_id]['isChecked'] = is_checked

            graph_request(
                "PATCH",
                f"/planner/tasks/{task_id}/details",
                {"checklist": clean_checklist},
                {"If-Match": etag}
            )

            status = "checked ✅" if is_checked else "unchecked ⬜"
            return [TextContent(type="text", text=f"✅ Checklist item {status}: {found_title}")]

        # =====================================================================
        # ADD CHECKLIST ITEM
        # =====================================================================
        elif name == "add_checklist_item":
            task_id = arguments.get("task_id")
            item_title = arguments.get("item_title")

            # Get current task details
            details = graph_request("GET", f"/planner/tasks/{task_id}/details")
            etag = details.get('@odata.etag')
            checklist = details.get('checklist', {})

            # Build clean checklist with only writable fields
            clean_checklist = {}
            for item_id, item in checklist.items():
                clean_checklist[item_id] = {
                    "@odata.type": "#microsoft.graph.plannerChecklistItem",
                    "title": item.get('title'),
                    "isChecked": item.get('isChecked', False)
                }

            # Generate a unique ID and add new item
            new_id = str(uuid.uuid4())[:8]
            clean_checklist[new_id] = {
                "@odata.type": "#microsoft.graph.plannerChecklistItem",
                "title": item_title,
                "isChecked": False
            }

            graph_request(
                "PATCH",
                f"/planner/tasks/{task_id}/details",
                {"checklist": clean_checklist},
                {"If-Match": etag}
            )

            return [TextContent(type="text", text=f"✅ Checklist item added: {item_title}")]
        
        # =====================================================================
        # UNKNOWN TOOL
        # =====================================================================
        else:
            return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
    
    except requests.exceptions.HTTPError as e:
        return [TextContent(type="text", text=f"❌ Graph API Error: {e.response.status_code} - {e.response.text[:500]}")]
    except ConnectionError as e:
        return [TextContent(type="text", text=f"❌ SSH Connection Error: {e}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {type(e).__name__}: {str(e)}")]


# ============================================================================
# MAIN
# ============================================================================

async def main():
    print("=" * 60, file=sys.stderr)
    print("Charter & Stone MCP Server V2.6.1 - Interactive Edition", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Pre-flight checks (no blocking auth)
    print("[INFO] Microsoft Graph: Auth will happen on first API call", file=sys.stderr)
    
    try:
        oracle_ssh.connect()
        print(f"[OK] SSH to Pi: Connected ({SSH_HOST})", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] SSH to Pi: Not connected - {e}", file=sys.stderr)
    
    print("", file=sys.stderr)
    print("Available tools: search_oracle, list_tasks, get_task_details,", file=sys.stderr)
    print("                 create_task, update_task, complete_task,", file=sys.stderr)
    print("                 move_task, list_buckets, update_checklist_item,", file=sys.stderr)
    print("                 add_checklist_item", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
