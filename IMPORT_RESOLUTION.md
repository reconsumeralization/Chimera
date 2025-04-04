# Fixing Import Resolution Issues

This guide explains how to fix import resolution issues when using the Enhanced Developer's Toolkit with VS Code or Cursor.

## Common Pylance Diagnostics and Solutions

### `importResolveFailure`

This error occurs when Pylance cannot find a module or package you're trying to import.

**How to Fix:**
1. Run `fix_environment.bat` (Windows) or `./fix_environment.sh` (Unix/Linux)
2. Make sure you have the virtual environment activated 
3. Ensure all dependencies are installed
4. Configure VS Code/Cursor to use the correct Python interpreter from your virtual environment

### `importResolveSourceFailure`

This error occurs when Pylance finds type stubs for the package but can't find the package itself.

**How to Fix:**
1. Install the missing package: `python -m pip install <package_name>`
2. Select the correct Python interpreter in VS Code/Cursor

## Manual Configuration Steps

If the automatic fix script doesn't resolve the issue, you can try these manual steps:

### 1. Configure VS Code/Cursor Settings

Create or edit `.vscode/settings.json` with these settings:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
    "python.analysis.extraPaths": [
        ".",
        "./lib"
    ],
    "python.analysis.autoImportCompletions": true,
    "python.analysis.packageIndexDepths": [
        {
            "name": "mcp",
            "depth": 3
        },
        {
            "name": "fastapi",
            "depth": 2
        }
    ],
    "python.terminal.activateEnvInCurrentTerminal": true
}
```

### 2. Manually Install Dependencies

If you encounter dependency conflicts:

```bash
# Activate virtual environment
# Windows
venv\Scripts\activate.bat

# Unix/Linux
source venv/bin/activate

# Install base dependencies
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn jinja2 psutil httpx httpx-sse pydantic

# Install MCP
python -m pip install mcp
```

### 3. Fix Specific Import Issues

#### For `psutil` Import Issues:

```bash
python -m pip install --upgrade --force-reinstall psutil
```

#### For `mcp` Import Issues:

```bash
python -m pip install --upgrade mcp
```

## Understanding Pylance Diagnostics

Pylance, the default language server for Python in VS Code and Cursor, provides diagnostics to help identify issues in your code. When it shows import resolution errors, it's usually because:

1. **The module is not installed** in your active Python environment
2. **The module is installed, but in a different environment** than the one VS Code is using
3. **VS Code can't find the module** due to path configuration issues
4. **There are dependency conflicts** preventing modules from working together

Our `fix_environment.py` script addresses all these issues by:
- Checking installed dependencies
- Resolving version conflicts
- Setting up proper VS Code configuration
- Ensuring the correct Python interpreter is used

## Further Resources

- [Official Pylance Import Resolution Guide](https://aka.ms/pylanceImportResolve)
- [VS Code Python Documentation](https://code.visualstudio.com/docs/python/python-tutorial)
- [Python Virtual Environments Guide](https://docs.python.org/3/tutorial/venv.html)

If you continue to experience issues after trying these solutions, check the project's issue tracker for additional guidance. 