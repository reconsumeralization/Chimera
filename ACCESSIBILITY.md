# Project Chimera Accessibility Guide

This guide provides information on how to use Project Chimera if you have a disability or mobility limitations. We've created simplified tools to make system management easier.

## Accessibility Tools

We've created several tools to make managing Project Chimera easier for users with disabilities:

### 1. Simplified Startup Scripts

- **Windows**: `easy_start.bat` - Runs just the core web server
- **Linux/Mac/WSL/Git Bash**: `easy_start.sh` - Runs just the core web server

These scripts:
- Use clear, high-contrast output
- Start only essential services
- Provide detailed feedback
- Run in foreground for easier monitoring

### 2. System Check Tool

Run `python check_system.py` to:
- Diagnose common issues
- Get clear feedback on what's working
- Fix problems automatically with `python check_system.py --fix`

### 3. Visual Status Dashboard

- **Windows**: `status.bat`
- **Linux/Mac/WSL/Git Bash**: `status.sh`

Features:
- Color-coded status information
- Simple menu-based interface
- Start/stop/restart functionality
- Easy system checks

### 4. MCP Fix Tool

If you encounter MCP import errors, run:
```
python fix_mcp.py
```

This will create a simplified MCP implementation that doesn't require external dependencies.

## Voice Control Tips

If you use voice control software:

1. The simplified scripts use common commands that are easier to speak
2. Use the status dashboard with numbered options (just say "one", "two", etc.)
3. All tools provide clear success/failure messages that can be read aloud

## Using Assistive Technologies

### Screen Readers

All tools use:
- Clear text output
- Structured information
- Semantic organization of content
- Avoiding reliance on visual-only feedback

### Limited Mobility

- Reduced number of command-line parameters needed
- Centralized control through status dashboard
- Automatic fixing of common issues
- Simplified debugging

## Getting Additional Help

If you need further assistance with accessibility:

1. Check the documentation directory for more guides
2. Contact the project maintainers for specific accommodations
3. Open an issue detailing your accessibility needs

## Keyboard Shortcuts

When using the web interface at http://localhost:8000:

- Tab: Navigate between elements
- Space/Enter: Activate buttons
- Escape: Cancel operations
- Alt+H: Show help

We're committed to making Project Chimera accessible to all users regardless of ability. 