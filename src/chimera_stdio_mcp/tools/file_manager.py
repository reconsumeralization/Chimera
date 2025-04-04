"""
File Manager Tool for Project Chimera.

This tool provides file system operations through the MCP protocol.
"""

import os
import shutil
import glob
import logging
import json
import asyncio
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
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the File Manager Tool.
        
        Args:
            base_path: Optional base path to restrict operations within.
                      If provided, all file operations will be restricted to this path.
        """
        super().__init__()
        self.base_path = Path(base_path).resolve() if base_path else None
        logger.info(f"File Manager Tool initialized with base path: {self.base_path}")
    
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
    
    def _validate_path(self, path: str) -> Path:
        """
        Validate path is safe and within base_path if set.
        
        Args:
            path: The path to validate.
            
        Returns:
            The resolved Path object.
            
        Raises:
            ValueError: If the path is outside allowed base_path.
        """
        # Path resolution handles symbolic links and normalizes the path.
        # Security Note: Path.resolve() might interact with the filesystem.
        # Consider potential implications in highly sensitive environments.
        try:
            resolved_path = Path(path).resolve(strict=True) # strict=True ensures the path exists
        except FileNotFoundError:
            # Handle cases where intermediate components might not exist yet (e.g., for mkdir)
            # We still resolve to get an absolute path, but don't require existence here.
            # The existence check will happen in the specific handler if needed.
            resolved_path = Path(path).resolve()
        except Exception as e:
            # Catch other resolution errors (e.g., invalid characters on Windows)
            raise ValueError(f"Invalid path format or resolution error: {path} - {e}") from e

        # Check if path is within base_path if base_path is set
        if self.base_path:
            # Ensure base_path itself is resolved and exists for comparison
            if not self.base_path.exists() or not self.base_path.is_dir():
                raise ValueError(f"Invalid base path configuration: {self.base_path}")
                
            if not resolved_path.is_relative_to(self.base_path):
                raise ValueError(f"Path {path} is outside allowed base path {self.base_path}")
        
        return resolved_path
    
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
            # Validate path
            path_obj = self._validate_path(path)
            
            if not await asyncio.to_thread(os.path.exists, path_obj):
                return {"error": f"Path does not exist: {path_obj}"}
            
            if not await asyncio.to_thread(os.path.isdir, path_obj):
                return {"error": f"Path is not a directory: {path_obj}"}
            
            entries = []
            dir_entries = await asyncio.to_thread(os.listdir, path_obj)
            
            for entry in dir_entries:
                # Skip hidden files if not explicitly included
                if entry.startswith('.') and not include_hidden:
                    continue
                
                entry_path = os.path.join(path_obj, entry)
                is_dir = await asyncio.to_thread(os.path.isdir, entry_path)
                size = await asyncio.to_thread(os.path.getsize, entry_path) if not is_dir else None
                last_modified = await asyncio.to_thread(os.path.getmtime, entry_path)
                
                entry_info = {
                    "name": entry,
                    "path": str(entry_path),
                    "is_dir": is_dir,
                    "size": size,
                    "last_modified": last_modified,
                }
                entries.append(entry_info)
            
            return {
                "path": str(path_obj),
                "entries": entries,
                "total_entries": len(entries),
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except ValueError as e:
            return {"error": str(e)}
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
            # Validate path
            path_obj = self._validate_path(path)
            
            if not await asyncio.to_thread(os.path.exists, path_obj):
                return {"error": f"Path does not exist: {path_obj}"}
            
            # Use asyncio.to_thread for all os functions
            stats = await asyncio.to_thread(os.stat, path_obj)
            is_dir = await asyncio.to_thread(os.path.isdir, path_obj)
            size = await asyncio.to_thread(os.path.getsize, path_obj) if not is_dir else 0
            is_readable = await asyncio.to_thread(os.access, path_obj, os.R_OK)
            is_writable = await asyncio.to_thread(os.access, path_obj, os.W_OK)
            is_executable = await asyncio.to_thread(os.access, path_obj, os.X_OK)
            
            details = {
                "name": os.path.basename(path_obj),
                "path": str(path_obj),
                "type": "directory" if is_dir else "file",
                "size": size,
                "created": stats.st_ctime,
                "modified": stats.st_mtime,
                "accessed": stats.st_atime,
                "is_hidden": os.path.basename(path_obj).startswith('.'),
                "is_readable": is_readable,
                "is_writable": is_writable,
                "is_executable": is_executable,
            }
            
            return details
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Error getting file details: {str(e)}"}
    
    async def _handle_create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new directory.
        
        Parameters:
            path: Path to the directory to create.
            parents: Create parent directories if needed (default: True).
            exist_ok: Don't raise error if directory already exists (default: False).
        
        Returns:
            Dictionary indicating success or error.
        """
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        parents = params.get("parents", True)
        exist_ok = params.get("exist_ok", False)
        
        try:
            # Validate path - note: path might not exist yet, so _validate_path handles this
            path_obj = self._validate_path(path)
            
            # Use asyncio.to_thread for os.makedirs/os.mkdir
            if parents:
                await asyncio.to_thread(os.makedirs, path_obj, exist_ok=exist_ok)
            else:
                await asyncio.to_thread(os.mkdir, path_obj) # exist_ok not directly supported for mkdir, handled by check below
            
            return {
                "success": True,
                "path": str(path_obj),
                "message": f"Directory created: {path_obj}"
            }
            
        except FileExistsError:
            if exist_ok:
                 return {
                    "success": True,
                    "path": str(path_obj),
                    "message": f"Directory already exists: {path_obj}"
                 }
            else:
                return {"error": f"Directory already exists: {path_obj}"}
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Error creating directory: {str(e)}"}
    
    async def _handle_copy_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy a file or directory.
        
        Parameters:
            source: Path to the source file or directory.
            destination: Path to the destination.
            overwrite: Whether to overwrite if destination exists (default: False).
        
        Returns:
            Dictionary indicating success or error.
        """
        valid, error = self.validate_params(params, ["source", "destination"])
        if not valid:
            return {"error": error}
        
        source = params.get("source", "")
        destination = params.get("destination", "")
        overwrite = params.get("overwrite", False)
        
        try:
            # Validate paths
            source_obj = self._validate_path(source)
            # Destination might not exist, or be a directory, validation needs care
            dest_parent = Path(destination).parent
            self._validate_path(str(dest_parent)) # Validate parent dir is within bounds
            dest_obj = dest_parent.resolve() / Path(destination).name # Construct resolved dest path

            # Check source existence using asyncio.to_thread
            if not await asyncio.to_thread(os.path.exists, source_obj):
                return {"error": f"Source does not exist: {source_obj}"}
            
            # Check destination existence using asyncio.to_thread
            dest_exists = await asyncio.to_thread(os.path.exists, dest_obj)
            if dest_exists and not overwrite:
                return {"error": f"Destination already exists: {dest_obj}"}
            
            # Perform copy operation using asyncio.to_thread
            is_dir = await asyncio.to_thread(os.path.isdir, source_obj)
            
            if is_dir:
                # Copying a directory
                if dest_exists and overwrite:
                    await asyncio.to_thread(shutil.rmtree, dest_obj)
                await asyncio.to_thread(shutil.copytree, source_obj, dest_obj)
            else:
                # Copying a file
                dest_is_dir = await asyncio.to_thread(os.path.isdir, dest_obj) if dest_exists else False
                if dest_is_dir:
                     # If destination is an existing directory, copy the file into it
                     final_dest_obj = dest_obj / source_obj.name
                     if await asyncio.to_thread(os.path.exists, final_dest_obj) and not overwrite:
                          return {"error": f"Destination file already exists in directory: {final_dest_obj}"}
                     await asyncio.to_thread(shutil.copy2, source_obj, final_dest_obj)
                else:
                     # If destination is a file path or doesn't exist
                     if dest_exists and overwrite:
                          await asyncio.to_thread(os.remove, dest_obj)
                     # Ensure destination directory exists if copying a file to a new path
                     await asyncio.to_thread(os.makedirs, dest_obj.parent, exist_ok=True)
                     await asyncio.to_thread(shutil.copy2, source_obj, dest_obj)
            
            return {
                "success": True,
                "source": str(source_obj),
                "destination": str(dest_obj),
                "message": f"Copied '{source_obj}' to '{dest_obj}'"
            }
            
        except PermissionError:
            return {"error": f"Permission denied for source '{source}' or destination '{destination}'"}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Error copying file: {str(e)}"}
    
    async def _handle_move_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Move/rename a file or directory.
        
        Parameters:
            source: Path to the source file or directory.
            destination: Path to the destination.
            overwrite: Whether to overwrite if destination exists (default: False).
        
        Returns:
            Dictionary indicating success or error.
        """
        valid, error = self.validate_params(params, ["source", "destination"])
        if not valid:
            return {"error": error}
        
        source = params.get("source", "")
        destination = params.get("destination", "")
        overwrite = params.get("overwrite", False)
        
        try:
            # Validate paths
            source_obj = self._validate_path(source)
            # Destination might not exist, validate parent
            dest_parent = Path(destination).parent
            self._validate_path(str(dest_parent))
            dest_obj = dest_parent.resolve() / Path(destination).name
            
            # Check source existence
            if not await asyncio.to_thread(os.path.exists, source_obj):
                return {"error": f"Source does not exist: {source_obj}"}
            
            # Check destination existence and handle overwrite
            dest_exists = await asyncio.to_thread(os.path.exists, dest_obj)
            if dest_exists and not overwrite:
                return {"error": f"Destination already exists: {dest_obj}"}
            
            # Handle overwrite case using asyncio.to_thread
            if dest_exists and overwrite:
                if await asyncio.to_thread(os.path.isdir, dest_obj):
                    await asyncio.to_thread(shutil.rmtree, dest_obj)
                else:
                    await asyncio.to_thread(os.remove, dest_obj)
            
            # Perform the move operation using asyncio.to_thread
            await asyncio.to_thread(shutil.move, source_obj, dest_obj)
            
            return {
                "success": True,
                "source": str(source_obj),
                "destination": str(dest_obj),
                "message": f"Moved '{source_obj}' to '{dest_obj}'"
            }
            
        except PermissionError:
            return {"error": f"Permission denied for source '{source}' or destination '{destination}'"}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Error moving file: {str(e)}"}
    
    async def _handle_delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete a file or directory.
        
        Parameters:
            path: Path to the file or directory to delete.
            recursive: Allow deleting non-empty directories (default: True).
        
        Returns:
            Dictionary indicating success or error.
        """
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        recursive = params.get("recursive", True)
        
        try:
            # Validate path
            path_obj = self._validate_path(path)
            
            # Check existence
            if not await asyncio.to_thread(os.path.exists, path_obj):
                # Allow deletion attempt on non-existent path to be idempotent
                return {
                    "success": True, 
                    "path": str(path_obj), 
                    "message": f"Path does not exist (considered success): {path_obj}"
                }
            
            # Perform delete operation using asyncio.to_thread
            is_dir = await asyncio.to_thread(os.path.isdir, path_obj)
            
            if is_dir:
                 if recursive:
                     await asyncio.to_thread(shutil.rmtree, path_obj)
                 else:
                     # Check if directory is empty before deleting
                     if await asyncio.to_thread(os.listdir, path_obj):
                          return {"error": f"Directory not empty, cannot delete non-recursively: {path_obj}"}
                     await asyncio.to_thread(os.rmdir, path_obj)
            else:
                 await asyncio.to_thread(os.remove, path_obj)
            
            return {
                "success": True,
                "path": str(path_obj),
                "message": f"Deleted: {path_obj}"
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except ValueError as e:
            return {"error": str(e)}
        except OSError as e:
            # Catch specific OS errors like directory not empty if non-recursive delete fails
            if not recursive and e.errno == 39: # ENOTEMPTY
                 return {"error": f"Directory not empty: {path}"}
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
            # Validate path
            path_obj = self._validate_path(path)
            
            if not await asyncio.to_thread(os.path.exists, path_obj):
                return {"error": f"Path does not exist: {path_obj}"}
            
            if not await asyncio.to_thread(os.path.isfile, path_obj):
                return {"error": f"Path is not a file: {path_obj}"}
            
            # Check file size before reading to avoid OOM issues
            file_size = await asyncio.to_thread(os.path.getsize, path_obj)
            if file_size > 10 * 1024 * 1024:  # 10 MB limit
                return {"error": f"File too large to read: {file_size} bytes"}
            
            async def read_file_content(path, encoding, max_lines, start_line):
                """Helper function to read file content asynchronously."""
                def _read_file(path, encoding, max_lines, start_line):
                    """Synchronous file read function to be run in a thread."""
                    try:
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
                        return content
                    except Exception as e:
                        raise e
                
                return await asyncio.to_thread(_read_file, path, encoding, max_lines, start_line)
            
            # Read the file content
            content = await read_file_content(path_obj, encoding, max_lines, start_line)
            
            return {
                "path": str(path_obj),
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
        except ValueError as e:
            return {"error": str(e)}
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
            # Validate path
            path_obj = self._validate_path(path)
            
            # Create parent directories if needed
            if create_dirs:
                await asyncio.to_thread(os.makedirs, os.path.dirname(path_obj), exist_ok=True)
            
            # Write to the file using asyncio.to_thread
            async def write_file_content(path, content, mode, encoding):
                """Helper function to write file content asynchronously."""
                def _write_file(path, content, mode, encoding):
                    """Synchronous file write function to be run in a thread."""
                    try:
                        with open(path, mode, encoding=encoding) as f:
                            f.write(content)
                    except Exception as e:
                        raise e
                
                return await asyncio.to_thread(_write_file, path, content, mode, encoding)
            
            # Write the file content
            mode = 'a' if append else 'w'
            await write_file_content(path_obj, content, mode, encoding)
            
            file_size = await asyncio.to_thread(os.path.getsize, path_obj)
            
            return {
                "success": True,
                "path": str(path_obj),
                "size": file_size,
                "encoding": encoding,
                "append": append,
                "message": f"{'Appended to' if append else 'Wrote'} file: {path_obj}"
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except ValueError as e:
            return {"error": str(e)}
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
            # Validate path
            path_obj = self._validate_path(path)
            
            if not await asyncio.to_thread(os.path.exists, path_obj):
                return {"error": f"Path does not exist: {path_obj}"}
            
            if not await asyncio.to_thread(os.path.isdir, path_obj):
                return {"error": f"Path is not a directory: {path_obj}"}
            
            # Use asyncio.to_thread for glob.glob
            def _perform_glob(search_pattern, recursive):
                return glob.glob(search_pattern, recursive=recursive)

            search_path_str = str(path_obj)
            if recursive:
                search_pattern = os.path.join(search_path_str, "**", pattern)
                matches = await asyncio.to_thread(_perform_glob, search_pattern, True)
            else:
                search_pattern = os.path.join(search_path_str, pattern)
                matches = await asyncio.to_thread(_perform_glob, search_pattern, False)
            
            # Limit results
            limited = len(matches) > max_results
            if limited:
                matches = matches[:max_results]
            
            # Get details for each match using asyncio.to_thread
            result_matches = []
            for match_path_str in matches:
                try:
                     match_path_obj = Path(match_path_str) # Resolve not strictly needed, glob gives absolute
                     # Validate each match is still within the base path (important for recursive searches)
                     if self.base_path and not match_path_obj.is_relative_to(self.base_path):
                          logger.warning(f"Skipping search result outside base path: {match_path_str}")
                          continue
                     
                     is_dir = await asyncio.to_thread(os.path.isdir, match_path_obj)
                     size = await asyncio.to_thread(os.path.getsize, match_path_obj) if not is_dir else None
                     last_modified = await asyncio.to_thread(os.path.getmtime, match_path_obj)
                     
                     result_matches.append({
                          "name": match_path_obj.name,
                          "path": str(match_path_obj),
                          "is_dir": is_dir,
                          "size": size,
                          "last_modified": last_modified,
                     })
                except (FileNotFoundError, PermissionError, Exception) as e:
                     # Log error but continue processing other matches
                     logger.warning(f"Error processing search match '{match_path_str}': {e}")
            
            return {
                "pattern": pattern,
                "path": str(path_obj),
                "matches": result_matches,
                "total_matches": len(result_matches),
                "limited": limited
            }
            
        except PermissionError:
            return {"error": f"Permission denied for path: {path}"}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Error searching files: {str(e)}"} 