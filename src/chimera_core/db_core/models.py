"""
ORM models for the Chimera Core database.

This module contains SQLModel models that map directly to database tables.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, func, String, JSON, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlmodel import Field, SQLModel, Relationship

from src.chimera_core.db_core.base import Base


class SettingOrm(SQLModel, table=True):
    """
    Database model for settings.
    """
    __tablename__ = "settings"

    key: str = Field(primary_key=True)
    value: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SnapshotLogOrm(SQLModel, table=True):
    """
    Database model for snapshot logs.
    """
    __tablename__ = "snapshot_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_id: str
    operation: str
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    meta_data: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False, default={}))
    timestamp: datetime = Field(default_factory=datetime.now)


class ContextSnapshotOrm(SQLModel, table=True):
    """
    Database model for context snapshots.
    """
    __tablename__ = "context_snapshots"

    id: str = Field(primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    workspace_root: str = Field(...)
    active_file: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    size_bytes: Optional[int] = None

    # Relationships
    files: List["FileDataOrm"] = Relationship(
        back_populates="snapshot",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    diagnostics: List["DiagnosticItemOrm"] = Relationship(
        back_populates="snapshot",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class FileDataOrm(SQLModel, table=True):
    """
    Database model for file data within context snapshots.
    """
    __tablename__ = "context_files"

    id: str = Field(primary_key=True)
    snapshot_id: str = Field(foreign_key="context_snapshots.id")
    path: str = Field(...)
    language: Optional[str] = None
    size_bytes: Optional[int] = None
    last_modified: Optional[datetime] = None
    is_open: bool = Field(default=False)
    is_dirty: bool = Field(default=False)
    has_content: bool = Field(default=False)
    content: Optional[str] = None  # Optional content storage if needed
    
    # Relationships
    snapshot: Optional[ContextSnapshotOrm] = Relationship(back_populates="files")


class DiagnosticItemOrm(SQLModel, table=True):
    """
    Database model for diagnostic items within context snapshots.
    """
    __tablename__ = "context_diagnostics"

    id: str = Field(primary_key=True)
    snapshot_id: str = Field(foreign_key="context_snapshots.id")
    file_path: str = Field(...)
    message: str = Field(...)
    severity: str = Field(...)
    line: int = Field(...)
    column: Optional[int] = None
    source: Optional[str] = None
    code: Optional[str] = None
    
    # Relationships
    snapshot: Optional[ContextSnapshotOrm] = Relationship(back_populates="diagnostics")


class RuleSetOrm(SQLModel, table=True):
    """
    Database model for rule sets.
    """
    __tablename__ = "rule_sets"

    id: str = Field(primary_key=True)
    name: str
    description: Optional[str] = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    rules: List["RuleOrm"] = Relationship(
        back_populates="rule_set",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class RuleOrm(SQLModel, table=True):
    """
    Database model for rules.
    """
    __tablename__ = "rules"

    id: str = Field(primary_key=True)
    rule_set_id: str = Field(foreign_key="rule_sets.id")
    name: str
    description: Optional[str] = None
    condition: str
    actions: List[Dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False, default=[]))
    enabled: bool = True
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    rule_set: Optional[RuleSetOrm] = Relationship(back_populates="rules")

# TODO (Phase 3+): Add RuleOrm, RuleSetOrm models
# TODO (Phase 8+): Add DtgsToolOrm, DtgsInvocationOrm models
# TODO (Phase 9+): Add ContextEmbeddingOrm model (might require pgvector extension for Postgres) 