from mcp.server.fastmcp import FastMCP
import asyncio
import logging
import sys
import os
import subprocess
import json
import re
import glob
import shutil
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import ast
import platform
import signal
import uuid
import argparse
import time

# Import the data collector
from mcp_data_collector import get_collector

# Try to import psutil but provide fallback if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    logging.warning("psutil not available, some system monitoring features will be limited")
    HAS_PSUTIL = False

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    logging.error("mcp package not available. Please install it with 'pip install mcp'")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastMCP instance with proper error handling
class DevToolkitMCP(FastMCP):
    def __init__(self):
        super().__init__("Enhanced Developer's Toolkit", version="1.0.0")
        
        # Initialize data collector
        self.data_collector = get_collector()
        logger.info(f"Data collection is {'enabled' if self.data_collector.enabled else 'disabled'}")
        
    async def handle_error(self, error: Exception) -> Dict[str, Any]:
        logger.error(f"Error in MCP server: {str(error)}", exc_info=True)
        return {
            "error": str(error),
            "type": error.__class__.__name__
        }
    
    async def handle_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Override the handle_tool method to log requests and responses."""
        start_time = time.time()
        request_id = ""
        
        # Log the request
        try:
            request_id = self.data_collector.log_mcp_request(name, params)
        except Exception as e:
            logger.error(f"Error logging MCP request: {e}")
        
        # Call the original method
        try:
            result = await super().handle_tool(name, params)
            status = "success"
        except Exception as e:
            result = await self.handle_error(e)
            status = "error"
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Log the response
        try:
            self.data_collector.log_mcp_response(request_id, result, status, execution_time)
        except Exception as e:
            logger.error(f"Error logging MCP response: {e}")
        
        return result

mcp = DevToolkitMCP()

# ===== Code Analysis Service =====

@mcp.tool()
async def analyze_code(file_path: str) -> Dict[str, Any]:
    """
    Analyze code in the specified file.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic code analysis
        analysis = {
            "file_path": file_path,
            "size_bytes": os.path.getsize(file_path),
            "line_count": len(content.splitlines()),
            "language": detect_language(file_path),
            "issues": [],
            "metrics": calculate_code_metrics(content, file_path)
        }
        
        # Check for common issues
        if analysis["language"] == "python":
            analysis["issues"].extend(analyze_python_code(content))
        elif analysis["language"] in ["javascript", "typescript"]:
            analysis["issues"].extend(analyze_js_code(content))
        
        return analysis
    except Exception as e:
        logger.error(f"Error in analyze_code: {str(e)}", exc_info=True)
        return {"error": str(e)}

