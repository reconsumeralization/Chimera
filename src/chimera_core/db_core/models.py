"""
ORM models for the Chimera Core database.

This module contains SQLModel models that map directly to database tables.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, func, String, JSON, Integer, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
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

# Define a base class using SQLAlchemy's DeclarativeBase
class Base(DeclarativeBase):
    # Define a type annotation map if needed, e.g., for JSON handling
    type_annotation_map = {
        Dict[str, Any]: JSON,
        List[Dict[str, Any]]: JSON,
    }

# --- Core Models ---

class SnapshotLog(Base):
    """Log entry for each context snapshot received."""
    __tablename__ = "snapshot_log"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_identifier: Mapped[Optional[str]] = mapped_column(String(255)) # E.g., VSCode instance ID
    trigger_type: Mapped[Optional[str]] = mapped_column(String(50)) # E.g., 'manual', 'on_save', 'on_focus'
    workspace_path: Mapped[Optional[str]] = mapped_column(Text)
    processing_status: Mapped[str] = mapped_column(String(50), default="received") # received, processing, completed, failed
    processing_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationship to the actual snapshot data
    context_snapshot: Mapped["ContextSnapshot"] = relationship(back_populates="log_entry", cascade="all, delete-orphan")

class ContextSnapshot(Base):
    """Stores the detailed context snapshot data."""
    __tablename__ = "context_snapshot"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    log_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("snapshot_log.id"), unique=True)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True)) # Timestamp from the client
    active_file_path: Mapped[Optional[str]] = mapped_column(Text)
    project_language: Mapped[Optional[str]] = mapped_column(String(50))
    cursor_position_start: Mapped[Optional[int]] = mapped_column(Integer)
    cursor_position_end: Mapped[Optional[int]] = mapped_column(Integer)
    selected_text: Mapped[Optional[str]] = mapped_column(Text)
    clipboard_content: Mapped[Optional[str]] = mapped_column(Text) # Consider security implications
    client_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON) # Renamed from metadata
    
    log_entry: Mapped["SnapshotLog"] = relationship(back_populates="context_snapshot")
    files: Mapped[List["FileData"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")
    diagnostics: Mapped[List["DiagnosticItem"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")

class FileData(Base):
    """Represents a single file within a context snapshot."""
    __tablename__ = "file_data"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("context_snapshot.id"))
    file_path: Mapped[str] = mapped_column(Text, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text) # Store full content or reference to external storage?
    language: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64)) # E.g., SHA-256 hash

    snapshot: Mapped["ContextSnapshot"] = relationship(back_populates="files")
    
    __table_args__ = (UniqueConstraint('snapshot_id', 'file_path', name='uq_snapshot_file'),)


class DiagnosticItem(Base):
    """Represents a diagnostic message (error, warning) within a context snapshot."""
    __tablename__ = "diagnostic_item"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("context_snapshot.id"))
    file_path: Mapped[str] = mapped_column(Text, index=True)
    severity: Mapped[str] = mapped_column(String(50)) # error, warning, info, hint
    message: Mapped[str] = mapped_column(Text)
    line_start: Mapped[int] = mapped_column(Integer)
    line_end: Mapped[int] = mapped_column(Integer)
    column_start: Mapped[int] = mapped_column(Integer)
    column_end: Mapped[int] = mapped_column(Integer)
    source: Mapped[Optional[str]] = mapped_column(String(100)) # e.g., 'pylint', 'typescript'

    snapshot: Mapped["ContextSnapshot"] = relationship(back_populates="diagnostics")

# --- Rule Engine Models ---

class RuleSet(Base):
    """A collection of rules."""
    __tablename__ = "rule_set"
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    rules: Mapped[List["Rule"]] = relationship(back_populates="rule_set", cascade="all, delete-orphan")

class Rule(Base):
    """A single rule definition within a RuleSet."""
    __tablename__ = "rule"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rule_set.id"))
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    trigger_event: Mapped[str] = mapped_column(String(100)) # e.g., 'on_snapshot', 'on_file_change'
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON) # JSON defining the conditions
    actions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON) # JSON defining actions (e.g., call_api, log_message)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    rule_set: Mapped["RuleSet"] = relationship(back_populates="rules")
    
    __table_args__ = (UniqueConstraint('rule_set_id', 'name', name='uq_ruleset_rule_name'),)

# --- Settings Model ---
# Simple key-value store for dynamic settings if needed, or specific tables.
# Example: Key-value approach
class Settings(Base):
    """Stores dynamic application settings in the database."""
    __tablename__ = "settings"
    
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON) # Store various types as JSON
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) 