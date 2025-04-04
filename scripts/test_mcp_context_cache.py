#!/usr/bin/env python3
"""Test script for the MCP context cache tool."""
import asyncio
import json
import logging
import os
import sys
from pprint import pprint

# Add src to the Python path to allow importing from the packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.chimera_stdio_mcp.tools.context_cache import ContextCacheTool
from chimera_core.services.context_cache import ContextCacheService, ContextCacheOptions
from src.schemas.context import ContextSnapshot, FileData, DiagnosticItem
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("TestMCPContextCache")

async def create_test_context_snapshot() -> ContextCacheService:
    """Create a test context snapshot and return the service."""
    logger.info("Creating test context cache service...")
    
    # Create a context cache service with an in-memory cache
    options = ContextCacheOptions(
        cache_dir="./test_cache",
        max_snapshots=10,
        ttl_days=1,
        max_cache_size_mb=10,
        enable_db_storage=True,
        enable_persistent_storage=True,
    )
    
    context_cache = ContextCacheService(options)
    
    # Create a test snapshot
    snapshot = ContextSnapshot(
        workspace_root="/test/workspace",
        active_file="/test/workspace/main.py",
        files={
            "main.py": FileData(
                path="main.py",
                content="print('Hello, world!')",
                language="python",
                last_modified=datetime.now(),
                size_bytes=100,
                is_open=True,
                is_dirty=False,
            ),
            "utils.py": FileData(
                path="utils.py",
                content="def add(a, b):\n    return a + b",
                language="python",
                last_modified=datetime.now(),
                size_bytes=150,
                is_open=False,
                is_dirty=False,
            ),
            "index.html": FileData(
                path="index.html",
                content="<!DOCTYPE html>\n<html>\n<body>\n<h1>Hello</h1>\n</body>\n</html>",
                language="html",
                last_modified=datetime.now(),
                size_bytes=200,
                is_open=False,
                is_dirty=False,
            ),
        },
        diagnostics=[
            DiagnosticItem(
                file_path="main.py",
                message="Missing docstring",
                severity="info",
                line=1,
                column=0,
                source="pylint",
                code="C0111",
            ),
        ],
        metadata={
            "editor": "VS Code",
            "test": True,
        },
    )
    
    # Store the snapshot
    snapshot_id = await context_cache.store_snapshot(snapshot)
    logger.info(f"Created test snapshot with ID: {snapshot_id}")
    
    return context_cache

async def test_context_cache_tool():
    """Test the context cache tool."""
    logger.info("Testing context cache tool...")
    
    # Create test context and cache it
    context_cache = await create_test_context_snapshot()
    
    # Create the tool
    tool = ContextCacheTool()
    tool.context_cache = context_cache
    
    # Test stats operation
    logger.info("Testing stats operation...")
    stats_result = await tool.execute({"operation": "stats"})
    logger.info("Stats result:")
    pprint(stats_result)
    
    # Test query operation (all files)
    logger.info("Testing query operation (all files)...")
    query_result = await tool.execute({
        "operation": "query",
        "include_content": True,
    })
    logger.info(f"Query result: {len(query_result.get('matches', []))} files found")
    pprint(query_result)
    
    # Test query operation (filter by language)
    logger.info("Testing query operation (python files)...")
    query_python_result = await tool.execute({
        "operation": "query",
        "languages": ["python"],
        "include_content": True,
    })
    logger.info(f"Python files query result: {len(query_python_result.get('matches', []))} files found")
    pprint(query_python_result)
    
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
        await test_context_cache_tool()
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 