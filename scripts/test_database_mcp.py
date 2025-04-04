#!/usr/bin/env python
"""
Test script for the Database MCP Server.
"""

import asyncio
import json
import logging
import sys
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_database_mcp")

# Sample schema definitions (typically in the real server)
SAMPLE_SCHEMAS = {
    "users": {
        "columns": [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "username", "type": "VARCHAR(50)", "nullable": False},
            {"name": "email", "type": "VARCHAR(100)", "nullable": False},
            {"name": "created_at", "type": "TIMESTAMP", "nullable": False}
        ],
        "description": "User accounts table"
    },
    "products": {
        "columns": [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "VARCHAR(100)", "nullable": False},
            {"name": "price", "type": "DECIMAL(10,2)", "nullable": False},
            {"name": "category", "type": "VARCHAR(50)", "nullable": True}
        ],
        "description": "Product catalog table"
    }
}

# Mock tool classes for testing
class BaseTool:
    """Mock base tool class."""
    
    def validate_params(self, params, required_params):
        """Validate required parameters."""
        missing = [param for param in required_params if param not in params]
        if missing:
            error_msg = f"Missing required parameters: {', '.join(missing)}"
            return False, error_msg
        return True, None

class MockDatabaseQueryTool(BaseTool):
    """Mock database query tool for testing."""
    
    # Mock SQL safety patterns
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
    
    async def execute(self, params):
        """Execute mock database query."""
        valid, error = self.validate_params(params, ["query"])
        if not valid:
            return {"error": error}
        
        query = params.get("query", "")
        database = params.get("database", "default")
        
        logger.info(f"Querying database: {database}")
        logger.info(f"SQL query: {query}")
        
        # Validate SQL for safety
        if not self._is_safe_query(query):
            error_msg = "Only read-only SELECT queries are allowed"
            logger.warning("Unsafe query rejected")
            return {"error": error_msg}
        
        # Simulate query execution
        if "users" in query.lower():
            return {
                "columns": ["id", "username", "email", "created_at"],
                "rows": [
                    [1, "alice", "alice@example.com", "2025-01-15 10:00:00"],
                    [2, "bob", "bob@example.com", "2025-01-20 14:30:00"],
                    [3, "charlie", "charlie@example.com", "2025-02-05 09:15:00"]
                ],
                "row_count": 3,
                "database": database,
                "elapsed_ms": 15
            }
        elif "products" in query.lower():
            return {
                "columns": ["id", "name", "price", "category"],
                "rows": [
                    [101, "Laptop", 1299.99, "Electronics"],
                    [102, "Headphones", 199.99, "Electronics"],
                    [103, "Desk Chair", 249.99, "Furniture"]
                ],
                "row_count": 3,
                "database": database,
                "elapsed_ms": 12
            }
        else:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "database": database,
                "elapsed_ms": 5
            }
    
    def _is_safe_query(self, query):
        """Check if a SQL query is safe (read-only)."""
        # Check that it starts with SELECT
        if not self.ALLOWED_SQL_PATTERN.match(query):
            return False
            
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_SQL_PATTERNS:
            if pattern.search(query):
                return False
                
        return True

class TestClient:
    """Simple client for testing the Database MCP."""
    
    def __init__(self):
        """Initialize the test client."""
        self.next_id = 1
        self.db_tool = MockDatabaseQueryTool()
    
    async def request(self, method, params=None):
        """Simulate sending a request to the server."""
        request_id = str(self.next_id)
        self.next_id += 1
        
        if params is None:
            params = {}
        
        logger.info(f"Sending request: {method}")
        
        # For testing purposes, call the tools directly
        if method == "callTool":
            tool_name = params.get("name", "")
            tool_params = params.get("params", {})
            
            logger.info(f"Calling tool: {tool_name}")
            
            if tool_name == "database_query":
                return await self.db_tool.execute(tool_params)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        elif method == "listResources":
            # Simulate resource listing
            resources = []
            for name, schema in SAMPLE_SCHEMAS.items():
                resources.append({
                    "name": name,
                    "description": schema.get("description", "")
                })
                
            return {"resources": resources}
            
        elif method == "readResource":
            # Simulate resource reading
            resource_name = params.get("name", "")
            
            if resource_name in SAMPLE_SCHEMAS:
                return {
                    "content": json.dumps(SAMPLE_SCHEMAS[resource_name], indent=2),
                    "mimeType": "application/json"
                }
            else:
                return {"error": f"Resource not found: {resource_name}"}
                
        else:
            return {"error": f"Unsupported method: {method}"}

async def test_resource_listing():
    """Test listing database schema resources."""
    client = TestClient()
    
    logger.info("\n\nTesting resource listing...")
    
    result = await client.request("listResources")
    logger.info(f"Available resources:\n{json.dumps(result, indent=2)}")
    
    return result

async def test_resource_reading():
    """Test reading database schema resources."""
    client = TestClient()
    
    logger.info("\n\nTesting resource reading...")
    
    # Read users schema
    result = await client.request("readResource", {"name": "users"})
    logger.info(f"Users schema:\n{result.get('content', '')}")
    
    # Read products schema
    result = await client.request("readResource", {"name": "products"})
    logger.info(f"Products schema:\n{result.get('content', '')}")
    
    return result

async def test_database_query():
    """Test the database query tool."""
    client = TestClient()
    
    logger.info("\n\nTesting database query...")
    
    # Test a SELECT query on users
    params = {
        "name": "database_query",
        "params": {
            "query": "SELECT * FROM users",
            "database": "default"
        }
    }
    
    result = await client.request("callTool", params)
    logger.info(f"Users query result:\n{json.dumps(result, indent=2)}")
    
    # Test a SELECT query on products
    params = {
        "name": "database_query",
        "params": {
            "query": "SELECT * FROM products",
            "database": "default"
        }
    }
    
    result = await client.request("callTool", params)
    logger.info(f"Products query result:\n{json.dumps(result, indent=2)}")
    
    # Test safety with a forbidden query
    logger.info("\n\nTesting SQL safety...")
    params = {
        "name": "database_query",
        "params": {
            "query": "DELETE FROM users",
            "database": "default"
        }
    }
    
    result = await client.request("callTool", params)
    logger.info(f"Unsafe query result:\n{json.dumps(result, indent=2)}")
    
    return result

async def main():
    """Run all tests."""
    await test_resource_listing()
    await test_resource_reading()
    await test_database_query()

if __name__ == "__main__":
    asyncio.run(main()) 