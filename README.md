# Charter & Stone Operations Tools

A comprehensive suite of automation tools and utilities for Charter & Stone operations, featuring a Model Context Protocol (MCP) server for Microsoft Planner integration.

## Overview

This project provides automated workflows and integrations for managing operations, scheduling, and task management through Microsoft Planner and other services.

## Components

### Planner MCP Server
The core component providing MCP server functionality for Microsoft Planner integration.

**Key Features:**
- Microsoft Planner API integration via MCP protocol
- Authentication management for Microsoft services
- Task and plan orchestration
- Automated scheduling capabilities
- Watchdog monitoring for task execution
- IRS scraper utilities

**Main Files:**
- `server.py` - MCP server implementation
- `orchestrator.py` - Task orchestration engine
- `scheduler.py` - Scheduling management
- `watchdog.py` - Process monitoring and management
- `auth_setup_v2.py` - Microsoft authentication setup
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

## Usage

### Running the MCP Server

```bash
cd Planner-MCP
python server.py
```

### Configuration

Configuration files and authentication tokens are stored locally. Refer to the authentication setup script for details on connecting to Microsoft services.

## Documentation

- [Quick Reference](Planner-MCP/QUICK_REFERENCE.md) - Quick start guide and common operations
- [Upgrade Guide](Planner-MCP/UPGRADE_GUIDE.md) - Version upgrade instructions
- [Upgrade Complete](Planner-MCP/UPGRADE_COMPLETE.md) - Latest upgrade details

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
