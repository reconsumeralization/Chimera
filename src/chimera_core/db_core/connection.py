"""
Database connection module.

This module provides utilities for creating and managing database connections.
"""
import contextlib
from typing import AsyncGenerator, Optional, Union, Any, Callable

import structlog
from sqlalchemy import URL, Engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import create_engine, Session as SQLModelSession, SQLModel

from src.chimera_core.exceptions import DatabaseError

logger = structlog.get_logger(__name__)

# Global variables
_engine: Optional[Union[AsyncEngine, Engine]] = None
_session_factory: Optional[Union[async_sessionmaker, Callable[[], SQLModelSession]]] = None
_is_async: bool = True


async def init_db(connection_string: str, echo: bool = False) -> Union[AsyncEngine, Engine]:
    """
    Initialize the database connection.

    Args:
        connection_string: The SQLAlchemy database URL
        echo: Whether to echo SQL statements

    Returns:
        Union[AsyncEngine, Engine]: The SQLAlchemy engine

    Raises:
        DatabaseError: If the database connection cannot be initialized
    """
    global _engine, _session_factory, _is_async

    try:
        logger.info("Initializing database connection", connection_string=connection_string)
        
        # Determine if we should use async or sync engine based on the URL
        _is_async = '+aiosqlite' in connection_string or '+asyncpg' in connection_string
        
        if _is_async:
            # Create the async engine
            _engine = create_async_engine(
                connection_string,
                echo=echo,
                future=True,
                pool_pre_ping=True,
            )
            
            # Create the session factory
            _session_factory = async_sessionmaker(
                _engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
        else:
            # Create a sync engine for non-async drivers
            _engine = create_engine(
                connection_string,
                echo=echo,
                future=True,
                pool_pre_ping=True,
            )
            
            # Create the session factory - use SQLModel's Session
            _session_factory = lambda: SQLModelSession(_engine, expire_on_commit=False)
        
        logger.info("Database connection initialized successfully", is_async=_is_async)
        return _engine
    except Exception as e:
        logger.error("Failed to initialize database connection", error=str(e), exc_info=True)
        raise DatabaseError(f"Failed to initialize database connection: {str(e)}") from e


async def close_db() -> None:
    """Close the database connection."""
    global _engine, _is_async
    
    if _engine is not None:
        logger.info("Closing database connection")
        try:
            if _is_async and isinstance(_engine, AsyncEngine):
                await _engine.dispose()
            else:
                _engine.dispose()
            _engine = None
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error("Error closing database connection", error=str(e), exc_info=True)
            raise DatabaseError(f"Error closing database connection: {str(e)}") from e


async def get_engine() -> Union[AsyncEngine, Engine]:
    """
    Get the SQLAlchemy engine.

    Returns:
        Union[AsyncEngine, Engine]: The SQLAlchemy engine

    Raises:
        DatabaseError: If the engine is not initialized
    """
    if _engine is None:
        logger.error("Database engine not initialized")
        raise DatabaseError("Database engine not initialized")
    return _engine


@contextlib.asynccontextmanager
async def get_db_session() -> AsyncGenerator[Union[AsyncSession, SQLModelSession], None]:
    """
    Get a database session.

    Yields:
        Union[AsyncSession, SQLModelSession]: A SQLAlchemy session

    Raises:
        DatabaseError: If the session factory is not initialized
    """
    global _session_factory, _is_async
    
    if _session_factory is None:
        logger.error("Database session factory not initialized")
        raise DatabaseError("Database session factory not initialized")
    
    session = _session_factory()
    try:
        yield session
        if _is_async and isinstance(session, AsyncSession):
            await session.commit()
        else:
            session.commit()
    except Exception as e:
        if _is_async and isinstance(session, AsyncSession):
            await session.rollback()
        else:
            session.rollback()
        logger.error("Database session error", error=str(e), exc_info=True)
        raise DatabaseError(f"Database session error: {str(e)}") from e
    finally:
        if _is_async and isinstance(session, AsyncSession):
            await session.close()
        else:
            session.close() 