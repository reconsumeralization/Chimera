#!/usr/bin/env python
"""
MCP Fixer for Project Chimera

This script helps fix common MCP-related issues by creating a simple wrapper
that doesn't require the missing FastMCP import.
"""

import os
import sys
import shutil
from pathlib import Path

def print_colored(message, color="white"):
    """Print colored text if supported by the terminal."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    
    if os.name != "nt":  # Use colors on non-Windows systems
        print(f"{colors.get(color, colors['white'])}{message}{colors['reset']}")
    else:
        print(message)

def create_simplified_mcp_server():
    """Create a simplified MCP server that doesn't use FastMCP."""
    project_root = Path(__file__).resolve().parent
    mcp_dir = project_root / "src" / "chimera_stdio_mcp"
    
    # Ensure the directory exists
    if not mcp_dir.exists():
        mcp_dir.mkdir(parents=True, exist_ok=True)
        print_colored(f"Created directory: {mcp_dir}", "green")
    
    # Create __init__.py if it doesn't exist
    init_file = mcp_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, "w") as f:
            f.write('"""Chimera stdio MCP package."""\n')
        print_colored(f"Created: {init_file}", "green")
    
    # Create a simplified server.py
    server_file = mcp_dir / "server.py"
    with open(server_file, "w") as f:
        f.write('''"""
Simplified MCP Server for Project Chimera.

This is a basic implementation that doesn't require the full MCP functionality.
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("chimera_mcp")

class SimpleMCP:
    """A simple MCP implementation that reads from stdin and writes to stdout."""
    
    def __init__(self, service_type="code_analysis"):
        """Initialize the SimpleMCP server.
        
        Args:
            service_type: Type of service to provide ('code_analysis' or 'tools')
        """
        self.service_type = service_type
        self.handlers = {
            "code_analysis": {
                "roots/list": self.handle_roots_list,
                "file_search": self.handle_file_search,
                "code_explanation": self.handle_code_explanation,
            },
            "tools": {
                "roots/list": self.handle_roots_list,
                "file_system/list_directory": self.handle_list_directory,
                "tool_execution/run": self.handle_tool_execution,
            }
        }
        logger.info(f"SimpleMCP server initialized for service: {service_type}")
    
    def start(self):
        """Start the MCP server loop."""
        logger.info(f"Starting SimpleMCP server for {self.service_type}")
        print_startup_message(self.service_type)
        
        while True:
            try:
                # Read a line from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                # Parse the request
                request = json.loads(line)
                request_id = request.get("id", 0)
                method = request.get("method", "")
                params = request.get("params", {})
                
                # Log the request
                logger.info(f"Received request: {method}")
                
                # Handle the request
                if method in self.handlers.get(self.service_type, {}):
                    handler = self.handlers[self.service_type][method]
                    result = handler(params)
                    self.send_response(request_id, result)
                else:
                    error = {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                    self.send_error(request_id, error)
            
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error = {
                    "code": -32700,
                    "message": "Parse error"
                }
                self.send_error(0, error)
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                error = {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
                self.send_error(request_id if 'request_id' in locals() else 0, error)
    
    def send_response(self, request_id, result):
        """Send a successful response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        sys.stdout.write(json.dumps(response) + "\\n")
        sys.stdout.flush()
    
    def send_error(self, request_id, error):
        """Send an error response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error
        }
        sys.stdout.write(json.dumps(response) + "\\n")
        sys.stdout.flush()
    
    # Handler implementations
    def handle_roots_list(self, params):
        """Handle roots/list method."""
        # Return a basic response
        return {
            "roots": [
                {
                    "name": "workspace",
                    "path": str(Path.cwd())
                }
            ]
        }
    
    def handle_file_search(self, params):
        """Handle file_search method."""
        # Just return an empty result
        return {
            "files": []
        }
    
    def handle_code_explanation(self, params):
        """Handle code_explanation method."""
        return {
            "explanation": "Code explanation is not available in simplified mode."
        }
    
    def handle_list_directory(self, params):
        """Handle file_system/list_directory method."""
        path = params.get("path", ".")
        try:
            items = []
            for item in Path(path).iterdir():
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file"
                })
            return {"items": items}
        except Exception as e:
            logger.error(f"Error listing directory: {e}")
            return {"items": []}
    
    def handle_tool_execution(self, params):
        """Handle tool_execution/run method."""
        return {
            "output": "Tool execution is not available in simplified mode."
        }


def print_startup_message(service_type):
    """Print a startup message to the console."""
    print(f"SimpleMCP {service_type} server started", file=sys.stderr)
    print(f"This is a simplified implementation for Project Chimera", file=sys.stderr)
    print(f"Listening for JSON-RPC requests on stdin...", file=sys.stderr)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Simplified MCP Server")
    parser.add_argument("--service", choices=["code_analysis", "tools"], 
                      default="code_analysis", help="Service type to provide")
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    server = SimpleMCP(args.service)
    server.start()


if __name__ == "__main__":
    main()
''')
    print_colored(f"Created simplified MCP server: {server_file}", "green")

    # Create tools directory if it doesn't exist
    tools_dir = mcp_dir / "tools"
    if not tools_dir.exists():
        tools_dir.mkdir(parents=True, exist_ok=True)
        print_colored(f"Created directory: {tools_dir}", "green")
    
    # Create __init__.py in tools directory
    tools_init = tools_dir / "__init__.py"
    if not tools_init.exists():
        with open(tools_init, "w") as f:
            f.write('"""Chimera MCP tools."""\n')
        print_colored(f"Created: {tools_init}", "green")

def main():
    """Main entry point."""
    print_colored("Project Chimera MCP Fixer", "cyan")
    print_colored("==========================", "cyan")
    print()
    print_colored("This tool will create a simplified MCP implementation that doesn't require FastMCP.", "white")
    print()
    
    try:
        create_simplified_mcp_server()
        print()
        print_colored("✓ MCP fix applied successfully!", "green")
        print()
        print_colored("You can now use the simplified startup scripts:", "white")
        print_colored("  - Windows: easy_start.bat", "yellow")
        print_colored("  - Linux/Mac/WSL/Git Bash: ./easy_start.sh", "yellow")
        print()
        print_colored("These simplified scripts only start the core web server", "white")
        print_colored("without requiring the full MCP functionality.", "white")
        print()
    except Exception as e:
        print()
        print_colored(f"✗ Error: {str(e)}", "red")
        print()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 