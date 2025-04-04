import os
import re

def find_protocol_version():
    sdk_path = r"C:\Users\recon\MCPServers\python-sdk\src\mcp"
    for root, dirs, files in os.walk(sdk_path):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Look for protocol version constants or checks
                        matches = re.finditer(r'(?:PROTOCOL_VERSION|protocol_version|protocolVersion)\s*[=:]\s*["\']([^"\']+)["\']', content)
                        for match in matches:
                            print(f"Found in {path}:")
                            print(f"  Version: {match.group(1)}")
                            # Print surrounding context
                            start = max(0, content.rfind('\n', 0, match.start()) + 1)
                            end = content.find('\n', match.end())
                            if end == -1:
                                end = len(content)
                            print(f"  Context: {content[start:end].strip()}")
                            print()
                except Exception as e:
                    print(f"Error reading {path}: {e}")

if __name__ == "__main__":
    find_protocol_version() 