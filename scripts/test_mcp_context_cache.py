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
    
    # Create the tool
    tool = ContextCacheTool()
    
    # First, try the store operation
    logger.info("Testing store operation...")
    snapshot = {
        "workspace_root": "/test/workspace/store_op",
        "active_file": "/test/workspace/store_op/app.py",
        "files": {
            "app.py": {
                "path": "app.py",
                "content": "from flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/')\ndef hello():\n    return 'Hello, world!'",
                "language": "python",
                "last_modified": datetime.now().isoformat(),
                "size_bytes": 200,
                "is_open": True,
                "is_dirty": False,
            },
            "README.md": {
                "path": "README.md",
                "content": "# Test App\n\nThis is a test application.",
                "language": "markdown",
                "last_modified": datetime.now().isoformat(),
                "size_bytes": 100,
                "is_open": False,
                "is_dirty": False,
            }
        },
        "diagnostics": [
            {
                "file_path": "app.py",
                "message": "Missing type annotations",
                "severity": "info",
                "line": 5,
                "column": 0,
                "source": "pyright",
                "code": "reportMissingTypeStubs"
            }
        ],
        "metadata": {
            "operation": "test_store",
            "timestamp": datetime.now().isoformat()
        }
    }
    
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
        await test_context_cache_tool()
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 