"""
Base module for SQLAlchemy ORM models.

This module provides the base classes for SQLAlchemy ORM models.
"""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declared_attr
from sqlmodel import SQLModel


class Base(SQLModel, AsyncAttrs):
    """Base class for all SQLAlchemy ORM models."""

    __abstract__ = True

    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:
        """Set default table name to lowercase class name."""
        return cls.__name__.lower()

    class Config:
        """Pydantic configuration."""
        
        arbitrary_types_allowed = True 