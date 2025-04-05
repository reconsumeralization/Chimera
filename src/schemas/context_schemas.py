"""Context schemas for Chimera API."""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ContextItem(BaseModel):
    """Base class for context items."""
    type: str = Field(..., description="Type of context item")
    content: Any = Field(..., description="Content of the context item")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CodeContext(BaseModel):
    """Context information from code files."""
    items: List[ContextItem] = Field(default_factory=list, description="List of context items")
    workspace_root: Optional[str] = Field(None, description="Root directory of the workspace")
    timestamp: Optional[str] = Field(None, description="Timestamp when context was collected")


class ContextRequest(BaseModel):
    """Request to store context."""
    context: CodeContext = Field(..., description="Context to store")
    session_id: str = Field(..., description="Session identifier")
    overwrite: bool = Field(False, description="Whether to overwrite existing context")


class ContextResponse(BaseModel):
    """Response with stored context."""
    success: bool = Field(..., description="Whether the operation was successful")
    context_id: Optional[str] = Field(None, description="ID of the stored context")
    message: Optional[str] = Field(None, description="Additional information")


class SnapshotLogBase(BaseModel):
    """Base class for snapshot logs."""
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the snapshot")
    context_size: int = Field(..., description="Size of the context in bytes")
    source_type: str = Field(..., description="Source of the context (e.g., 'vscode', 'cursor')")


class SnapshotLogCreate(SnapshotLogBase):
    """Schema for creating a new snapshot log entry."""
    pass


class SnapshotLog(SnapshotLogBase):
    """Schema for a snapshot log entry with ID."""
    id: int = Field(..., description="Unique identifier")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
