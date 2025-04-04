"""API request and response schemas for Project Chimera."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, field_validator

from .context import ContextQuery, ContextResponse, ContextSnapshot


class APIStatus(str, Enum):
    """Status code for API responses."""
    
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"


class APIErrorCode(str, Enum):
    """Error codes for API error responses."""
    
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED = "unauthorized"
    SERVER_ERROR = "server_error"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    RESOURCE_EXHAUSTED = "resource_exhausted"


class APIRequest(BaseModel):
    """Base class for all API requests."""
    
    request_id: str = Field(..., description="Unique identifier for the request")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the request")


class APIResponse(BaseModel):
    """Base class for all API responses."""
    
    request_id: str = Field(..., description="Unique identifier for the request")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the response")
    status: APIStatus = Field(default=APIStatus.SUCCESS, description="Status of the response")
    message: Optional[str] = Field(None, description="Human-readable status message")
    error_code: Optional[APIErrorCode] = Field(None, description="Error code if status is error")
    elapsed_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


class ContextSnapshotRequest(APIRequest):
    """Request to store a context snapshot."""
    
    snapshot: ContextSnapshot = Field(..., description="The context snapshot to store")


class ContextSnapshotResponse(APIResponse):
    """Response to a context snapshot request."""
    
    snapshot_id: Optional[str] = Field(None, description="Identifier for the stored snapshot")
    stored_file_count: Optional[int] = Field(None, description="Number of files stored")


class ContextQueryRequest(APIRequest):
    """Request to query the context cache."""
    
    query: ContextQuery = Field(..., description="The context query")


class ContextQueryResponse(APIResponse):
    """Response to a context query request."""
    
    result: Optional[ContextResponse] = Field(None, description="The query result")


class ContextCacheStatsRequest(APIRequest):
    """Request to get statistics about the context cache."""
    
    pass


class ContextCacheStatsResponse(APIResponse):
    """Response with statistics about the context cache."""
    
    total_snapshots: int = Field(0, description="Total number of snapshots in the cache")
    total_files: int = Field(0, description="Total number of unique files in the cache")
    last_update: Optional[datetime] = Field(None, description="Timestamp of the last update")
    cache_size_bytes: Optional[int] = Field(None, description="Size of the cache in bytes")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Additional statistics") 