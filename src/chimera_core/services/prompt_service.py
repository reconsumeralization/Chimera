"""Prompt management service for Project Chimera.

This module provides a service for managing and filling AI prompt templates
with context data from the context cache.
"""

import structlog
from typing import Any, Dict, List, Optional, Union

from ...schemas.context import ContextQuery, ContextSnapshot, FileData
from ..prompts import templates
from .context_cache import ContextCacheService

# Set up logging
logger = structlog.get_logger(__name__)

class PromptService:
    """Service for managing AI prompts with context integration."""
    
    def __init__(self, context_cache_service: ContextCacheService):
        """
        Initialize the prompt service.
        
        Args:
            context_cache_service: The context cache service for retrieving context
        """
        self.context_cache = context_cache_service
        self.log = logger.bind(service="prompt_service")
        self.log.info("Prompt service initialized")
    
    async def create_code_explanation_prompt(
        self,
        code_content: str,
        language: str,
        detailed: bool = True,
        context_query: Optional[str] = None,
        file_path: Optional[str] = None,
        max_context_files: int = 3
    ) -> Dict[str, str]:
        """
        Create a prompt for code explanation.
        
        Args:
            code_content: The code to explain
            language: Programming language of the code
            detailed: Whether to generate a detailed explanation
            context_query: Optional query to find relevant context
            file_path: Optional file path for the code
            max_context_files: Maximum number of context files to include
            
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        template = templates.CODE_EXPLANATION_DETAILED if detailed else templates.CODE_EXPLANATION_BRIEF
        
        # Start with basic context
        context = {
            "code_content": code_content,
            "language": language,
        }
        
        # Add file path if provided
        if file_path:
            context["active_file_path"] = file_path
            
            # Try to get full file content
            try:
                snapshot = await self.context_cache.get_latest_snapshot()
                if snapshot:
                    for file in snapshot.files:
                        if file.path == file_path and file.content:
                            context["active_file_content"] = file.content
                            break
            except Exception as e:
                self.log.warning("Failed to retrieve file content from context cache", 
                                error=str(e), file_path=file_path)
        
        # Get relevant context if query provided
        if context_query and self.context_cache:
            try:
                relevant_files = await self.context_cache.get_relevant_context_for_task(
                    task_description=context_query,
                    max_files=max_context_files,
                    include_content=True
                )
                
                if relevant_files:
                    context_files = []
                    for file in relevant_files:
                        if isinstance(file, dict):
                            context_files.append(file)
                        elif isinstance(file, FileData):
                            context_files.append({
                                "path": file.path,
                                "content": file.content or "(Content not available)",
                                "language": file.language or "unknown"
                            })
                    
                    context["context_files"] = context_files
            except Exception as e:
                self.log.warning("Failed to retrieve relevant context", 
                                error=str(e), context_query=context_query)
        
        # Fill the template with context
        return templates.fill_template(template, context)
    
    async def create_code_generation_prompt(
        self,
        generation_request: str,
        language: str,
        file_path: Optional[str] = None,
        insertion_point_code: Optional[str] = None,
        context_query: Optional[str] = None,
        max_context_files: int = 5
    ) -> Dict[str, str]:
        """
        Create a prompt for code generation.
        
        Args:
            generation_request: The request describing what code to generate
            language: Programming language for the generated code
            file_path: Optional file path for context
            insertion_point_code: Optional code at the insertion point
            context_query: Optional query to find relevant context
            max_context_files: Maximum number of context files to include
            
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        template = templates.CODE_GENERATION
        
        # Start with basic context
        context = {
            "generation_request": generation_request,
            "language": language,
            "insertion_point_code": insertion_point_code or "",
        }
        
        # Add file path if provided
        if file_path:
            context["active_file_path"] = file_path
        
        # Get relevant context if query provided
        if context_query and self.context_cache:
            try:
                relevant_files = await self.context_cache.get_relevant_context_for_task(
                    task_description=f"{context_query} {generation_request}",
                    max_files=max_context_files,
                    include_content=True
                )
                
                if relevant_files:
                    context_files = []
                    for file in relevant_files:
                        if isinstance(file, dict):
                            context_files.append(file)
                        elif isinstance(file, FileData):
                            context_files.append({
                                "path": file.path,
                                "content": file.content or "(Content not available)",
                                "language": file.language or "unknown"
                            })
                    
                    context["context_files"] = context_files
            except Exception as e:
                self.log.warning("Failed to retrieve relevant context", 
                                error=str(e), context_query=context_query)
        
        # Fill the template with context
        return templates.fill_template(template, context)
    
    async def create_code_review_prompt(
        self,
        code_content: str,
        language: str,
        file_path: Optional[str] = None,
        json_output: bool = False,
        context_query: Optional[str] = None,
        max_context_files: int = 3
    ) -> Dict[str, str]:
        """
        Create a prompt for code review.
        
        Args:
            code_content: The code to review
            language: Programming language of the code
            file_path: Optional file path for the code
            json_output: Whether to request JSON-formatted output
            context_query: Optional query to find relevant context
            max_context_files: Maximum number of context files to include
            
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        template = templates.CODE_ANALYSIS_JSON if json_output else templates.CODE_REVIEW
        
        # Start with basic context
        context = {
            "code_content": code_content,
            "language": language,
        }
        
        # Add file path if provided
        if file_path:
            context["active_file_path"] = file_path
        
        # Get diagnostics if file path provided
        if file_path and self.context_cache:
            try:
                snapshot = await self.context_cache.get_latest_snapshot()
                if snapshot:
                    file_diagnostics = []
                    for diag in snapshot.diagnostics:
                        if diag.file_path == file_path:
                            file_diagnostics.append({
                                "line": diag.line,
                                "message": diag.message,
                                "severity": diag.severity,
                                "file_path": diag.file_path,
                                "column": diag.column,
                                "source": diag.source,
                                "code": diag.code
                            })
                    
                    if file_diagnostics:
                        context["diagnostics"] = file_diagnostics
            except Exception as e:
                self.log.warning("Failed to retrieve diagnostics from context cache", 
                                error=str(e), file_path=file_path)
        
        # Fill the template with context
        return templates.fill_template(template, context)
    
    async def create_test_generation_prompt(
        self,
        code_content: str,
        language: str,
        test_framework: str,
        file_path: Optional[str] = None,
        context_query: Optional[str] = None,
        max_context_files: int = 3
    ) -> Dict[str, str]:
        """
        Create a prompt for test generation.
        
        Args:
            code_content: The code to test
            language: Programming language of the code
            test_framework: Testing framework to use
            file_path: Optional file path for the code
            context_query: Optional query to find relevant context
            max_context_files: Maximum number of context files to include
            
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        template = templates.TEST_GENERATION
        
        # Start with basic context
        context = {
            "code_content": code_content,
            "language": language,
            "test_framework": test_framework,
        }
        
        # Add file path if provided
        if file_path:
            context["active_file_path"] = file_path
        
        # Get relevant context if query provided
        if context_query and self.context_cache:
            try:
                relevant_files = await self.context_cache.get_relevant_context_for_task(
                    task_description=f"Create tests for: {context_query}",
                    max_files=max_context_files,
                    include_content=True
                )
                
                if relevant_files:
                    context_files = []
                    for file in relevant_files:
                        if isinstance(file, dict):
                            context_files.append(file)
                        elif isinstance(file, FileData):
                            context_files.append({
                                "path": file.path,
                                "content": file.content or "(Content not available)",
                                "language": file.language or "unknown"
                            })
                    
                    context["context_files"] = context_files
            except Exception as e:
                self.log.warning("Failed to retrieve relevant context", 
                                error=str(e), context_query=context_query)
        
        # Fill the template with context
        return templates.fill_template(template, context)
    
    async def create_chat_prompt(
        self,
        user_query: str,
        file_path: Optional[str] = None,
        selection_content: Optional[str] = None,
        language: Optional[str] = None,
        context_query: Optional[str] = None,
        max_context_files: int = 3
    ) -> Dict[str, str]:
        """
        Create a prompt for general chat/Q&A with context.
        
        Args:
            user_query: The user's query
            file_path: Optional active file path
            selection_content: Optional selected code content
            language: Optional programming language
            context_query: Optional query to find relevant context
            max_context_files: Maximum number of context files to include
            
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        template = templates.GENERAL_CODING_ASSISTANT
        
        # Start with basic context
        context = {
            "user_query": user_query,
            "selection_content": selection_content or "",
            "language": language or "plaintext",
        }
        
        # Add file path if provided
        if file_path:
            context["active_file_path"] = file_path
        
        # Get diagnostics from context cache
        if self.context_cache:
            try:
                snapshot = await self.context_cache.get_latest_snapshot()
                if snapshot:
                    # Include relevant diagnostics
                    all_diagnostics = []
                    for diag in snapshot.diagnostics:
                        # If we have a file path, only include diagnostics for that file
                        if not file_path or diag.file_path == file_path:
                            all_diagnostics.append({
                                "line": diag.line,
                                "message": diag.message,
                                "severity": diag.severity,
                                "file_path": diag.file_path,
                                "column": diag.column,
                                "source": diag.source,
                                "code": diag.code
                            })
                    
                    if all_diagnostics:
                        context["diagnostics"] = all_diagnostics
            except Exception as e:
                self.log.warning("Failed to retrieve diagnostics from context cache", 
                                error=str(e))
        
        # Get relevant context based on the query
        query_for_context = context_query if context_query else user_query
        if query_for_context and self.context_cache:
            try:
                relevant_files = await self.context_cache.get_relevant_context_for_task(
                    task_description=query_for_context,
                    max_files=max_context_files,
                    include_content=True
                )
                
                if relevant_files:
                    context_files = []
                    for file in relevant_files:
                        if isinstance(file, dict):
                            context_files.append(file)
                        elif isinstance(file, FileData):
                            context_files.append({
                                "path": file.path,
                                "content": file.content or "(Content not available)",
                                "language": file.language or "unknown"
                            })
                    
                    context["context_files"] = context_files
            except Exception as e:
                self.log.warning("Failed to retrieve relevant context", 
                                error=str(e), query=query_for_context)
        
        # Fill the template with context
        return templates.fill_template(template, context)
    
    async def create_relevance_assessment_prompt(
        self,
        task_description: str,
        available_files: List[Dict[str, Any]],
        max_files: int = 5
    ) -> Dict[str, str]:
        """
        Create a prompt for assessing file relevance to a task.
        
        Args:
            task_description: Description of the task
            available_files: List of available files with snippets
            max_files: Maximum number of files to select
            
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        template = templates.CONTEXT_RELEVANCE_ASSESSMENT
        
        # Format available files into JSON-like string
        files_str = "[\n"
        for i, file in enumerate(available_files):
            files_str += f"  {{\n"
            files_str += f'    "path": "{file.get("path", "unknown")}",\n'
            files_str += f'    "language": "{file.get("language", "unknown")}",\n'
            
            # Add a short snippet of the content if available
            content = file.get("content", "")
            if content:
                # Limit content to ~500 chars
                if len(content) > 500:
                    content = content[:500] + "..."
                # Escape quotes and newlines
                content = content.replace('"', '\\"').replace('\n', '\\n')
                files_str += f'    "snippet": "{content}"\n'
            else:
                files_str += f'    "snippet": "(Content not available)"\n'
            
            files_str += f"  }}{'' if i == len(available_files) - 1 else ','}\n"
        files_str += "]"
        
        context = {
            "task_description": task_description,
            "max_files": max_files,
            "available_files": files_str,
        }
        
        return templates.fill_template(template, context)
    
    async def create_context_summarization_prompt(
        self,
        content: str,
        target_sentence_count: int = 3
    ) -> Dict[str, str]:
        """
        Create a prompt for summarizing context content.
        
        Args:
            content: The content to summarize
            target_sentence_count: Target number of sentences in the summary
            
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        template = templates.CONTEXT_SUMMARIZATION
        
        context = {
            "content": content,
            "target_sentence_count": target_sentence_count,
        }
        
        return templates.fill_template(template, context) 