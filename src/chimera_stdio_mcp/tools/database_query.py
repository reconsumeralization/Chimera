"""Database query tool for executing read-only SQL queries through MCP."""
import json
import structlog
import asyncio
from typing import Any, Dict, List, Optional, Union
import time
import re

from .base import BaseTool

logger = structlog.get_logger(__name__)

class DatabaseQueryTool(BaseTool):
    """
    Tool for executing read-only SQL queries.
    
    This tool allows for safe execution of SQL SELECT queries against
    configured database connections.
    """
    
    TOOL_NAME = "database_query"
    DESCRIPTION = "Executes read-only SQL queries against configured databases."
    
    # Regular expressions for SQL safety validation
    ALLOWED_SQL_PATTERN = re.compile(r"^\s*SELECT\s+", re.IGNORECASE)
    FORBIDDEN_SQL_PATTERNS = [
        re.compile(r"\s*INSERT\s+", re.IGNORECASE),
        re.compile(r"\s*UPDATE\s+", re.IGNORECASE),
        re.compile(r"\s*DELETE\s+", re.IGNORECASE),
        re.compile(r"\s*DROP\s+", re.IGNORECASE),
        re.compile(r"\s*ALTER\s+", re.IGNORECASE),
        re.compile(r"\s*CREATE\s+", re.IGNORECASE),
        re.compile(r"\s*GRANT\s+", re.IGNORECASE),
        re.compile(r"\s*TRUNCATE\s+", re.IGNORECASE),
        re.compile(r";.*", re.IGNORECASE)  # Prevent multiple statements
    ]
    
    def __init__(self):
        """Initialize the database query tool."""
        super().__init__()
        self.log = logger.bind(tool="database_query")
        
        # Placeholder for DB connection - in a real implementation, 
        # this would be configured from environment variables or settings
        self._db_config = None
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a database query tool request."""
        try:
            # Basic parameters validation
            valid, error = self.validate_params(params, ["query"])
            if not valid:
                return {"error": error}
            
            # Extract parameters
            query = params.get("query", "")
            database = params.get("database", "default")
            
            # Log the request (excluding sensitive content)
            self.log.info(
                "Database query requested",
                database=database,
                query_length=len(query)
            )
            
            # Validate SQL for safety
            if not self._is_safe_query(query):
                error_msg = "Only read-only SELECT queries are allowed"
                self.log.warning("Unsafe query rejected", query=query)
                return {"error": error_msg}
            
            # Execute the query
            start_time = time.time()
            
            try:
                # In a real implementation, this would use a database client
                # to execute the query. For now, we'll simulate a response.
                result = await self._execute_query(database, query)
                
                # Log successful completion
                elapsed_time = time.time() - start_time
                self.log.info(
                    "Query executed successfully",
                    elapsed_time_ms=int(elapsed_time * 1000),
                    row_count=len(result.get("rows", [])),
                    database=database
                )
                
                return {
                    "columns": result.get("columns", []),
                    "rows": result.get("rows", []),
                    "row_count": len(result.get("rows", [])),
                    "database": database,
                    "elapsed_ms": int(elapsed_time * 1000)
                }
                
            except Exception as e:
                # Handle database-specific errors
                error_msg = f"Error executing query: {str(e)}"
                self.log.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            self.log.exception("Error in database query tool", error=str(e))
            return {"error": f"Error in database query: {str(e)}"}
    
    def _is_safe_query(self, query: str) -> bool:
        """
        Check if a SQL query is safe (read-only).
        
        Args:
            query: The SQL query to validate
            
        Returns:
            bool: True if the query is a safe SELECT statement, False otherwise
        """
        # Check that it starts with SELECT
        if not self.ALLOWED_SQL_PATTERN.match(query):
            return False
            
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_SQL_PATTERNS:
            if pattern.search(query):
                return False
                
        return True
    
    async def _execute_query(self, database: str, query: str) -> Dict[str, Any]:
        """
        Execute a SQL query against the specified database.
        
        Args:
            database: The database identifier
            query: The SQL query to execute
            
        Returns:
            Dict containing columns and rows
        """
        # In a real implementation, this would execute the query using 
        # a proper database client (e.g., asyncpg, aiomysql)
        
        # For demonstration purposes, return mock data
        if "users" in query.lower():
            return {
                "columns": ["id", "username", "email", "created_at"],
                "rows": [
                    [1, "alice", "alice@example.com", "2025-01-15 10:00:00"],
                    [2, "bob", "bob@example.com", "2025-01-20 14:30:00"],
                    [3, "charlie", "charlie@example.com", "2025-02-05 09:15:00"]
                ]
            }
        elif "products" in query.lower():
            return {
                "columns": ["id", "name", "price", "category"],
                "rows": [
                    [101, "Laptop", 1299.99, "Electronics"],
                    [102, "Headphones", 199.99, "Electronics"],
                    [103, "Desk Chair", 249.99, "Furniture"]
                ]
            }
        else:
            # Default empty result
            return {
                "columns": [],
                "rows": []
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Return the JSON schema for this tool."""
        return {
            "name": cls.TOOL_NAME,
            "description": cls.DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (must be a SELECT statement)"
                    },
                    "database": {
                        "type": "string",
                        "description": "Database identifier to query against"
                    }
                },
                "required": ["query"]
            }
        } 