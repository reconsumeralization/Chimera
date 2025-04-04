"""Sampling tool for requesting LLM completions through MCP."""
import json
import structlog
import asyncio
from typing import Any, Dict, List, Optional, Literal, Union
import time

from .base import BaseTool
from ..mcp_client import send_request, MCPError

logger = structlog.get_logger(__name__)

class SamplingTool(BaseTool):
    """
    Tool for requesting LLM completions through the client.
    
    This tool allows servers to request text generation from LLMs through the MCP client,
    enabling sophisticated agentic behaviors while maintaining security and privacy.
    The client provides human-in-the-loop review of prompts and completions.
    """
    
    TOOL_NAME = "sampling"
    DESCRIPTION = "Requests LLM completions through the client with human oversight."
    
    def __init__(self):
        """Initialize the sampling tool."""
        super().__init__()
        self.log = logger.bind(tool="sampling")
    
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
            
            # Parse operation from parameters (default to createMessage)
            operation = params.get("operation", "createMessage")
            if not operation:
                operation = "createMessage"
                
            if operation not in ["createMessage"]:
                return {"error": f"Unsupported sampling operation: {operation}"}
            
            # Create MCP request
            mcp_method = f"sampling/{operation}"
            mcp_params = self._create_sampling_request(params)
            
            # Log the request (excluding potentially sensitive content)
            self.log.info(
                "Requesting LLM completion",
                message_count=len(messages),
                max_tokens=params.get("maxTokens"),
                include_context=params.get("includeContext", "none"),
                has_system_prompt=bool(params.get("systemPrompt")),
                operation=operation
            )
            
            start_time = time.time()
            
            try:
                # Send request to client and wait for response
                response = await send_request(mcp_method, mcp_params)
                
                # Log successful completion
                elapsed_time = time.time() - start_time
                self.log.info(
                    "LLM completion received",
                    elapsed_time_ms=int(elapsed_time * 1000),
                    model=response.get("model", "unknown"),
                    stop_reason=response.get("stopReason", "unknown")
                )
                
                return response
                
            except MCPError as e:
                # Handle MCP-specific errors
                error_msg = f"MCP error during sampling: {str(e)}"
                self.log.error(error_msg, error_code=getattr(e, "code", None))
                return {"error": error_msg, "mcp_error": True, "code": getattr(e, "code", None)}
                
            except asyncio.TimeoutError:
                # Handle timeout
                error_msg = "Timeout waiting for LLM completion"
                self.log.error(error_msg, timeout_ms=int((time.time() - start_time) * 1000))
                return {"error": error_msg, "timeout": True}
                
            except Exception as e:
                # Handle other errors during MCP communication
                error_msg = f"Error communicating with client: {str(e)}"
                self.log.error(error_msg)
                return {"error": error_msg}
        
        except Exception as e:
            self.log.exception("Error executing sampling operation", error=str(e))
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
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Get the JSON schema for this tool.
        
        Returns:
            Dict: Tool schema
        """
        return {
            "name": cls.TOOL_NAME,
            "description": cls.DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": "Array of messages in the conversation history",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "enum": ["user", "assistant"],
                                    "description": "Role of the message sender"
                                },
                                "content": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": ["text", "image"],
                                            "description": "Type of content"
                                        },
                                        "text": {
                                            "type": "string",
                                            "description": "Text content for text messages"
                                        },
                                        "data": {
                                            "type": "string",
                                            "description": "Base64-encoded image data for image messages"
                                        },
                                        "mimeType": {
                                            "type": "string",
                                            "description": "MIME type for image content"
                                        }
                                    },
                                    "required": ["type"],
                                    "description": "Content of the message"
                                }
                            },
                            "required": ["role", "content"]
                        }
                    },
                    "modelPreferences": {
                        "type": "object",
                        "description": "Preferences for model selection",
                        "properties": {
                            "hints": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Suggested model name/family"
                                        }
                                    }
                                },
                                "description": "Hints for model selection"
                            },
                            "costPriority": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Importance of minimizing cost (0-1)"
                            },
                            "speedPriority": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Importance of low latency (0-1)"
                            },
                            "intelligencePriority": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Importance of capabilities (0-1)"
                            }
                        }
                    },
                    "systemPrompt": {
                        "type": "string",
                        "description": "Optional system prompt for the LLM"
                    },
                    "includeContext": {
                        "type": "string",
                        "enum": ["none", "thisServer", "allServers"],
                        "description": "What MCP context to include in the prompt"
                    },
                    "temperature": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Sampling temperature (0-1)"
                    },
                    "maxTokens": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Maximum tokens to generate"
                    },
                    "stopSequences": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Sequences that will stop generation"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional provider-specific parameters"
                    }
                },
                "required": ["messages", "maxTokens"]
            }
        } 