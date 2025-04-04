"""Code analysis tool for analyzing code through MCP."""
import json
import structlog
import asyncio
from typing import Any, Dict, List, Optional, Union
import time

from .base import BaseTool
from ..mcp_client import send_request, MCPError

logger = structlog.get_logger(__name__)

class CodeAnalysisTool(BaseTool):
    """
    Tool for analyzing code through LLM.
    
    This tool leverages the SamplingTool with specialized prompts
    for code analysis tasks.
    """
    
    TOOL_NAME = "code_analysis"
    DESCRIPTION = "Analyzes code for issues, improvements, and best practices."
    
    def __init__(self):
        """Initialize the code analysis tool."""
        super().__init__()
        self.log = logger.bind(tool="code_analysis")
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the code analysis tool."""
        try:
            # Basic parameters validation
            valid, error = self.validate_params(params, ["code"])
            if not valid:
                return {"error": error}
            
            # Extract parameters
            code = params.get("code", "")
            language = params.get("language", "")
            analysis_type = params.get("analysis_type", "general")
            
            # Log the request
            self.log.info(
                "Requesting code analysis",
                language=language,
                analysis_type=analysis_type
            )
            
            # Build messages for the SamplingTool
            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Analyze this {language} code:\n\n```{language}\n{code}\n```"
                    }
                }
            ]
            
            # Create system prompt based on analysis type
            system_prompt = "You are an expert code reviewer. "
            
            if analysis_type == "security":
                system_prompt += "Focus on security vulnerabilities, potential exploits, and secure coding practices."
            elif analysis_type == "performance":
                system_prompt += "Focus on performance issues, optimizations, and efficiency improvements."
            elif analysis_type == "style":
                system_prompt += "Focus on code style, readability, and adherence to best practices."
            else:  # general
                system_prompt += "Provide a comprehensive analysis covering bugs, edge cases, improvements, and best practices."
            
            # Create MCP request for sampling tool
            sampling_params = {
                "operation": "createMessage",
                "messages": messages,
                "systemPrompt": system_prompt,
                "includeContext": "none",
                "maxTokens": 1000,
                "temperature": 0.3
            }
            
            start_time = time.time()
            
            try:
                # Send request to sampling tool
                response = await send_request("sampling/createMessage", sampling_params)
                
                # Extract analysis from the response
                if response and "message" in response:
                    content = response["message"].get("content", {})
                    analysis = content.get("text", "")
                    
                    # Log successful completion
                    elapsed_time = time.time() - start_time
                    self.log.info(
                        "Code analysis completed",
                        elapsed_time_ms=int(elapsed_time * 1000),
                        analysis_type=analysis_type,
                        model=response.get("model", "unknown")
                    )
                    
                    return {
                        "analysis": analysis,
                        "language": language,
                        "analysis_type": analysis_type,
                        "model": response.get("model", "unknown"),
                        "elapsed_ms": int(elapsed_time * 1000)
                    }
                else:
                    return {"error": "Invalid response from LLM"}
                
            except MCPError as e:
                # Handle MCP-specific errors
                error_msg = f"MCP error during code analysis: {str(e)}"
                self.log.error(error_msg, error_code=getattr(e, "code", None))
                return {"error": error_msg}
                
            except asyncio.TimeoutError:
                # Handle timeout
                error_msg = "Timeout waiting for code analysis"
                self.log.error(error_msg)
                return {"error": error_msg, "timeout": True}
                
        except Exception as e:
            self.log.exception("Error executing code analysis", error=str(e))
            return {"error": f"Error during code analysis: {str(e)}"}
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Return the JSON schema for this tool."""
        return {
            "name": cls.TOOL_NAME,
            "description": cls.DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code to analyze"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language of the code"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["general", "security", "performance", "style"],
                        "description": "Type of analysis to perform"
                    }
                },
                "required": ["code"]
            }
        } 