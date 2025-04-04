#!/bin/bash

echo "Updating Enhanced Developer's Toolkit..."

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "Warning: Git is not installed or not in PATH."
    echo "Manual update required."
else
    # Check if this is a git repository
    if [ ! -d ".git" ]; then
        echo "Warning: This does not appear to be a git repository."
        echo "Manual update required."
    else
        # Pull latest changes
        echo "Pulling latest changes from repository..."
        git pull
        if [ $? -ne 0 ]; then
            echo "Warning: Failed to pull latest changes."
            echo "There may be local modifications or network issues."
        fi
    fi
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting up from scratch..."
    bash setup.sh
    exit 0
fi

echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

# Update pip itself
echo "Updating pip..."
python -m pip install --upgrade pip

# Update dependencies
echo "Updating dependencies..."
python -m pip install -r requirements.txt --upgrade

echo ""
echo "Update completed!"
echo "Run './run_with_proxy.sh' to start the Enhanced Developer's Toolkit"
echo ""

# Make scripts executable
chmod +x setup.sh run_with_proxy.sh 