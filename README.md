# Charter & Stone Operations Tools

A comprehensive suite of automation tools and utilities for Charter & Stone operations, featuring a Model Context Protocol (MCP) server for Microsoft Planner integration with Claude Desktop.

## Overview

This project provides automated workflows and integrations for managing operations, scheduling, and task management through Microsoft Planner and other services. The MCP server enables seamless Planner task management directly from Claude Desktop.

## Components

### Planner MCP Server (V2.6.1)
The core component providing MCP server functionality for Microsoft Planner integration.

**Key Features:**
- ✅ **Claude Desktop Integration** - Native MCP protocol support
- ✅ **Microsoft Planner Full CRUD** - Create, read, update, delete tasks
- ✅ **Non-Blocking Authentication** - Pre-validated tokens, no runtime delays
- ✅ **SSH Oracle Search** - Search Charter & Stone knowledge base on Raspberry Pi
- ✅ **Bucket Management** - Organize tasks across multiple buckets
- ✅ **Checklist Operations** - Add and update task checklist items
- ✅ **Priority Management** - Urgent, Important, Medium, Low priority levels
- ✅ **Auto-Reconnect** - Resilient SSH and API connections

**Main Files:**
- `server.py` - MCP server implementation (V2.6.1 - Interactive Edition)
- `auth_setup_v2.py` - Microsoft authentication setup (non-blocking)
- `orchestrator.py` - Task orchestration engine
- `scheduler.py` - Scheduling management
- `watchdog.py` - Process monitoring and management
- `irs_scraper.py` - IRS data scraping utilities

## Setup

### Prerequisites
- Python 3.8 or higher
- Microsoft account with Planner access
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/aaronshirley751/charter-stone-operations-tools.git
cd charter-stone-operations-tools
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

3. Install dependencies:
```bash
cd Planner-MCP
pip install -r requirements.txt
```

4. Set up authentication:
```bash
python auth_setup_v2.py
```
Follow the device code flow instructions to authenticate with Microsoft Graph.

### Claude Desktop Setup

1. Add the MCP server to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "charterstone": {
      "command": "C:\\Users\\tasms\\my-new-project\\CharterStoneOperationsTools\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\tasms\\my-new-project\\CharterStoneOperationsTools\\Planner-MCP\\server.py"
      ]
    }
  }
}
```

2. Restart Claude Desktop

3. Verify the MCP toggle activates (should show "charterstone" server)

### Re-Authentication

If you receive an "AUTHENTICATION REQUIRED" error:
```bash
cd Planner-MCP
python auth_setup_v2.py
# Complete device code flow
# Restart Claude Desktop
```

Token cache location: `~/.planner_mcp_token_cache.json`

## Usage

### Available MCP Tools

When connected via Claude Desktop, the following tools are available:

**Oracle Knowledge Base:**
- `search_oracle` - Search Charter & Stone knowledge base on Raspberry Pi

**Planner Read Operations:**
- `list_buckets` - List all available Planner buckets
- `list_tasks` - List tasks (optionally filtered by bucket)
- `get_task_details` - Get full task details including description and checklist

**Planner Write Operations:**
- `create_task` - Create a new Planner task with title, bucket, priority, due date
- `update_task` - Update task title, priority, due date, or description
- `complete_task` - Mark a task as complete
- `move_task` - Move a task to a different bucket

**Checklist Operations:**
- `add_checklist_item` - Add a new checklist item to a task
- `update_checklist_item` - Check or uncheck a checklist item

### Running the MCP Server (Standalone)

For testing or development outside Claude Desktop:
```bash
cd Planner-MCP
python server.py
```

**Note:** The server is designed for Claude Desktop integration. Standalone mode is primarily for debugging.

### Configuration

Configuration files and authentication tokens are stored locally. Refer to the authentication setup script for details on connecting to Microsoft services.

## Documentation

- [Quick Reference](Planner-MCP/QUICK_REFERENCE.md) - Quick start guide and common operations
- [Upgrade Guide](Planner-MCP/UPGRADE_GUIDE.md) - Version upgrade instructions
- [Upgrade Complete](Planner-MCP/UPGRADE_COMPLETE.md) - Latest upgrade details
- [Troubleshooting Session (2026-02-05)](Planner-MCP/TROUBLESHOOTING_SESSION_2026-02-05.md) - Critical MCP initialization fix documentation

## Recent Updates

### V2.6.1 - February 5, 2026
**Critical Fix: MCP Server Initialization & Authentication**

**Problem:** Server initialization failure causing Claude Desktop toggle to not activate, with 4-minute tool execution timeouts.

**Root Cause:** Cascade of three initialization errors culminating in blocking authentication flows that violated MCP's non-blocking requirements.

**Solution Implemented:**
- ✅ Fixed `InitializationOptions` API structure with required `capabilities` parameter
- ✅ Implemented pre-flight token validation at startup
- ✅ Removed blocking device code flow from tool execution
- ✅ Added `check_token_validity()` with detailed debug logging
- ✅ Fixed token cache filename mismatch (.bin → .json)
- ✅ Enforced authentication-before-startup architecture

**Impact:**
- Server startup: 1-2 seconds (with validation)
- Tool execution: < 1 second (was 240+ seconds timeout)
- User experience: Fully restored with improved error messaging

**See:** [Complete troubleshooting documentation](Planner-MCP/TROUBLESHOOTING_SESSION_2026-02-05.md)

## Project Structure

```
.
├── Planner-MCP/           # Main MCP server and utilities
│   ├── server.py          # MCP server implementation
│   ├── orchestrator.py    # Task orchestration
│   ├── scheduler.py       # Scheduling engine
│   ├── watchdog.py        # Process monitoring
│   ├── auth_setup_v2.py   # Authentication setup
│   ├── irs_scraper.py     # IRS utilities
│   └── requirements.txt   # Python dependencies
├── .venv/                 # Virtual environment (not tracked)
└── README.md             # This file
```

## Development

### Running Tests

```bash
cd Planner-MCP
python test_upgrade.py
```

## Security Notes

- SSH keys and authentication tokens are excluded from version control
- Environment variables should be stored in `.env` files (not tracked)
- Watchdog history and logs are excluded from the repository

## License

Private repository - Charter & Stone internal use only.

## Support

For issues or questions, contact the development team.
