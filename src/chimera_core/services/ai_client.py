"""AI client service for Project Chimera.

This module provides a client for AI services used by Project Chimera,
including support for code generation, code explanation, and other AI-driven
features.
"""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union
import logging
from functools import lru_cache

import structlog

# Try to import OpenAI client
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Try to import Google Generative AI client
try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel
    from google.generativeai.types import GenerationConfig
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Import our own modules
from ..ai.char_prefix_openai import integrate_with_openai_client
from ..ai.char_prefix_gemini import GeminiCharacterPrefixSampler, GeminiTokenizerWrapper

# Set up logging
logger = structlog.get_logger(__name__)


class AIClient:
    """Client for AI services.
    
    This class provides a unified interface for interacting with various AI providers,
    including OpenAI and Google Generative AI (Gemini). It handles initialization,
    error handling, and provides methods for common AI tasks such as code generation
    and explanation.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        prompt_service = None
    ):
        """
        Initialize the AI client.
        
        Args:
            api_key: API key for the service
            model: Model name to use
            api_base: Base URL for the API
            api_version: API version to use
            max_tokens: Maximum number of tokens in a response
            temperature: Temperature for sampling
            prompt_service: Optional prompt service for getting prompts
        """
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.api_version = api_version
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.prompt_service = prompt_service
        
        # For Gemini and OpenAI client instances
        self.client = None
        self.llm_client_type = None
        
        # Initialize the appropriate client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate client based on settings."""
        # Determine client type from model name or api_base
        if "gpt" in self.model.lower() or (self.api_base and "openai" in self.api_base.lower()):
            self._initialize_openai_client()
        elif "gemini" in self.model.lower():
            self._initialize_gemini_client()
        else:
            # Default to OpenAI
            self._initialize_openai_client()
    
    def _initialize_openai_client(self):
        """Initialize the OpenAI client."""
        if not HAS_OPENAI:
            logger.error("Failed to import OpenAI package. Please install it with 'pip install openai'")
            raise ImportError("OpenAI package is required but not installed")
            
        try:
            # Set up the client
            client_args = {
                "api_key": self.api_key,
            }
            
            if self.api_base:
                client_args["base_url"] = self.api_base
            
            self.client = openai.AsyncOpenAI(**client_args)
            self.llm_client_type = "openai"
            
            logger.info(
                "OpenAI client initialized",
                model=self.model,
                api_base=self.api_base
            )
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
            raise
    
    def _initialize_gemini_client(self):
        """Initialize the Google Generative AI (Gemini) client."""
        if not HAS_GEMINI:
            logger.error("Failed to import Google Generative AI package. Please install it with 'pip install google-generativeai'")
            raise ImportError("Google Generative AI package is required but not installed")
            
        try:
            # Configure the Gemini API
            genai.configure(api_key=self.api_key)
            
            # Create a model instance
            generation_config = GenerationConfig(
                temperature=self.temperature,
                top_p=0.95,
                top_k=40,
                max_output_tokens=self.max_tokens
            )
            
            self.client = GenerativeModel(
                model_name=self.model,
                generation_config=generation_config
            )
            
            # Create the tokenizer wrapper with LRU caching
            self.tokenizer = GeminiTokenizerWrapper(
                vocab_size=50000,
                cache_size=1000
            )
            
            # Create the character prefix sampler
            self.char_prefix_sampler = GeminiCharacterPrefixSampler(
                model=self.client,
                candidates_per_step=10
            )
            
            self.llm_client_type = "gemini"
            
            logger.info(
                "Gemini client initialized",
                model=self.model
            )
        except Exception as e:
            logger.error("Failed to initialize Gemini client", error=str(e))
            raise
    
    async def close(self):
        """Close the client connection."""
        # OpenAI client doesn't require explicit closing
        # For Gemini, check if there's a close method in the future
        pass
    
    @lru_cache(maxsize=100)
    def _get_system_prompt(self, language: str) -> str:
        """
        Get system prompt for a language.
        
        Args:
            language: Programming language
            
        Returns:
            System prompt for the language
        """
        if self.prompt_service:
            try:
                return self.prompt_service.get_system_prompt(language)
            except Exception as e:
                logger.warning(
                    "Failed to get system prompt from prompt service",
                    language=language,
                    error=str(e)
                )
        
        # Default system prompt
        return f"You are an expert {language} developer. Provide clear, concise, and correct code."
    
    async def generate_code(
        self,
        prompt: str, 
        language: str = "python", 
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate code based on a prompt.
        
        Args:
            prompt: The prompt to generate code from
            language: The programming language to generate code in
            stream: Whether to stream the response
            **kwargs: Additional keyword arguments for the model
            
        Returns:
            Generated code or a generator if streaming
        """
        try:
            if self.llm_client_type == "openai":
                return await self._openai_generate_code(prompt, language, stream, **kwargs)
            elif self.llm_client_type == "gemini":
                return await self._gemini_generate_code(prompt, language, stream, **kwargs)
            else:
                raise ValueError(f"Unsupported LLM client type: {self.llm_client_type}")
        except Exception as e:
            logger.error(
                "Error generating code",
                error=str(e),
                error_type=type(e).__name__,
                prompt_length=len(prompt),
                language=language,
                stream=stream
            )
            if stream:
                async def error_generator():
                    yield f"Error generating code: {str(e)}"
                return error_generator()
            else:
                return f"Error generating code: {str(e)}"
    
    async def _openai_generate_code(
        self,
        prompt: str, 
        language: str = "python", 
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate code using OpenAI.
        
        Args:
            prompt: The prompt to generate code from
            language: The programming language
            stream: Whether to stream the response
            **kwargs: Additional arguments for the model
            
        Returns:
            Generated code or a generator if streaming
        """
        system_message = self._get_system_prompt(language)
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        response_format = kwargs.pop("response_format", {"type": "text"})
        
        completion_args = {
            "model": kwargs.pop("model", self.model),
            "messages": messages,
            "temperature": kwargs.pop("temperature", self.temperature),
            "max_tokens": kwargs.pop("max_tokens", self.max_tokens),
            "response_format": response_format,
            "stream": stream,
            **kwargs
        }
        
        if stream:
            async def stream_generator():
                try:
                    response_stream = await self.client.chat.completions.create(**completion_args)
                    async for chunk in response_stream:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                except Exception as e:
                    logger.error("Error in OpenAI streaming", error=str(e))
                    yield f"Error in streaming: {str(e)}"
            
            return stream_generator()
        else:
            response = await self.client.chat.completions.create(**completion_args)
            return response.choices[0].message.content
    
    async def _gemini_generate_code(
        self, 
        prompt: str, 
        language: str = "python", 
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate code using Gemini.
        
        Args:
            prompt: The prompt to generate code from
            language: The programming language
            stream: Whether to stream the response
            **kwargs: Additional arguments for the model
            
        Returns:
            Generated code or a generator if streaming
        """
        system_message = self._get_system_prompt(language)
        
        # Combine system message and prompt
        full_prompt = f"{system_message}\n\n{prompt}"
        
        # Set up generation config with any overrides
        generation_config = GenerationConfig(
            temperature=kwargs.pop("temperature", self.temperature),
            top_p=kwargs.pop("top_p", 0.95),
            top_k=kwargs.pop("top_k", 40),
            max_output_tokens=kwargs.pop("max_tokens", self.max_tokens),
            **kwargs
        )
        
        if stream:
            async def stream_generator():
                try:
                    response_stream = await self.client.generate_content_async(
                        full_prompt, 
                        generation_config=generation_config,
                        stream=True
                    )
                    
                    async for chunk in response_stream:
                        if hasattr(chunk, "text") and chunk.text:
                            yield chunk.text
                        elif hasattr(chunk, "parts") and chunk.parts:
                            for part in chunk.parts:
                                if hasattr(part, "text") and part.text:
                                    yield part.text
                except Exception as e:
                    logger.error("Error in Gemini streaming", error=str(e))
                    yield f"Error in streaming: {str(e)}"
            
            return stream_generator()
            else:
            response = await self.client.generate_content_async(
                full_prompt, 
                generation_config=generation_config
            )
            
            return self._extract_text_from_response(response)
    
    def _extract_text_from_response(self, response: Any) -> str:
        """
        Extract text from a Gemini response.
        
        Args:
            response: The Gemini response object
            
        Returns:
            Extracted text from the response
        """
        if hasattr(response, "text"):
            return response.text
        elif hasattr(response, "parts"):
            return "".join(part.text for part in response.parts if hasattr(part, "text"))
        elif hasattr(response, "candidates") and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, "content") and candidate.content:
                    if hasattr(candidate.content, "parts") and candidate.content.parts:
                        return "".join(part.text for part in candidate.content.parts if hasattr(part, "text"))
        
        # Fallback - log and return empty string
        logger.warning("Could not extract text from Gemini response", response_type=type(response).__name__)
        return ""
    
    async def explain_code(
        self,
        code: str, 
        language: str = "python", 
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Explain a piece of code.
        
        Args:
            code: The code to explain
            language: The programming language
            stream: Whether to stream the response
            **kwargs: Additional keyword arguments for the model
            
        Returns:
            Explanation or a generator if streaming
        """
        prompt = f"""
        Please explain the following {language} code:
        
        ```{language}
        {code}
        ```
        
        Provide a clear and concise explanation of what the code does, and any important aspects or potential issues.
        """
        
        try:
            if self.llm_client_type == "openai":
                return await self._openai_generate_code(prompt, language, stream, **kwargs)
            elif self.llm_client_type == "gemini":
                return await self._gemini_generate_code(prompt, language, stream, **kwargs)
            else:
                raise ValueError(f"Unsupported LLM client type: {self.llm_client_type}")
        except Exception as e:
            logger.error(
                "Error explaining code",
                error=str(e),
                error_type=type(e).__name__,
                code_length=len(code),
                language=language,
                stream=stream
            )
            if stream:
                async def error_generator():
                    yield f"Error explaining code: {str(e)}"
                return error_generator()
            else:
                return f"Error explaining code: {str(e)}"
    
    async def generate_with_char_prefix(
        self, 
        context: str, 
        char_prefix: str, 
        language: str = "python",
        model_type: str = None,
        stream: bool = False, 
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate code completion that starts with a specific character prefix.
        
        This uses the Character Prefix Conditioning algorithm to ensure the generated
        code starts with the specified prefix.
        
        Args:
            context: The text context before the generation
            char_prefix: The character prefix that the generation must start with
            language: The programming language for the generation
            model_type: The model type to use (defaults to client's configured model)
            stream: Whether to stream the response tokens
            **kwargs: Additional parameters for the model
            
        Returns:
            Generated text with the specified character prefix, or a generator if streaming
        """
        logger.info("Generating with character prefix constraint", 
                   context_length=len(context), 
                   prefix=char_prefix,
                   language=language,
                   model_type=model_type or self.llm_client_type,
                   stream=stream)
        
        # If streaming is requested, we need to handle differently
        # as sampling with character prefix conditioning requires 
        # access to all token probabilities at each step
        if stream:
            # Just prepend the prefix to the prompt as a simple fallback
            # and hope the model respects it
            logger.warning(
                "Streaming not fully supported with character prefix conditioning. "
                "Using simple prefix constraint as fallback"
            )
            
            prompt = f"{context}\n{char_prefix}"
            async for chunk in self.generate_code(prompt, language, stream=True, **kwargs):
                yield chunk
            return
        
        # For non-streaming, use the appropriate character prefix implementation
        actual_model_type = model_type or self.llm_client_type
        
        try:
            # Use the OpenAI-specific implementation if available and appropriate
            if actual_model_type.lower() == "openai" and HAS_OPENAI:
                from ..ai.char_prefix_openai import integrate_with_openai_client
                
                # Prepare any base prompts through the prompt service if available
                system_message = None
                if self.prompt_service:
                    system_prompt = self.prompt_service.get_system_prompt(language)
                    system_message = {"role": "system", "content": system_prompt}
                
                # Set up model parameters
                model_params = {
                    "model": kwargs.get("model", self.model),
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 150),
                    "top_p": kwargs.get("top_p", 0.95),
                    "system_message": system_message
                }
                
                result = await integrate_with_openai_client(
                    self.client, 
                    char_prefix, 
                    context, 
                    model_params
                )
                
                logger.info("Successfully generated with OpenAI character prefix conditioning",
                           result_length=len(result))
                return result
            
            # Use the Gemini-specific implementation
            elif actual_model_type.lower() == "gemini" and HAS_GEMINI:
                # Use our instance of GeminiCharacterPrefixSampler
                
                # Sample with the character prefix constraint
                result_tokens = await self.char_prefix_sampler.sample_with_prefix(
                    prefix=char_prefix,
                    max_tokens=kwargs.get("max_tokens", 150),
                    temperature=kwargs.get("temperature", 0.7),
                    top_p=kwargs.get("top_p", 0.95),
                    top_k=kwargs.get("top_k", 40),
                    lm_params={"prompt_prefix": context}
                )
                
                # Convert token IDs to text
                result = self.char_prefix_sampler.tokenizer.decode(result_tokens)
                
                logger.info("Successfully generated with Gemini character prefix conditioning",
                           result_length=len(result))
                return result
            
            else:
                # Generic fallback for other models or if specific implementations not available
                logger.warning(
                    "No specific character prefix implementation available for model type",
                    model_type=actual_model_type,
                    fallback="simple prefix constraint"
                )
                
                # Simple fallback: just prepend the prefix to the output
                result = await self.generate_code(context, language, stream=False, **kwargs)
                return char_prefix + result
        
        except Exception as e:
            logger.error(
                "Error in character prefix generation",
                error=str(e),
                error_type=type(e).__name__,
                model_type=actual_model_type
            )
            
            # Last resort fallback: just prepend the prefix to a simple completion
            result = await self.generate_code(context, language, stream=False, **kwargs)
            return char_prefix + result 