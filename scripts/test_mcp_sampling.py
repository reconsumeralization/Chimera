#!/usr/bin/env python
"""
Test script for the MCP Sampling Tool.

This script demonstrates both server-side and client-side aspects of the sampling
feature, showing how servers can request LLM completions and how clients can
receive, review, and respond to these requests.
"""

import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("TestMCPSampling")

# Server-side components (simplified for demonstration)
class BaseTool:
    """Simplified base tool class for testing."""
    
    def __init__(self):
        """Initialize the tool."""
        self.log = logger
    
    def validate_params(self, params: Dict[str, Any], required_params: List[str]) -> tuple[bool, Optional[str]]:
        """Validate that all required parameters are present."""
        missing = [param for param in required_params if param not in params]
        if missing:
            error_msg = f"Missing required parameters: {', '.join(missing)}"
            self.log.warning(error_msg, extra={"missing_params": missing})
            return False, error_msg
        return True, None

class SamplingTool(BaseTool):
    """
    Server-side tool for requesting LLM completions through the client.
    
    This tool sends requests to the client for LLM completions with human oversight.
    """
    
    def __init__(self, client_connector):
        """Initialize the sampling tool with a client connector."""
        super().__init__()
        self.client_connector = client_connector
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the sampling tool to request an LLM completion."""
        try:
            # Basic parameters validation
            valid, error = self.validate_params(params, ["messages", "maxTokens"])
            if not valid:
                return {"error": error}
            
            # Validate message format
            messages = params.get("messages", [])
            if not self._validate_messages(messages):
                return {"error": "Invalid message format"}
            
            # Parse operation from parameters (default to createMessage)
            operation = params.get("operation", "createMessage")
            if not operation:
                operation = "createMessage"
                
            # Create MCP request
            mcp_method = f"sampling/{operation}"
            mcp_params = self._create_sampling_request(params)
            
            # Log the request
            self.log.info(
                "Requesting LLM completion", 
                extra={
                    "message_count": len(messages),
                    "max_tokens": params.get("maxTokens"),
                    "include_context": params.get("includeContext", "none"),
                    "has_system_prompt": bool(params.get("systemPrompt")),
                    "operation": operation
                }
            )
            
            # Send request to client and wait for response
            response = await self.client_connector.send_request(mcp_method, mcp_params)
            
            # Return the response
            return response
            
        except Exception as e:
            self.log.exception("Error executing sampling operation", extra={"error": str(e)})
            return {"error": f"Error executing sampling: {str(e)}"}
    
    def _validate_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """Validate that messages are in the correct format."""
        if not isinstance(messages, list):
            return False
        
        for msg in messages:
            # Check required fields
            if not isinstance(msg, dict):
                return False
                
            if "role" not in msg or "content" not in msg:
                return False
                
            # Validate role
            if msg["role"] not in ["user", "assistant"]:
                return False
                
            # Validate content
            content = msg["content"]
            if not isinstance(content, dict):
                return False
                
            if "type" not in content:
                return False
                
            # Validate content type and required fields
            if content["type"] == "text":
                if "text" not in content:
                    return False
            elif content["type"] == "image":
                if "data" not in content:
                    return False
            else:
                return False
        
        return True
    
    def _create_sampling_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a standardized sampling request from params."""
        request = {
            "messages": params["messages"],
            "maxTokens": params["maxTokens"]
        }
        
        # Add optional parameters if present
        for param in ["modelPreferences", "systemPrompt", "includeContext", 
                     "temperature", "stopSequences", "metadata"]:
            if param in params:
                request[param] = params[param]
        
        return request

