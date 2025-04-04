#!/usr/bin/env python
"""
Utility script to make shell scripts executable.
This can be used if chmod +x doesn't work for some reason.
"""

import os
import stat
import sys

SCRIPT_EXTENSIONS = ['.sh', '.py']

def make_executable(file_path):
    """
    Make a file executable by adding the execution bit to its permissions.
    """
    try:
        current_permissions = os.stat(file_path).st_mode
        new_permissions = current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        os.chmod(file_path, new_permissions)
        print(f"Made {file_path} executable")
        return True
    except Exception as e:
        print(f"Error setting permissions for {file_path}: {e}")
        return False

def main():
    """
    Make all script files in the current directory executable.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    success_count = 0
    fail_count = 0
    
    for filename in os.listdir(current_dir):
        file_path = os.path.join(current_dir, filename)
        if os.path.isfile(file_path) and any(filename.endswith(ext) for ext in SCRIPT_EXTENSIONS):
            if make_executable(file_path):
                success_count += 1
            else:
                fail_count += 1
    
    print(f"\nSummary: Made {success_count} files executable. Failed for {fail_count} files.")
    
    if success_count > 0:
        print("\nYou can now run './run_with_proxy.sh' to start the toolkit.")
    
    if fail_count > 0:
        print("\nFor files that failed, try running the following command manually:")
        print("chmod +x *.sh *.py")
    
    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 