def detect_language(file_path: str) -> str:
    """Detect programming language based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".md": "markdown",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".sh": "shell",
        ".bat": "batch",
        ".ps1": "powershell"
    }
    return language_map.get(ext, "unknown")

def calculate_code_metrics(content: str, file_path: str) -> Dict[str, Any]:
    """Calculate code metrics like complexity, etc."""
    metrics = {
        "characters": len(content),
        "words": len(content.split()),
        "blank_lines": content.count("\n\n") + 1,
        "indentation_levels": max([len(line) - len(line.lstrip()) for line in content.splitlines() if line.strip()], default=0) // 4
    }
    
    # Language-specific metrics
    if detect_language(file_path) == "python":
        try:
            tree = ast.parse(content)
            metrics["functions"] = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            metrics["classes"] = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            metrics["imports"] = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
        except:
            pass
    
    return metrics

def analyze_python_code(content: str) -> List[Dict[str, Any]]:
    """Analyze Python code for common issues."""
    issues = []
    
    # Check for unused imports
    try:
        tree = ast.parse(content)
        imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
        imports.extend([node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)])
        
        for imp in imports:
            if imp not in content.replace("import " + imp, "").replace("from " + imp, ""):
                issues.append({
                    "type": "warning",
                    "message": f"Unused import: {imp}",
                    "line": next((i+1 for i, line in enumerate(content.splitlines()) if f"import {imp}" in line or f"from {imp}" in line), 0)
                })
    except:
        pass
    
    # Check for hardcoded values
    hardcoded_patterns = [
        (r'password\s*=\s*["\'].*["\']', "Hardcoded password detected"),
        (r'api_key\s*=\s*["\'].*["\']', "Hardcoded API key detected"),
        (r'secret\s*=\s*["\'].*["\']', "Hardcoded secret detected")
    ]
    
    for pattern, message in hardcoded_patterns:
        for i, line in enumerate(content.splitlines()):
            if re.search(pattern, line):
                issues.append({
                    "type": "error",
                    "message": message,
                    "line": i + 1
                })
    
    # Check for missing type hints
    if "typing" in content:
        for i, line in enumerate(content.splitlines()):
            if "def " in line and "(" in line and ")" in line and "->" not in line:
                issues.append({
                    "type": "info",
                    "message": "Missing return type hint",
                    "line": i + 1
                })
    
    return issues

def analyze_js_code(content: str) -> List[Dict[str, Any]]:
    """Analyze JavaScript/TypeScript code for common issues."""
    issues = []
    
    # Check for console.log statements
    for i, line in enumerate(content.splitlines()):
        if "console.log" in line:
            issues.append({
                "type": "warning",
                "message": "Debug console.log statement found",
                "line": i + 1
            })
    
    # Check for == instead of ===
    for i, line in enumerate(content.splitlines()):
        if "==" in line and "===" not in line and "!==" not in line:
            issues.append({
                "type": "warning",
                "message": "Consider using === instead of == for strict equality",
                "line": i + 1
            })
    
    return issues

# ===== Terminal Service =====

@mcp.tool()
async def execute_command(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a command in the terminal.
    
    Args:
        command: The command to execute
        cwd: Current working directory (optional)
        
    Returns:
        Dictionary containing command output and status
    """
    try:
        if not cwd:
            cwd = os.getcwd()
        
        # Security check - prevent dangerous commands
        dangerous_commands = ["rm -rf", "format", "mkfs", "dd", ":(){ :|:& };:", "> /dev/sda"]
        if any(dc in command.lower() for dc in dangerous_commands):
            return {
                "error": "Command blocked for security reasons",
                "command": command
            }
        
        # Execute the command
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        
        stdout, stderr = process.communicate(timeout=30)
        
        return {
            "command": command,
            "exit_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "cwd": cwd
        }
    except subprocess.TimeoutExpired:
        return {
            "error": "Command timed out after 30 seconds",
            "command": command
        }
    except Exception as e:
        logger.error(f"Error in execute_command: {str(e)}", exc_info=True)
        return {"error": str(e)}

# ===== File System Service =====

@mcp.tool()
async def list_directory(path: str = ".") -> Dict[str, Any]:
    """
    List files and directories in the specified path.
    
    Args:
        path: Directory path to list
        
    Returns:
        Dictionary containing directory contents
    """
    try:
        if not os.path.exists(path):
            return {"error": f"Path not found: {path}"}
        
        if not os.path.isdir(path):
            return {"error": f"Not a directory: {path}"}
        
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            items.append({
                "name": item,
                "path": item_path,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None,
                "modified": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
            })
        
        return {
            "path": path,
            "items": items
        }
    except Exception as e:
        logger.error(f"Error in list_directory: {str(e)}", exc_info=True)
        return {"error": str(e)}

@mcp.tool()
async def read_file(path: str) -> Dict[str, Any]:
    """
    Read the contents of a file.
    
    Args:
        path: Path to the file
        
    Returns:
        Dictionary containing file contents
    """
    try:
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}
        
        if not os.path.isfile(path):
            return {"error": f"Not a file: {path}"}
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "path": path,
            "content": content,
            "size": os.path.getsize(path),
            "modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
        }
    except Exception as e:
        logger.error(f"Error in read_file: {str(e)}", exc_info=True)
        return {"error": str(e)}