# Client-side components (simplified for demonstration)
class ClientConnector:
    """
    Simulates the client-side connector for MCP communication.
    
    In a real implementation, this would be part of the VS Code extension
    or other client application.
    """
    
    def __init__(self):
        """Initialize the client connector."""
        self.pending_requests = {}
        self.log = logger
        
        # For simulation, store a function for handling client-to-server responses
        self.server_response_handler = None
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request from server to client.
        
        Args:
            method: The MCP method (e.g., "sampling/createMessage")
            params: The parameters for the method
            
        Returns:
            The response from the client
        """
        # Generate a request ID
        request_id = str(uuid.uuid4())
        
        # Create a future for the response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        # Create the JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        # Log the request
        self.log.info(f"Server -> Client: {method}", extra={"id": request_id})
        
        # Simulate sending to client by calling the handle_server_request method
        # In a real implementation, this would be sent over a communication channel
        asyncio.create_task(self.handle_server_request(request))
        
        # Wait for the response
        try:
            response = await asyncio.wait_for(future, timeout=30.0)
            return response
        except asyncio.TimeoutError:
            self.log.error("Timeout waiting for client response", extra={"id": request_id})
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            raise
    
    async def handle_server_request(self, request: Dict[str, Any]) -> None:
        """
        Handle a request from the server.
        
        This simulates the client-side processing of a request, including
        user review and response generation.
        
        Args:
            request: The JSON-RPC request from the server
        """
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})
        
        self.log.info(f"Client received request: {method}", extra={"id": request_id})
        
        # Parse the method to determine what type of request this is
        if method.startswith("sampling/"):
            # This is a sampling request
            operation = method.split("/")[1] if "/" in method else "unknown"
            
            # Display request for user review (simulated)
            self.log.info("User reviewing sampling request:", extra={
                "operation": operation,
                "message_count": len(params.get("messages", [])),
                "system_prompt": params.get("systemPrompt", "(none)"),
                "max_tokens": params.get("maxTokens", 0)
            })
            
            # Extract the last user message for display
            last_user_message = None
            for msg in reversed(params.get("messages", [])):
                if msg.get("role") == "user":
                    content = msg.get("content", {})
                    if content.get("type") == "text":
                        last_user_message = content.get("text")
                        break
            
            if last_user_message:
                self.log.info(f"Last user message: {last_user_message[:100]}...")
            
            # Simulate user approval (would be interactive in real implementation)
            self.log.info("User approved sampling request")
            
            # Simulate LLM generation with a mock response
            await asyncio.sleep(1.0)  # Simulate LLM API call taking time
            
            # Create a simulated LLM response
            if operation == "createMessage":
                llm_response = self._create_mock_llm_response(params)
                
                # Display response for user review (simulated)
                self.log.info("User reviewing LLM response:", extra={
                    "model": llm_response.get("model"),
                    "stop_reason": llm_response.get("stopReason"),
                    "text_length": len(llm_response.get("content", {}).get("text", ""))
                })
                
                # Simulate user approval (would be interactive in real implementation)
                self.log.info("User approved LLM response")
                
                # Send response back to server
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": llm_response
                }
                
                # Complete the future to resolve the server's waiting send_request call
                if request_id in self.pending_requests:
                    self.pending_requests[request_id].set_result(llm_response)
                    del self.pending_requests[request_id]
                
                # In a real implementation, this would be sent back over a communication channel
                self.log.info(f"Client -> Server response sent", extra={"id": request_id})
                
            else:
                error = {
                    "code": -32601,
                    "message": f"Unsupported sampling operation: {operation}"
                }
                
                # Send error response back to server
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": error
                }
                
                # Complete the future with an error
                if request_id in self.pending_requests:
                    self.pending_requests[request_id].set_exception(
                        Exception(f"Unsupported sampling operation: {operation}")
                    )
                    del self.pending_requests[request_id]
                
                self.log.error(f"Client -> Server error response sent", extra={"id": request_id})
        else:
            # Unsupported method
            error = {
                "code": -32601,
                "message": f"Unsupported method: {method}"
            }
            
            # Send error response back to server
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": error
            }
            
            # Complete the future with an error
            if request_id in self.pending_requests:
                self.pending_requests[request_id].set_exception(
                    Exception(f"Unsupported method: {method}")
                )
                del self.pending_requests[request_id]
            
            self.log.error(f"Client -> Server error response sent", extra={"id": request_id})
    
    def _create_mock_llm_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a mock LLM response for simulation purposes.
        
        Args:
            params: The request parameters
            
        Returns:
            A simulated LLM response
        """
        # Extract the last user message to generate a contextual response
        last_user_message = None
        for msg in reversed(params.get("messages", [])):
            if msg.get("role") == "user":
                content = msg.get("content", {})
                if content.get("type") == "text":
                    last_user_message = content.get("text")
                    break
        
        # Generate a contextual response
        response_text = ""
        if last_user_message:
            if "file" in last_user_message.lower() or "directory" in last_user_message.lower():
                response_text = "I can see you're asking about files. The current directory contains several Python files including main.py, utils.py, and server.py. There are also configuration files like config.yaml and package.json."
            elif "context" in last_user_message.lower() or "cache" in last_user_message.lower():
                response_text = "The context cache is a core component that stores snapshots of the user's workspace, including file contents, diagnostics, and metadata. It supports querying by file patterns, text content, and time ranges. The cache can store data both in memory and in a database for persistence."
            elif "database" in last_user_message.lower() or "db" in last_user_message.lower():
                response_text = "Yes, the context cache works with the database. It can store snapshots in SQLite using SQLAlchemy/SQLModel as the ORM layer. This enables persistent storage of context across sessions and allows for complex queries against historical data."
            else:
                response_text = "I'm a helpful assistant integrated with Chimera. I can provide information about your code, explain concepts, and help with development tasks. Is there something specific you'd like to know about the project?"
        
        # Create the response object
        return {
            "model": "mock-llm-model-3",
            "stopReason": "endTurn",
            "role": "assistant",
            "content": {
                "type": "text",
                "text": response_text
            }
        }

