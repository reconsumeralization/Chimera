"""API request and response models for the FastAPI routes.

This module defines the Pydantic models used for API request and response bodies
in the FastAPI routes.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class CodeGenerationRequest(BaseModel):
    """Request model for code generation."""
    
    prompt: str = Field(..., description="Prompt describing the code to generate")
    language: str = Field(..., description="Programming language for the generated code")
    context_files: Optional[List[str]] = Field(None, description="List of file paths to include as context")
    context_query: Optional[str] = Field(None, description="Natural language query to find relevant context")
    temperature: Optional[float] = Field(0.2, description="Temperature for code generation (0.0-1.0)")


class CodeGenerationResponse(BaseModel):
    """Response model for code generation."""
    
    code: str = Field(..., description="Generated code")
    language: str = Field(..., description="Programming language of the generated code")


class CodeExplanationRequest(BaseModel):
    """Request model for code explanation."""
    
    code: str = Field(..., description="Code to explain")
    language: str = Field(..., description="Programming language of the code")
    detailed: bool = Field(True, description="Whether to provide a detailed explanation")
    file_path: Optional[str] = Field(None, description="Path to the file containing the code")
    context_query: Optional[str] = Field(None, description="Natural language query to find relevant context")


class CodeExplanationResponse(BaseModel):
    """Response model for code explanation."""
    
    explanation: str = Field(..., description="Explanation of the code")
    language: str = Field(..., description="Programming language of the code")


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""
    
    code: str = Field(..., description="Code to analyze")
    language: str = Field(..., description="Programming language of the code")
    json_output: bool = Field(False, description="Whether to return the analysis as a JSON object")
    file_path: Optional[str] = Field(None, description="Path to the file containing the code")
    context_query: Optional[str] = Field(None, description="Natural language query to find relevant context")


class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis."""
    
    analysis: Union[str, Dict[str, Any]] = Field(..., description="Analysis of the code")
    language: str = Field(..., description="Programming language of the code")


class CodeChatRequest(BaseModel):
    """Request model for chat with code context."""
    
    prompt: str = Field(..., description="User's prompt or question")
    code: Optional[str] = Field(None, description="Code to discuss")
    language: Optional[str] = Field(None, description="Programming language of the code")
    active_file: Optional[str] = Field(None, description="Path to the active file")
    context_files: Optional[List[str]] = Field(None, description="List of file paths to include as context")
    context_query: Optional[str] = Field(None, description="Natural language query to find relevant context")


class CodeChatResponse(BaseModel):
    """Response model for chat with code context."""
    
    response: str = Field(..., description="AI's response to the chat prompt")


class CodeTestRequest(BaseModel):
    """Request model for test generation."""
    
    code: str = Field(..., description="Code to generate tests for")
    language: str = Field(..., description="Programming language of the code")
    test_framework: str = Field(..., description="Test framework to use (e.g. pytest, jest)")
    file_path: Optional[str] = Field(None, description="Path to the file containing the code")
    context_query: Optional[str] = Field(None, description="Natural language query to find relevant context")


class CodeTestResponse(BaseModel):
    """Response model for test generation."""
    
    tests: str = Field(..., description="Generated tests")
    language: str = Field(..., description="Programming language of the tests")
    test_framework: str = Field(..., description="Test framework used")


class StreamingResponse(BaseModel):
    """Model for streaming responses."""
    
    chunk: str = Field(..., description="Chunk of the response") 