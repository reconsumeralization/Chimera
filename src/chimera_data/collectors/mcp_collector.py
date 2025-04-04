"""MCP data collector for logging MCP traffic."""
import datetime
import json
import os
import sqlite3
import structlog
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from chimera_core.config import get_settings

logger = structlog.get_logger(__name__)

class MCPDataCollector:
    """Collects and stores MCP traffic data."""
    
    def __init__(self, 
                db_path: Optional[str] = None, 
                enabled: Optional[bool] = None):
        """Initialize the MCP data collector.
        
        Args:
            db_path: Path to the SQLite database
            enabled: Whether data collection is enabled
        """
        settings = get_settings()
        
        # Determine if data collection is enabled
        self.enabled = enabled if enabled is not None else settings.enable_data_collection
        
        # Set up database path
        if db_path is None:
            data_dir = Path(settings.data_directory)
            db_path = data_dir / "mcp_data.db"
        else:
            db_path = Path(db_path)
        
        self.db_path = db_path
        
        # Ensure the parent directory exists
        os.makedirs(db_path.parent, exist_ok=True)
        
        self.log = logger.bind(component="MCPDataCollector", enabled=self.enabled)
        
        if self.enabled:
            self.log.info("MCP data collector enabled", db_path=str(db_path))
            self._init_db()
        else:
            self.log.info("MCP data collector disabled")
    
    def _init_db(self) -> None:
        """Initialize the database schema."""
        if not self.enabled:
            return
        
        self.log.debug("Initializing database schema")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create mcp_requests table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS mcp_requests (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    parameters TEXT,
                    anonymized INTEGER DEFAULT 0
                )
                ''')
                
                # Create mcp_responses table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS mcp_responses (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    response_data TEXT,
                    execution_time_ms INTEGER,
                    anonymized INTEGER DEFAULT 0,
                    FOREIGN KEY (request_id) REFERENCES mcp_requests (id)
                )
                ''')
                
                # Create collection_stats table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS collection_stats (
                    name TEXT PRIMARY KEY,
                    value INTEGER DEFAULT 0,
                    last_updated TEXT
                )
                ''')
                
                conn.commit()
                self.log.debug("Database schema initialized")
        
        except sqlite3.Error as e:
            self.log.error("Failed to initialize database", error=str(e))
            # Disable data collection if database initialization fails
            self.enabled = False
    
    def log_request(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Log an MCP request.
        
        Args:
            tool_name: The name of the tool being called
            parameters: The parameters for the tool call
            
        Returns:
            The ID of the logged request
        """
        if not self.enabled:
            return str(uuid.uuid4())  # Return a dummy ID if disabled
        
        request_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        
        # Anonymize parameters if needed
        parameters_json = json.dumps(parameters)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO mcp_requests (id, timestamp, tool_name, parameters, anonymized)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (request_id, timestamp, tool_name, parameters_json, 0)
                )
                
                # Update collection stats
                cursor.execute(
                    '''
                    INSERT INTO collection_stats (name, value, last_updated)
                    VALUES ('request_count', 1, ?)
                    ON CONFLICT(name) DO UPDATE SET
                    value = value + 1,
                    last_updated = ?
                    ''',
                    (timestamp, timestamp)
                )
                
                conn.commit()
                self.log.debug("Logged MCP request", tool=tool_name, request_id=request_id)
        
        except sqlite3.Error as e:
            self.log.error("Failed to log MCP request", error=str(e), tool=tool_name)
        
        return request_id
    
    def log_response(self, 
                    request_id: str, 
                    response_data: Dict[str, Any],
                    execution_time_ms: Optional[int] = None) -> None:
        """Log an MCP response.
        
        Args:
            request_id: The ID of the corresponding request
            response_data: The response data
            execution_time_ms: The execution time in milliseconds
        """
        if not self.enabled:
            return
        
        response_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        
        # Anonymize response data if needed
        response_json = json.dumps(response_data)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO mcp_responses (id, request_id, timestamp, response_data, execution_time_ms, anonymized)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (response_id, request_id, timestamp, response_json, execution_time_ms, 0)
                )
                
                # Update collection stats
                cursor.execute(
                    '''
                    INSERT INTO collection_stats (name, value, last_updated)
                    VALUES ('response_count', 1, ?)
                    ON CONFLICT(name) DO UPDATE SET
                    value = value + 1,
                    last_updated = ?
                    ''',
                    (timestamp, timestamp)
                )
                
                conn.commit()
                self.log.debug("Logged MCP response", request_id=request_id, response_id=response_id)
        
        except sqlite3.Error as e:
            self.log.error("Failed to log MCP response", error=str(e), request_id=request_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Dictionary of collection statistics
        """
        if not self.enabled:
            return {
                "enabled": False,
                "request_count": 0,
                "response_count": 0
            }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, value FROM collection_stats")
                rows = cursor.fetchall()
                
                stats = {"enabled": True}
                for name, value in rows:
                    stats[name] = value
                
                return stats
        
        except sqlite3.Error as e:
            self.log.error("Failed to get collection statistics", error=str(e))
            return {"enabled": self.enabled, "error": str(e)}
    
    def clear_data(self) -> bool:
        """Clear all collected data.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return True
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM mcp_responses")
                cursor.execute("DELETE FROM mcp_requests")
                cursor.execute("UPDATE collection_stats SET value = 0")
                conn.commit()
                
                self.log.info("Cleared all collected data")
                return True
        
        except sqlite3.Error as e:
            self.log.error("Failed to clear collected data", error=str(e))
            return False
    
    def enable(self) -> None:
        """Enable data collection."""
        if not self.enabled:
            self.enabled = True
            self._init_db()
            self.log.info("MCP data collection enabled")
    
    def disable(self) -> None:
        """Disable data collection."""
        if self.enabled:
            self.enabled = False
            self.log.info("MCP data collection disabled") 