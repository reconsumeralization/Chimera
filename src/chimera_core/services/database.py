"""Database service layer for Chimera Core.

Provides a higher-level interface for database operations,
using the underlying connection and CRUD functions.
"""
import structlog
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from src.chimera_core.exceptions import DatabaseError, NotFoundError
from src.chimera_core.db_core import connection, crud
from src.chimera_core.db_core.models import SettingOrm, SnapshotLogOrm

logger = structlog.get_logger(__name__)

class DatabaseService:
    """Service layer for database operations."""

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize DatabaseService.
        
        Args:
            connection_string: Optional connection string to override the one from config
        """
        # Engine/Session managed by connection module and context manager
        self.log = logger.bind(service="DatabaseService")
        self._connection_string = connection_string
        self.engine = None
        self.metadata = None
        self.log.info("DatabaseService initialized")

    async def initialize(self) -> None:
        """Initialize the database connection and ensure tables exist."""
        try:
            # Initialize the database
            self.engine = await connection.init_db()
            
            # Get metadata for use in schema operations
            from src.chimera_core.db_core.base import Base
            self.metadata = Base.metadata
            
            self.log.info("Database tables created")
        except Exception as e:
            self.log.error("Failed to initialize database", error=str(e), exc_info=True)
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    async def close(self) -> None:
        """Close database connections."""
        try:
            await connection.close_db()
            self.log.info("Database connection closed")
        except Exception as e:
            self.log.error("Failed to close database connection", error=str(e), exc_info=True)

    # --- Settings Methods ---
    async def get_setting_value(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Gets the value of a setting, returning default if not found.
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Any: Setting value or default
        """
        self.log.debug("Getting setting value", key=key)
        try:
            async with connection.get_db_session() as db:
                setting = await crud.get_setting(db, key)
                return setting.value if setting else default
        except Exception as e:
            self.log.error("Failed to get setting value", key=key, error=str(e))
            # Decide whether to return default or re-raise
            return default # Graceful degradation for settings

    async def save_setting_value(self, key: str, value: Dict[str, Any]) -> bool:
        """Saves a setting value.
        
        Args:
            key: Setting key
            value: Setting value dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log.info("Saving setting value", key=key)
        try:
            async with connection.get_db_session() as db:
                await crud.upsert_setting(db, key, value)
                await db.commit() # Commit transaction started by context manager
            return True
        except Exception as e:
            self.log.error("Failed to save setting value", key=key, error=str(e))
            return False

    async def get_all_settings_as_dict(self) -> Dict[str, Any]:
        """Gets all settings as a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary of settings
        """
        self.log.debug("Getting all settings as dict")
        settings_dict = {}
        try:
            async with connection.get_db_session() as db:
                all_settings = await crud.get_all_settings(db)
                for setting in all_settings:
                    settings_dict[setting.key] = setting.value
            return settings_dict
        except Exception as e:
            self.log.error("Failed to get all settings", error=str(e))
            return {} # Return empty on error

    # --- Snapshot Log Methods ---
    async def log_snapshot(
        self,
        trigger: str,
        active_uri: Optional[str] = None,
        file_count: Optional[int] = None,
        diag_count: Optional[int] = None,
        git_branch: Optional[str] = None
    ) -> bool:
        """Logs metadata about a processed snapshot.
        
        Args:
            trigger: Event that triggered the snapshot
            active_uri: Active URI when snapshot was taken
            file_count: Number of files in the snapshot
            diag_count: Number of diagnostics in the snapshot
            git_branch: Git branch name
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.log.debug("Logging snapshot metadata", trigger=trigger)
        try:
            async with connection.get_db_session() as db:
                await crud.create_snapshot_log(
                    db,
                    trigger_event=trigger,
                    active_uri=active_uri,
                    file_count=file_count,
                    diag_count=diag_count,
                    git_branch=git_branch
                )
                await db.commit()
            return True
        except Exception as e:
            self.log.error("Failed to log snapshot", trigger=trigger, error=str(e))
            return False

    async def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Gets recent snapshot logs.
        
        Args:
            limit: Maximum number of logs to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of snapshot logs as dictionaries
        """
        self.log.debug("Getting recent snapshot logs", limit=limit)
        try:
            async with connection.get_db_session() as db:
                logs_orm = await crud.get_recent_snapshot_logs(db, limit)
                # Convert ORM objects to simple dicts for API responses
                return [
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat(),
                        "trigger": log.trigger_event,
                        "active_uri": log.active_uri,
                        "files": log.file_count,
                        "diagnostics": log.diag_count,
                        "branch": log.git_branch,
                    }
                    for log in logs_orm
                ]
        except Exception as e:
            self.log.error("Failed to get recent logs", error=str(e))
            return []

    # Connection check and info methods
    async def check_connection(self) -> bool:
        """Check if the database connection works.
        
        Returns:
            bool: True if the connection works, False otherwise
        """
        return await connection.check_connection()

    async def get_db_info(self) -> Dict[str, Any]:
        """Get information about the database connection.
        
        Returns:
            Dict[str, Any]: Information about the database
        """
        return await connection.get_db_info()

    def session(self) -> AsyncSession:
        """Gets a database session context manager.
        
        Returns:
            AsyncContextManager[AsyncSession]: Session context manager
        """
        return connection.get_db_session() 