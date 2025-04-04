#!/bin/bash

echo "Setting up Enhanced Developer's Toolkit..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    echo "Please install Python 3.8 or newer and try again."
    exit 1
fi

# Check Python version
python3 --version | grep -q "Python 3.[89]" || python3 --version | grep -q "Python 3.1[0-9]"
if [ $? -ne 0 ]; then
    echo "Warning: Python version 3.8 or newer is recommended."
    echo "You may encounter issues with older versions."
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi

# Update pip
echo "Updating pip..."
python -m pip install --upgrade pip

# Install required packages
echo "Installing required packages..."
python -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Warning: Some packages failed to install."
    echo "Continuing with basic installation..."
    python -m pip install -r requirements.txt --no-deps
fi

# Create required directories
echo "Creating project directories..."
mkdir -p templates
mkdir -p logs
mkdir -p ui_build

# Make scripts executable
chmod +x update.sh run_with_proxy.sh

echo ""
echo "Setup completed successfully!"
echo "Run './run_with_proxy.sh' to start the Enhanced Developer's Toolkit"
echo "" 