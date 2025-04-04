#!/usr/bin/env python
"""
Run the MCP server from the command line.

This script is a convenience wrapper around the MCP server implementation.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root directory to the Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.chimera_core.config import get_settings
from src.chimera_stdio_mcp.server import main as mcp_server_main


if __name__ == "__main__":
    # Run the MCP server main function
    mcp_server_main()