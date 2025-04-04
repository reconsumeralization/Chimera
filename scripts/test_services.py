#!/usr/bin/env python
"""Test script for verifying that core services are working correctly."""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from src.schemas.context import ContextQuery, ContextSnapshot, FileData, DiagnosticItem

from src.chimera_core import factory
from src.chimera_core.config import get_settings


# Set up logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


async def create_test_snapshot() -> ContextSnapshot:
    """Create a test context snapshot."""
    # Create a few test files
    files = {
        "src/app.ts": FileData(
            path="src/app.ts",
            content="""
            const app = express();
            const port = 3000;
            
            app.get('/', (req, res) => {
                res.send('Hello World!');
            });
            
            app.listen(port, () => {
                console.log(`Server listening at http://localhost:${port}`);
            });
            """,
            language="typescript",
            last_modified=datetime.utcnow(),
            size_bytes=200,
            is_open=True,
            is_dirty=False,
        ),
        "src/types.ts": FileData(
            path="src/types.ts",
            content="""
            export interface User {
                id: string;
                name: string;
                email: string;
                role: any;  // TODO: Define proper type
            }
            
            export interface AppConfig {
                port: number;
                debug: boolean;
                database: any;  // TODO: Define proper type
            }
            """,
            language="typescript",
            last_modified=datetime.utcnow(),
            size_bytes=250,
            is_open=True,
            is_dirty=True,
        ),
        "src/utils.ts": FileData(
            path="src/utils.ts",
            content="""
            export function formatDate(date: Date): string {
                return date.toISOString();
            }
            
            export function parseConfig(config): AppConfig {
                return config as AppConfig;
            }
            """,
            language="typescript",
            last_modified=datetime.utcnow(),
            size_bytes=150,
            is_open=False,
            is_dirty=False,
        ),
    }
    
    # Create a few diagnostics
    diagnostics = [
        DiagnosticItem(
            file_path="src/types.ts",
            message="'any' type is not recommended",
            severity="warning",
            line=5,
            column=18,
            source="typescript",
            code="TS7024",
        ),
        DiagnosticItem(
            file_path="src/types.ts",
            message="'any' type is not recommended",
            severity="warning",
            line=11,
            column=22,
            source="typescript",
            code="TS7024",
        ),
        DiagnosticItem(
            file_path="src/utils.ts",
            message="Parameter 'config' implicitly has an 'any' type",
            severity="error",
            line=5,
            column=32,
            source="typescript",
            code="TS7006",
        ),
    ]
    
    # Create the snapshot
    snapshot = ContextSnapshot(
        timestamp=datetime.utcnow(),
        workspace_root="/path/to/workspace",
        active_file="src/types.ts",
        files=files,
        diagnostics=diagnostics,
        selections=[],
        metadata={
            "editor": "vscode",
            "version": "1.60.0",
        },
    )
    
    return snapshot


async def test_context_cache() -> None:
    """Test the context cache service."""
    logger.info("Testing context cache service")
    
    factory_instance = await factory.init_services()
    context_cache = factory_instance.get_service("context_cache")
    
    if not context_cache:
        logger.error("Failed to get context cache service")
        return
    
    # Create a test snapshot
    snapshot = await create_test_snapshot()
    
    # Store the snapshot
    snapshot_id = await context_cache.store_snapshot(snapshot)
    
    if not snapshot_id:
        logger.error("Failed to store snapshot")
        return
    
    logger.info("Stored snapshot", id=snapshot_id)
    
    # Query all TypeScript files
    query = ContextQuery(
        query_text="",
        file_patterns=["*.ts"],
        languages=["typescript"],
        include_content=True,
        max_files=10,
    )
    
    result = await context_cache.query_context(query)
    
    logger.info(
        "Query result",
        total_matches=result.total_matches,
        has_more=result.has_more,
        query_time_ms=result.query_time_ms,
    )
    
    # Query files with 'any' type
    query = ContextQuery(
        query_text="any",
        file_patterns=["*.ts"],
        languages=["typescript"],
        include_content=True,
        max_files=10,
    )
    
    result = await context_cache.query_context(query)
    
    logger.info(
        "Query for 'any' result",
        total_matches=result.total_matches,
        has_more=result.has_more,
        query_time_ms=result.query_time_ms,
    )
    
    # Get cache stats
    stats = await context_cache.get_stats()
    
    logger.info(
        "Cache stats",
        total_snapshots=stats["total_snapshots"],
        total_files=stats["total_files"],
        cache_size_bytes=stats["cache_size_bytes"],
    )


async def test_rule_engine() -> None:
    """Test the rule engine service."""
    logger.info("Testing rule engine service")
    
    factory_instance = await factory.init_services()
    rule_engine = factory_instance.get_service("rule_engine")
    
    if not rule_engine:
        logger.error("Failed to get rule engine service")
        return
    
    # List all rule sets
    rule_sets = rule_engine.get_all_rule_sets()
    
    logger.info(
        "Rule sets",
        count=len(rule_sets),
        rule_sets=[rs.id for rs in rule_sets],
    )
    
    # Create a test snapshot
    snapshot = await create_test_snapshot()
    
    # Evaluate rules
    result = rule_engine.evaluate_rules(snapshot)
    
    logger.info(
        "Rule evaluation result",
        total_rules_evaluated=result.total_rules_evaluated,
        total_matches=result.total_matches,
        evaluation_time_ms=result.evaluation_time_ms,
        matched_rules=[
            {
                "id": rule.rule_id,
                "name": rule.rule_name,
                "priority": rule.priority,
                "actions": [a.title for a in rule.actions],
            }
            for rule in result.matched_rules
        ],
    )


async def test_database() -> None:
    """Test the database service."""
    logger.info("Testing database service")
    
    factory_instance = await factory.init_services()
    db_service = factory_instance.get_service("database")
    
    if not db_service:
        logger.error("Failed to get database service")
        return
    
    # Check connection
    connection_ok = await db_service.check_connection()
    
    logger.info("Database connection", status="OK" if connection_ok else "Failed")
    
    # Get database info
    db_info = await db_service.get_db_info()
    
    logger.info(
        "Database info",
        type=db_info["type"],
        version=db_info["version"],
        tables=db_info["tables"],
    )


async def main() -> None:
    """Main entry point for the test script."""
    logger.info("Starting service tests")
    
    # Make sure the rules directory exists with our sample rule
    settings = get_settings()
    os.makedirs(settings.rules_dir, exist_ok=True)
    
    # Check if our sample rule exists
    sample_rule_path = os.path.join(settings.rules_dir, "typescript-rules.json")
    
    if not os.path.exists(sample_rule_path):
        logger.warning("Sample rule set not found, tests might not work as expected")
    
    # Test the database service
    await test_database()
    
    # Test the context cache service
    await test_context_cache()
    
    # Test the rule engine service
    await test_rule_engine()
    
    # Close all services
    await factory.close_services()
    
    logger.info("All tests completed")


if __name__ == "__main__":
    asyncio.run(main()) 