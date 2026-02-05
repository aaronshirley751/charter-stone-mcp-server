@echo off
echo ================================================================================
echo Committing MCP Server V2.6.1 Critical Fixes
echo ================================================================================
echo.

cd /d "C:\Users\tasms\my-new-project\CharterStoneOperationsTools"

echo [1/5] Staging all changes...
git add -A

echo.
echo [2/5] Checking status...
git status

echo.
echo [3/5] Creating commit...
git commit -m "Fix: Critical MCP server initialization and authentication (V2.6.1)

CRITICAL FIX - Server now functional in Claude Desktop

Problem Fixed:
- MCP server initialization cascade failure (3 sequential errors)
- Blocking authentication causing 4-minute tool timeouts
- Token cache filename mismatch preventing auth validation

Root Cause:
1. Invalid InitializationOptions API call (missing capabilities param)
2. Blocking device code flow during tool execution (violated MCP protocol)
3. Token cache path mismatch (.bin vs .json)

Solution Implemented:
- Added check_token_validity() with pre-flight auth validation
- Removed blocking device code flow from get_access_token()
- Fixed InitializationOptions structure with ServerCapabilities
- Standardized token cache filename (.json)
- Enforced authenticate-before-startup architecture

Impact:
- Server startup: 1-2s with validation (was failing)
- Tool execution: <1s (was 240s timeout)
- User experience: FULLY RESTORED

Files Changed:
- Planner-MCP/server.py - Core authentication and initialization fix
- CharterStone/PlannerMCP/server.py - Synchronized changes
- README.md - Updated with V2.6.1 details and Claude Desktop setup
- Planner-MCP/TROUBLESHOOTING_SESSION_2026-02-05.md - Complete documentation

Testing: ✅ Server initializes, ✅ Toggle activates, ✅ Tools execute instantly

See: Planner-MCP/TROUBLESHOOTING_SESSION_2026-02-05.md for complete analysis"

echo.
echo [4/5] Viewing commit...
git log -1 --stat

echo.
echo [5/5] Pushing to remote...
git push origin main

echo.
echo ================================================================================
echo Commit Complete!
echo ================================================================================
pause
