#!/bin/bash
# Project Chimera startup script for Unix-like systems
echo "Starting Project Chimera..."

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."
RUN_SCRIPT="$PROJECT_ROOT/scripts/common/run_all.py"

# Check for Python environment
if [ ! -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo "Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Parse command line arguments
ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --enable-data-collection)
            ARGS="$ARGS --enable-data-collection"
            shift
            ;;
        --no-ui)
            ARGS="$ARGS --no-ui"
            shift
            ;;
        --no-browser)
            ARGS="$ARGS --no-browser"
            shift
            ;;
        --log-level)
            ARGS="$ARGS --log-level=$2"
            shift
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            shift
            ;;
    esac
done

# Run the Python script
echo "Running: python $RUN_SCRIPT $ARGS"
python "$RUN_SCRIPT" $ARGS

# Capture exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

# Exit with the same code as the Python script
exit $EXIT_CODE 