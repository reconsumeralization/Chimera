"""
File Manager Tool for Project Chimera.

This tool provides file system operations through the MCP protocol.
"""

import os
import shutil
import glob
import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import re

from .base import BaseTool

logger = logging.getLogger(__name__)

class FileManagerTool(BaseTool):
    """
    File Manager Tool for Project Chimera.
    
    Provides file system operations including:
    - List directory contents
    - Get file/directory details
    - Create directories
    - Copy files/directories
    - Move/rename files/directories
    - Delete files/directories
    - Read text files
    - Write text files
    - Search for files
    """
    
    TOOL_NAME = "fileManager"
    
    def __init__(self):
        """Initialize the File Manager Tool."""
        super().__init__()
        logger.info("File Manager Tool initialized")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema definition for this tool."""
        return {
            "name": self.TOOL_NAME,
            "description": "Provides file system operations like listing, creating, copying, moving, and deleting files and directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The file operation to perform.",
                        "enum": [
                            "listDirectory",
                            "getFileDetails",
                            "createDirectory",
                            "copyFile",
                            "moveFile",
                            "deleteFile",
                            "readTextFile",
                            "writeTextFile",
                            "searchFiles"
                        ]
                    }
                },
                "required": ["operation"]
            }
        }
    
    def _is_path_traversal_attack(self, path: str) -> bool:
        """
        Check if the path contains path traversal patterns.
        
        Args:
            path: The path to check.
            
        Returns:
            True if the path contains traversal patterns, False otherwise.
        """
        # Check for patterns like "../" or "..\" that might indicate path traversal
        return bool(re.search(r'\.\.[\\/]', path))
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize a path to ensure it's absolute and doesn't contain path traversal.
        
        Args:
            path: The path to normalize.
            
        Returns:
            The normalized path.
            
        Raises:
            ValueError: If the path contains path traversal patterns.
        """
        if self._is_path_traversal_attack(path):
            raise ValueError(f"Path contains path traversal patterns: {path}")
        
        # Normalize the path
        return os.path.normpath(os.path.abspath(path))
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a file system operation.
        
        Args:
            params: Parameters for the operation.
            
        Returns:
            The result of the operation.
        """
        valid, error = self.validate_params(params, ["operation"])
        if not valid:
            return {"error": error}
        
        operation = params.get("operation", "")
        
        try:
            if operation == "listDirectory":
                return await self._handle_list_directory(params)
            elif operation == "getFileDetails":
                return await self._handle_get_file_details(params)
            elif operation == "createDirectory":
                return await self._handle_create_directory(params)
            elif operation == "copyFile":
                return await self._handle_copy_file(params)
            elif operation == "moveFile":
                return await self._handle_move_file(params)
            elif operation == "deleteFile":
                return await self._handle_delete_file(params)
            elif operation == "readTextFile":
                return await self._handle_read_text_file(params)
            elif operation == "writeTextFile":
                return await self._handle_write_text_file(params)
            elif operation == "searchFiles":
                return await self._handle_search_files(params)
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            logger.error(f"Error executing file operation {operation}: {str(e)}", exc_info=True)
            return {"error": f"Error executing file operation: {str(e)}"}
    
    async def _handle_list_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Parameters:
            path: Path to the directory to list.
            include_hidden: Whether to include hidden files (default: False).
        
        Returns:
            Dictionary with entries and additional information.
        """
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        include_hidden = params.get("include_hidden", False)
        
        try:
            # Normalize and validate the path
            path = self._normalize_path(path)
            
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            if not os.path.isdir(path):
                return {"error": f"Path is not a directory: {path}"}
            
            entries = []
            for entry in os.listdir(path):
                # Skip hidden files if not explicitly included
                if entry.startswith('.') and not include_hidden:
                    continue
                
                entry_path = os.path.join(path, entry)
                entry_info = {
                    "name": entry,
                    "path": entry_path,
                    "is_dir": os.path.isdir(entry_path),
                    "size": os.path.getsize(entry_path) if os.path.isfile(entry_path) else None,
                    "last_modified": os.path.getmtime(entry_path),
                }
                entries.append(entry_info)
            
            return {
                "path": path,
                "entries": entries,
                "total_entries": len(entries),
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error listing directory: {str(e)}"}
    
    async def _handle_get_file_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed information about a file or directory.
        
        Parameters:
            path: Path to the file or directory.
        
        Returns:
            Dictionary with detailed file information.
        """
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        
        try:
            # Normalize and validate the path
            path = self._normalize_path(path)
            
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            stats = os.stat(path)
            
            details = {
                "name": os.path.basename(path),
                "path": path,
                "type": "directory" if os.path.isdir(path) else "file",
                "size": os.path.getsize(path) if os.path.isfile(path) else 0,
                "created": stats.st_ctime,
                "modified": stats.st_mtime,
                "accessed": stats.st_atime,
                "is_hidden": os.path.basename(path).startswith('.'),
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK),
                "is_executable": os.access(path, os.X_OK),
            }
            
            return details
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error getting file details: {str(e)}"}
    
    async def _handle_create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new directory.
        
        Parameters:
            path: Path to the directory to create.
            parents: Whether to create parent directories as needed (default: True).
            exist_ok: Whether to ignore if the directory already exists (default: True).
        
        Returns:
            Dictionary with status and path information.
        """
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        parents = params.get("parents", True)
        exist_ok = params.get("exist_ok", True)
        
        try:
            # Normalize and validate the path
            path = self._normalize_path(path)
            
            if parents:
                os.makedirs(path, exist_ok=exist_ok)
            else:
                os.mkdir(path, exist_ok=exist_ok)
            
            return {
                "success": True,
                "path": path,
                "message": f"Directory created: {path}"
            }
            
        except FileExistsError:
            return {"error": f"Directory already exists: {path}"}
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error creating directory: {str(e)}"}
    
    async def _handle_copy_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy a file or directory.
        
        Parameters:
            source: Path to the source file or directory.
            destination: Path to the destination.
            overwrite: Whether to overwrite existing destination (default: False).
        
        Returns:
            Dictionary with status and path information.
        """
        valid, error = self.validate_params(params, ["source", "destination"])
        if not valid:
            return {"error": error}
        
        source = params.get("source", "")
        destination = params.get("destination", "")
        overwrite = params.get("overwrite", False)
        
        try:
            # Normalize and validate the paths
            source = self._normalize_path(source)
            destination = self._normalize_path(destination)
            
            if not os.path.exists(source):
                return {"error": f"Source does not exist: {source}"}
            
            if os.path.exists(destination) and not overwrite:
                return {"error": f"Destination already exists: {destination}"}
            
            if os.path.isdir(source):
                if os.path.exists(destination) and overwrite:
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
            else:
                if os.path.isdir(destination):
                    # If destination is a directory, copy the file into it
                    destination = os.path.join(destination, os.path.basename(source))
                shutil.copy2(source, destination)
            
            return {
                "success": True,
                "source": source,
                "destination": destination,
                "message": f"Copied '{source}' to '{destination}'"
            }
            
        except PermissionError:
            return {"error": f"Permission denied for source '{source}' or destination '{destination}'"}
        except Exception as e:
            return {"error": f"Error copying file: {str(e)}"}
    
    async def _handle_move_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Move or rename a file or directory.
        
        Parameters:
            source: Path to the source file or directory.
            destination: Path to the destination.
            overwrite: Whether to overwrite existing destination (default: False).
        
        Returns:
            Dictionary with status and path information.
        """
        valid, error = self.validate_params(params, ["source", "destination"])
        if not valid:
            return {"error": error}
        
        source = params.get("source", "")
        destination = params.get("destination", "")
        overwrite = params.get("overwrite", False)
        
        try:
            # Normalize and validate the paths
            source = self._normalize_path(source)
            destination = self._normalize_path(destination)
            
            if not os.path.exists(source):
                return {"error": f"Source does not exist: {source}"}
            
            if os.path.exists(destination) and not overwrite:
                return {"error": f"Destination already exists: {destination}"}
            
            if os.path.exists(destination) and overwrite:
                if os.path.isdir(destination):
                    shutil.rmtree(destination)
                else:
                    os.remove(destination)
            
            shutil.move(source, destination)
            
            return {
                "success": True,
                "source": source,
                "destination": destination,
                "message": f"Moved '{source}' to '{destination}'"
            }
            
        except PermissionError:
            return {"error": f"Permission denied for source '{source}' or destination '{destination}'"}
        except Exception as e:
            return {"error": f"Error moving file: {str(e)}"}
    
    async def _handle_delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete a file or directory.
        
        Parameters:
            path: Path to the file or directory to delete.
            recursive: Whether to recursively delete directories (default: False).
        
        Returns:
            Dictionary with status and path information.
        """
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        recursive = params.get("recursive", False)
        
        try:
            # Normalize and validate the path
            path = self._normalize_path(path)
            
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            if os.path.isdir(path):
                if recursive:
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)
            else:
                os.remove(path)
            
            return {
                "success": True,
                "path": path,
                "message": f"Deleted: {path}"
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except OSError as e:
            if "Directory not empty" in str(e):
                return {"error": f"Directory is not empty and recursive delete is not enabled: {path}"}
            else:
                return {"error": f"Error deleting file: {str(e)}"}
        except Exception as e:
            return {"error": f"Error deleting file: {str(e)}"}
    
    async def _handle_read_text_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read the contents of a text file.
        
        Parameters:
            path: Path to the text file to read.
            encoding: Text encoding to use (default: utf-8).
            max_lines: Maximum number of lines to read (default: None, meaning all lines).
            start_line: Line number to start reading from (0-based, default: 0).
        
        Returns:
            Dictionary with file content and metadata.
        """
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        encoding = params.get("encoding", "utf-8")
        max_lines = params.get("max_lines", None)
        start_line = params.get("start_line", 0)
        
        try:
            # Normalize and validate the path
            path = self._normalize_path(path)
            
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            if not os.path.isfile(path):
                return {"error": f"Path is not a file: {path}"}
            
            # Check file size before reading to avoid OOM issues
            file_size = os.path.getsize(path)
            if file_size > 10 * 1024 * 1024:  # 10 MB limit
                return {"error": f"File too large to read: {file_size} bytes"}
            
            if max_lines is not None or start_line > 0:
                # Read specific lines
                content = ""
                with open(path, 'r', encoding=encoding) as f:
                    # Skip lines if start_line > 0
                    for _ in range(start_line):
                        f.readline()
                    
                    # Read up to max_lines
                    if max_lines is not None:
                        lines = []
                        for _ in range(max_lines):
                            line = f.readline()
                            if not line:
                                break
                            lines.append(line)
                        content = "".join(lines)
                    else:
                        content = f.read()
            else:
                # Read the whole file
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
            
            return {
                "path": path,
                "content": content,
                "size": file_size,
                "encoding": encoding,
                "start_line": start_line,
                "max_lines": max_lines
            }
            
        except UnicodeDecodeError:
            return {"error": f"File cannot be decoded with encoding '{encoding}': {path}"}
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error reading text file: {str(e)}"}
    
    async def _handle_write_text_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write content to a text file.
        
        Parameters:
            path: Path to the text file to write.
            content: Content to write to the file.
            encoding: Text encoding to use (default: utf-8).
            append: Whether to append to the file instead of overwriting (default: False).
            create_dirs: Whether to create parent directories if they don't exist (default: True).
        
        Returns:
            Dictionary with status and file metadata.
        """
        valid, error = self.validate_params(params, ["path", "content"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        content = params.get("content", "")
        encoding = params.get("encoding", "utf-8")
        append = params.get("append", False)
        create_dirs = params.get("create_dirs", True)
        
        try:
            # Normalize and validate the path
            path = self._normalize_path(path)
            
            # Create parent directories if needed
            if create_dirs:
                os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Write to the file
            mode = 'a' if append else 'w'
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            file_size = os.path.getsize(path)
            
            return {
                "success": True,
                "path": path,
                "size": file_size,
                "encoding": encoding,
                "append": append,
                "message": f"{'Appended to' if append else 'Wrote'} file: {path}"
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error writing text file: {str(e)}"}
    
    async def _handle_search_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for files matching a pattern.
        
        Parameters:
            path: Base directory for the search.
            pattern: Glob pattern to match files (e.g., "*.txt").
            recursive: Whether to search recursively (default: True).
            max_results: Maximum number of results to return (default: 100).
        
        Returns:
            Dictionary with matching files and metadata.
        """
        valid, error = self.validate_params(params, ["path", "pattern"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        pattern = params.get("pattern", "*")
        recursive = params.get("recursive", True)
        max_results = params.get("max_results", 100)
        
        try:
            # Normalize and validate the path
            path = self._normalize_path(path)
            
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            if not os.path.isdir(path):
                return {"error": f"Path is not a directory: {path}"}
            
            # Construct the search pattern
            if recursive:
                search_pattern = os.path.join(path, "**", pattern)
                matches = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(path, pattern)
                matches = glob.glob(search_pattern, recursive=False)
            
            # Limit results
            if len(matches) > max_results:
                matches = matches[:max_results]
            
            result_matches = []
            for match in matches:
                result_matches.append({
                    "name": os.path.basename(match),
                    "path": match,
                    "is_dir": os.path.isdir(match),
                    "size": os.path.getsize(match) if os.path.isfile(match) else None,
                    "last_modified": os.path.getmtime(match),
                })
            
            return {
                "pattern": pattern,
                "path": path,
                "matches": result_matches,
                "total_matches": len(result_matches),
                "limited": len(matches) >= max_results
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error searching files: {str(e)}"} 