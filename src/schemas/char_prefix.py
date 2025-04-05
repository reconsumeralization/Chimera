"""Character Prefix Conditioning schemas.

This module defines the schema models for the Character Prefix Conditioning
functionality, which allows generating text that starts with a specific
character prefix.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class CharPrefixRequest(BaseModel):
    """Base request model for character prefix conditioning."""
    
    prefix: str = Field(..., description="Character prefix that the generated text must start with")
    prompt: str = Field(..., description="The prompt describing what to generate")
    max_tokens: Optional[int] = Field(500, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature (0.0-1.0)")
    top_p: Optional[float] = Field(0.9, description="Nucleus sampling probability threshold")
    top_k: Optional[int] = Field(40, description="Top-k sampling parameter")
    stop_sequences: Optional[List[str]] = Field(None, description="Sequences that stop generation")


class CharPrefixResponse(BaseModel):
    """Base response model for character prefix conditioning."""
    
    text: str = Field(..., description="Generated text that starts with the specified prefix")
    prefix: str = Field(..., description="Character prefix that was used for conditioning")
    truncated: bool = Field(False, description="Whether the response was truncated")


class CharPrefixCodeRequest(CharPrefixRequest):
    """Request model for character prefix conditioning with code context."""
    
    language: str = Field(..., description="Programming language for the generated code")
    file_path: Optional[str] = Field(None, description="Path to the file containing context")
    context_files: Optional[List[str]] = Field(None, description="List of file paths to include as context")
    context_query: Optional[str] = Field(None, description="Natural language query to find relevant context")


class CharPrefixCodeResponse(CharPrefixResponse):
    """Response model for character prefix conditioning with code context."""
    
    language: str = Field(..., description="Programming language of the generated code")
    context_used: Optional[List[str]] = Field(None, description="List of context files that were used") 