@mcp.tool()
async def write_file(path: str, content: str) -> Dict[str, Any]:
    """
    Write content to a file.
    
    Args:
        path: Path to the file
        content: Content to write
        
    Returns:
        Dictionary containing operation status
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "path": path,
            "success": True,
            "size": os.path.getsize(path)
        }
    except Exception as e:
        logger.error(f"Error in write_file: {str(e)}", exc_info=True)
        return {"error": str(e)}

# ===== Git Service =====

@mcp.tool()
async def git_operations(operation: str, path: str = ".") -> Dict[str, Any]:
    """
    Perform git operations.
    
    Args:
        operation: Git operation to perform (status, branch, log, etc.)
        path: Repository path
        
    Returns:
        Dictionary containing operation results
    """
    try:
        if not os.path.exists(os.path.join(path, ".git")):
            return {"error": f"Not a git repository: {path}"}
        
        if operation == "status":
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {"error": result.stderr}
            
            # Parse git status output
            status_lines = result.stdout.strip().split("\n")
            status = {
                "branch": subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=path,
                    capture_output=True,
                    text=True
                ).stdout.strip(),
                "changes": []
            }
            
            for line in status_lines:
                if line:
                    status_code = line[:2]
                    file_path = line[3:]
                    status["changes"].append({
                        "file": file_path,
                        "status": status_code
                    })
            
            return status
            
        elif operation == "branch":
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {"error": result.stderr}
            
            branches = result.stdout.strip().split("\n")
            current_branch = None
            
            for i, branch in enumerate(branches):
                if branch.startswith("*"):
                    current_branch = i
                    branches[i] = branch[2:].strip()
                else:
                    branches[i] = branch.strip()
            
            return {
                "branches": branches,
                "current": current_branch
            }
            
        elif operation == "log":
            result = subprocess.run(
                ["git", "log", "--pretty=format:%h|%an|%s|%ad", "--date=iso"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {"error": result.stderr}
            
            log_entries = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    hash, author, message, date = line.split("|", 3)
                    log_entries.append({
                        "hash": hash,
                        "author": author,
                        "message": message,
                        "date": date
                    })
            
            return {"entries": log_entries}
            
        else:
            return {"error": f"Unsupported git operation: {operation}"}
    except Exception as e:
        logger.error(f"Error in git_operations: {str(e)}", exc_info=True)
        return {"error": str(e)}

# ===== Project Metrics Service =====

@mcp.tool()
async def get_project_metrics(path: str = ".") -> Dict[str, Any]:
    """
    Get metrics for the entire project.
    
    Args:
        path: Project root path
        
    Returns:
        Dictionary containing project metrics
    """
    try:
        metrics = {
            "path": path,
            "files": 0,
            "directories": 0,
            "total_lines": 0,
            "languages": {},
            "largest_files": [],
            "recent_files": []
        }
        
        # Walk through the directory
        for root, dirs, files in os.walk(path):
            # Skip .git directory
            if ".git" in root:
                continue
                
            metrics["directories"] += len(dirs)
            metrics["files"] += len(files)
            
            # Process each file
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip binary files
                if is_binary_file(file_path):
                    continue
                
                # Count lines
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                        metrics["total_lines"] += lines
                except:
                    continue
                
                # Track language statistics
                ext = os.path.splitext(file)[1].lower()
                if ext:
                    if ext not in metrics["languages"]:
                        metrics["languages"][ext] = {"files": 0, "lines": 0}
                    metrics["languages"][ext]["files"] += 1
                    metrics["languages"][ext]["lines"] += lines
                
                # Track file size
                size = os.path.getsize(file_path)
                metrics["largest_files"].append({
                    "path": file_path,
                    "size": size,
                    "lines": lines
                })
                
                # Track recent files
                modified = os.path.getmtime(file_path)
                metrics["recent_files"].append({
                    "path": file_path,
                    "modified": modified
                })
        
        # Sort largest files
        metrics["largest_files"] = sorted(
            metrics["largest_files"],
            key=lambda x: x["size"],
            reverse=True
        )[:10]
        
        # Sort recent files
        metrics["recent_files"] = sorted(
            metrics["recent_files"],
            key=lambda x: x["modified"],
            reverse=True
        )[:10]
        
        # Convert timestamps to ISO format
        for file in metrics["recent_files"]:
            file["modified"] = datetime.fromtimestamp(file["modified"]).isoformat()
        
        return metrics
    except Exception as e:
        logger.error(f"Error in get_project_metrics: {str(e)}", exc_info=True)
        return {"error": str(e)}

def is_binary_file(file_path: str) -> bool:
    """Check if a file is binary."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk
    except:
        return True

