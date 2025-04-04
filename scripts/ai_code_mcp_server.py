#!/usr/bin/env python
"""
AI Code Tools MCP Server.

This script starts an MCP server providing AI-powered code tools via stdio.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))

# Import chimera components
from src.chimera_stdio_mcp.tools.code_generation import CodeGenerationTool
from src.chimera_stdio_mcp.tools.code_analysis import CodeAnalysisTool
from src.chimera_stdio_mcp.tools.base import BaseTool
from src.chimera_stdio_mcp import mcp_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(project_root, "data", "ai_code_mcp.log")),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger("ai_code_mcp_server")

class AICodeMCPServer:
    """MCP server for AI code tools."""
    
    def __init__(self):
        """Initialize the server."""
        self.tools: Dict[str, BaseTool] = {}
        self.register_tools()
        logger.info("AI Code MCP Server initialized")
    
    def register_tools(self):
        """Register all available tools."""
        # Code Generation Tool
        code_gen_tool = CodeGenerationTool()
        self.tools[code_gen_tool.TOOL_NAME] = code_gen_tool
        
        # Code Analysis Tool
        code_analysis_tool = CodeAnalysisTool()
        self.tools[code_analysis_tool.TOOL_NAME] = code_analysis_tool
        
        logger.info(f"Registered {len(self.tools)} tools")
        
        # Initialize MCP client
        mcp_client.initialize(self)
    
    async def process_request(self, request_json: str) -> Optional[str]:
        """Process a JSON-RPC request and return a response."""
        try:
            request = json.loads(request_json)
            
            # Validate JSON-RPC request
            if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32600, "message": "Invalid Request"}
                })
            
            request_id = request.get("id")
            method = request.get("method", "")
            params = request.get("params", {})
            
            # Handle initialize method
            if method == "initialize":
                logger.info("Received initialize request")
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "capabilities": {
                            "tools": {
                                "tools": [tool.get_schema() for tool in self.tools.values()]
                            }
                        }
                    }
                })
            
            # Handle tool calls
            if method == "callTool":
                tool_name = params.get("name", "")
                tool_params = params.get("params", {})
                
                logger.info(f"Tool call: {tool_name}")
                
                if tool_name in self.tools:
                    tool = self.tools[tool_name]
                    result = await tool.execute(tool_params)
                    
                    return json.dumps({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    })
                else:
                    logger.warning(f"Unknown tool: {tool_name}")
                    return json.dumps({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                    })
            
            # Handle response from client that we need to process
            if method == "" and "result" in request:
                # Pass to the mcp_client to handle
                mcp_client.handle_response(request_json)
                return None
                
            # Handle unknown methods
            logger.warning(f"Unknown method: {method}")
            return json.dumps({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": "Method not found"}
            })
            
        except json.JSONDecodeError:
            logger.exception("Invalid JSON")
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            })
            
        except Exception as e:
            logger.exception(f"Error processing request: {e}")
            return json.dumps({
                "jsonrpc": "2.0",
                "id": request.get("id") if "request" in locals() else None,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            })
    
    async def run(self):
        """Run the server, reading from stdin and writing to stdout."""
        logger.info("AI Code MCP Server started")
        
        while True:
            try:
                # Read a line from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                
                if not line:
                    logger.info("End of input, shutting down")
                    break
                
                # Process the request
                response = await self.process_request(line.strip())
                
                # Write the response to stdout
                if response:
                    sys.stdout.write(response + "\n")
                    sys.stdout.flush()
                    
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")

async def main():
    """Main entry point."""
    server = AICodeMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main()) 