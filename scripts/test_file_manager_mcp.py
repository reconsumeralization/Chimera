#!/usr/bin/env python
"""
Test script for the File Manager MCP Tool.
"""

import asyncio
import json
import logging
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_file_manager_mcp")

# Mock File Manager tool for testing
class BaseTool:
    """Mock base tool class."""
    
    def validate_params(self, params, required_params):
        """Validate required parameters."""
        missing = [param for param in required_params if param not in params]
        if missing:
            error_msg = f"Missing required parameters: {', '.join(missing)}"
            return False, error_msg
        return True, None

class MockFileManagerTool(BaseTool):
    """Mock File Manager tool for testing."""
    
    def __init__(self):
        """Initialize with a temporary test directory."""
        self.test_dir = tempfile.mkdtemp(prefix="file_manager_test_")
        logger.info(f"Created test directory: {self.test_dir}")
        
        # Create some files in the test directory
        self._create_test_files()
    
    def _create_test_files(self):
        """Create test files and directories."""
        # Create a few subdirectories
        docs_dir = os.path.join(self.test_dir, "documents")
        os.makedirs(docs_dir)
        
        images_dir = os.path.join(self.test_dir, "images")
        os.makedirs(images_dir)
        
        # Create some text files
        with open(os.path.join(self.test_dir, "readme.txt"), "w") as f:
            f.write("This is a test readme file.\nIt has multiple lines.\nUsed for testing the file manager MCP.")
        
        with open(os.path.join(docs_dir, "document1.txt"), "w") as f:
            f.write("This is document 1.")
        
        with open(os.path.join(docs_dir, "document2.txt"), "w") as f:
            f.write("This is document 2.")
        
        # Create a hidden file
        with open(os.path.join(self.test_dir, ".hidden_file"), "w") as f:
            f.write("This is a hidden file.")
    
    def cleanup(self):
        """Clean up temporary test directory."""
        try:
            shutil.rmtree(self.test_dir)
            logger.info(f"Cleaned up test directory: {self.test_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up test directory: {e}")
    
    async def execute(self, params):
        """Execute mock file manager operations."""
        valid, error = self.validate_params(params, ["operation"])
        if not valid:
            return {"error": error}
        
        operation = params.get("operation", "")
        
        if operation == "listDirectory":
            return await self._mock_list_directory(params)
        elif operation == "getFileDetails":
            return await self._mock_get_file_details(params)
        elif operation == "createDirectory":
            return await self._mock_create_directory(params)
        elif operation == "copyFile":
            return await self._mock_copy_file(params)
        elif operation == "moveFile":
            return await self._mock_move_file(params)
        elif operation == "deleteFile":
            return await self._mock_delete_file(params)
        elif operation == "readTextFile":
            return await self._mock_read_text_file(params)
        elif operation == "writeTextFile":
            return await self._mock_write_text_file(params)
        elif operation == "searchFiles":
            return await self._mock_search_files(params)
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    async def _mock_list_directory(self, params):
        """Mock listing directory contents."""
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        include_hidden = params.get("include_hidden", False)
        
        # If path is a relative path, make it relative to the test directory
        if not os.path.isabs(path):
            path = os.path.join(self.test_dir, path)
        
        logger.info(f"Listing directory: {path}")
        
        try:
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
            
        except FileNotFoundError:
            return {"error": f"Path not found: {path}"}
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error listing directory: {str(e)}"}
    
    async def _mock_get_file_details(self, params):
        """Mock getting file details."""
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        
        # If path is a relative path, make it relative to the test directory
        if not os.path.isabs(path):
            path = os.path.join(self.test_dir, path)
        
        logger.info(f"Getting file details: {path}")
        
        try:
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
    
    async def _mock_create_directory(self, params):
        """Mock creating a directory."""
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        
        # If path is a relative path, make it relative to the test directory
        if not os.path.isabs(path):
            path = os.path.join(self.test_dir, path)
        
        logger.info(f"Creating directory: {path}")
        
        try:
            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": path,
                "message": f"Directory created: {path}"
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error creating directory: {str(e)}"}
    
    async def _mock_copy_file(self, params):
        """Mock copying a file."""
        valid, error = self.validate_params(params, ["source", "destination"])
        if not valid:
            return {"error": error}
        
        source = params.get("source", "")
        destination = params.get("destination", "")
        
        # If paths are relative, make them relative to the test directory
        if not os.path.isabs(source):
            source = os.path.join(self.test_dir, source)
        if not os.path.isabs(destination):
            destination = os.path.join(self.test_dir, destination)
        
        logger.info(f"Copying file: {source} to {destination}")
        
        try:
            if not os.path.exists(source):
                return {"error": f"Source does not exist: {source}"}
            
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
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
    
    async def _mock_move_file(self, params):
        """Mock moving a file."""
        valid, error = self.validate_params(params, ["source", "destination"])
        if not valid:
            return {"error": error}
        
        source = params.get("source", "")
        destination = params.get("destination", "")
        
        # If paths are relative, make them relative to the test directory
        if not os.path.isabs(source):
            source = os.path.join(self.test_dir, source)
        if not os.path.isabs(destination):
            destination = os.path.join(self.test_dir, destination)
        
        logger.info(f"Moving file: {source} to {destination}")
        
        try:
            if not os.path.exists(source):
                return {"error": f"Source does not exist: {source}"}
            
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
    
    async def _mock_delete_file(self, params):
        """Mock deleting a file."""
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        recursive = params.get("recursive", False)
        
        # If path is a relative path, make it relative to the test directory
        if not os.path.isabs(path):
            path = os.path.join(self.test_dir, path)
        
        logger.info(f"Deleting file: {path}")
        
        try:
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
    
    async def _mock_read_text_file(self, params):
        """Mock reading a text file."""
        valid, error = self.validate_params(params, ["path"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        encoding = params.get("encoding", "utf-8")
        
        # If path is a relative path, make it relative to the test directory
        if not os.path.isabs(path):
            path = os.path.join(self.test_dir, path)
        
        logger.info(f"Reading text file: {path}")
        
        try:
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            if not os.path.isfile(path):
                return {"error": f"Path is not a file: {path}"}
            
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                "path": path,
                "content": content,
                "size": os.path.getsize(path),
                "encoding": encoding
            }
            
        except UnicodeDecodeError:
            return {"error": f"File cannot be decoded with encoding '{encoding}': {path}"}
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error reading text file: {str(e)}"}
    
    async def _mock_write_text_file(self, params):
        """Mock writing to a text file."""
        valid, error = self.validate_params(params, ["path", "content"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        content = params.get("content", "")
        encoding = params.get("encoding", "utf-8")
        append = params.get("append", False)
        
        # If path is a relative path, make it relative to the test directory
        if not os.path.isabs(path):
            path = os.path.join(self.test_dir, path)
        
        logger.info(f"Writing text file: {path}")
        
        try:
            mode = 'a' if append else 'w'
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "path": path,
                "size": os.path.getsize(path),
                "encoding": encoding,
                "append": append,
                "message": f"{'Appended to' if append else 'Wrote'} file: {path}"
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error writing text file: {str(e)}"}
    
    async def _mock_search_files(self, params):
        """Mock searching for files matching a pattern."""
        valid, error = self.validate_params(params, ["path", "pattern"])
        if not valid:
            return {"error": error}
        
        path = params.get("path", "")
        pattern = params.get("pattern", "*")
        recursive = params.get("recursive", True)
        
        # If path is a relative path, make it relative to the test directory
        if not os.path.isabs(path):
            path = os.path.join(self.test_dir, path)
        
        logger.info(f"Searching files: {path} with pattern {pattern}")
        
        try:
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            if not os.path.isdir(path):
                return {"error": f"Path is not a directory: {path}"}
            
            import glob
            
            # Construct the search pattern
            if recursive:
                search_pattern = os.path.join(path, "**", pattern)
                matches = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(path, pattern)
                matches = glob.glob(search_pattern, recursive=False)
            
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
                "total_matches": len(result_matches)
            }
            
        except PermissionError:
            return {"error": f"Permission denied: {path}"}
        except Exception as e:
            return {"error": f"Error searching files: {str(e)}"}

async def test_list_directory():
    """Test listing directory contents."""
    tool = MockFileManagerTool()
    
    try:
        logger.info("\n\nTesting list directory...")
        
        # Test listing the root test directory
        params = {
            "operation": "listDirectory",
            "path": tool.test_dir
        }
        
        result = await tool.execute(params)
        logger.info(f"List directory result:\n{json.dumps(result, indent=2)}")
        
        # Test listing with hidden files
        params = {
            "operation": "listDirectory",
            "path": tool.test_dir,
            "include_hidden": True
        }
        
        result = await tool.execute(params)
        logger.info(f"List directory with hidden files result:\n{json.dumps(result, indent=2)}")
        
        # Test listing a subdirectory
        params = {
            "operation": "listDirectory",
            "path": os.path.join(tool.test_dir, "documents")
        }
        
        result = await tool.execute(params)
        logger.info(f"List subdirectory result:\n{json.dumps(result, indent=2)}")
        
        return result
    finally:
        tool.cleanup()

async def test_file_operations():
    """Test file operations (create, read, write, copy, move, delete)."""
    tool = MockFileManagerTool()
    
    try:
        logger.info("\n\nTesting file operations...")
        
        # Create a new directory
        params = {
            "operation": "createDirectory",
            "path": os.path.join(tool.test_dir, "new_directory")
        }
        
        result = await tool.execute(params)
        logger.info(f"Create directory result:\n{json.dumps(result, indent=2)}")
        
        # Write a new file
        params = {
            "operation": "writeTextFile",
            "path": os.path.join(tool.test_dir, "new_directory", "test_file.txt"),
            "content": "This is a test file.\nCreated for testing the file manager MCP."
        }
        
        result = await tool.execute(params)
        logger.info(f"Write file result:\n{json.dumps(result, indent=2)}")
        
        # Read the file
        params = {
            "operation": "readTextFile",
            "path": os.path.join(tool.test_dir, "new_directory", "test_file.txt")
        }
        
        result = await tool.execute(params)
        logger.info(f"Read file result:\n{json.dumps(result, indent=2)}")
        
        # Copy the file
        params = {
            "operation": "copyFile",
            "source": os.path.join(tool.test_dir, "new_directory", "test_file.txt"),
            "destination": os.path.join(tool.test_dir, "test_file_copy.txt")
        }
        
        result = await tool.execute(params)
        logger.info(f"Copy file result:\n{json.dumps(result, indent=2)}")
        
        # Move the file
        params = {
            "operation": "moveFile",
            "source": os.path.join(tool.test_dir, "test_file_copy.txt"),
            "destination": os.path.join(tool.test_dir, "test_file_moved.txt")
        }
        
        result = await tool.execute(params)
        logger.info(f"Move file result:\n{json.dumps(result, indent=2)}")
        
        # Get file details
        params = {
            "operation": "getFileDetails",
            "path": os.path.join(tool.test_dir, "test_file_moved.txt")
        }
        
        result = await tool.execute(params)
        logger.info(f"Get file details result:\n{json.dumps(result, indent=2)}")
        
        # Delete the file
        params = {
            "operation": "deleteFile",
            "path": os.path.join(tool.test_dir, "test_file_moved.txt")
        }
        
        result = await tool.execute(params)
        logger.info(f"Delete file result:\n{json.dumps(result, indent=2)}")
        
        return result
    finally:
        tool.cleanup()

async def test_search_files():
    """Test searching for files."""
    tool = MockFileManagerTool()
    
    try:
        logger.info("\n\nTesting search files...")
        
        # Search for text files
        params = {
            "operation": "searchFiles",
            "path": tool.test_dir,
            "pattern": "*.txt",
            "recursive": True
        }
        
        result = await tool.execute(params)
        logger.info(f"Search files result:\n{json.dumps(result, indent=2)}")
        
        return result
    finally:
        tool.cleanup()

async def main():
    """Run all tests."""
    await test_list_directory()
    await test_file_operations()
    await test_search_files()

if __name__ == "__main__":
    asyncio.run(main()) 