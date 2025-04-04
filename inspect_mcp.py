import os
import sys
import importlib.util
import inspect

def find_module_path(module_name):
    """Find the path to a module."""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        return None
    return spec.origin

def inspect_module(module_name):
    """Inspect a module to find protocol version information."""
    try:
        module = importlib.import_module(module_name)
        print(f"Module: {module_name}")
        print(f"Path: {find_module_path(module_name)}")
        
        # Look for protocol version constants
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, (str, int, float, bool)) and "protocol" in name.lower() and "version" in name.lower():
                print(f"  {name} = {obj}")
        
        # Look for protocol version in functions
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                try:
                    source = inspect.getsource(obj)
                    if "protocol" in source.lower() and "version" in source.lower():
                        print(f"  Function {name} contains protocol version references:")
                        for line in source.split('\n'):
                            if "protocol" in line.lower() and "version" in line.lower():
                                print(f"    {line.strip()}")
                except (TypeError, OSError):
                    pass
        
        print()
    except Exception as e:
        print(f"Error inspecting {module_name}: {e}")

# Inspect the MCP proxy modules
inspect_module("mcp_proxy")
inspect_module("mcp_proxy.proxy_server")
inspect_module("mcp_proxy.sse_server")

# Try to find the MCP SDK modules
try:
    inspect_module("mcp")
    inspect_module("mcp.client.session")
except Exception as e:
    print(f"Error finding MCP SDK modules: {e}")

# Look for protocol version in the site-packages directory
site_packages = os.path.dirname(os.path.dirname(find_module_path("mcp_proxy")))
print(f"Searching in site-packages: {site_packages}")

for root, dirs, files in os.walk(site_packages):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "protocol" in content.lower() and "version" in content.lower():
                        print(f"Found protocol version reference in {path}")
                        for line in content.split('\n'):
                            if "protocol" in line.lower() and "version" in line.lower():
                                print(f"  {line.strip()}")
            except Exception as e:
                pass 