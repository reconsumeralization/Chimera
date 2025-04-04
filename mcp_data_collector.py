#!/usr/bin/env python
"""
MCP Data Collector

Collects and processes MCP traffic data for AI training purposes.
This module provides functionality to:
1. Intercept and log MCP communications
2. Store data in a structured format for later training
3. Anonymize sensitive information
4. Configure what data is collected based on user preferences
"""

import os
import json
import logging
import sqlite3
import time
import uuid
import re
import hashlib
import shutil
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global instance for singleton pattern
_collector_instance = None

def get_collector(data_dir: str = "data", enabled: bool = True) -> 'MCPDataCollector':
    """
    Get or create the MCPDataCollector instance.
    
    Args:
        data_dir: Directory to store collected data (only used on first initialization)
        enabled: Whether data collection is enabled (only used on first initialization)
        
    Returns:
        The MCPDataCollector instance
    """
    global _collector_instance
    if _collector_instance is None:
        logger.info(f"Initializing data collector (data_dir={data_dir}, enabled={enabled})")
        _collector_instance = MCPDataCollector(data_dir, enabled)
    return _collector_instance

class MCPDataCollector:
    """
    Collects MCP traffic data for AI training.
    
    This class is responsible for intercepting and logging MCP communications,
    storing the data in a structured format, and providing tools for exporting
    the collected data for AI training purposes.
    """
    
    def __init__(self, data_dir: str = "data", enabled: bool = True):
        """
        Initialize the data collector.
        
        Args:
            data_dir: Directory to store collected data
            enabled: Whether data collection is enabled
        """
        self.data_dir = data_dir
        self.enabled = enabled
        self.db_path = os.path.join(data_dir, "mcp_data.db")
        self.session_id = str(uuid.uuid4())
        self.anonymize_patterns = [
            (r'password\s*=\s*["\'].*["\']', 'password="***"'),
            (r'api_key\s*=\s*["\'].*["\']', 'api_key="***"'),
            (r'secret\s*=\s*["\'].*["\']', 'secret="***"'),
            (r'token\s*=\s*["\'].*["\']', 'token="***"')
        ]
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize the database
        self._init_db()
        
        logger.info(f"MCPDataCollector initialized (enabled={enabled}, data_dir={data_dir})")
    
    def _init_db(self):
        """Initialize the SQLite database with the required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create requests table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                tool_name TEXT,
                params TEXT
            )
            ''')
            
            # Create responses table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id TEXT PRIMARY KEY,
                request_id TEXT,
                timestamp TEXT,
                result TEXT,
                status TEXT,
                execution_time REAL,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
            ''')
            
            # Create code_snapshots table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_snapshots (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                file_path TEXT,
                code TEXT,
                language TEXT,
                request_id TEXT,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
            ''')
            
            # Create user_interactions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_interactions (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                interaction_type TEXT,
                content TEXT,
                request_id TEXT,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable data collection."""
        self.enabled = enabled
        logger.info(f"Data collection {'enabled' if enabled else 'disabled'}")
    
    def log_mcp_request(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        Log an MCP request.
        
        Args:
            tool_name: Name of the MCP tool
            params: Parameters sent to the tool
            
        Returns:
            Request ID (UUID)
        """
        if not self.enabled:
            return ""
        
        try:
            request_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now().isoformat()
            
            # Anonymize sensitive data in params
            anonymized_params = self._anonymize_data(params)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO requests VALUES (?, ?, ?, ?)",
                (request_id, timestamp, tool_name, json.dumps(anonymized_params))
            )
            conn.commit()
            conn.close()
            
            logger.debug(f"Logged MCP request: {tool_name} (request_id={request_id})")
            return request_id
        except Exception as e:
            logger.error(f"Error logging MCP request: {e}")
            return ""
    
    def log_mcp_response(self, request_id: str, result: Dict[str, Any], 
                         status: str, execution_time: float) -> str:
        """
        Log an MCP response.
        
        Args:
            request_id: ID of the corresponding request
            result: Result returned by the MCP tool
            status: Status of the response (success/error)
            execution_time: Time taken to execute the request (in seconds)
            
        Returns:
            Response ID (UUID)
        """
        if not self.enabled or not request_id:
            return ""
        
        try:
            response_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now().isoformat()
            
            # Anonymize sensitive data in result
            anonymized_result = self._anonymize_data(result)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO responses VALUES (?, ?, ?, ?, ?, ?)",
                (response_id, request_id, timestamp, json.dumps(anonymized_result), 
                 status, execution_time)
            )
            conn.commit()
            conn.close()
            
            logger.debug(f"Logged MCP response (request_id={request_id}, status={status})")
            return response_id
        except Exception as e:
            logger.error(f"Error logging MCP response: {e}")
            return ""
    
    def log_code_snapshot(self, file_path: str, code: str, language: str, 
                          request_id: str = "") -> str:
        """
        Log a snapshot of code.
        
        Args:
            file_path: Path to the file
            code: Code content
            language: Programming language
            request_id: ID of the related request (if applicable)
            
        Returns:
            Snapshot ID (UUID)
        """
        if not self.enabled:
            return ""
        
        try:
            snapshot_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO code_snapshots VALUES (?, ?, ?, ?, ?, ?)",
                (snapshot_id, timestamp, file_path, code, language, request_id)
            )
            conn.commit()
            conn.close()
            
            logger.debug(f"Logged code snapshot: {file_path} (snapshot_id={snapshot_id})")
            return snapshot_id
        except Exception as e:
            logger.error(f"Error logging code snapshot: {e}")
            return ""
    
    def log_user_interaction(self, interaction_type: str, content: str, 
                            request_id: str = "") -> str:
        """
        Log a user interaction.
        
        Args:
            interaction_type: Type of interaction (e.g., message, command)
            content: Content of the interaction
            request_id: ID of the related request (if applicable)
            
        Returns:
            Interaction ID (UUID)
        """
        if not self.enabled:
            return ""
        
        try:
            interaction_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now().isoformat()
            
            # Anonymize sensitive data in content
            anonymized_content = self._anonymize_text(content)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_interactions VALUES (?, ?, ?, ?, ?)",
                (interaction_id, timestamp, interaction_type, anonymized_content, request_id)
            )
            conn.commit()
            conn.close()
            
            logger.debug(f"Logged user interaction: {interaction_type} (interaction_id={interaction_id})")
            return interaction_id
        except Exception as e:
            logger.error(f"Error logging user interaction: {e}")
            return ""
    
    def _anonymize_data(self, data: Any) -> Any:
        """
        Anonymize sensitive data in a complex data structure.
        
        Args:
            data: Data structure to anonymize
            
        Returns:
            Anonymized data structure
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Check if the key suggests sensitive information
                if any(pattern in key.lower() for pattern in [
                    "password", "token", "key", "secret", "auth", "credential", "api_key"
                ]):
                    result[key] = "***REDACTED***"
                else:
                    result[key] = self._anonymize_data(value)
            return result
        elif isinstance(data, list):
            return [self._anonymize_data(item) for item in data]
        elif isinstance(data, str):
            return self._anonymize_text(data)
        else:
            return data
    
    def _anonymize_text(self, text: str) -> str:
        """
        Anonymize sensitive data in text.
        
        Args:
            text: Text to anonymize
            
        Returns:
            Anonymized text
        """
        # Patterns for various sensitive information
        patterns = [
            # API Keys, Authentication tokens
            (r'(api[_-]?key|auth[_-]?token|access[_-]?token)[=:"\'\s]+([a-zA-Z0-9]{16,})', r'\1=***REDACTED***'),
            # Passwords in config or code
            (r'(password|passwd|pwd)[=:"\'\s]+([^\'"\s&;]{3,})', r'\1=***REDACTED***'),
            # Email addresses
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL***'),
            # Connection strings
            (r'(mongodb|postgresql|mysql|jdbc|connection)[=:"\'\s]+([^\'"\s&;]{10,})', r'\1=***REDACTED***'),
            # OAuth client secrets
            (r'(client[_-]?secret)[=:"\'\s]+([a-zA-Z0-9_-]{10,})', r'\1=***REDACTED***'),
        ]
        
        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about collected data.
        
        Returns:
            Dictionary containing statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get counts from each table
            cursor.execute("SELECT COUNT(*) FROM requests")
            request_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM responses")
            response_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM code_snapshots")
            snapshot_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_interactions")
            interaction_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT tool_name, COUNT(*) FROM requests GROUP BY tool_name")
            tool_usage = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get database size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            conn.close()
            
            return {
                "enabled": self.enabled,
                "request_count": request_count,
                "response_count": response_count,
                "snapshot_count": snapshot_count,
                "interaction_count": interaction_count,
                "tool_usage": tool_usage,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "data_directory": self.data_dir
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "enabled": self.enabled,
                "error": str(e),
                "data_directory": self.data_dir
            }
    
    def export_data(self, output_dir: str = "exported_data") -> bool:
        """
        Export collected data for AI training.
        
        Args:
            output_dir: Directory to export data to
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Data collection is disabled, nothing to export")
            return False
        
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            export_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            export_subdir = os.path.join(output_dir, f"export_{export_time}")
            os.makedirs(export_subdir, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Export requests
            cursor.execute("SELECT * FROM requests")
            requests = [dict(row) for row in cursor.fetchall()]
            with open(os.path.join(export_subdir, "requests.json"), "w") as f:
                json.dump(requests, f, indent=2)
            
            # Export responses
            cursor.execute("""
                SELECT r.*, q.tool_name 
                FROM responses r
                JOIN requests q ON r.request_id = q.id
            """)
            responses = [dict(row) for row in cursor.fetchall()]
            with open(os.path.join(export_subdir, "responses.json"), "w") as f:
                json.dump(responses, f, indent=2)
            
            # Export code snapshots
            cursor.execute("SELECT * FROM code_snapshots")
            snapshots = [dict(row) for row in cursor.fetchall()]
            with open(os.path.join(export_subdir, "code_snapshots.json"), "w") as f:
                json.dump(snapshots, f, indent=2)
            
            # Export user interactions
            cursor.execute("SELECT * FROM user_interactions")
            interactions = [dict(row) for row in cursor.fetchall()]
            with open(os.path.join(export_subdir, "user_interactions.json"), "w") as f:
                json.dump(interactions, f, indent=2)
            
            # Generate statistics
            stats = self.get_statistics()
            with open(os.path.join(export_subdir, "statistics.json"), "w") as f:
                json.dump(stats, f, indent=2)
            
            # Copy database backup
            shutil.copy2(self.db_path, os.path.join(export_subdir, "mcp_data.db"))
            
            # Generate report
            with open(os.path.join(export_subdir, "README.md"), "w") as f:
                f.write(f"# MCP Data Export ({export_time})\n\n")
                f.write(f"* Requests: {stats['request_count']}\n")
                f.write(f"* Responses: {stats['response_count']}\n")
                f.write(f"* Code Snapshots: {stats['snapshot_count']}\n")
                f.write(f"* User Interactions: {stats['interaction_count']}\n")
                f.write(f"* Database Size: {stats['database_size_mb']} MB\n\n")
                
                f.write("## Tool Usage\n\n")
                for tool, count in stats.get('tool_usage', {}).items():
                    f.write(f"* {tool}: {count}\n")
            
            conn.close()
            
            logger.info(f"Data exported to {export_subdir}")
            return True
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False

if __name__ == "__main__":
    # When run directly, show statistics
    collector = get_collector()
    stats = collector.get_statistics()
    print(f"MCP Data Collector Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}") 