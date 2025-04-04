#!/usr/bin/env python
"""
Simple port checker that finds two available ports without requiring psutil.
Used as a fallback when psutil is not available.
"""

import socket
import random
import sys

def find_available_port():
    """Find an available TCP port by creating a socket and letting the OS assign a port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))  # Bind to any address, let OS choose port
    port = s.getsockname()[1]
    s.close()
    return port

def is_port_available(port):
    """Check if a specific port is available."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        s.close()
        return True
    except OSError:
        return False

def find_two_available_ports():
    """Find two available ports that don't conflict with each other."""
    # Try to get dynamically assigned ports first
    try:
        port1 = find_available_port()
        port2 = find_available_port()
        
        # Double-check they're both still available
        if is_port_available(port1) and is_port_available(port2):
            return port1, port2
    except:
        pass
    
    # Fallback to checking specific port ranges
    # Common ports that might be free on developer machines
    preferred_ranges = [
        (3000, 3100),  # Common for web development
        (8000, 8100),  # Common for web servers
        (9000, 9100)   # Often free
    ]
    
    for start, end in preferred_ranges:
        # Randomize within range to reduce chance of conflicts
        ports = list(range(start, end))
        random.shuffle(ports)
        
        found_ports = []
        for port in ports:
            if is_port_available(port):
                found_ports.append(port)
                if len(found_ports) == 2:
                    return found_ports[0], found_ports[1]
    
    # Last resort - return fixed ports with a warning
    print("Warning: Could not find available ports dynamically. Using defaults:", file=sys.stderr)
    return 3000, 9999

if __name__ == "__main__":
    try:
        ui_port, proxy_port = find_two_available_ports()
        print(f"{ui_port},{proxy_port}")
    except Exception as e:
        print(f"Error finding available ports: {e}", file=sys.stderr)
        print("3000,9999")  # Default fallback 