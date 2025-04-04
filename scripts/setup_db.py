#!/usr/bin/env python3
"""
Database setup script for Chimera Core.

This script initializes the database schema, creating tables if they don't exist,
and optionally runs migrations if needed.
"""
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command
from sqlalchemy import text, inspect

from src.chimera_core.db_core.connection import init_db, close_db, get_engine
from src.chimera_core.db_core.base import Base
from src.chimera_core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("setup_db")

async def check_tables_exist(engine, table_names) -> bool:
    """Check if the specified tables already exist in the database."""
    is_async = hasattr(engine, 'connect_async')
    
    if is_async:
        from sqlalchemy.ext.asyncio import AsyncEngine
        async with engine.begin() as conn:
            insp = await conn.run_sync(inspect)
            tables = await conn.run_sync(lambda sync_conn: insp.get_table_names())
            exists = all(table in tables for table in table_names)
            return exists
    else:
        with engine.connect() as conn:
            insp = inspect(engine)
            tables = insp.get_table_names()
            exists = all(table in tables for table in table_names)
            return exists

async def initialize_database(connection_string: str, apply_migrations: bool = False):
    """Initialize the database schema and optionally apply migrations."""
    try:
        # Initialize database connection
        logger.info(f"Initializing database with connection string: {connection_string}")
        engine = await init_db(connection_string)
        
        # Check if tables already exist
        tables_exist = await check_tables_exist(engine, ['settings', 'snapshot_logs', 'rule_sets', 'rules'])
        
        if not tables_exist:
            # Create tables
            is_async = '+aiosqlite' in connection_string or '+asyncpg' in connection_string
            
            if is_async:
                from sqlalchemy.ext.asyncio import AsyncEngine
                async with engine.begin() as conn:
                    logger.info("Creating database schema if it doesn't exist")
                    await conn.run_sync(Base.metadata.create_all)
                    
                    # Test connection
                    result = await conn.execute(text("SELECT 1"))
                    logger.info(f"Database connection test: {result.scalar()}")
            else:
                logger.info("Creating database schema if it doesn't exist")
                Base.metadata.create_all(engine)
                
                # Test connection
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    logger.info(f"Database connection test: {result.scalar_one()}")
        else:
            logger.info("Tables already exist, skipping schema creation")
        
        if apply_migrations and not tables_exist:
            # Convert async URL to sync for alembic
            sync_url = connection_string
            if '+aiosqlite' in sync_url:
                sync_url = sync_url.replace('+aiosqlite', '')
            if '+asyncpg' in sync_url:
                sync_url = sync_url.replace('+asyncpg', '')
                
            # Use alembic for migrations
            logger.info("Applying database migrations")
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
            command.upgrade(alembic_cfg, "head")
        elif apply_migrations and tables_exist:
            logger.info("Tables already exist, skipping migrations")
        
        logger.info("Database setup completed successfully")
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise
    finally:
        await close_db()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Set up the Chimera Core database")
    parser.add_argument(
        "--migrations", 
        action="store_true", 
        help="Apply migrations after initializing the database"
    )
    parser.add_argument(
        "--connection-string",
        type=str,
        help="Database connection string (overrides environment settings)"
    )
    return parser.parse_args()

async def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Get database URL from args or config
    settings = get_settings()
    connection_string = args.connection_string or settings.DATABASE_URL
    
    if not connection_string:
        logger.error("No database connection string provided. Set DATABASE_URL environment variable or use --connection-string")
        sys.exit(1)
    
    # Initialize the database
    await initialize_database(connection_string, args.migrations)

if __name__ == "__main__":
    asyncio.run(main()) 