# ===== System Information Service =====

@mcp.tool()
async def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    try:
        info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "working_directory": os.getcwd()
        }
        
        # Add psutil info if available
        if HAS_PSUTIL:
            info.update({
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": {"/": {
                    "total": psutil.disk_usage("/").total,
                    "used": psutil.disk_usage("/").used,
                    "free": psutil.disk_usage("/").free,
                    "percent": psutil.disk_usage("/").percent
                }},
                "process_id": os.getpid()
            })
        else:
            # Provide basic fallback info
            info.update({
                "note": "Limited system info (psutil not available)",
                "process_id": os.getpid()
            })
            
        return info
    except Exception as e:
        logger.error(f"Error in get_system_info: {str(e)}", exc_info=True)
        return {"error": str(e)}

@mcp.tool()
async def get_data_collection_status() -> Dict[str, Any]:
    """
    Get the status of data collection for AI training.
    
    Returns:
        Dictionary containing data collection statistics
    """
    try:
        stats = mcp.data_collector.get_statistics()
        return {
            "status": "success",
            "enabled": stats["enabled"],
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting data collection status: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

@mcp.tool()
async def set_data_collection_enabled(enabled: bool) -> Dict[str, Any]:
    """
    Enable or disable data collection for AI training.
    
    Args:
        enabled: Whether data collection should be enabled
        
    Returns:
        Dictionary containing the updated status
    """
    try:
        mcp.data_collector.set_enabled(enabled)
        return {
            "status": "success",
            "enabled": enabled,
            "message": f"Data collection {'enabled' if enabled else 'disabled'}"
        }
    except Exception as e:
        logger.error(f"Error setting data collection status: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

@mcp.tool()
async def export_collected_data(output_dir: str = "exported_data") -> Dict[str, Any]:
    """
    Export collected data for AI training.
    
    Args:
        output_dir: Directory to export data to
        
    Returns:
        Dictionary containing the export status
    """
    try:
        success = mcp.data_collector.export_data(output_dir)
        if success:
            return {
                "status": "success",
                "message": f"Data exported to {output_dir}",
                "output_dir": output_dir
            }
        else:
            return {
                "status": "error",
                "message": "Failed to export data"
            }
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

async def main():
    """Main function to run the MCP server."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Enhanced Developer's Toolkit MCP Server")
    parser.add_argument("--mcp-port", type=int, default=9999, help="Port for MCP server")
    parser.add_argument("--data-collection", type=bool, default=True, help="Enable data collection for AI training")
    args = parser.parse_args()
    
    print(f"Starting MCP server on port {args.mcp_port}...")
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(loop)))
    
    # Configure the data collector
    mcp.data_collector.set_enabled(args.data_collection)
    
    # Configure server
    config = {
        "title": "Enhanced Developer's Toolkit",
        "version": "1.0.0",
        "port": args.mcp_port,
        "host": "127.0.0.1"
    }
    
    # Start server
    await mcp.run(**config)

async def shutdown(loop):
    """Gracefully shutdown the server."""
    logger.info("Shutting down MCP server...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
        
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    logger.info("Server shutdown complete")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            # Use the ProactorEventLoop on Windows for better performance
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server terminated by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1) 