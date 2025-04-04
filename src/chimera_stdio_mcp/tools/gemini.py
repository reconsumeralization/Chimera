"""Gemini AI model integration tool for Project Chimera."""
import json
import structlog
import asyncio
import os
from typing import Any, Dict, List, Optional, Union
import time

import google.generativeai as genai

from .base import BaseTool

logger = structlog.get_logger(__name__)

class GeminiTool(BaseTool):
    """
    Tool for interacting with Google's Gemini models.
    
    This tool provides access to Google's Gemini AI models for text generation,
    content creation, and other AI-powered features.
    """
    
    TOOL_NAME = "gemini"
    DESCRIPTION = "Interacts with Google Gemini AI models for text and content generation."
    
    def __init__(self):
        """Initialize the Gemini tool."""
        super().__init__()
        self.log = logger.bind(tool="gemini")
        
        # Initialize Gemini API with API key from environment
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            self.log.warning("No Google API key found in environment variables (GOOGLE_API_KEY)")
        else:
            genai.configure(api_key=api_key)
            self.log.info("Gemini API initialized successfully")
        
        # Available models for reference
        self.available_models = {
            "gemini-1.0-pro": "Versatile text and image understanding, reasoning",
            "gemini-1.5-pro": "Advanced reasoning, longer context, multimodal capabilities",
            "gemini-1.5-flash": "Fast, efficient text processing for everyday use cases"
        }
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Gemini tool with the given parameters."""
        try:
            # Basic parameters validation
            valid, error = self.validate_params(params, ["operation"])
            if not valid:
                return {"error": error}
            
            # Extract operation and dispatch to appropriate handler
            operation = params.get("operation", "")
            
            if operation == "generateText":
                return await self._handle_generate_text(params)
            elif operation == "listModels":
                return await self._handle_list_models(params)
            else:
                error_msg = f"Unknown operation: {operation}"
                self.log.warning(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            self.log.exception("Error executing Gemini tool", error=str(e))
            return {"error": f"Error during Gemini operation: {str(e)}"}
    
    async def _handle_generate_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text generation with Gemini models."""
        # Validate required parameters
        valid, error = self.validate_params(params, ["prompt"])
        if not valid:
            return {"error": error}
        
        # Extract parameters
        prompt = params.get("prompt", "")
        model_name = params.get("model", "gemini-1.5-flash")  # Default to fast model
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 1024)
        top_p = params.get("top_p", 0.95)
        top_k = params.get("top_k", 40)
        
        # Check if we have an API key configured
        if not os.environ.get("GOOGLE_API_KEY"):
            return {"error": "Gemini API key not configured. Set GOOGLE_API_KEY environment variable."}
        
        self.log.info(
            "Generating text with Gemini",
            model=model_name,
            prompt_length=len(prompt),
            temperature=temperature
        )
        
        try:
            # Create model configuration
            config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": top_p,
                "top_k": top_k
            }
            
            # Get the model
            model = genai.GenerativeModel(model_name)
            
            start_time = time.time()
            
            # Run text generation in a separate thread to not block the event loop
            response = await asyncio.to_thread(
                model.generate_content, 
                contents=prompt,
                generation_config=config
            )
            
            elapsed_time = time.time() - start_time
            
            # Extract the response text
            if hasattr(response, 'text'):
                generated_text = response.text
                
                self.log.info(
                    "Text generation completed",
                    model=model_name,
                    elapsed_ms=int(elapsed_time * 1000),
                    output_length=len(generated_text) if generated_text else 0
                )
                
                finish_reason = None
                if hasattr(response, 'candidates') and response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                
                return {
                    "text": generated_text,
                    "model": model_name,
                    "elapsed_ms": int(elapsed_time * 1000),
                    "finish_reason": finish_reason
                }
            else:
                return {"error": "No valid response generated from model"}
                
        except Exception as e:
            error_msg = f"Error generating text with Gemini: {str(e)}"
            self.log.error(error_msg)
            return {"error": error_msg}
    
    async def _handle_list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle listing available Gemini models."""
        try:
            # Check if we should fetch from API or use cached list
            use_api = params.get("use_api", False)
            
            if use_api and os.environ.get("GOOGLE_API_KEY"):
                # Fetch models from the API (run in separate thread to not block)
                models_list = await asyncio.to_thread(genai.list_models)
                
                # Format the models information
                models = []
                for model in models_list:
                    models.append({
                        "name": model.name,
                        "display_name": getattr(model, 'display_name', model.name),
                        "description": getattr(model, 'description', ''),
                        "input_token_limit": getattr(model, 'input_token_limit', 0),
                        "output_token_limit": getattr(model, 'output_token_limit', 0),
                        "supported_generation_methods": getattr(model, 'supported_generation_methods', [])
                    })
                    
                return {"models": models}
            else:
                # Return the cached list
                models = []
                for name, description in self.available_models.items():
                    models.append({
                        "name": name,
                        "description": description
                    })
                    
                return {"models": models}
                
        except Exception as e:
            error_msg = f"Error listing Gemini models: {str(e)}"
            self.log.error(error_msg)
            return {"error": error_msg}
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Return the JSON schema for this tool."""
        return {
            "name": cls.TOOL_NAME,
            "description": cls.DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["generateText", "listModels"],
                        "description": "Operation to perform with the Gemini tool"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Text prompt for text generation"
                    },
                    "model": {
                        "type": "string",
                        "description": "Name of the Gemini model to use (default: gemini-1.5-flash)"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature parameter for text generation (0.0 to 1.0)"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum number of tokens to generate"
                    },
                    "use_api": {
                        "type": "boolean",
                        "description": "Whether to fetch models from the API"
                    }
                },
                "required": ["operation"]
            }
        } 