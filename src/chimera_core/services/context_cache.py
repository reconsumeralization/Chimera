"""Context cache service for storing and retrieving IDE context data."""
import asyncio
import json
import os
import shutil
import sqlite3
import structlog
import time
import uuid
from datetime import datetime, timedelta
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from pydantic import BaseModel

from ..config import get_settings
from src.schemas.context import (
    ContextQuery, 
    ContextResponse, 
    ContextSnapshot, 
    FileData
)

logger = structlog.get_logger(__name__)


class ContextCacheOptions(BaseModel):
    """Configuration options for the context cache service."""
    
    cache_dir: str
    max_snapshots: int = 100
    min_time_between_snapshots_sec: int = 60
    max_cache_size_mb: int = 500
    ttl_days: int = 7
    enable_db_storage: bool = True
    enable_persistent_storage: bool = True


class ContextCacheService:
    """
    Service for storing and retrieving IDE context data.
    
    The ContextCacheService stores snapshots of the user's IDE context,
    including files, diagnostics, and editor state. It provides methods
    for querying the cache to retrieve context relevant to the user's
    current task or query.
    """
    
    def __init__(self, options: Optional[ContextCacheOptions] = None):
        """
        Initialize the context cache service.
        
        Args:
            options: Configuration options for the cache service
        """
        settings = get_settings()
        
        # Use provided options or create default
        if options is None:
            options = ContextCacheOptions(
                cache_dir=os.path.join(settings.data_directory, "context_cache")
            )
        
        self.options = options
        self.cache_dir = Path(options.cache_dir)
        self.snapshots_dir = self.cache_dir / "snapshots"
        self.db_path = self.cache_dir / "context_cache.db"
        
        # In-memory recent snapshots
        self.recent_snapshots: Dict[str, ContextSnapshot] = {}
        
        # Cache statistics
        self.stats = {
            "total_snapshots": 0,
            "total_files": 0,
            "cache_size_bytes": 0,
            "last_update": None,
            "query_count": 0,
            "hit_count": 0,
            "miss_count": 0
        }
        
        # Ensure the cache directory exists
        os.makedirs(self.snapshots_dir, exist_ok=True)
        
        # Set up the database if enabled
        if options.enable_db_storage:
            self._init_db()
        
        # Load recent snapshots into memory
        if options.enable_persistent_storage:
            self._load_recent_snapshots()
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info(
            "Context cache service initialized",
            cache_dir=str(self.cache_dir),
            options=options.model_dump()
        )
    
    def _init_db(self) -> None:
        """Initialize the SQLite database for the context cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging for better concurrency
                
                # Create snapshots table
                conn.execute('''
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    workspace_root TEXT NOT NULL,
                    active_file TEXT,
                    metadata TEXT,
                    size_bytes INTEGER
                )
                ''')
                
                # Create files table
                conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    snapshot_id TEXT NOT NULL,
                    path TEXT NOT NULL,
                    language TEXT,
                    size_bytes INTEGER,
                    last_modified TEXT,
                    is_open INTEGER,
                    is_dirty INTEGER,
                    has_content INTEGER,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots (id) ON DELETE CASCADE
                )
                ''')
                
                # Create index on snapshot_id and path for quick lookups
                conn.execute('CREATE INDEX IF NOT EXISTS idx_files_snapshot ON files (snapshot_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_files_path ON files (path)')
                
                # Create diagnostics table
                conn.execute('''
                CREATE TABLE IF NOT EXISTS diagnostics (
                    id TEXT PRIMARY KEY,
                    snapshot_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    line INTEGER NOT NULL,
                    column INTEGER,
                    source TEXT,
                    code TEXT,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots (id) ON DELETE CASCADE
                )
                ''')
                
                # Create index on snapshot_id and file_path
                conn.execute('CREATE INDEX IF NOT EXISTS idx_diagnostics_snapshot ON diagnostics (snapshot_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_diagnostics_file ON diagnostics (file_path)')
                
                conn.commit()
                logger.debug("Database initialized", db_path=str(self.db_path))
        
        except sqlite3.Error as e:
            logger.error("Failed to initialize database", error=str(e))
            # If DB init fails, we can still use in-memory cache only
            self.options.enable_db_storage = False
    
    def _load_recent_snapshots(self) -> None:
        """Load the most recent snapshots into memory."""
        if not self.options.enable_db_storage:
            return
        
        try:
            import asyncio
            from src.chimera_core.db_core import connection, crud
            
            # Use a synchronous loop to run our async code within this sync method
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Define the async function to do the loading
            async def _load_snapshots():
                async with connection.get_db_session() as session:
                    # Get the most recent snapshots up to max_snapshots
                    snapshots = await crud.get_recent_context_snapshots(
                        session=session,
                        limit=self.options.max_snapshots,
                        include_files=True,
                        include_diagnostics=True
                    )
                    
                    # Reset our in-memory cache
                    self.recent_snapshots = {}
                    
                    # Convert and store each snapshot
                    for snapshot_orm in snapshots:
                        # Convert ORM to schema
                        snapshot = await crud.convert_snapshot_to_schema(snapshot_orm)
                        
                        # Store in memory
                        self.recent_snapshots[snapshot_orm.id] = snapshot
                        
                        logger.debug("Loaded snapshot from database", id=snapshot_orm.id)
            
            # Run the async function
            loop.run_until_complete(_load_snapshots())
            
            # Update statistics
            self.stats["total_snapshots"] = len(self.recent_snapshots)
            
            # Count total unique files
            all_files = set()
            for snapshot in self.recent_snapshots.values():
                all_files.update(snapshot.files.keys())
            
            self.stats["total_files"] = len(all_files)
            
            logger.info(
                "Loaded recent snapshots from database", 
                count=len(self.recent_snapshots),
                max_snapshots=self.options.max_snapshots
            )
        
        except Exception as e:
            logger.error("Failed to load recent snapshots", error=str(e))
            # If DB loading fails, we still have the in-memory cache
    
    async def store_snapshot(self, snapshot: ContextSnapshot) -> str:
        """
        Store a new context snapshot.
        
        Args:
            snapshot: The context snapshot to store
            
        Returns:
            str: The ID of the stored snapshot
        """
        async with self._lock:
            # Generate a unique ID for the snapshot
            snapshot_id = str(uuid.uuid4())
            
            # Check if we need to rate limit snapshots
            if self.stats["last_update"] is not None:
                last_update = cast(datetime, self.stats["last_update"])
                min_time = timedelta(seconds=self.options.min_time_between_snapshots_sec)
                
                if datetime.utcnow() - last_update < min_time:
                    logger.debug(
                        "Skipping snapshot due to rate limiting",
                        last_update=last_update,
                        min_time_sec=self.options.min_time_between_snapshots_sec
                    )
                    return ""
            
            # Store snapshot in memory
            self.recent_snapshots[snapshot_id] = snapshot
            
            # Enforce max snapshots limit
            if len(self.recent_snapshots) > self.options.max_snapshots:
                # Remove oldest snapshot
                oldest_id = min(
                    self.recent_snapshots.keys(),
                    key=lambda k: self.recent_snapshots[k].timestamp
                )
                del self.recent_snapshots[oldest_id]
            
            # Write snapshot to disk if persistent storage is enabled
            if self.options.enable_persistent_storage:
                await self._write_snapshot_to_disk(snapshot_id, snapshot)
            
            # Store in database if enabled
            if self.options.enable_db_storage:
                await self._store_snapshot_in_db(snapshot_id, snapshot)
            
            # Update statistics
            self.stats["total_snapshots"] = len(self.recent_snapshots)
            self.stats["last_update"] = datetime.utcnow()
            
            # Count total unique files
            all_files: Set[str] = set()
            for s in self.recent_snapshots.values():
                all_files.update(file.path for file in s.files)
            
            self.stats["total_files"] = len(all_files)
            
            logger.info(
                "Stored new context snapshot", 
                id=snapshot_id, 
                workspace=snapshot.workspace_root,
                file_count=len(snapshot.files),
                diagnostic_count=len(snapshot.diagnostics)
            )
            
            # Clean up old snapshots if needed
            await self._cleanup_old_snapshots()
            
            return snapshot_id
    
    async def _write_snapshot_to_disk(self, snapshot_id: str, snapshot: ContextSnapshot) -> None:
        """
        Write a snapshot to disk.
        
        Args:
            snapshot_id: The ID of the snapshot
            snapshot: The snapshot to write
        """
        try:
            snapshot_path = self.snapshots_dir / f"{snapshot_id}.json"
            
            # Convert to JSON
            snapshot_json = snapshot.model_dump_json(indent=2)
            
            # Write to disk
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(snapshot_json)
            
            logger.debug(
                "Wrote snapshot to disk", 
                id=snapshot_id, 
                path=str(snapshot_path),
                size_bytes=len(snapshot_json)
            )
        
        except Exception as e:
            logger.error(
                "Failed to write snapshot to disk", 
                id=snapshot_id,
                error=str(e)
            )
    
    async def _store_snapshot_in_db(self, snapshot_id: str, snapshot: ContextSnapshot) -> None:
        """
        Store a snapshot in the database.
        
        Args:
            snapshot_id: The ID of the snapshot
            snapshot: The snapshot to store
        """
        if not self.options.enable_db_storage:
            return
        
        try:
            # Use the database service or direct DB operations to store the snapshot
            from src.chimera_core.db_core import connection, crud
            from src.chimera_core.services.database import DatabaseService
            
            # Get a session
            async with connection.get_db_session() as session:
                # Set the snapshot ID
                # We're storing the pre-generated ID to ensure consistency between
                # in-memory storage, file storage, and database storage
                snapshot_orm = await crud.create_context_snapshot(
                    session=session,
                    snapshot=snapshot
                )
                
                # Override the auto-generated ID with our pre-generated ID
                snapshot_orm.id = snapshot_id
                
                # Commit the transaction
                await session.commit()
                
                logger.debug(
                    "Stored snapshot in database", 
                    id=snapshot_id,
                    file_count=len(snapshot.files),
                    diagnostic_count=len(snapshot.diagnostics)
                )
        
        except Exception as e:
            logger.error("Failed to store snapshot in database", id=snapshot_id, error=str(e))
    
    async def _cleanup_old_snapshots(self) -> None:
        """Clean up old snapshots based on TTL and size limits."""
        if not self.options.enable_persistent_storage:
            return
        
        try:
            # Calculate cutoff date for TTL
            cutoff_date = datetime.utcnow() - timedelta(days=self.options.ttl_days)
            
            # Check if we need to clean up based on size
            total_size = 0
            for file_path in self.snapshots_dir.glob("*.json"):
                total_size += file_path.stat().st_size
            
            total_size_mb = total_size / (1024 * 1024)
            self.stats["cache_size_bytes"] = total_size
            
            if total_size_mb <= self.options.max_cache_size_mb and self.stats["total_snapshots"] <= self.options.max_snapshots:
                # No need to clean up
                return
            
            # Clean up old snapshots in the database if enabled
            if self.options.enable_db_storage:
                from src.chimera_core.db_core import connection, crud
                
                async with connection.get_db_session() as session:
                    # Delete snapshots older than TTL
                    deleted_count = await crud.delete_old_context_snapshots(
                        session=session,
                        days_old=self.options.ttl_days
                    )
                    
                    # If we still have too many snapshots after TTL cleanup,
                    # we need to delete some more based on size/count constraints
                    if total_size_mb > self.options.max_cache_size_mb or self.stats["total_snapshots"] > self.options.max_snapshots:
                        # Get list of snapshots ordered by timestamp
                        snapshots = await crud.get_recent_context_snapshots(
                            session=session,
                            limit=1000,  # Get a large batch to work with
                            include_files=False,
                            include_diagnostics=False
                        )
                        
                        # Delete oldest snapshots until we're under the limits
                        # We'll delete at least 20% of snapshots if we're over the limit
                        to_delete = max(
                            int(self.stats["total_snapshots"] * 0.2),  # 20% of total 
                            self.stats["total_snapshots"] - self.options.max_snapshots  # Or just what's over the limit
                        )
                        
                        if to_delete > 0 and len(snapshots) > 0:
                            # Sort oldest first (reverse the already desc-sorted list)
                            snapshots_oldest_first = list(reversed(snapshots))
                            
                            # Delete the oldest snapshots
                            for i, snapshot in enumerate(snapshots_oldest_first):
                                if i >= to_delete:
                                    break
                                    
                                # Delete this snapshot
                                await crud.delete_context_snapshot(session, snapshot.id)
                            
                            # Commit the transaction
                            await session.commit()
            
            # Clean up snapshot files on disk
            for file_path in sorted(
                self.snapshots_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime
            ):
                # Skip recent files
                if file_path.stat().st_mtime > cutoff_date.timestamp():
                    continue
                
                try:
                    file_path.unlink()
                    logger.debug("Deleted old snapshot file", path=str(file_path))
                except OSError as e:
                    logger.warning("Failed to delete snapshot file", path=str(file_path), error=str(e))
                
                # Check if we're under the size limit now
                total_size -= file_path.stat().st_size
                if total_size / (1024 * 1024) <= self.options.max_cache_size_mb:
                    break
            
            # Update in-memory cache to match what's on disk and in DB
            if self.options.enable_db_storage:
                # This will reload the most recent snapshots (limited by max_snapshots)
                self._load_recent_snapshots()
            
            logger.info(
                "Cleaned up old snapshots",
                cache_size_mb=total_size / (1024 * 1024),
                max_size_mb=self.options.max_cache_size_mb,
                total_snapshots=self.stats["total_snapshots"]
            )
        
        except Exception as e:
            logger.error("Failed to clean up old snapshots", error=str(e))
    
    async def query_context(self, query: ContextQuery) -> ContextResponse:
        """
        Query the context cache for relevant files.
        
        Args:
            query: The query parameters
            
        Returns:
            ContextResponse: The query results
        """
        async with self._lock:
            start_time = time.time()
            
            # Initialize response
            response = ContextResponse(
                query=query,
                matches=[],
                total_matches=0,
                has_more=False
            )
            
            # Get all snapshots to search (in-memory ones)
            snapshots_to_search = list(self.recent_snapshots.values())
            
            # Filter by time range if specified
            if query.time_range_start:
                snapshots_to_search = [
                    s for s in snapshots_to_search
                    if s.timestamp >= query.time_range_start
                ]
            
            if query.time_range_end:
                snapshots_to_search = [
                    s for s in snapshots_to_search
                    if s.timestamp <= query.time_range_end
                ]
            
            # Collect matching files from all snapshots
            matching_files: List[FileData] = []
            file_paths_seen = set()  # To keep track of files we've already added
            
            for snapshot in snapshots_to_search:
                for file_data in snapshot.files:
                    file_path = file_data.path
                    
                    # Skip if we've already added this file
                    if file_path in file_paths_seen:
                        continue
                    
                    # Check file pattern match
                    if query.file_patterns:
                        if not any(fnmatch(file_path, pattern) for pattern in query.file_patterns):
                            continue
                    
                    # Check exclude pattern match
                    if query.exclude_patterns:
                        if any(fnmatch(file_path, pattern) for pattern in query.exclude_patterns):
                            continue
                    
                    # Check language match
                    if query.languages and file_data.language:
                        if file_data.language.lower() not in [lang.lower() for lang in query.languages]:
                            continue
                    
                    # Check text match if specified
                    if query.query_text and query.query_text.strip():
                        query_text = query.query_text.lower()
                        
                        # Check file path
                        path_match = query_text in file_path.lower()
                        
                        # Check file content if available
                        content_match = False
                        if file_data.content:
                            content_match = query_text in file_data.content.lower()
                        
                        if not (path_match or content_match):
                            continue
                    
                    # Add to matches if we get here
                    file_paths_seen.add(file_path)
                    
                    # Create a copy of the file data
                    match = FileData(
                        path=file_data.path,
                        language=file_data.language,
                        size_bytes=file_data.size_bytes,
                        last_modified=file_data.last_modified,
                        is_open=file_data.is_open,
                        is_dirty=file_data.is_dirty,
                    )
                    
                    # Add content if requested
                    if query.include_content and file_data.content:
                        match.content = file_data.content
                    
                    matching_files.append(match)
            
            # Sort and limit results
            total_matches = len(matching_files)
            has_more = False
            
            # Sort by most recent and relevance (if query text)
            if query.query_text:
                # Simple relevance: sort by number of matches
                def relevance_score(file: FileData) -> float:
                    query_text = query.query_text.lower()
                    path_score = file.path.lower().count(query_text) * 2.0  # Weight path matches higher
                    content_score = file.content.lower().count(query_text) if file.content else 0
                    return path_score + content_score
                
                sorted_matches = sorted(matching_files, key=relevance_score, reverse=True)
            else:
                # Sort by recent modification time if available
                sorted_matches = sorted(
                    matching_files,
                    key=lambda f: f.last_modified or datetime.min,
                    reverse=True  # Most recent first
                )
            
            if query.max_files and total_matches > query.max_files:
                sorted_matches = sorted_matches[:query.max_files]
                has_more = True
            
            # Update response
            response.matches = sorted_matches
            response.total_matches = total_matches
            response.has_more = has_more
            response.query_time_ms = int((time.time() - start_time) * 1000)
            
            # Update statistics
            self.stats["query_count"] += 1
            
            if total_matches > 0:
                self.stats["hit_count"] += 1
            else:
                self.stats["miss_count"] += 1
            
            logger.info(
                "Context query completed",
                total_matches=total_matches,
                has_more=has_more,
                query_time_ms=response.query_time_ms
            )
            
            return response
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the context cache.
        
        Returns:
            Dict[str, Any]: Statistics about the cache
        """
        async with self._lock:
            # Update cache size
            if self.options.enable_persistent_storage:
                total_size = 0
                for file_path in self.snapshots_dir.glob("*.json"):
                    total_size += file_path.stat().st_size
                
                self.stats["cache_size_bytes"] = total_size
            
            return self.stats.copy()
    
    async def clear_cache(self) -> bool:
        """
        Clear the entire context cache.
        
        Returns:
            bool: True if successful, False otherwise
        """
        async with self._lock:
            try:
                # Clear in-memory cache
                self.recent_snapshots.clear()
                
                # Clear database if enabled
                if self.options.enable_db_storage:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("DELETE FROM snapshots")
                        conn.commit()
                
                # Clear files on disk
                if self.options.enable_persistent_storage:
                    for file_path in self.snapshots_dir.glob("*.json"):
                        try:
                            file_path.unlink()
                        except OSError as e:
                            logger.warning("Failed to delete file", path=str(file_path), error=str(e))
                
                # Reset statistics
                self.stats = {
                    "total_snapshots": 0,
                    "total_files": 0,
                    "cache_size_bytes": 0,
                    "last_update": datetime.utcnow(),
                    "query_count": 0,
                    "hit_count": 0,
                    "miss_count": 0
                }
                
                logger.info("Context cache cleared")
                return True
            
            except Exception as e:
                logger.error("Failed to clear context cache", error=str(e))
                return False
    
    async def get_relevant_context_for_task(
        self, 
        task_description: str, 
        max_files: int = 5, 
        include_content: bool = True,
        ai_client=None
    ) -> List[Dict[str, Any]]:
        """
        Get relevant context for a specific task or query.
        
        This method retrieves the most relevant files for a given task
        description, using a combination of keyword matching and, when available,
        AI-based relevance determination.
        
        Args:
            task_description: Description of the task or query
            max_files: Maximum number of files to return
            include_content: Whether to include file content
            ai_client: Optional AIClient for relevance ranking (if not provided, uses heuristics)
            
        Returns:
            List[Dict[str, Any]]: List of relevant files with metadata
        """
        logger.info(
            "Getting relevant context for task",
            task_description=task_description,
            max_files=max_files,
        )
        
        # Extract keywords from the task description
        keywords = self._extract_keywords(task_description)
        logger.debug("Extracted keywords", keywords=keywords)
        
        # Get recent snapshots to search through
        if not self.recent_snapshots:
            logger.warning("No snapshots available for context retrieval")
            return []
        
        # Use the most recent snapshot as the primary source
        recent_snapshot = self.recent_snapshots[-1]
        
        # Basic implementation: Score files based on keyword matches
        file_scores = []
        for file in recent_snapshot.files:
            if not file.content:
                continue
                
            # Skip very large files
            if file.size_bytes and file.size_bytes > 1024 * 1024:  # 1MB
                continue
                
            # Calculate relevance score based on keywords
            score = self._calculate_relevance_score(file, keywords)
            
            # Only include files with some relevance
            if score > 0:
                file_scores.append((file, score))
        
        # Sort files by relevance score (descending)
        file_scores.sort(key=lambda x: x[1], reverse=True)
        
        # If AI client is provided, use it to refine the selection
        selected_files = []
        if ai_client and len(file_scores) > max_files:
            try:
                # Take top candidates (2x max_files) for AI to analyze
                candidates = file_scores[:max_files * 2]
                candidate_files = []
                
                for file, score in candidates:
                    file_dict = {
                        "path": file.path,
                        "language": file.language or "unknown",
                        "size_bytes": file.size_bytes or 0,
                        "content": file.content[:1000] + "..." if file.content and len(file.content) > 1000 else file.content
                    }
                    candidate_files.append(file_dict)
                
                # Use AI to select the most relevant files
                relevant_files = await ai_client.get_relevant_context(
                    query=task_description,
                    available_files=candidate_files,
                    max_files=max_files
                )
                
                # Convert the results to the expected format
                for file_info in relevant_files:
                    # Find the original file object
                    for file, score in candidates:
                        if file.path == file_info.get("path"):
                            file_dict = {
                                "path": file.path,
                                "language": file.language,
                                "content": file.content if include_content else None,
                                "size_bytes": file.size_bytes,
                                "last_modified": file.last_modified,
                                "is_open": file.is_open,
                                "is_dirty": file.is_dirty,
                                "relevance": file_info.get("relevance", f"Relevance score: {score}")
                            }
                            selected_files.append(file_dict)
                            break
            
            except Exception as e:
                logger.error("Error using AI for context relevance", error=str(e))
                # Fall back to the heuristic approach below
                selected_files = []
        
        # If we don't have selected files yet (AI was not used or failed)
        if not selected_files:
            # Take the top scoring files based on keywords
            for file, score in file_scores[:max_files]:
                file_dict = {
                    "path": file.path,
                    "language": file.language,
                    "content": file.content if include_content else None,
                    "size_bytes": file.size_bytes,
                    "last_modified": file.last_modified,
                    "is_open": file.is_open,
                    "is_dirty": file.is_dirty,
                    "relevance": f"Keyword relevance score: {score}"
                }
                selected_files.append(file_dict)
        
        logger.info(
            "Retrieved relevant context",
            file_count=len(selected_files),
            task=task_description
        )
        
        return selected_files
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: The text to extract keywords from
            
        Returns:
            List[str]: List of keywords
        """
        # Simple keyword extraction - split by spaces and keep words longer than 3 chars
        words = text.lower().split()
        
        # Remove punctuation from words
        cleaned_words = []
        for word in words:
            cleaned = ''.join(c for c in word if c.isalnum())
            if len(cleaned) > 3:
                cleaned_words.append(cleaned)
        
        # Remove common stop words
        stop_words = {"the", "and", "for", "with", "this", "that", "what", "where", "when", "how", "why"}
        keywords = [word for word in cleaned_words if word not in stop_words]
        
        return keywords
    
    def _calculate_relevance_score(self, file: FileData, keywords: List[str]) -> float:
        """
        Calculate relevance score of a file for given keywords.
        
        Args:
            file: The file to score
            keywords: List of keywords to match
            
        Returns:
            float: Relevance score
        """
        score = 0.0
        
        # Check filename relevance
        filename = os.path.basename(file.path).lower()
        for keyword in keywords:
            if keyword in filename:
                score += 5.0  # High weight for filename matches
        
        # Check content relevance if available
        if file.content:
            content_lower = file.content.lower()
            for keyword in keywords:
                # Count occurrences of keyword in content
                count = content_lower.count(keyword)
                if count > 0:
                    # Logarithmic scaling to avoid too much weight for repeated terms
                    score += 1.0 + (1.0 * min(count, 10) / 10)
        
        # Boost score for open files
        if file.is_open:
            score *= 1.5
        
        # Boost score for dirty (modified) files
        if file.is_dirty:
            score *= 1.2
        
        return score 