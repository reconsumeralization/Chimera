#!/usr/bin/env python
"""
Project Chimera System Check Tool

This script performs diagnostics on the Project Chimera installation and
provides clear, accessible feedback about the system state and any issues.
"""

import os
import sys
import platform
import importlib.util
import subprocess
from pathlib import Path


def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def print_status(message, status, details=None):
    """Print a status message with color if available."""
    status_text = {
        "OK": "\033[92m[  OK  ]\033[0m" if os.name != "nt" else "[  OK  ]",
        "WARN": "\033[93m[ WARN ]\033[0m" if os.name != "nt" else "[ WARN ]",
        "ERROR": "\033[91m[ERROR ]\033[0m" if os.name != "nt" else "[ERROR ]",
        "INFO": "\033[94m[ INFO ]\033[0m" if os.name != "nt" else "[ INFO ]",
    }
    
    print(f"{status_text.get(status, status)} {message}")
    if details:
        for line in details.split("\n"):
            print(f"           {line}")


def check_python_version():
    """Check if Python version is compatible."""
    print_header("Python Environment")
    
    version = platform.python_version()
    if version.startswith("3.") and int(version.split(".")[1]) >= 9:
        print_status(f"Python version: {version}", "OK")
    else:
        print_status(f"Python version: {version}", "WARN", 
                   "Recommended version is 3.9 or higher")
    
    # Check for virtual environment
    if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        print_status("Virtual environment: Active", "OK", 
                   f"Location: {sys.prefix}")
    else:
        print_status("Virtual environment: Not active", "ERROR", 
                   "Please activate your virtual environment before running Chimera")


def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("Dependencies")
    
    required_packages = [
        "fastapi", "uvicorn", "pydantic", "sqlalchemy", 
        "openai", "google-generativeai", "python-dotenv"
    ]
    
    for package in required_packages:
        spec = importlib.util.find_spec(package)
        if spec is not None:
            try:
                module = importlib.import_module(package)
                version = getattr(module, "__version__", "unknown")
                print_status(f"{package}: {version}", "OK")
            except (ImportError, AttributeError):
                print_status(f"{package}: installed", "OK")
        else:
            print_status(f"{package}: not found", "ERROR", 
                       f"Please install with: pip install {package}")


def check_project_structure():
    """Check if the project structure is correct."""
    print_header("Project Structure")
    
    # Get project root dir (parent of script dir)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent
    
    print_status(f"Project root: {project_root}", "INFO")
    
    # Check essential directories
    directories = {
        "src": "Core source code directory",
        "src/chimera_core": "Core Chimera implementation",
        "src/schemas": "Schema definitions",
        "venv": "Virtual environment"
    }
    
    for directory, description in directories.items():
        dir_path = project_root / directory
        if dir_path.exists() and dir_path.is_dir():
            print_status(f"{directory}: Found", "OK", description)
        else:
            print_status(f"{directory}: Not found", "WARN", 
                       f"Missing directory: {description}")
    
    # Check essential files
    files = {
        "requirements.txt": "Dependencies file",
        ".env": "Environment configuration",
        "start_chimera.bat": "Windows startup script",
        "start_chimera.sh": "Unix startup script",
        "src/chimera_core/api/app.py": "Main FastAPI application"
    }
    
    for file, description in files.items():
        file_path = project_root / file
        if file_path.exists() and file_path.is_file():
            print_status(f"{file}: Found", "OK", description)
        else:
            if file == ".env" and (project_root / ".env.sample").exists():
                print_status(f"{file}: Not found", "WARN", 
                           "Copy .env.sample to .env and configure your settings")
            else:
                print_status(f"{file}: Not found", "WARN", description)


def check_network():
    """Check if the required ports are available."""
    print_header("Network")
    
    # Check if port 8000 is available
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 8000))
        s.close()
        print_status("Port 8000: Available", "OK", "Main API server port")
    except OSError:
        print_status("Port 8000: In use", "WARN", 
                   "Port 8000 is already in use. Chimera may not start correctly.")
    
    # Try to detect if we're online by connecting to a well-known site
    try:
        import urllib.request
        urllib.request.urlopen("https://www.google.com", timeout=1)
        print_status("Internet connection: Available", "OK")
    except:
        print_status("Internet connection: Unavailable", "WARN", 
                   "Internet connection may be required for AI API access")


def check_api_keys():
    """Check if API keys are configured."""
    print_header("API Keys")
    
    # Check for .env file
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print_status(".env file: Not found", "ERROR", 
                   "Please copy .env.sample to .env and configure your API keys")
        return
    
    # Check for API keys in .env
    try:
        with open(env_path, "r") as f:
            env_content = f.read()
        
        # Check for OpenAI API key
        if "OPENAI_API_KEY" in env_content and "OPENAI_API_KEY=" not in env_content:
            print_status("OpenAI API key: Configured", "OK")
        else:
            print_status("OpenAI API key: Not configured", "WARN", 
                       "Set OPENAI_API_KEY in your .env file")
        
        # Check for Google API key
        if "GOOGLE_API_KEY" in env_content and "GOOGLE_API_KEY=" not in env_content:
            print_status("Google API key: Configured", "OK")
        else:
            print_status("Google API key: Not configured", "WARN", 
                       "Set GOOGLE_API_KEY in your .env file")
    except Exception as e:
        print_status(f".env file: Error reading", "ERROR", str(e))


