#!/bin/bash
# Project Chimera Status Tool for Linux/Mac/WSL/Git Bash
# Shows running services and provides options to start/stop

# ANSI color codes for colored output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_header() {
    clear
    echo -e "${BLUE}"
    echo "================================================"
    echo "           PROJECT CHIMERA STATUS TOOL          "
    echo "================================================"
    echo -e "${NC}"
}

# Check if Python is available
check_python() {
    which python3 &> /dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Python not found. Please install Python 3.9+${NC}"
        exit 1
    fi
}

# Check running services
check_services() {
    echo "Checking running services..."
    echo

    WEB_RUNNING=0
    CODE_RUNNING=0
    TOOLS_RUNNING=0

    # Check for Web Server
    if netstat -tuln 2>/dev/null | grep -q ":8000 "; then
        echo -e "${GREEN}[RUNNING]${NC} Web Server (port 8000)"
        WEB_RUNNING=1
    else
        echo -e "${RED}[STOPPED]${NC} Web Server (port 8000)"
    fi

    # Look for Python processes that might be MCP servers
    if ps aux | grep -v grep | grep -q "chimera_stdio_mcp"; then
        echo -e "${GREEN}[RUNNING]${NC} MCP Server processes detected"
        CODE_RUNNING=1
    else
        echo -e "${RED}[STOPPED]${NC} MCP Server processes"
    fi

    echo
    echo "------------------------------------------------"
    echo
}

# Show available options
show_options() {
    if [ $WEB_RUNNING -eq 1 ]; then
        echo "1. STOP all services"
        echo "2. Restart all services"
    else
        echo "1. START services (simplified mode)"
        echo "2. START services (full mode)"
    fi

    echo "3. Run system check"
    echo "4. Exit"
    echo
}

# Process user choice
process_choice() {
    read -p "Enter your choice (1-4): " CHOICE

    case $CHOICE in
        1)
            if [ $WEB_RUNNING -eq 1 ]; then
                echo "Stopping all services..."
                kill $(ps aux | grep "[u]vicorn" | awk '{print $2}') 2>/dev/null
                kill $(ps aux | grep "[c]himera_stdio_mcp" | awk '{print $2}') 2>/dev/null
                echo "Services stopped."
            else
                echo "Starting services in simplified mode..."
                bash ./easy_start.sh &
                echo "Web server starting..."
            fi
            ;;
        2)
            if [ $WEB_RUNNING -eq 1 ]; then
                echo "Restarting all services..."
                kill $(ps aux | grep "[u]vicorn" | awk '{print $2}') 2>/dev/null
                kill $(ps aux | grep "[c]himera_stdio_mcp" | awk '{print $2}') 2>/dev/null
                sleep 2
                bash ./start_chimera.sh &
                echo "Services restarting..."
            else
                echo "Starting services in full mode..."
                bash ./start_chimera.sh &
                echo "All services starting..."
            fi
            ;;
        3)
            echo "Running system check..."
            python3 check_system.py
            read -p "Press Enter to continue..."
            ;;
        4)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Invalid choice.${NC}"
            ;;
    esac

    echo
    echo "Press Enter to return to the status screen..."
    read
}

# Main function
main() {
    while true; do
        show_header
        check_python
        check_services
        show_options
        process_choice
    done
}

# Run the main function
main 