async def test_sampling_tool():
    """Test the sampling tool with different requests, showing server and client interaction."""
    logger.info("Testing sampling tool with server-client interaction...")
    
    # Create the client connector
    client = ClientConnector()
    
    # Create the sampling tool with the client connector
    tool = SamplingTool(client)
    
    # Test basic text completion request
    logger.info("\n\n1. Testing basic text completion request...")
    basic_request = {
        "operation": "createMessage",
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "What files are in the current directory?"
                }
            }
        ],
        "systemPrompt": "You are a helpful file system assistant.",
        "includeContext": "thisServer",
        "maxTokens": 100
    }
    
    basic_result = await tool.execute(basic_request)
    logger.info(f"Basic result:\n{json.dumps(basic_result, indent=2)}")
    
    # Test request with model preferences
    logger.info("\n\n2. Testing request with model preferences...")
    preference_request = {
        "operation": "createMessage",
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Summarize the main features of the context cache."
                }
            }
        ],
        "modelPreferences": {
            "hints": [{"name": "claude-3-sonnet"}],
            "intelligencePriority": 0.8,
            "speedPriority": 0.5,
            "costPriority": 0.3
        },
        "systemPrompt": "You are a helpful coding assistant.",
        "includeContext": "thisServer",
        "temperature": 0.7,
        "maxTokens": 250
    }
    
    preference_result = await tool.execute(preference_request)
    logger.info(f"Model preference result:\n{json.dumps(preference_result, indent=2)}")
    
    # Test conversation completion (with history)
    logger.info("\n\n3. Testing conversation completion with history...")
    conversation_request = {
        "operation": "createMessage",
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "What can the context cache tool do?"
                }
            },
            {
                "role": "assistant",
                "content": {
                    "type": "text",
                    "text": "The context cache tool allows you to store and query information about files in your workspace. It can remember file contents, diagnostics, and metadata across sessions."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Can it work with the database?"
                }
            }
        ],
        "systemPrompt": "You are a helpful coding assistant who knows about the Chimera project.",
        "includeContext": "allServers",
        "maxTokens": 150
    }
    
    conversation_result = await tool.execute(conversation_request)
    logger.info(f"Conversation result:\n{json.dumps(conversation_result, indent=2)}")
    
    # Test invalid request
    logger.info("\n\n4. Testing invalid request (missing required field)...")
    invalid_request = {
        "operation": "createMessage",
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Hello!"
                }
            }
        ],
        "systemPrompt": "You are a helpful assistant."
        # Missing maxTokens
    }
    
    try:
        invalid_result = await tool.execute(invalid_request)
        logger.info(f"Invalid request result:\n{json.dumps(invalid_result, indent=2)}")
    except Exception as e:
        logger.error(f"Error handling invalid request: {str(e)}")
    
    logger.info("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_sampling_tool()) 