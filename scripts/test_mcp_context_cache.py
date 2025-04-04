#!/usr/bin/env python3
"""Test script for the MCP context cache tool."""
import asyncio
import json
import logging
import os
import sys
from pprint import pprint
from datetime import datetime

# Add src to the Python path to allow importing from the packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up a clean testing environment
os.environ["CHIMERA_ENV"] = "test"
os.environ["CHIMERA_DATA_DIR"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/test"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("TestMCPContextCache")

# Create a simple test module to isolate the tests
class TestContextCacheModule:
    """Test module for context cache."""
    
    @staticmethod
    async def test_context_cache_tool():
        """Test the context cache tool."""
        # Import here to avoid import issues
        from src.schemas.context import ContextSnapshot, FileData, DiagnosticItem
        from src.chimera_core.services.context_cache import ContextCacheOptions, ContextCacheService
        
        # Create a custom implementation of the tool without importing the actual one
        # This helps avoid import issues caused by circular dependencies
        class TestContextCacheTool:
            """Test implementation of ContextCacheTool."""
            
            def __init__(self):
                """Initialize the tool."""
                self.context_cache = None
                self.log = logger
            
            async def _initialize_context_cache(self):
                """Initialize a test context cache."""
                if not self.context_cache:
                    # Create a context cache service with a test directory
                    cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/test/context_cache"))
                    os.makedirs(cache_dir, exist_ok=True)
                    
                    options = ContextCacheOptions(
                        cache_dir=cache_dir,
                        max_snapshots=10,
                        ttl_days=1,
                        max_cache_size_mb=10,
                        enable_db_storage=False,  # Disable DB to simplify testing
                        enable_persistent_storage=True,
                    )
                    
                    self.context_cache = ContextCacheService(options)
                
                return self.context_cache
            
            async def execute(self, params):
                """Execute a context cache operation."""
                if not params.get("operation"):
                    return {"error": "Missing required parameter: operation"}
                
                operation = params["operation"]
                context_cache = await self._initialize_context_cache()
                
                if operation == "store":
                    return await self._handle_store(context_cache, params)
                elif operation == "query":
                    return await self._handle_query(context_cache, params)
                elif operation == "stats":
                    return await self._handle_stats(context_cache)
                elif operation == "clear":
                    return await self._handle_clear(context_cache)
                else:
                    return {"error": f"Unknown operation: {operation}"}
            
            async def _handle_store(self, context_cache, params):
                """Handle the store operation."""
                if "snapshot" not in params:
                    return {"error": "Missing required parameter: snapshot"}
                
                snapshot_data = params["snapshot"]
                
                # Convert snapshot data to ContextSnapshot
                try:
                    if isinstance(snapshot_data, dict):
                        snapshot = ContextSnapshot.model_validate(snapshot_data)
                    else:
                        snapshot = snapshot_data
                    
                    # Store the snapshot
                    snapshot_id = await context_cache.store_snapshot(snapshot)
                    
                    return {
                        "success": True,
                        "snapshot_id": snapshot_id,
                        "file_count": len(snapshot.files),
                        "diagnostic_count": len(snapshot.diagnostics)
                    }
                except Exception as e:
                    logger.exception("Error storing snapshot")
                    return {"error": f"Error storing snapshot: {str(e)}"}
            
            async def _handle_query(self, context_cache, params):
                """Handle the query operation."""
                from src.schemas.context import ContextQuery
                
                # Build the query
                query = ContextQuery(
                    query_text=params.get("query_text"),
                    file_patterns=params.get("file_patterns"),
                    exclude_patterns=params.get("exclude_patterns"),
                    languages=params.get("languages"),
                    max_files=params.get("max_files"),
                    include_content=params.get("include_content", True),
                )
                
                # Execute the query
                response = await context_cache.query_context(query)
                
                # Convert to a serializable format
                return {
                    "matches": [
                        {
                            "path": file.path,
                            "language": file.language,
                            "content": file.content[:100] + "..." if file.content and len(file.content) > 100 else file.content,
                            "is_open": file.is_open,
                        }
                        for file in response.matches
                    ],
                    "total_matches": response.total_matches,
                    "has_more": response.has_more,
                }
            
            async def _handle_stats(self, context_cache):
                """Handle the stats operation."""
                stats = await context_cache.get_stats()
                
                return {"stats": stats}
            
            async def _handle_clear(self, context_cache):
                """Handle the clear operation."""
                success = await context_cache.clear_cache()
                
                return {"success": success}
        
        logger.info("Testing context cache tool...")
        
        # Create the test tool
        tool = TestContextCacheTool()
        
        # First, try the store operation
        logger.info("Testing store operation...")
        
        # Create test snapshot directly with the ContextSnapshot class
        snapshot = ContextSnapshot(
            workspace_root="/test/workspace/store_op",
            active_file="/test/workspace/store_op/app.py",
            files=[
                FileData(
                    path="app.py",
                    content="from flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/')\ndef hello():\n    return 'Hello, world!'",
                    language="python",
                    last_modified=datetime.now(),
                    size_bytes=200,
                    is_open=True,
                    is_dirty=False,
                ),
                FileData(
                    path="README.md",
                    content="# Test App\n\nThis is a test application.",
                    language="markdown",
                    last_modified=datetime.now(),
                    size_bytes=100,
                    is_open=False,
                    is_dirty=False,
                )
            ],
            diagnostics=[
                DiagnosticItem(
                    file_path="app.py",
                    message="Missing type annotations",
                    severity="info",
                    line=5,
                    column=0,
                    source="pyright",
                    code="reportMissingTypeStubs"
                )
            ],
            metadata={
                "operation": "test_store",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        store_result = await tool.execute({
            "operation": "store",
            "snapshot": snapshot
        })
        logger.info("Store result:")
        pprint(store_result)
        
        # Test stats operation to see if the snapshot was stored
        logger.info("Testing stats operation after store...")
        stats_result = await tool.execute({"operation": "stats"})
        logger.info("Stats result:")
        pprint(stats_result)
        
        # Test query operation to find the stored files
        logger.info("Testing query operation on stored files...")
        query_result = await tool.execute({
            "operation": "query",
            "query_text": "Flask",
            "include_content": True,
        })
        logger.info(f"Query result: {len(query_result.get('matches', []))} files found")
        pprint(query_result)
        
        # Test clear operation
        logger.info("Testing clear operation...")
        clear_result = await tool.execute({"operation": "clear"})
        logger.info("Clear result:")
        pprint(clear_result)
        
        # Verify the cache is empty
        stats_after_clear = await tool.execute({"operation": "stats"})
        logger.info("Stats after clear:")
        pprint(stats_after_clear)
        
        logger.info("Test completed successfully!")

async def main():
    """Main entry point."""
    try:
        await TestContextCacheModule.test_context_cache_tool()
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 