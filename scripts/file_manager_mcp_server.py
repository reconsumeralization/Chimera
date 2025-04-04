#!/usr/bin/env python
"""
MCP server for the File Manager Tool.
This server provides a JSON-RPC interface to file system operations.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Union

# Import the FileManagerTool from the chimera_stdio_mcp package
sys.path.append(".")  # Add the current directory to the path

try:
    from src.chimera_stdio_mcp.tools.file_manager import FileManagerTool
except ImportError:
    print("Error: Could not import FileManagerTool. Please ensure the project is correctly installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stderr)
    ]
)

logger = logging.getLogger("file_manager_mcp_server")

class FileManagerMCPServer:
    """MCP server for file manager operations."""
    
    def __init__(self):
        """Initialize the server and register tools."""
        self.file_manager_tool = FileManagerTool()
        self.initialized = False
        logger.info("File Manager MCP Server initialized")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a JSON-RPC request.
        
        Args:
            request_data: The JSON-RPC request data.
            
        Returns:
            The JSON-RPC response data.
        """
        request_id = request_data.get("id", None)
        method = request_data.get("method", "")
        params = request_data.get("params", {})
        
        logger.debug(f"Processing request: method={method}, id={request_id}")
        
        # Prepare the basic response structure
        response = {
            "jsonrpc": "2.0",
            "id": request_id
        }
        
        try:
            # Handle different methods
            if method == "initialize":
                # Initialize the server
                logger.info("Initializing server")
                self.initialized = True
                response["result"] = {
                    "capabilities": {
                        "toolCalls": True,
                        "fileManager": True
                    }
                }
            elif method == "callTool":
                # Check if the server is initialized
                if not self.initialized:
                    raise ValueError("Server not initialized")
                
                # Validate the params
                if "name" not in params:
                    raise ValueError("Missing required parameter: name")
                
                tool_name = params.get("name", "")
                tool_params = params.get("parameters", {})
                
                logger.info(f"Calling tool: {tool_name}")
                
                # Call the appropriate tool method
                if tool_name == "fileManager":
                    result = await self.file_manager_tool.execute(tool_params)
                    response["result"] = result
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
            else:
                # Unknown method
                raise ValueError(f"Unknown method: {method}")
        
        except Exception as e:
            # Handle errors
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            response["error"] = {
                "code": -32603,
                "message": str(e)
            }
        
        return response
    
    async def run(self):
        """
        Run the server, reading from stdin and writing to stdout.
        """
        logger.info("Starting File Manager MCP Server")
        
        # Create a stream reader for stdin
        stdin_reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(stdin_reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        # Use stdout for writing responses
        stdout_writer = sys.stdout
        
        while True:
            try:
                # Read a line from stdin
                line = await stdin_reader.readline()
                if not line:
                    logger.info("Received EOF, exiting")
                    break
                
                # Parse the request
                try:
                    request_data = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON: {str(e)}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    stdout_writer.write(json.dumps(response).encode("utf-8") + b"\n")
                    stdout_writer.flush()
                    continue
                
                # Process the request
                response = await self.process_request(request_data)
                
                # Write the response
                stdout_writer.write((json.dumps(response) + "\n").encode("utf-8"))
                stdout_writer.flush()
                
                logger.debug(f"Sent response for request id: {response.get('id')}")
                
            except Exception as e:
                logger.error(f"Unhandled error: {str(e)}", exc_info=True)
                # Try to send an error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "Internal server error"
                    }
                }
                stdout_writer.write((json.dumps(error_response) + "\n").encode("utf-8"))
                stdout_writer.flush()

async def main():
    """Run the MCP server."""
    server = FileManagerMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main()) 