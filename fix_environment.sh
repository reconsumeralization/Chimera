#!/bin/bash

echo "Running Enhanced Developer's Toolkit Environment Fix..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Run the environment fix script
python3 fix_environment.py

echo "Press Enter to exit..."
read 