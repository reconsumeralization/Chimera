#!/usr/bin/env python3
"""
Test database CRUD operations.

This script tests the database CRUD operations by performing various
operations on the database models.
"""
import asyncio
import datetime
import json
import logging
import sys
import os
from pathlib import Path
from uuid import uuid4
from typing import List, Optional

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

import structlog
from dotenv import load_dotenv

from src.chimera_core.db_core.connection import init_db, close_db, get_db_session
from src.chimera_core.db_core.crud import (
    create_or_update_setting,
    get_setting,
    get_settings as db_get_settings,
    create_snapshot_log,
    get_snapshot_logs,
    create_or_update_rule_set,
    get_rule_set,
    get_rule_sets,
    create_or_update_rule,
    get_rule,
    get_rules,
)
from src.chimera_core.config import get_settings
from src.chimera_core.exceptions import NotFoundError
from src.chimera_core.db_core.models import (
    SettingOrm,
    SnapshotLogOrm,
    RuleSetOrm,
    RuleOrm,
)
from src.chimera_core.db_core.base import Base
from sqlmodel import SQLModel
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = structlog.get_logger(__name__)

# Load the environment variables
load_dotenv()

async def create_tables(engine):
    """Create database tables if they don't exist."""
    logger.info("Creating database tables")
    
    from src.chimera_core.db_core.connection import _is_async
    
    # Drop tables if they exist to ensure clean schema
    logger.info("Dropping existing tables to ensure clean schema")
    if _is_async:
        # For async engines
        async with engine.begin() as conn:
            # Drop tables in reverse dependency order
            await conn.execute(text("DROP TABLE IF EXISTS rules CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS rule_sets CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS snapshot_logs CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS settings CASCADE"))
            
            # Create tables
            await conn.run_sync(SQLModel.metadata.create_all)
    else:
        # For sync engines
        with engine.begin() as conn:
            # Drop tables in reverse dependency order
            conn.execute(text("DROP TABLE IF EXISTS rules CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS rule_sets CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS snapshot_logs CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS settings CASCADE"))
            
            # Create tables
            SQLModel.metadata.create_all(conn)
            
    logger.info("Database tables created successfully")

async def test_settings_crud():
    """Test settings CRUD operations."""
    logger.info("Testing settings CRUD operations")

    # Create and retrieve a setting
    async with get_db_session() as session:
        # Create a setting
        logger.info("Creating test setting")
        setting = await create_or_update_setting(
            session,
            key="test.setting",
            value="test value",
            description="Test setting",
        )
        assert setting is not None
        assert setting.key == "test.setting"
        assert setting.value == "test value"
        assert setting.description == "Test setting"
        logger.info("Setting created successfully", key=setting.key, value=setting.value)

        # Get the setting
        retrieved = await get_setting(session, "test.setting")
        assert retrieved is not None
        assert retrieved.key == "test.setting"
        assert retrieved.value == "test value"
        assert retrieved.description == "Test setting"
        logger.info("Setting retrieved successfully", key=retrieved.key, value=retrieved.value)

        # Update the setting
        updated = await create_or_update_setting(
            session,
            key="test.setting",
            value="updated value",
            description="Updated test setting",
        )
        assert updated is not None
        assert updated.key == "test.setting"
        assert updated.value == "updated value"
        assert updated.description == "Updated test setting"
        logger.info("Setting updated successfully", key=updated.key, value=updated.value)

        # Get all settings
        all_settings = await db_get_settings(session)
        assert len(all_settings) >= 1
        logger.info("Retrieved all settings", count=len(all_settings))

    logger.info("Settings CRUD tests completed successfully")

async def test_snapshot_logs_crud():
    """Test snapshot logs CRUD operations."""
    logger.info("Testing snapshot logs CRUD operations")

    # Create and retrieve a snapshot log
    async with get_db_session() as session:
        # Create a snapshot log
        logger.info("Creating test snapshot log")
        snapshot_id = "test-snapshot-id"
        snapshot_log = await create_snapshot_log(
            session,
            snapshot_id=snapshot_id,
            operation="create",
            user_id="test-user",
            workspace_id="test-workspace",
            metadata={"source": "test", "file_count": 10},
        )
        assert snapshot_log is not None
        assert snapshot_log.snapshot_id == snapshot_id
        assert snapshot_log.operation == "create"
        assert "source" in snapshot_log.meta_data
        logger.info("Snapshot log created successfully", id=snapshot_log.id)

        # Get snapshot logs
        logs = await get_snapshot_logs(session, snapshot_id=snapshot_id)
        assert len(logs) >= 1
        logger.info("Retrieved snapshot logs", count=len(logs))

    logger.info("Snapshot logs CRUD tests completed successfully")

