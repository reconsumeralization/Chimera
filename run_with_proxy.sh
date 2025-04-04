#!/bin/bash

echo "Starting Enhanced Developer's Toolkit..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    exit 1
fi

# Check for virtual environment, create if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi

# Install required packages
echo "Installing required packages..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --no-deps

# Try to install psutil, but don't fail if it doesn't work
echo "Attempting to install psutil (optional)..."
python -m pip install psutil 2>/dev/null || echo "psutil installation failed - will use fallback port checker"

# Check if templates directory exists, create if not
if [ ! -d "templates" ]; then
    echo "Creating templates directory..."
    mkdir -p templates
fi

# Check if psutil is installed
PSUTIL_INSTALLED=0
python -c "import psutil" 2>/dev/null && PSUTIL_INSTALLED=1

# Determine available ports
if [ $PSUTIL_INSTALLED -eq 1 ]; then
    echo "Using psutil to find available ports..."
    PORTS=$(python -c "import psutil, socket; s1=socket.socket(); s1.bind(('', 0)); p1=s1.getsockname()[1]; s2=socket.socket(); s2.bind(('', 0)); p2=s2.getsockname()[1]; s1.close(); s2.close(); print(f'{p1},{p2}')")
    IFS=',' read -r UI_PORT PROXY_PORT <<< "$PORTS"
else
    echo "Using simple port checker fallback..."
    if [ -f "simple_port_checker.py" ]; then
        PORTS=$(python simple_port_checker.py)
        IFS=',' read -r UI_PORT PROXY_PORT <<< "$PORTS"
    else
        echo "Fallback port checker not found. Using default ports..."
        UI_PORT=3000
        PROXY_PORT=9999
    fi
fi

echo "UI will use port: $UI_PORT"
echo "MCP proxy will use port: $PROXY_PORT"

# Create necessary directories
mkdir -p logs
mkdir -p ui_build

# Start the UI server and MCP proxy
echo "Starting the UI server..."
python ui_server.py --ui-port $UI_PORT &
UI_PID=$!

echo "Starting the MCP proxy..."
python mcp_server.py --mcp-port $PROXY_PORT &
MCP_PID=$!

# Display connection information
sleep 2
echo ""
echo "=================================================="
echo "Enhanced Developer's Toolkit is now running!"
echo "--------------------------------------------------"
echo "Connect to the UI at: http://localhost:$UI_PORT"
echo "CLI command: mcp connect localhost:$PROXY_PORT"
echo "--------------------------------------------------"
echo "Press Ctrl+C to stop the servers"
echo "=================================================="

# Wait for Ctrl+C
trap "kill $UI_PID $MCP_PID; exit" INT TERM
wait 