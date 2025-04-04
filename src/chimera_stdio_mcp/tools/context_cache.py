"""Context cache tool for MCP."""
import structlog
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseTool
from chimera_core.services.context_cache import ContextCacheService
from chimera_core.factory import ServiceFactory
from src.schemas.context import ContextQuery, ContextSnapshot

logger = structlog.get_logger(__name__)

class ContextCacheTool(BaseTool):
    """Tool for interacting with the context cache."""
    
    TOOL_NAME = "context_cache"
    DESCRIPTION = "Queries and manages the context cache service."
    
    def __init__(self):
        """Initialize the context cache tool."""
        super().__init__()
        self.context_cache = None
    
    async def _get_context_cache(self) -> ContextCacheService:
        """Get or initialize the context cache service."""
        if not self.context_cache:
            try:
                # Get the context cache service from the factory
                self.context_cache = ServiceFactory.get_context_cache_service()
                self.log.info("Retrieved context cache service from factory")
            except ValueError:
                # Create context cache service if not available
                self.log.info("Context cache service not available, creating new instance via factory")
                factory = ServiceFactory()
                self.context_cache = await factory.create_context_cache_service()
        
        return self.context_cache
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the context_cache tool.
        
        Args:
            params: Dictionary containing:
                - operation: The operation to perform (query, stats, clear, etc.)
                - query_params: Parameters for query operation (optional)
                - time_range_start: Start of time range for queries (optional)
                - time_range_end: End of time range for queries (optional)
                - max_files: Maximum number of files to return (optional)
                - file_patterns: File patterns to include (optional)
        
        Returns:
            Dictionary with operation results
        """
        valid, error = self.validate_params(params, ["operation"])
        if not valid:
            return {"error": error}
        
        operation = params.get("operation", "").lower()
        
        try:
            # Get the context cache service
            context_cache = await self._get_context_cache()
            
            # Perform the requested operation
            if operation == "query":
                return await self._handle_query(context_cache, params)
            elif operation == "stats":
                return await self._handle_stats(context_cache)
            elif operation == "clear":
                return await self._handle_clear(context_cache)
            elif operation == "store":
                return await self._handle_store(context_cache, params)
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            self.log.exception("Error executing context cache operation", operation=operation, error=str(e))
            return {"error": f"Error executing operation: {str(e)}"}
    
    async def _handle_query(self, context_cache: ContextCacheService, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle query operation."""
        # Build query from parameters
        query = ContextQuery(
            query_text=params.get("query_text"),
            file_patterns=params.get("file_patterns"),
            exclude_patterns=params.get("exclude_patterns"),
            languages=params.get("languages"),
            max_files=params.get("max_files"),
            include_content=params.get("include_content", True),
        )
        
        # Parse time range if provided
        if "time_range_start" in params:
            if isinstance(params["time_range_start"], str):
                query.time_range_start = datetime.fromisoformat(params["time_range_start"])
            elif isinstance(params["time_range_start"], int):
                # Assume Unix timestamp (seconds since epoch)
                query.time_range_start = datetime.fromtimestamp(params["time_range_start"])
        
        if "time_range_end" in params:
            if isinstance(params["time_range_end"], str):
                query.time_range_end = datetime.fromisoformat(params["time_range_end"])
            elif isinstance(params["time_range_end"], int):
                # Assume Unix timestamp (seconds since epoch)
                query.time_range_end = datetime.fromtimestamp(params["time_range_end"])
        
        # Execute query
        response = await context_cache.query_context(query)
        
        # Convert to serializable format
        return {
            "query": {
                "query_text": response.query.query_text,
                "file_patterns": response.query.file_patterns,
                "exclude_patterns": response.query.exclude_patterns,
                "languages": response.query.languages,
                "max_files": response.query.max_files,
                "include_content": response.query.include_content,
                "time_range_start": response.query.time_range_start.isoformat() if response.query.time_range_start else None,
                "time_range_end": response.query.time_range_end.isoformat() if response.query.time_range_end else None,
            },
            "matches": [
                {
                    "path": file.path,
                    "language": file.language,
                    "size_bytes": file.size_bytes,
                    "last_modified": file.last_modified.isoformat() if file.last_modified else None,
                    "is_open": file.is_open,
                    "is_dirty": file.is_dirty,
                    # Include content only if it's not too large (to avoid huge responses)
                    "content": file.content[:10000] + "..." if file.content and len(file.content) > 10000 else file.content,
                }
                for file in response.matches
            ],
            "total_matches": response.total_matches,
            "has_more": response.has_more,
            "query_time_ms": response.query_time_ms,
        }
    
    async def _handle_stats(self, context_cache: ContextCacheService) -> Dict[str, Any]:
        """Handle stats operation."""
        stats = await context_cache.get_stats()
        
        # Convert to serializable format
        serializable_stats = {
            "total_snapshots": stats["total_snapshots"],
            "total_files": stats["total_files"],
            "cache_size_bytes": stats["cache_size_bytes"],
            "cache_size_mb": round(stats["cache_size_bytes"] / (1024 * 1024), 2) if stats["cache_size_bytes"] else 0,
            "last_update": stats["last_update"].isoformat() if stats["last_update"] else None,
            "query_count": stats["query_count"],
            "hit_count": stats["hit_count"],
            "miss_count": stats["miss_count"],
        }
        
        return {"stats": serializable_stats}
    
    async def _handle_clear(self, context_cache: ContextCacheService) -> Dict[str, Any]:
        """Handle clear operation."""
        success = await context_cache.clear_cache()
        return {"success": success}
    
    async def _handle_store(self, context_cache: ContextCacheService, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle store operation."""
        valid, error = self.validate_params(params, ["snapshot"])
        if not valid:
            return {"error": error}
        
        snapshot_data = params["snapshot"]
        
        try:
            # If snapshot is already a ContextSnapshot, use it directly
            if isinstance(snapshot_data, ContextSnapshot):
                snapshot = snapshot_data
            else:
                # If snapshot_data is a string, try to parse it as JSON
                if isinstance(snapshot_data, str):
                    try:
                        snapshot_data = json.loads(snapshot_data)
                    except json.JSONDecodeError:
                        return {"error": "Invalid JSON in snapshot data"}
                
                # Convert files dictionary to list if necessary
                if (
                    isinstance(snapshot_data, dict) 
                    and "files" in snapshot_data 
                    and isinstance(snapshot_data["files"], dict)
                ):
                    # Convert dict of files to list of FileData
                    files_dict = snapshot_data["files"]
                    snapshot_data["files"] = [
                        {
                            "path": file_path,
                            **file_data
                        } if isinstance(file_data, dict) and "path" not in file_data else file_data
                        for file_path, file_data in files_dict.items()
                    ]
                
                # Create ContextSnapshot from the data
                try:
                    snapshot = ContextSnapshot.model_validate(snapshot_data)
                except Exception as e:
                    return {"error": f"Invalid snapshot data: {str(e)}"}
            
            # Store the snapshot
            snapshot_id = await context_cache.store_snapshot(snapshot)
            
            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "file_count": len(snapshot.files),
                "diagnostic_count": len(snapshot.diagnostics)
            }
        except Exception as e:
            self.log.exception("Error storing snapshot", error=str(e))
            return {"error": f"Error storing snapshot: {str(e)}"}
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get the JSON schema for the context_cache tool."""
        return {
            "name": cls.TOOL_NAME,
            "description": cls.DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The operation to perform (query, stats, clear, store)",
                        "enum": ["query", "stats", "clear", "store"]
                    },
                    "query_text": {
                        "type": "string",
                        "description": "Text to search for in files"
                    },
                    "file_patterns": {
                        "type": "array",
                        "description": "Glob patterns for files to include",
                        "items": {
                            "type": "string"
                        }
                    },
                    "exclude_patterns": {
                        "type": "array",
                        "description": "Glob patterns for files to exclude",
                        "items": {
                            "type": "string"
                        }
                    },
                    "languages": {
                        "type": "array",
                        "description": "Programming languages to include",
                        "items": {
                            "type": "string"
                        }
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "Maximum number of files to return"
                    },
                    "include_content": {
                        "type": "boolean",
                        "description": "Whether to include file content in the results"
                    },
                    "time_range_start": {
                        "type": "string",
                        "description": "Start of time range (ISO format or Unix timestamp)"
                    },
                    "time_range_end": {
                        "type": "string",
                        "description": "End of time range (ISO format or Unix timestamp)"
                    },
                    "snapshot": {
                        "type": "object",
                        "description": "Snapshot data to store (for store operation)"
                    }
                },
                "required": ["operation"]
            }
        } 