async def test_rules_crud():
    """Test rules CRUD operations."""
    logger.info("Testing rules CRUD operations")

    # Create and retrieve rule sets and rules
    async with get_db_session() as session:
        # Create a rule set
        logger.info("Creating test rule set")
        rule_set_id = "test-rule-set"
        rule_set = await create_or_update_rule_set(
            session,
            rule_set_id=rule_set_id,
            name="Test Rule Set",
            description="Test rule set",
            enabled=True,
        )
        assert rule_set is not None
        assert rule_set.id == rule_set_id
        assert rule_set.name == "Test Rule Set"
        assert rule_set.description == "Test rule set"
        assert rule_set.enabled is True
        logger.info("Rule set created successfully", id=rule_set.id, name=rule_set.name)

        # Create rules for the rule set
        logger.info("Creating test rules")
        rule1_id = "test-rule-1"
        rule1 = await create_or_update_rule(
            session,
            rule_id=rule1_id,
            rule_set_id=rule_set_id,
            name="Test Rule 1",
            description="Test rule 1",
            condition="file == '*.py'",
            actions=[{"type": "format", "options": {}}],
            enabled=True,
            priority=1,
        )
        assert rule1 is not None
        assert rule1.id == rule1_id
        assert rule1.rule_set_id == rule_set_id
        logger.info("Rule 1 created successfully", id=rule1.id, name=rule1.name)

        rule2_id = "test-rule-2"
        rule2 = await create_or_update_rule(
            session,
            rule_id=rule2_id,
            rule_set_id=rule_set_id,
            name="Test Rule 2",
            description="Test rule 2",
            condition="file == '*.js'",
            actions=[{"type": "format", "options": {}}],
            enabled=True,
            priority=2,
        )
        assert rule2 is not None
        assert rule2.id == rule2_id
        assert rule2.rule_set_id == rule_set_id
        logger.info("Rule 2 created successfully", id=rule2.id, name=rule2.name)

        # Get the rule set
        retrieved_rule_set = await get_rule_set(session, rule_set_id)
        assert retrieved_rule_set is not None
        assert retrieved_rule_set.id == rule_set_id
        assert retrieved_rule_set.name == "Test Rule Set"
        logger.info(
            "Rule set retrieved successfully",
            id=retrieved_rule_set.id,
            name=retrieved_rule_set.name,
        )

        # Get all rule sets
        rule_sets = await get_rule_sets(session)
        assert len(rule_sets) >= 1
        logger.info("Retrieved all rule sets", count=len(rule_sets))

        # Get a specific rule
        retrieved_rule = await get_rule(session, rule1_id)
        assert retrieved_rule is not None
        assert retrieved_rule.id == rule1_id
        logger.info(
            "Rule retrieved successfully",
            id=retrieved_rule.id,
            name=retrieved_rule.name,
        )

        # Get all rules for a rule set
        rules = await get_rules(session, rule_set_id=rule_set_id)
        assert len(rules) == 2
        logger.info("Retrieved all rules for rule set", count=len(rules))

    logger.info("Rules CRUD tests completed successfully")

async def run_tests():
    """Run all database tests."""
    logger.info("Starting database CRUD tests")
    
    # Get the database URL from the environment
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:54322/postgres")
    logger.info("Initializing database", url=db_url)
    
    try:
        # Initialize the database
        engine = await init_db(db_url)
        
        # Create tables
        await create_tables(engine)
        
        # Run tests
        await test_settings_crud()
        await test_snapshot_logs_crud()
        await test_rules_crud()
        
        logger.info("All database tests completed successfully")
    except Exception as e:
        logger.error("Error in database tests", error=str(e))
        raise
    finally:
        # Close the database connection
        await close_db()
        logger.info("Test completed")


if __name__ == "__main__":
    asyncio.run(run_tests()) 