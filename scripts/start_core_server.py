#!/usr/bin/env python
"""Script to start the Chimera Core server."""
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chimera_core.main import main

if __name__ == "__main__":
    main() 