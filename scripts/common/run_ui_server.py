#!/usr/bin/env python
"""
Run the UI server from the command line.

This script is a convenience wrapper around the UI server implementation.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root directory to the Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.chimera_ui.main import main as ui_server_main


if __name__ == "__main__":
    # Run the UI server main function
    ui_server_main() 