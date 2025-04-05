"""API routes for AI features.

This module provides the API routes for AI features such as code generation,
explanation, review, and chat functionality.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError, Field

from src.chimera_core.api.dependencies import APIKey, get_ai_client, get_context_cache_service, get_prompt_service
from src.chimera_core.services.ai_client import AIClient
from src.chimera_core.services.context_cache import ContextCacheService
from src.chimera_core.services.prompt_service import PromptService
from src.chimera_core.api.models import (
    CodeAnalysisRequest, CodeAnalysisResponse,
    CodeExplanationRequest, CodeExplanationResponse,
    CodeGenerationRequest, CodeGenerationResponse,
    CodeChatRequest, CodeChatResponse,
    CodeTestRequest, CodeTestResponse,
    StreamingResponse as StreamingResponseModel
)
from src.schemas.context import ContextQuery

# Create the router
router = APIRouter(prefix="/ai", tags=["ai"])

# Set up logger
logger = logging.getLogger(__name__)

# Add the new request and response models for character prefix generation
class CharPrefixGenerationRequest(CodeGenerationRequest):
    """Request model for character-prefix-constrained generation."""
    
    prefix: str = Field(..., description="Character prefix that the generated code must start with")
    model_type: Optional[Literal["openai", "gemini"]] = Field(None, description="Explicitly specify the model type to use")


class CharPrefixGenerationResponse(CodeGenerationResponse):
    """Response model for character-prefix-constrained generation."""
    
    prefix: str = Field(..., description="Character prefix that the generated code starts with")
    model_used: str = Field("default", description="The model type that was used for generation")


@router.post("/generate", response_model=CodeGenerationResponse, dependencies=[Depends(APIKey)])
async def generate_code(
    request: CodeGenerationRequest,
    ai_client: Annotated[AIClient, Depends(get_ai_client)],
    context_cache: Annotated[ContextCacheService, Depends(get_context_cache_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)]
) -> CodeGenerationResponse:
    """Generate code based on the prompt and context."""
    try:
        # Prepare context
        context = {}
        context_files = []
        
        # If specific files are provided, use them directly
        if request.context_files:
            file_paths = request.context_files
            # Get the files from context cache
            context_files = await context_cache.get_files_by_paths(file_paths)
            if context_files:
                context["files"] = context_files
        
        # If a context query is provided, use it to retrieve relevant context
        elif request.context_query:
            # Create a context query
            query = ContextQuery(
                query_text=request.context_query,
                languages=[request.language] if request.language else None,
                max_files=5,
                include_content=True
            )
            
            # Get relevant context
            relevant_context = await context_cache.query_context(query)
            if relevant_context and relevant_context.matches:
                context_files = relevant_context.matches
                context["files"] = context_files
        
        # Use prompt service to create a code generation prompt
        generation_prompt = await prompt_service.create_code_generation_prompt(
            generation_request=request.prompt,
            language=request.language,
            context_files=context_files,
            context_query=request.context_query
        )
        
        # Log the prompt creation
        logger.debug(
            "Created code generation prompt",
            extra={
                "language": request.language,
                "has_context": bool(context_files),
                "context_query": request.context_query
            }
        )
        
        # Generate the code using the prompt service-generated prompt
        generated_code = await ai_client.generate_code(
            prompt=request.prompt,
            language=request.language,
            context=context,
            custom_prompt=generation_prompt,
            stream=False
        )
        
        return CodeGenerationResponse(
            code=generated_code,
            language=request.language
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "Failed to generate code",
            exc_info=True,
            extra={
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate code: {str(e)}"
        )


@router.post("/generate/stream", dependencies=[Depends(APIKey)])
async def generate_code_stream(
    request: CodeGenerationRequest,
    ai_client: Annotated[AIClient, Depends(get_ai_client)],
    context_cache: Annotated[ContextCacheService, Depends(get_context_cache_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)]
) -> StreamingResponse:
    """Generate code with streaming response based on the prompt and context."""
    try:
        # Prepare context
        context = {}
        
        # If specific files are provided, use them directly
        if request.context_files:
            file_paths = request.context_files
            # Get the files from context cache
            context_files = await context_cache.get_files_by_paths(file_paths)
            if context_files:
                context["files"] = context_files
        
        # If a context query is provided, use it to retrieve relevant context
        elif request.context_query:
            # Create a context query
            query = ContextQuery(
                query_text=request.context_query,
                languages=[request.language] if request.language else None,
                max_files=5,
                include_content=True
            )
            
            # Get relevant context
            relevant_context = await context_cache.query_context(query)
            if relevant_context and relevant_context.matches:
                context["files"] = relevant_context.matches
        
        # Generate the code with streaming
        stream = await ai_client.generate_code(
            prompt=request.prompt,
            language=request.language,
            context=context,
            stream=True
        )
        
        # Helper function to convert the stream to SSE format
        async def event_stream():
            try:
                async for chunk in stream:
                    yield f"data: {chunk}\n\n"
                yield "event: close\ndata: \n\n"
            except Exception as e:
                yield f"event: error\ndata: {str(e)}\n\n"
                yield "event: close\ndata: \n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream"
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate code: {str(e)}"
        )


@router.post("/explain", response_model=CodeExplanationResponse)
async def explain_code(
    request: CodeExplanationRequest,
    ai_client: Annotated[AIClient, Depends(get_ai_client)],
    context_cache: Annotated[ContextCacheService, Depends(get_context_cache_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)]
) -> CodeExplanationResponse:
    """Explain the provided code with optional context."""
    try:
        # Prepare context
        context = {}
        file_content = None
        
        # If file path is provided, get the file from context cache
        if request.file_path:
            context_files = await context_cache.get_files_by_paths([request.file_path])
            if context_files:
                context["files"] = context_files
                # Find the file content to display
                for file in context_files:
                    if file.get("path") == request.file_path:
                        file_content = file.get("content")
                        break
        
        # Use prompt service to create an explanation prompt
        explanation_prompt = await prompt_service.create_code_explanation_prompt(
            code=request.code,
            language=request.language,
            detailed=request.detailed,
            file_path=request.file_path,
            context_query=request.context_query,
            file_content=file_content
        )
        
        # Log the prompt creation
        logger.debug(
            "Created explanation prompt",
            extra={
                "detailed": request.detailed,
                "has_context": bool(context),
                "has_file_path": bool(request.file_path)
            }
        )
        
        # Get explanation from AI using the prompt service-generated prompt
        explanation = await ai_client.explain_code(
            code=request.code,
            language=request.language,
            detailed=request.detailed,
            context=context,
            prompt=explanation_prompt
        )
        
        return CodeExplanationResponse(
            explanation=explanation,
            language=request.language
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            "Failed to explain code",
            exc_info=True,
            extra={
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain code: {str(e)}"
        )


@router.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(
    request: CodeAnalysisRequest,
    ai_client: Annotated[AIClient, Depends(get_ai_client)],
    context_cache: Annotated[ContextCacheService, Depends(get_context_cache_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)]
) -> CodeAnalysisResponse:
    """Analyze the provided code for issues and improvement opportunities."""
    try:
        # Prepare context
        context = {"file_path": request.file_path} if request.file_path else {}
        
        # Get analysis from AI
        analysis = await ai_client.analyze_code_issues(
            code=request.code,
            language=request.language,
            json_output=request.json_output,
            context=context
        )
        
        return CodeAnalysisResponse(
            analysis=analysis,
            language=request.language
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze code: {str(e)}"
        )


@router.post("/chat", response_model=CodeChatResponse)
async def chat_with_code(
    request: CodeChatRequest,
    ai_client: Annotated[AIClient, Depends(get_ai_client)],
    context_cache: Annotated[ContextCacheService, Depends(get_context_cache_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)]
) -> CodeChatResponse:
    """Chat with AI about code, providing context from the IDE."""
    try:
        # Prepare context
        context = {}
        
        # If specific files are provided, use them directly
        if request.context_files:
            file_paths = request.context_files
            # Get the files from context cache
            context_files = await context_cache.get_files_by_paths(file_paths)
            if context_files:
                context["files"] = context_files
        
        # If a context query is provided, use it to retrieve relevant context
        elif request.context_query:
            # Create a context query
            query = ContextQuery(
                query_text=request.context_query,
                languages=[request.language] if request.language else None,
                max_files=5,
                include_content=True
            )
            
            # Get relevant context
            relevant_context = await context_cache.query_context(query)
            if relevant_context and relevant_context.matches:
                context["files"] = relevant_context.matches
        
        # Add active file to context if provided
        if request.active_file:
            context["active_file"] = request.active_file
        
        # Get chat response from AI
        response = await ai_client.chat_with_code(
            prompt=request.prompt,
            code=request.code,
            language=request.language,
            context=context,
            stream=False
        )
        
        return CodeChatResponse(
            response=response
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chat with code: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_with_code_stream(
    request: CodeChatRequest,
    ai_client: Annotated[AIClient, Depends(get_ai_client)],
    context_cache: Annotated[ContextCacheService, Depends(get_context_cache_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)]
) -> StreamingResponse:
    """Chat with AI about code with streaming response, providing context from the IDE."""
    try:
        # Prepare context
        context = {}
        
        # If specific files are provided, use them directly
        if request.context_files:
            file_paths = request.context_files
            # Get the files from context cache
            context_files = await context_cache.get_files_by_paths(file_paths)
            if context_files:
                context["files"] = context_files
        
        # If a context query is provided, use it to retrieve relevant context
        elif request.context_query:
            # Create a context query
            query = ContextQuery(
                query_text=request.context_query,
                languages=[request.language] if request.language else None,
                max_files=5,
                include_content=True
            )
            
            # Get relevant context
            relevant_context = await context_cache.query_context(query)
            if relevant_context and relevant_context.matches:
                context["files"] = relevant_context.matches
        
        # Add active file to context if provided
        if request.active_file:
            context["active_file"] = request.active_file
        
        # Get chat response from AI with streaming
        stream = await ai_client.chat_with_code(
            prompt=request.prompt,
            code=request.code,
            language=request.language,
            context=context,
            stream=True
        )
        
        # Helper function to convert the stream to SSE format
        async def event_stream():
            try:
                async for chunk in stream:
                    yield f"data: {chunk}\n\n"
                yield "event: close\ndata: \n\n"
            except Exception as e:
                yield f"event: error\ndata: {str(e)}\n\n"
                yield "event: close\ndata: \n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream"
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chat with code: {str(e)}"
        )


@router.post("/test", response_model=CodeTestResponse)
async def generate_tests(
    request: CodeTestRequest,
    ai_client: Annotated[AIClient, Depends(get_ai_client)],
    context_cache: Annotated[ContextCacheService, Depends(get_context_cache_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)]
) -> CodeTestResponse:
    """Generate tests for the provided code."""
    try:
        # Prepare context
        context = {"file_path": request.file_path} if request.file_path else {}
        
        # Get tests from AI
        tests = await ai_client.generate_test(
            code=request.code,
            language=request.language,
            test_framework=request.test_framework,
            context=context
        )
        
        return CodeTestResponse(
            tests=tests,
            language=request.language,
            test_framework=request.test_framework
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tests: {str(e)}"
        )


@router.post("/generate/prefix", response_model=CharPrefixGenerationResponse, dependencies=[Depends(APIKey)])
async def generate_with_prefix(
    request: CharPrefixGenerationRequest,
    ai_client: Annotated[AIClient, Depends(get_ai_client)],
    context_cache: Annotated[ContextCacheService, Depends(get_context_cache_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)]
) -> CharPrefixGenerationResponse:
    """Generate code that starts with a specific character prefix."""
    try:
        # Check if we need to override the model type
        original_client_type = ai_client.llm_client_type
        model_used = original_client_type
        
        # If model_type is specified, validate it
        if request.model_type and request.model_type != original_client_type:
            # Log the model type override
            logging.info(
                "Overriding model type for character prefix generation",
                original_type=original_client_type,
                requested_type=request.model_type
            )
            
            # Currently, we don't actually switch the client, but we could if needed
            # This would require creating a new AIClient with the requested model type
            
            # Just log for now
            model_used = f"{original_client_type} (requested {request.model_type})"
        
        # Prepare context
        context = {}
        context_files = []
        
        # If specific files are provided, use them directly
        if request.context_files:
            file_paths = request.context_files
            # Get the files from context cache
            context_files = await context_cache.get_files_by_paths(file_paths)
            if context_files:
                context["files"] = context_files
        
        # If a context query is provided, use it to retrieve relevant context
        elif request.context_query:
            # Create a context query
            query = ContextQuery(
                query_text=request.context_query,
                languages=[request.language] if request.language else None,
                max_files=5,
                include_content=True
            )
            
            # Get relevant context
            relevant_context = await context_cache.query_context(query)
            if relevant_context and relevant_context.matches:
                context_files = relevant_context.matches
                context["files"] = context_files
        
        # Use prompt service to create a code generation prompt
        generation_prompt = await prompt_service.create_code_generation_prompt(
            generation_request=f"{request.prompt} (Must start with: {request.prefix})",
            language=request.language,
            context_query=request.context_query
        )
        
        # Log the prefix requirement
        logging.debug(
            "Generating code with character prefix",
            extra={
                "prefix": request.prefix,
                "language": request.language,
                "has_context": bool(context_files),
                "model_type": model_used
            }
        )
        
        # Generate the code using the character prefix method
        generated_code = await ai_client.generate_with_char_prefix(
            prompt=request.prompt,
            prefix=request.prefix,
            language=request.language,
            context=context,
            custom_prompt=generation_prompt,
            temperature=request.temperature,
            stream=False
        )
        
        return CharPrefixGenerationResponse(
            code=generated_code,
            language=request.language,
            prefix=request.prefix,
            model_used=model_used
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        logging.error(
            "Failed to generate code with prefix",
            exc_info=True,
            extra={
                "error": str(e),
                "prefix": request.prefix
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate code with prefix: {str(e)}"
        )


@router.post("/generate/prefix/stream", dependencies=[Depends(APIKey)])
async def generate_with_prefix_stream(
    request: CharPrefixGenerationRequest,
    ai_client: Annotated[AIClient, Depends(get_ai_client)],
    context_cache: Annotated[ContextCacheService, Depends(get_context_cache_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)]
) -> StreamingResponse:
    """Generate code with streaming response that starts with a specific character prefix."""
    try:
        # Check if we need to override the model type
        original_client_type = ai_client.llm_client_type
        
        # If model_type is specified, validate it
        if request.model_type and request.model_type != original_client_type:
            # Log the model type override
            logging.info(
                "Overriding model type for character prefix generation (streaming)",
                original_type=original_client_type,
                requested_type=request.model_type
            )
        
        # Prepare context
        context = {}
        
        # If specific files are provided, use them directly
        if request.context_files:
            file_paths = request.context_files
            # Get the files from context cache
            context_files = await context_cache.get_files_by_paths(file_paths)
            if context_files:
                context["files"] = context_files
        
        # If a context query is provided, use it to retrieve relevant context
        elif request.context_query:
            # Create a context query
            query = ContextQuery(
                query_text=request.context_query,
                languages=[request.language] if request.language else None,
                max_files=5,
                include_content=True
            )
            
            # Get relevant context
            relevant_context = await context_cache.query_context(query)
            if relevant_context and relevant_context.matches:
                context["files"] = relevant_context.matches
        
        # Generate the code with streaming and character prefix
        stream = await ai_client.generate_with_char_prefix(
            prompt=request.prompt,
            prefix=request.prefix,
            language=request.language,
            context=context,
            temperature=request.temperature,
            stream=True
        )
        
        # Helper function to convert the stream to SSE format
        async def event_stream():
            try:
                # Ensure the first chunk includes the prefix
                first_chunk = True
                async for chunk in stream:
                    if first_chunk:
                        # Make sure the chunk starts with the prefix
                        if not chunk.startswith(request.prefix):
                            chunk = request.prefix + chunk
                        first_chunk = False
                    
                    yield f"data: {chunk}\n\n"
                
                yield "event: close\ndata: \n\n"
            except Exception as e:
                yield f"event: error\ndata: {str(e)}\n\n"
                yield "event: close\ndata: \n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream"
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate code with prefix: {str(e)}"
        ) 