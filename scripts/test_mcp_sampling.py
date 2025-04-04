#!/usr/bin/env python
"""
Test script for the MCP Sampling Tool.

This script tests the sampling tool which allows servers to request LLM completions
through the client with human oversight.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("TestMCPSampling")

# Create a simplified version of the BaseTool class for testing
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

# Create a simplified version of the SamplingTool for testing
class SamplingTool(BaseTool):
    """
    Tool for requesting LLM completions through the client.
    
    This tool allows servers to request text generation from LLMs through the MCP client,
    enabling sophisticated agentic behaviors while maintaining security and privacy.
    The client provides human-in-the-loop review of prompts and completions.
    """
    
    def __init__(self):
        """Initialize the sampling tool."""
        super().__init__()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the sampling tool to request an LLM completion.
        
        Args:
            params: Dictionary containing:
                - messages: List of conversation messages
                - modelPreferences: Optional model selection preferences
                - systemPrompt: Optional system prompt
                - includeContext: Optional context inclusion level
                - temperature: Optional sampling temperature
                - maxTokens: Maximum tokens to generate
                - stopSequences: Optional sequences that stop generation
                - metadata: Optional provider-specific parameters
                
        Returns:
            Dictionary with the completion results or error
        """
        try:
            # Basic parameters validation
            valid, error = self.validate_params(params, ["messages", "maxTokens"])
            if not valid:
                return {"error": error}
            
            # Validate message format
            messages = params.get("messages", [])
            if not self._validate_messages(messages):
                return {"error": "Invalid message format"}
            
            # Create completion request
            request = self._create_sampling_request(params)
            
            # Log the request (excluding potentially sensitive content)
            self.log.info(
                "Requesting LLM completion", 
                extra={
                    "message_count": len(messages),
                    "max_tokens": params.get("maxTokens"),
                    "include_context": params.get("includeContext", "none"),
                    "has_system_prompt": bool(params.get("systemPrompt"))
                }
            )
            
            # Here we would normally send the request to the client
            # For now, we'll return a stub response indicating the request format is valid
            # but the actual sampling functionality is not yet implemented
            return {
                "status": "not_implemented",
                "message": "The sampling tool is correctly configured but not yet fully implemented",
                "request_format_valid": True,
                "expected_response": {
                    "model": "(model name)",
                    "stopReason": "endTurn",
                    "role": "assistant",
                    "content": {
                        "type": "text",
                        "text": "(LLM completion would appear here)"
                    }
                }
            }
        
        except Exception as e:
            self.log.exception("Error executing sampling operation", extra={"error": str(e)})
            return {"error": f"Error executing sampling: {str(e)}"}
    
    def _validate_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Validate that messages are in the correct format.
        
        Args:
            messages: List of message objects to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
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
        """
        Create a standardized sampling request from params.
        
        Args:
            params: Original parameters
            
        Returns:
            Dict: Formatted sampling request
        """
        request = {
            "messages": params["messages"],
            "maxTokens": params["maxTokens"]
        }
        
        # Add optional parameters if present
        if "modelPreferences" in params:
            request["modelPreferences"] = params["modelPreferences"]
            
        if "systemPrompt" in params:
            request["systemPrompt"] = params["systemPrompt"]
            
        if "includeContext" in params:
            request["includeContext"] = params["includeContext"]
            
        if "temperature" in params:
            request["temperature"] = params["temperature"]
            
        if "stopSequences" in params:
            request["stopSequences"] = params["stopSequences"]
            
        if "metadata" in params:
            request["metadata"] = params["metadata"]
        
        return request

async def test_sampling_tool():
    """Test the sampling tool with different requests."""
    logger.info("Testing sampling tool...")
    
    # Create the tool
    tool = SamplingTool()
    
    # Test basic text completion request
    logger.info("Testing basic text completion request...")
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
    logger.info("Testing request with model preferences...")
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
    logger.info("Testing conversation completion with history...")
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
    logger.info("Testing invalid request (missing required field)...")
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
    
    invalid_result = await tool.execute(invalid_request)
    logger.info(f"Invalid request result:\n{json.dumps(invalid_result, indent=2)}")
    
    logger.info("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_sampling_tool()) 