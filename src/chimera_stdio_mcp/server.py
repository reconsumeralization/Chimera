"""MCP server for Project Chimera."""
import argparse
import asyncio
import json
import logging
import os
import signal
import structlog
import sys
import time
from typing import Any, Dict, List, Optional

from mcp import FastMCP

from .registry import registry
from chimera_core.utils.logging_config import setup_logging
from chimera_core.config import get_settings
from chimera_data.collectors.mcp_collector import MCPDataCollector

logger = structlog.get_logger(__name__)

class ChimeraMCP:
    """Chimera MCP server implementation."""
    
    def __init__(self, port: int = 9999, register_tools: bool = True):
        """Initialize the MCP server.
        
        Args:
            port: The port to run the MCP server on
            register_tools: Whether to register the built-in tools
        """
        self.port = port
        self.log = logger.bind(component="ChimeraMCP")
        self.mcp = None
        
        # Initialize data collector if enabled
        settings = get_settings()
        self.data_collector = MCPDataCollector(enabled=settings.enable_data_collection)
        
        if register_tools:
            self._register_tools()
    
    def _register_tools(self) -> None:
        """Register built-in tools with the registry."""
        from .tools.analyze import AnalyzeTool
        from .tools.context_cache import ContextCacheTool
        
        # Register tools
        registry.register(AnalyzeTool)
        registry.register(ContextCacheTool)
        
        # More tools will be registered here
        
        self.log.info(
            "Registered tools with registry",
            tool_count=len(registry._tools),
            tools=list(registry._tools.keys())
        )
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool request from the MCP.
        
        Args:
            request: The request dictionary
            
        Returns:
            The response dictionary
        """
        start_time = time.time()
        
        try:
            # Extract the tool name and parameters
            tool_name = request.get("name")
            params = request.get("parameters", {})
            
            self.log.info("Received tool request", tool=tool_name)
            self.log.debug("Tool parameters", params=params)
            
            if not tool_name:
                error_msg = "Missing tool name in request"
                self.log.error(error_msg)
                return {"error": error_msg}
            
            # Log the request
            request_id = self.data_collector.log_request(tool_name, params)
            
            # Get the tool from the registry
            try:
                tool = registry.get_tool(tool_name)
            except KeyError:
                error_msg = f"Tool '{tool_name}' not found"
                self.log.error(error_msg, available_tools=list(registry._tools.keys()))
                
                # Log the error response
                error_response = {"error": error_msg}
                self.data_collector.log_response(request_id, error_response)
                
                return error_response
            
            # Execute the tool
            response = await tool.execute(params)
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            self.log.info(
                "Tool execution complete", 
                tool=tool_name, 
                execution_time_ms=execution_time_ms
            )
            
            # Log the response
            self.data_collector.log_response(
                request_id, 
                response, 
                execution_time_ms=execution_time_ms
            )
            
            return response
        
        except Exception as e:
            error_msg = f"Error executing tool request: {str(e)}"
            self.log.exception("Tool execution failed", error=str(e))
            
            # Log the error response if possible
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_response = {"error": error_msg}
            
            if 'request_id' in locals():
                self.data_collector.log_response(
                    request_id, 
                    error_response, 
                    execution_time_ms=execution_time_ms
                )
            
            return error_response
    
    async def start(self) -> None:
        """Start the MCP server."""
        self.log.info(f"Starting MCP server on port {self.port}")
        
        config = {
            "title": "Project Chimera MCP Server",
            "version": "0.1.0",
            "port": self.port,
            "host": get_settings().mcp_server_host,
        }
        
        # Create the MCP server
        self.mcp = FastMCP(config)
        
        # Register tools with the MCP
        for tool_schema in registry.get_schemas():
            self.mcp.register_tool(tool_schema, self.handle_request)
        
        # Start the server
        await self.mcp.start()
        self.log.info("MCP server started successfully")
    
    async def stop(self) -> None:
        """Stop the MCP server."""
        if self.mcp:
            self.log.info("Stopping MCP server")
            await self.mcp.stop()
            self.log.info("MCP server stopped")


async def run_server(port: int) -> None:
    """Run the MCP server."""
    # Set up signal handlers for graceful shutdown
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        stop_event.set()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(sig, signal_handler)
    
    # Create and start the server
    server = ChimeraMCP(port=port)
    await server.start()
    
    # Wait for shutdown signal
    await stop_event.wait()
    
    # Stop the server
    await server.stop()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Chimera MCP Server")
    parser.add_argument(
        "--port",
        type=int,
        default=get_settings().mcp_server_port,
        help=f"Port to run the MCP server on (default: {get_settings().mcp_server_port})"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Logging level (default: from settings)"
    )
    parser.add_argument(
        "--enable-data-collection",
        action="store_true",
        help="Enable data collection (overrides settings)"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for the MCP server."""
    args = parse_args()
    
    # Set up logging
    setup_logging(log_level=args.log_level)
    
    # Override data collection setting if specified
    if args.enable_data_collection:
        settings = get_settings()
        settings.enable_data_collection = True
        logger.info("Data collection enabled via command line argument")
    
    try:
        logger.info(f"Starting MCP server on port {args.port}")
        asyncio.run(run_server(args.port))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Add parent directory to path if running directly
    if __name__ == "__main__":
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    
    main() 