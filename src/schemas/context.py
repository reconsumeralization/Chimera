"""Context snapshot schemas for Project Chimera."""
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, field_validator


class FileData(BaseModel):
    """Data for a single file in the context."""
    
    path: str = Field(..., description="Relative path to the file from workspace root")
    content: Optional[str] = Field(None, description="File content, if available")
    language: Optional[str] = Field(None, description="Programming language of the file")
    last_modified: Optional[datetime] = Field(None, description="Last modification time")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    is_open: bool = Field(False, description="Whether the file is open in the editor")
    is_dirty: bool = Field(False, description="Whether the file has unsaved changes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "path": "src/main.py",
                "content": "print('Hello, world!')",
                "language": "python",
                "last_modified": "2023-10-15T12:34:56Z",
                "size_bytes": 150,
                "is_open": True,
                "is_dirty": False
            }
        }


class EditorSelection(BaseModel):
    """User's current selection in the editor."""
    
    file_path: str = Field(..., description="Path to the file with the selection")
    start_line: int = Field(..., description="Start line of selection (0-indexed)")
    start_column: int = Field(..., description="Start column of selection (0-indexed)")
    end_line: int = Field(..., description="End line of selection (0-indexed)")
    end_column: int = Field(..., description="End column of selection (0-indexed)")
    selected_text: Optional[str] = Field(None, description="Text content of the selection")


class DiagnosticItem(BaseModel):
    """A diagnostic (error, warning, info) item from the editor."""
    
    file_path: str = Field(..., description="Path to the file with the diagnostic")
    message: str = Field(..., description="Diagnostic message")
    severity: str = Field(..., description="Severity level (error, warning, info, hint)")
    line: int = Field(..., description="Line number of the diagnostic (0-indexed)")
    column: Optional[int] = Field(None, description="Column number of the diagnostic (0-indexed)")
    source: Optional[str] = Field(None, description="Source of the diagnostic (e.g., linter name)")
    code: Optional[str] = Field(None, description="Error code if available")


class ContextSnapshot(BaseModel):
    """A snapshot of the user's context in the IDE."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the snapshot")
    workspace_root: str = Field(..., description="Absolute path to the workspace root")
    active_file: Optional[str] = Field(None, description="Path to the currently active file")
    selections: List[EditorSelection] = Field(default_factory=list, description="Current editor selections")
    files: List[FileData] = Field(default_factory=list, description="Files in the context")
    diagnostics: List[DiagnosticItem] = Field(default_factory=list, description="Diagnostics in the context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator("files")
    def limit_file_content_size(cls, files: List[FileData]) -> List[FileData]:
        """Limit the content size of files to prevent excessive memory usage."""
        # Max file size for storing content (100KB)
        max_size = 100 * 1024
        
        for file_data in files:
            if file_data.content and len(file_data.content) > max_size:
                # Truncate content and add a note
                file_data.content = file_data.content[:max_size] + "\n\n[Content truncated due to size]"
        
        return files


class ContextQuery(BaseModel):
    """A query for retrieving context based on specific criteria."""
    
    query_text: Optional[str] = Field(None, description="Free-text search query")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns to include (glob)")
    exclude_patterns: Optional[List[str]] = Field(None, description="File patterns to exclude (glob)")
    languages: Optional[List[str]] = Field(None, description="Programming languages to include")
    max_files: Optional[int] = Field(None, description="Maximum number of files to return")
    include_content: bool = Field(True, description="Whether to include file content")
    time_range_start: Optional[datetime] = Field(None, description="Start of time range to query")
    time_range_end: Optional[datetime] = Field(None, description="End of time range to query")


class ContextResponse(BaseModel):
    """Response to a context query."""
    
    query: ContextQuery = Field(..., description="The original query")
    matches: List[FileData] = Field(default_factory=list, description="Matching files")
    total_matches: int = Field(0, description="Total number of matches")
    has_more: bool = Field(False, description="Whether there are more matches")
    query_time_ms: Optional[int] = Field(None, description="Query execution time in milliseconds") 