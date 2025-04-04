#!/usr/bin/env python
"""
Environment Diagnostic and Fix Tool for Enhanced Developer's Toolkit
Helps diagnose and fix common environment issues including import resolution and dependency conflicts.
"""

import os
import sys
import subprocess
import json
import platform
import shutil
import tempfile
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}\n")

def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_info(text):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")

def get_python_executable():
    """Get the Python executable based on the virtual environment."""
    if os.name == 'nt':  # Windows
        return os.path.join('venv', 'Scripts', 'python.exe')
    else:  # Unix-like
        return os.path.join('venv', 'bin', 'python')

def run_command(cmd, check=True, shell=False, capture_output=True):
    """Run a command and return the result."""
    try:
        if isinstance(cmd, str) and not shell:
            cmd = cmd.split()
        
        result = subprocess.run(
            cmd, 
            check=check, 
            shell=shell, 
            text=True, 
            capture_output=capture_output
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if capture_output:
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
        return e

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Checking Python Version")
    
    version = platform.python_version()
    version_tuple = tuple(map(int, version.split('.')))
    
    if version_tuple >= (3, 7):
        print_success(f"Python version {version} is compatible")
        return True
    else:
        print_error(f"Python version {version} is not compatible. Need 3.7+")
        return False

def check_virtual_env():
    """Check if virtual environment exists and is activated."""
    print_header("Checking Virtual Environment")
    
    if not os.path.exists('venv'):
        print_warning("Virtual environment not found")
        return False
    
    # Check if venv is activated
    if os.environ.get('VIRTUAL_ENV'):
        print_success("Virtual environment is activated")
        return True
    else:
        print_warning("Virtual environment exists but is not activated")
        return False

def activate_virtual_env():
    """Activate the virtual environment."""
    print_info("Activating virtual environment...")
    
    if os.name == 'nt':  # Windows
        activate_script = os.path.join('venv', 'Scripts', 'activate.bat')
        if os.path.exists(activate_script):
            # Cannot directly activate in the current process, so instruct user
            print_info(f"Please run: {activate_script}")
            return False
    else:  # Unix-like
        activate_script = os.path.join('venv', 'bin', 'activate')
        if os.path.exists(activate_script):
            print_info(f"Please run: source {activate_script}")
            return False
    
    return False

def create_virtual_env():
    """Create a virtual environment."""
    print_info("Creating virtual environment...")
    
    result = run_command([sys.executable, '-m', 'venv', 'venv'])
    if result.returncode == 0:
        print_success("Virtual environment created")
        return True
    else:
        print_error("Failed to create virtual environment")
        return False

def check_dependencies():
    """Check if all dependencies are installed and compatible."""
    print_header("Checking Dependencies")
    
    # Get the Python executable path
    python = get_python_executable()
    
    # Check if python executable exists
    if not os.path.exists(python):
        print_error(f"Python executable not found at: {python}")
        return False
    
    print_info("Checking installed packages...")
    pip_list = run_command([python, '-m', 'pip', 'list', '--format=json'])
    
    if pip_list.returncode != 0:
        print_error("Failed to list installed packages")
        return False
    
    try:
        installed_packages = json.loads(pip_list.stdout)
        installed_dict = {pkg['name'].lower(): pkg['version'] for pkg in installed_packages}
    except json.JSONDecodeError:
        print_error("Failed to parse installed packages")
        return False
    
    # Critical packages to check
    critical_packages = ['mcp', 'fastapi', 'uvicorn', 'starlette', 'anyio', 'httpx', 'psutil']
    missing_packages = []
    
    for package in critical_packages:
        if package.lower() not in installed_dict:
            missing_packages.append(package)
            print_warning(f"Missing package: {package}")
        else:
            print_success(f"Found package: {package} (version: {installed_dict[package.lower()]})")
    
    # Specifically check for anyio version conflict
    if 'anyio' in installed_dict and 'mcp' in installed_dict:
        anyio_version = installed_dict['anyio']
        print_info(f"Installed anyio version: {anyio_version}")
        
        # Try to determine if there's a conflict
        first_digit = anyio_version.split('.')[0]
        if first_digit == '3' and 'mcp' in installed_dict:
            print_warning("Potential version conflict: MCP may require anyio 4.x but version 3.x is installed")
    
    if missing_packages:
        print_warning(f"Missing critical packages: {', '.join(missing_packages)}")
        return False
    
    return True

def fix_dependencies():
    """Fix dependency issues."""
    print_header("Fixing Dependencies")
    
    # Get the Python executable path
    python = get_python_executable()
    
    # Check if requirements.txt exists
    if not os.path.exists('requirements.txt'):
        print_error("requirements.txt not found")
        return False
    
    # Create a temporary modified requirements file to handle conflicts
    with open('requirements.txt', 'r') as f:
        requirements = f.readlines()
    
    # Modify requirements to handle version conflicts
    modified_requirements = []
    anyio_fixed = False
    
    for req in requirements:
        # Remove specific version for anyio to avoid conflicts
        if req.strip().startswith('anyio'):
            modified_requirements.append('anyio>=3.7.1\n')
            anyio_fixed = True
        # Skip specific starlette version that might be causing conflicts
        elif req.strip().startswith('starlette==0.27.0'):
            modified_requirements.append('starlette>=0.27.0,<0.31.0\n')
        else:
            modified_requirements.append(req)
    
    # Add anyio if not in requirements
    if not anyio_fixed:
        modified_requirements.append('anyio>=3.7.1\n')
    
    # Write to temporary file
    temp_req_file = tempfile.mktemp(suffix='.txt')
    with open(temp_req_file, 'w') as f:
        f.writelines(modified_requirements)
    
    print_info("Installing base dependencies first...")
    run_command([python, '-m', 'pip', 'install', '--upgrade', 'pip'], check=False)
    
    # Install key dependencies individually to avoid conflicts
    key_packages = [
        'fastapi',
        'uvicorn',
        'jinja2',
        'psutil',
        'httpx',
        'httpx-sse',
        'pydantic',
    ]
    
    for package in key_packages:
        print_info(f"Installing {package}...")
        run_command([python, '-m', 'pip', 'install', package], check=False)
    
    print_info("Installing MCP dependencies...")
    result = run_command([python, '-m', 'pip', 'install', '-r', temp_req_file], check=False)
    
    if result.returncode != 0:
        print_warning("Some dependencies may not have installed correctly")
        print_info("Trying individual installations...")
        
        # Try installing each package individually
        with open(temp_req_file, 'r') as f:
            individual_reqs = f.readlines()
        
        for req in individual_reqs:
            req = req.strip()
            if req and not req.startswith('#'):
                print_info(f"Installing {req}...")
                run_command([python, '-m', 'pip', 'install', req], check=False)
    
    # Remove temporary file
    try:
        os.remove(temp_req_file)
    except:
        pass
    
    # Check specifically for psutil
    result = run_command([python, '-c', 'import psutil'], check=False)
    if result.returncode != 0:
        print_warning("psutil not installed correctly, trying again...")
        run_command([python, '-m', 'pip', 'install', '--upgrade', 'psutil'], check=False)
    
    # Check for MCP
    result = run_command([python, '-c', 'import mcp'], check=False)
    if result.returncode != 0:
        print_warning("mcp not installed correctly, trying again...")
        run_command([python, '-m', 'pip', 'install', '--upgrade', 'mcp'], check=False)
    
    print_success("Dependency fix completed")
    return True

def check_vscode_settings():
    """Check VS Code settings for Python and Pylance configuration."""
    print_header("Checking VS Code/Cursor Settings")
    
    vscode_dir = '.vscode'
    settings_file = os.path.join(vscode_dir, 'settings.json')
    
    if not os.path.exists(vscode_dir):
        os.makedirs(vscode_dir)
        print_info(f"Created {vscode_dir} directory")
    
    settings = {}
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            print_success(f"Found {settings_file}")
        except json.JSONDecodeError:
            print_warning(f"{settings_file} exists but is not valid JSON")
            settings = {}
    else:
        print_info(f"{settings_file} does not exist, will create it")
    
    # Check Python settings
    python_path = str(Path('venv') / ('Scripts' if os.name == 'nt' else 'bin') / ('python.exe' if os.name == 'nt' else 'python'))
    
    changes_made = False
    
    # Python interpreter path
    if 'python.defaultInterpreterPath' not in settings:
        settings['python.defaultInterpreterPath'] = python_path
        changes_made = True
        print_info(f"Set python.defaultInterpreterPath to {python_path}")
    
    # Auto-detect interpreter
    if 'python.terminal.activateEnvInCurrentTerminal' not in settings:
        settings['python.terminal.activateEnvInCurrentTerminal'] = True
        changes_made = True
        print_info("Enabled automatic environment activation in terminal")
    
    # Extra paths for imports
    if 'python.analysis.extraPaths' not in settings:
        # Add current directory and any lib directories
        extra_paths = ['.']
        if os.path.exists('lib'):
            extra_paths.append('./lib')
        settings['python.analysis.extraPaths'] = extra_paths
        changes_made = True
        print_info(f"Set python.analysis.extraPaths to {extra_paths}")
    
    # Pylance settings for auto-imports
    if 'python.analysis.autoImportCompletions' not in settings:
        settings['python.analysis.autoImportCompletions'] = True
        changes_made = True
        print_info("Enabled auto import completions")
    
    # Deeper package indexing
    if 'python.analysis.packageIndexDepths' not in settings:
        settings['python.analysis.packageIndexDepths'] = [
            {"name": "sklearn", "depth": 2},
            {"name": "matplotlib", "depth": 2},
            {"name": "scipy", "depth": 2},
            {"name": "django", "depth": 2},
            {"name": "fastapi", "depth": 2},
            {"name": "mcp", "depth": 3}
        ]
        changes_made = True
        print_info("Set package index depths for better auto-imports")
    
    # Save settings if changes were made
    if changes_made:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
        print_success(f"Updated {settings_file}")
    else:
        print_success("VS Code/Cursor settings look good")
    
    return True

def main():
    """Main function to run all checks and fixes."""
    print_header("Enhanced Developer's Toolkit - Environment Diagnostic")
    print(f"Running diagnostics on: {os.getcwd()}")
    
    # Check Python version
    python_ok = check_python_version()
    if not python_ok:
        print_error("Python version check failed. Please install Python 3.7+")
        return
    
    # Check and setup virtual environment
    venv_ok = check_virtual_env()
    if not venv_ok:
        if os.path.exists('venv'):
            activate_virtual_env()
        else:
            create_virtual_env()
            activate_virtual_env()
    
    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        fix_dependencies()
    
    # Check VS Code settings
    check_vscode_settings()
    
    print_header("Summary")
    print_success("Diagnostic completed!")
    print_info("If you're still experiencing issues:")
    print("1. Make sure to activate the virtual environment before running scripts")
    print("2. Try running the appropriate script for your OS:")
    print("   - Windows: run_with_proxy.bat")
    print("   - Linux/macOS: ./run_with_proxy.sh")
    print("3. If port conflicts occur, close any other applications using ports 9998-9999")
    print("4. For Pylance import issues in VS Code/Cursor, restart the editor")

if __name__ == "__main__":
    main() 