"""Code generation tool for creating code through MCP."""
import json
import structlog
import asyncio
from typing import Any, Dict, List, Optional, Union
import time

from .base import BaseTool
from ..mcp_client import send_request, MCPError

logger = structlog.get_logger(__name__)

class CodeGenerationTool(BaseTool):
    """
    Tool for generating code through LLM completions.
    
    This tool leverages the SamplingTool with specialized prompts
    for code generation tasks.
    """
    
    TOOL_NAME = "code_generation"
    DESCRIPTION = "Generates code based on prompts and context."
    
    def __init__(self):
        """Initialize the code generation tool."""
        super().__init__()
        self.log = logger.bind(tool="code_generation")
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the code generation tool."""
        try:
            # Basic parameters validation
            valid, error = self.validate_params(params, ["prompt", "language"])
            if not valid:
                return {"error": error}
            
            # Extract parameters
            prompt = params.get("prompt", "")
            language = params.get("language", "")
            context_files = params.get("context_files", [])
            context_query = params.get("context_query", "")
            
            # Log the request (excluding sensitive content)
            self.log.info(
                "Requesting code generation",
                language=language,
                has_context_files=bool(context_files),
                has_context_query=bool(context_query)
            )
            
            # Build messages for the SamplingTool
            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Generate {language} code for: {prompt}"
                    }
                }
            ]
            
            # Create system prompt with context instructions
            system_prompt = "You are an expert code generator. Write clean, efficient, and well-documented code."
            if context_files or context_query:
                system_prompt += " Use the provided context to ensure the code integrates properly with the existing codebase."
            
            # Create MCP request for sampling tool
            sampling_params = {
                "operation": "createMessage",
                "messages": messages,
                "systemPrompt": system_prompt,
                "includeContext": "thisServer" if (context_files or context_query) else "none",
                "maxTokens": 1500,
                "temperature": 0.2  # Lower temperature for more deterministic code
            }
            
            # Add context metadata
            if context_files or context_query:
                sampling_params["metadata"] = {
                    "contextFiles": context_files,
                    "contextQuery": context_query
                }
            
            start_time = time.time()
            
            try:
                # Send request to sampling tool
                response = await send_request("sampling/createMessage", sampling_params)
                
                # Extract code from the response
                if response and "message" in response:
                    content = response["message"].get("content", {})
                    generated_code = content.get("text", "")
                    
                    # Log successful completion
                    elapsed_time = time.time() - start_time
                    self.log.info(
                        "Code generation completed",
                        elapsed_time_ms=int(elapsed_time * 1000),
                        language=language,
                        model=response.get("model", "unknown")
                    )
                    
                    return {
                        "code": generated_code,
                        "language": language,
                        "model": response.get("model", "unknown"),
                        "elapsed_ms": int(elapsed_time * 1000)
                    }
                else:
                    return {"error": "Invalid response from LLM"}
                
            except MCPError as e:
                # Handle MCP-specific errors
                error_msg = f"MCP error during code generation: {str(e)}"
                self.log.error(error_msg, error_code=getattr(e, "code", None))
                return {"error": error_msg}
                
            except asyncio.TimeoutError:
                # Handle timeout
                error_msg = "Timeout waiting for code generation"
                self.log.error(error_msg)
                return {"error": error_msg, "timeout": True}
                
        except Exception as e:
            self.log.exception("Error executing code generation", error=str(e))
            return {"error": f"Error during code generation: {str(e)}"}
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Return the JSON schema for this tool."""
        return {
            "name": cls.TOOL_NAME,
            "description": cls.DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Description of the code to generate"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language for the generated code"
                    },
                    "context_files": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of file paths to use as context"
                    },
                    "context_query": {
                        "type": "string",
                        "description": "Query to search for relevant context"
                    }
                },
                "required": ["prompt", "language"]
            }
        } 