def run_quick_fix():
    """Attempt to fix common issues."""
    print_header("Quick Fix")
    
    # Create schemas directory if missing
    schema_dir = Path(__file__).parent / "src" / "schemas"
    if not schema_dir.exists():
        try:
            schema_dir.mkdir(parents=True, exist_ok=True)
            print_status("Created schemas directory", "OK")
        except Exception as e:
            print_status("Failed to create schemas directory", "ERROR", str(e))
    
    # Create context_schemas.py if missing
    schema_file = schema_dir / "context_schemas.py"
    if not schema_file.exists():
        try:
            with open(schema_file, "w") as f:
                f.write('''"""Context schemas for Chimera API."""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ContextItem(BaseModel):
    """Base class for context items."""
    type: str = Field(..., description="Type of context item")
    content: Any = Field(..., description="Content of the context item")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CodeContext(BaseModel):
    """Context information from code files."""
    items: List[ContextItem] = Field(default_factory=list, description="List of context items")
    workspace_root: Optional[str] = Field(None, description="Root directory of the workspace")
    timestamp: Optional[str] = Field(None, description="Timestamp when context was collected")


class ContextRequest(BaseModel):
    """Request to store context."""
    context: CodeContext = Field(..., description="Context to store")
    session_id: str = Field(..., description="Session identifier")
    overwrite: bool = Field(False, description="Whether to overwrite existing context")


class ContextResponse(BaseModel):
    """Response with stored context."""
    success: bool = Field(..., description="Whether the operation was successful")
    context_id: Optional[str] = Field(None, description="ID of the stored context")
    message: Optional[str] = Field(None, description="Additional information")


class SnapshotLogBase(BaseModel):
    """Base class for snapshot logs."""
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the snapshot")
    context_size: int = Field(..., description="Size of the context in bytes")
    source_type: str = Field(..., description="Source of the context (e.g., 'vscode', 'cursor')")


class SnapshotLogCreate(SnapshotLogBase):
    """Schema for creating a new snapshot log entry."""
    pass


class SnapshotLog(SnapshotLogBase):
    """Schema for a snapshot log entry with ID."""
    id: int = Field(..., description="Unique identifier")

    class Config:
        """Pydantic configuration."""
        orm_mode = True
''')
            print_status("Created context_schemas.py file", "OK")
        except Exception as e:
            print_status("Failed to create context_schemas.py file", "ERROR", str(e))
    
    # Create .env file from sample if missing
    env_file = Path(__file__).parent / ".env"
    env_sample = Path(__file__).parent / ".env.sample"
    if not env_file.exists() and env_sample.exists():
        try:
            with open(env_sample, "r") as src, open(env_file, "w") as dst:
                dst.write(src.read())
            print_status("Created .env file from .env.sample", "OK", 
                        "Please edit .env to configure your API keys")
        except Exception as e:
            print_status("Failed to create .env file", "ERROR", str(e))
    
    # Ensure chimera_core/__init__.py exists
    init_file = Path(__file__).parent / "src" / "chimera_core" / "__init__.py"
    if not init_file.exists():
        try:
            init_file.parent.mkdir(parents=True, exist_ok=True)
            with open(init_file, "w") as f:
                f.write('"""Chimera Core package."""\n')
            print_status("Created missing __init__.py file", "OK")
        except Exception as e:
            print_status("Failed to create __init__.py file", "ERROR", str(e))


def run_summary():
    """Provide a summary of system status and recommendations."""
    print_header("Summary & Recommendations")
    
    # Add specific recommendations based on findings
    print("""
Recommended actions:
1. Use the simplified startup scripts for easier operation:
   - Windows: easy_start.bat
   - Linux/Mac/WSL/Git Bash: ./easy_start.sh

2. If you encounter import errors:
   - Run this script with the --fix flag: python check_system.py --fix

3. For the best experience:
   - Make sure all dependencies are installed: pip install -r requirements.txt
   - Configure your API keys in the .env file
   - Use a Python version 3.9 or higher

Need further assistance? Contact support or refer to the documentation.
""")


def main():
    """Main entry point."""
    print_header("Project Chimera System Check")
    print("Running comprehensive system check...")
    
    # Run checks
    check_python_version()
    check_dependencies()
    check_project_structure()
    check_network()
    check_api_keys()
    
    # Run quick fix if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        run_quick_fix()
    
    # Provide summary
    run_summary()


if __name__ == "__main__":
    main() 