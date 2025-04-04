# Project Chimera Scripts

This directory contains utility scripts for setting up, running, updating, and managing the Project Chimera environment.

## Directory Structure

- `windows/`: Scripts specifically for Windows environments (.bat files)
- `unix/`: Scripts for Unix-like environments (.sh files)
- `common/`: Shared Python scripts that work across platforms

## Script Categories

### Setup Scripts
- `setup.bat`/`setup.sh`: Set up the Python virtual environment and install dependencies
- `fix_environment.py`: Diagnose and fix common environment issues

### Run Scripts
- `run_with_proxy.bat`/`run_with_proxy.sh`: Run the Chimera environment with MCP proxy
- `start_agent.bat`/`start_agent.sh`: Run the MCP agent standalone

### Update Scripts
- `update.bat`/`update.sh`: Update the Chimera environment with latest changes

### Utility Scripts
- `port_checker.py`/`simple_port_checker.py`: Check and manage port availability
- `make_executable.py`: Make scripts executable on Unix systems

## Usage Guidelines

1. Always use the scripts from the root directory of the project
2. Use the corresponding platform-specific script for your OS
3. If encountering issues, run the fix_environment script first
4. Make sure your virtual environment is activated before running Python scripts directly

## Adding New Scripts

When adding new scripts:

1. Place platform-specific scripts in the appropriate subdirectory
2. Place cross-platform Python scripts in the common directory
3. Update this README with information about the new script
4. Ensure the script follows the naming and style conventions
5. Add proper error handling and user feedback
6. Test on the target platforms 