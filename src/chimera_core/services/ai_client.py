"""AI client service for Project Chimera.

This module provides a service for interacting with AI models,
primarily using OpenAI API for code understanding and generation.
"""
import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union, cast

import aiohttp
import structlog

from ..config import get_settings
from .prompt_service import PromptService

# Set up logging
logger = structlog.get_logger(__name__)

# Default model configuration
DEFAULT_MODEL = "gpt-4"  # Default model


class AIClient:
    """
    Service for interacting with AI models.
    
    This service provides methods for making requests to AI models,
    particularly OpenAI's models, for tasks such as code understanding,
    generation, and analysis.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo",
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        prompt_service = None
    ):
        """
        Initialize the AI client.
        
        Args:
            api_key: API key for the AI service
            model: Model to use for completions
            api_base: Base URL for the API
            api_version: API version
            temperature: Temperature for completions
            max_tokens: Maximum tokens for completions
            prompt_service: Optional PromptService for generating structured prompts
        """
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.api_version = api_version
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_service = prompt_service
        self.client = None
        self.llm_client_type = "unknown"
        self.templates = None
        
        # Initialize logger
        self.logger = logger
        
        # Import templates
        try:
            from src.chimera_core.prompts.templates import Templates
            self.templates = Templates()
        except ImportError:
            self.logger.warning("Could not import prompt templates, using defaults")
            # Will need to implement fallback templates
        
        # Initialize the client
        self._initialize_client()
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self._session
    
    async def generate_code(
        self, 
        prompt: str, 
        language: str = "",
        context: Optional[Dict[str, Any]] = None,
        custom_prompt: Optional[Dict[str, str]] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate code based on the prompt and optional context.
        
        Args:
            prompt: The user's request for code generation
            language: The programming language for the code
            context: Optional context information
            custom_prompt: Optional custom prompt from the PromptService
            stream: Whether to stream the response
            
        Returns:
            The generated code or a stream of code chunks
        """
        try:
            if not prompt.strip():
                return "" if not stream else self._empty_stream()
            
            # Prepare the prompt parameters
            system_prompt = custom_prompt["system"] if custom_prompt and "system" in custom_prompt else (
                self.templates.CODE_GENERATION_SYSTEM
            )
            
            user_prompt = custom_prompt["user"] if custom_prompt and "user" in custom_prompt else (
                self.templates.CODE_GENERATION_USER
            )
            
            # Format the user prompt if it's the default
            if user_prompt == self.templates.CODE_GENERATION_USER:
                user_prompt = user_prompt.format(
                    language=language if language else "code",
                    request=prompt
                )
            
            # Get the code from the AI
            result = await self._generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                stream=stream
            )
            
            return result
        
        except Exception as e:
            self.logger.error(
                "Failed to generate code",
                error=str(e),
                exc_info=True
            )
            if stream:
                return self._error_stream(f"Error generating code: {str(e)}")
            return f"Error generating code: {str(e)}"
    
    async def explain_code(
        self, 
        code: str, 
        language: str = "", 
        detailed: bool = True, 
        context: Optional[Dict[str, Any]] = None,
        prompt: Optional[Dict[str, str]] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Explain the given code with optional context.
        
        Args:
            code: The code to explain
            language: The programming language of the code
            detailed: Whether to generate a detailed explanation
            context: Optional context information
            prompt: Optional custom prompt from the PromptService
            stream: Whether to stream the response
            
        Returns:
            The explanation text or a stream of explanation chunks
        """
        try:
            if not code.strip():
                return "" if not stream else self._empty_stream()
            
            # Prepare the prompt parameters
            system_prompt = prompt["system"] if prompt and "system" in prompt else (
                self.templates.CODE_EXPLANATION_DETAILED_SYSTEM if detailed else 
                self.templates.CODE_EXPLANATION_BRIEF_SYSTEM
            )
            
            user_prompt = prompt["user"] if prompt and "user" in prompt else (
                self.templates.CODE_EXPLANATION_DETAILED_USER if detailed else 
                self.templates.CODE_EXPLANATION_BRIEF_USER
            )
            
            # Format the user prompt
            user_prompt = user_prompt.format(
                language=language if language else "code",
                code=code
            )
            
            # Get the explanation from the AI
            result = await self._generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                stream=stream
            )
            
            return result
        
        except Exception as e:
            self.logger.error(
                "Failed to explain code",
                error=str(e),
                exc_info=True
            )
            if stream:
                return self._error_stream(f"Error explaining code: {str(e)}")
            return f"Error explaining code: {str(e)}"
    
    async def analyze_code_issues(
        self, 
        code: str, 
        language: str = "python", 
        context: Optional[Dict[str, Any]] = None,
        json_output: bool = True,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze code for issues and improvements.
        
        Args:
            code: Code to analyze
            language: Programming language of the code
            context: Optional context data (e.g., file contents)
            json_output: Whether to request JSON output
            model_override: Optional model to use instead of the default
            
        Returns:
            Analysis results (as dict if json_output=True, otherwise as string)
        """
        # Use the prompt service if available
        if self.prompt_service:
            analysis_context = {
                "code_content": code,
                "language": language,
                "json_output": json_output
            }
            
            # Add context if provided
            if context:
                file_path = context.get("file_path", None)
                if file_path:
                    analysis_context["file_path"] = file_path
                
                context_query = context.get("context_query", None)
                if context_query:
                    analysis_context["context_query"] = context_query
            
            # Generate the structured prompt
            filled_prompts = await self.prompt_service.create_code_review_prompt(**analysis_context)
            
            system_prompt = filled_prompts.get("system_prompt", "")
            user_prompt = filled_prompts.get("user_prompt", f"Analyze this {language} code for issues:\n\n```{language}\n{code}\n```")
        else:
            # Fallback to basic prompt structure
            if json_output:
                system_prompt = f"""You are an expert {language} code analyzer. Analyze the provided code for bugs, security issues, performance problems, and style issues.
                Return your analysis as a valid JSON object with the following structure:
                {{
                "issues": [
                    {{
                    "severity": "high|medium|low",
                    "type": "bug|security|performance|style",
                    "description": "Clear description of the issue.",
                    "location": {{ "start_line": <line_num>, "end_line": <line_num> }}
                    }}
                ],
                "suggestions": [
                    "Suggestion 1",
                    "Suggestion 2"
                ],
                "summary": "Brief overall assessment"
                }}
                Do not include any text outside the JSON object."""
            else:
                system_prompt = f"You are an expert {language} code reviewer. Analyze the provided code for bugs, security issues, performance problems, and style issues. Provide clear, specific feedback on identified issues and suggestions for improvement."
            
            # Construct a full prompt with context if available
            user_prompt = f"Analyze this {language} code:\n\n```{language}\n{code}\n```"
            if context and "files" in context:
                context_str = "Additional context files:\n\n"
                for file in context["files"]:
                    file_path = file.get("path", "unknown")
                    file_content = file.get("content", "").strip()
                    context_str += f"File: {file_path}\n```\n{file_content}\n```\n\n"
                user_prompt = f"{user_prompt}\n\n{context_str}"
        
        # Prepare messages for the API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response_text = await self._get_completion(messages, model_override)
            
            # If JSON output is requested, parse the response
            if json_output:
                try:
                    # Try to extract JSON from the response (in case there's additional text)
                    import re
                    json_match = re.search(r'({.*})', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                    
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse AI response as JSON", response=response_text[:100])
                    return {
                        "error": "Failed to parse AI response as JSON",
                        "raw_response": response_text
                    }
            else:
                return {"analysis": response_text}
        except Exception as e:
            self.logger.error("Error analyzing code", error=str(e))
            return {"error": f"Error analyzing code: {str(e)}"}
    
    async def generate_test(
        self,
        code: str,
        language: str,
        test_framework: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        model_override: Optional[str] = None
    ) -> str:
        """
        Generate tests for the provided code.
        
        Args:
            code: Code to test
            language: Programming language of the code
            test_framework: Testing framework to use (e.g., pytest, jest)
            context: Optional context data
            model_override: Optional model to use instead of the default
            
        Returns:
            Generated test code
        """
        # Default test framework based on language if not provided
        if not test_framework:
            framework_mapping = {
                "python": "pytest",
                "javascript": "jest",
                "typescript": "jest",
                "java": "junit",
                "csharp": "nunit"
            }
            test_framework = framework_mapping.get(language.lower(), "")
        
        # Use the prompt service if available
        if self.prompt_service:
            test_context = {
                "code_content": code,
                "language": language,
                "test_framework": test_framework
            }
            
            # Add context if provided
            if context:
                file_path = context.get("file_path", None)
                if file_path:
                    test_context["file_path"] = file_path
                
                context_query = context.get("context_query", None)
                if context_query:
                    test_context["context_query"] = context_query
            
            # Generate the structured prompt
            filled_prompts = await self.prompt_service.create_test_generation_prompt(**test_context)
            
            system_prompt = filled_prompts.get("system_prompt", "")
            user_prompt = filled_prompts.get("user_prompt", f"Generate {test_framework} tests for this {language} code:\n\n```{language}\n{code}\n```")
        else:
            # Fallback to basic prompt structure
            system_prompt = f"You are an expert in writing tests for {language} using {test_framework}. Generate comprehensive, maintainable tests that cover the main functionality, edge cases, and error handling scenarios. Return ONLY the test code without explanations or markdown formatting."
            
            # Construct a full prompt with context if available
            user_prompt = f"Generate {test_framework} tests for this {language} code:\n\n```{language}\n{code}\n```"
            if context and "files" in context:
                context_str = "Additional context files:\n\n"
                for file in context["files"]:
                    file_path = file.get("path", "unknown")
                    file_content = file.get("content", "").strip()
                    context_str += f"File: {file_path}\n```\n{file_content}\n```\n\n"
                user_prompt = f"{user_prompt}\n\n{context_str}"
        
        # Prepare messages for the API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self._get_completion(messages, model_override)
            # Clean up markdown code block formatting if present
            import re
            clean_response = re.sub(r'^```\w*\n|```$', '', response, flags=re.MULTILINE).strip()
            return clean_response
        except Exception as e:
            self.logger.error("Error generating tests", error=str(e))
            return f"Error generating tests: {str(e)}"
    
    async def chat_with_code(
        self,
        messages: List[Dict[str, str]],
        code_context: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        model_override: Optional[str] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Chat with the AI about code.
        
        Args:
            messages: List of previous messages
            code_context: Optional code context
            context: Optional context data
            model_override: Optional model to use instead of the default
            stream: Whether to stream the response
            
        Returns:
            Chat response or async generator streaming the response
        """
        # Extract the user query from the last message
        user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_query = msg.get("content", "")
                break
        
        # Use the prompt service if available and there's a user query
        if self.prompt_service and user_query:
            chat_context = {
                "user_query": user_query
            }
            
            # Add code selection if provided
            if code_context:
                chat_context["selection_content"] = code_context
            
            # Add other context if provided
            if context:
                file_path = context.get("file_path", None)
                if file_path:
                    chat_context["file_path"] = file_path
                
                language = context.get("language", None)
                if language:
                    chat_context["language"] = language
                
                context_query = context.get("context_query", None)
                if context_query:
                    chat_context["context_query"] = context_query
            
            # Generate the structured prompt
            filled_prompts = await self.prompt_service.create_chat_prompt(**chat_context)
            
            # Replace the system message and last user message
            system_prompt = filled_prompts.get("system_prompt", "")
            full_user_prompt = filled_prompts.get("user_prompt", user_query)
            
            # Construct new messages preserving the conversation history
            new_messages = [{"role": "system", "content": system_prompt}]
            for i, msg in enumerate(messages):
                if i == len(messages) - 1 and msg.get("role") == "user":
                    # Replace the last user message with our enhanced prompt
                    new_messages.append({"role": "user", "content": full_user_prompt})
                else:
                    # Keep other messages as is
                    new_messages.append(msg)
            
            messages = new_messages
        else:
            # Ensure there's a system message
            has_system = any(msg.get("role") == "system" for msg in messages)
            if not has_system:
                system_msg = {"role": "system", "content": "You are Chimera, an expert AI coding assistant. You provide helpful, concise responses to coding questions, suggesting best practices and efficient solutions."}
                messages = [system_msg] + messages
            
            # Add code context if provided
            if code_context and messages[-1].get("role") == "user":
                # Append code context to the last user message
                last_msg = messages[-1]
                new_content = f"{last_msg['content']}\n\nCode context:\n```\n{code_context}\n```"
                messages[-1]["content"] = new_content
        
        # Use streaming if requested
        if stream:
            return self._stream_completion(messages, model_override)
        else:
            try:
                response = await self._get_completion(messages, model_override)
                return response
            except Exception as e:
                self.logger.error("Error in chat", error=str(e))
                return f"Error: {str(e)}"
    
    async def _get_completion(
        self, 
        messages: List[Dict[str, str]], 
        model_override: Optional[str] = None
    ) -> str:
        """
        Get a completion from the API.
        
        Args:
            messages: List of message objects
            model_override: Optional model to use
            
        Returns:
            The completion text
        """
        model = model_override or self.model
        
        try:
            if self.llm_client_type == "openai":
                # Handle OpenAI completion
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                return response.choices[0].message.content.strip()
            
            elif self.llm_client_type == "vertexai":
                # Handle Vertex AI completion (implementation depends on the client)
                # This is a placeholder
                self.logger.warning("Vertex AI implementation is a placeholder")
                return "Vertex AI implementation is a placeholder"
            
            else:
                raise ValueError(f"Unsupported LLM client type: {self.llm_client_type}")
        
        except Exception as e:
            self.logger.error(
                "Error getting completion",
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _stream_completion(
        self, 
        messages: List[Dict[str, str]],
        model_override: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion from the AI model.
        
        Args:
            messages: List of messages
            model_override: Optional model to use instead of the default
            
        Yields:
            Chunks of the AI model response
        """
        model = model_override or self.model
        url = f"{self.api_base}/chat/completions"
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True
        }
        
        session = await self.get_session()
        try:
            async with session.post(url, json=data, timeout=self.timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error("API request failed", status=response.status, response=error_text)
                    raise Exception(f"API request failed with status {response.status}: {error_text}")
                
                # Stream the response chunks
                async for line in response.content:
                    line = line.strip()
                    if not line or line == b"data: [DONE]":
                        continue
                    
                    if not line.startswith(b"data: "):
                        continue
                    
                    try:
                        json_data = json.loads(line[6:])  # Skip "data: "
                        if "choices" in json_data and len(json_data["choices"]) > 0:
                            content = json_data["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
        except aiohttp.ClientError as e:
            self.logger.error("HTTP error", error=str(e))
            raise Exception(f"HTTP error: {e}")
    
    async def get_relevant_context(
        self,
        query: str,
        available_files: List[Dict[str, Any]],
        max_files: int = 3,
        model_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the most relevant files for a given query.
        
        Args:
            query: The query to find relevant files for
            available_files: List of available files with snippets
            max_files: Maximum number of files to return
            model_override: Optional model to use instead of the default
            
        Returns:
            List of the most relevant files
        """
        if not self.prompt_service:
            self.logger.warning("Prompt service not available for relevance assessment")
            # Return a subset of files based on basic heuristics
            import re
            
            # Extract potential keywords from the query
            keywords = re.findall(r'\b[a-zA-Z0-9_]+\b', query.lower())
            scored_files = []
            
            for file in available_files:
                score = 0
                path = file.get("path", "").lower()
                content = file.get("content", "").lower()
                
                # Score based on keywords in path and content
                for keyword in keywords:
                    if keyword in path:
                        score += 3
                    if content and keyword in content:
                        score += 1
                
                # Bonus for currently open files
                if file.get("is_open", False):
                    score += 5
                
                scored_files.append((score, file))
            
            # Sort by score and return the top files
            scored_files.sort(reverse=True, key=lambda x: x[0])
            return [file for _, file in scored_files[:max_files]]
        
        # Use the prompt service for better relevance assessment
        try:
            filled_prompts = await self.prompt_service.create_relevance_assessment_prompt(
                task_description=query,
                available_files=available_files,
                max_files=max_files
            )
            
            system_prompt = filled_prompts.get("system_prompt", "")
            user_prompt = filled_prompts.get("user_prompt", "")
            
            # Prepare messages for the API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response_text = await self._get_completion(messages, model_override)
            
            try:
                # Extract JSON from the response text
                import re
                json_match = re.search(r'({.*})', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
                
                # Parse the JSON response
                response_data = json.loads(response_text)
                
                if "selected_files" in response_data and isinstance(response_data["selected_files"], list):
                    # Extract the selected file paths
                    selected_paths = [item.get("path") for item in response_data["selected_files"] if "path" in item]
                    
                    # Get the full file objects that match the selected paths
                    selected_files = []
                    for path in selected_paths:
                        for file in available_files:
                            if file.get("path") == path:
                                selected_files.append(file)
                                break
                    
                    return selected_files
            except (json.JSONDecodeError, KeyError) as e:
                self.log.error("Error parsing relevance assessment response", error=str(e))
        
        except Exception as e:
            self.log.error("Error in relevance assessment", error=str(e))
        
        # Fallback to returning the first max_files files
        return available_files[:max_files]
    
    async def close(self) -> None:
        """Close the client and free resources."""
        try:
            # Close any client-specific resources
            if self.llm_client_type == "openai" and hasattr(self.client, "close"):
                await self.client.close()
            
            # Set client to None
            self.client = None
            
            self.logger.info("AIClient closed successfully")
        except Exception as e:
            self.logger.error(
                "Error closing AIClient",
                error=str(e),
                exc_info=True
            )
    
    async def _empty_stream(self) -> AsyncGenerator[str, None]:
        """Return an empty stream."""
        # Just yield an empty string and then stop
        yield ""
        return
    
    async def _error_stream(self, error_message: str) -> AsyncGenerator[str, None]:
        """Return a stream with an error message."""
        yield error_message
        return
    
    async def _generate(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate text from the model.
        
        Args:
            system_prompt: The system prompt
            user_prompt: The user prompt
            stream: Whether to stream the response
            
        Returns:
            The generated text or a stream of text chunks
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if stream:
            return self._stream_completion(messages)
        else:
            return await self._get_completion(messages)
    
    async def _stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        model_override: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion from the API.
        
        Args:
            messages: List of message objects
            model_override: Optional model to use
            
        Returns:
            AsyncGenerator yielding text chunks
        """
        model = model_override or self.model
        
        try:
            if self.llm_client_type == "openai":
                # Handle OpenAI streaming
                stream = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            yield delta.content
            
            elif self.llm_client_type == "vertexai":
                # Handle Vertex AI streaming (implementation depends on the client)
                # This is a placeholder that would need to be implemented based on the Vertex API
                yield "Streaming not implemented for Vertex AI"
            
            else:
                # Generic implementation for other APIs (implement based on the client)
                yield "Streaming not implemented for this LLM provider"
        
        except Exception as e:
            self.logger.error(
                "Error streaming completion",
                error=str(e),
                exc_info=True
            )
            yield f"Error: {str(e)}"
    
    def _initialize_client(self):
        """Initialize the appropriate client based on settings."""
        # Determine client type from model name or api_base
        if "gpt" in self.model.lower() or (self.api_base and "openai" in self.api_base.lower()):
            self._initialize_openai_client()
        elif "vertex" in (self.api_base or "").lower() or "gemini" in self.model.lower():
            self._initialize_vertexai_client()
        else:
            # Default to OpenAI
            self._initialize_openai_client()
    
    def _initialize_openai_client(self):
        """Initialize the OpenAI client."""
        try:
            import openai
            
            # Set up the client
            client_args = {
                "api_key": self.api_key,
            }
            
            if self.api_base:
                client_args["base_url"] = self.api_base
            
            self.client = openai.AsyncOpenAI(**client_args)
            self.llm_client_type = "openai"
            
            self.logger.info(
                "OpenAI client initialized",
                model=self.model,
                api_base=self.api_base
            )
        except ImportError:
            self.logger.error("Failed to import OpenAI package. Please install it with 'pip install openai'")
            raise
        except Exception as e:
            self.logger.error("Failed to initialize OpenAI client", error=str(e))
            raise
    
    def _initialize_vertexai_client(self):
        """Initialize the Vertex AI client."""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            # Set up the client - implementation depends on the specific Vertex AI client
            # This is a placeholder
            self.client = {"type": "vertexai"}  # Replace with actual client initialization
            self.llm_client_type = "vertexai"
            
            self.logger.info(
                "Vertex AI client initialized",
                model=self.model
            )
        except ImportError:
            self.logger.error("Failed to import Vertex AI package. Please install it with 'pip install google-cloud-aiplatform'")
            raise
        except Exception as e:
            self.logger.error("Failed to initialize Vertex AI client", error=str(e))
            raise 