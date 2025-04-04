"""Network utilities for Project Chimera."""
import socket
import structlog
from typing import Optional, Tuple, List

from ..config import get_settings

logger = structlog.get_logger(__name__)

def is_port_available(host: str, port: int) -> bool:
    """
    Check if a host/port combination is available.
    
    Args:
        host: The host address to check
        port: The port number to check
        
    Returns:
        bool: True if the port is available, False otherwise
    """
    logger.debug("Checking port availability", host=host, port=port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind((host, port))
            logger.debug("Port is available", port=port)
            return True
        except (socket.error, OSError) as e:
            logger.debug("Port is not available", port=port, error=str(e))
            return False

def find_available_port(
    host: Optional[str] = None,
    start_port: Optional[int] = None,
    max_attempts: int = 10
) -> int:
    """
    Find an available port starting from start_port.
    
    Args:
        host: The host address to check (defaults to settings.mcp_server_host)
        start_port: The starting port number (defaults to settings.min_port)
        max_attempts: Maximum number of ports to check
        
    Returns:
        int: An available port number
        
    Raises:
        RuntimeError: If no available port could be found
    """
    settings = get_settings()
    host = host or settings.mcp_server_host
    start_port = start_port or settings.min_port
    
    port = start_port
    logger.info("Searching for available port", start_port=start_port, host=host)
    
    for attempt in range(max_attempts):
        logger.debug("Attempting port", port=port, attempt=attempt + 1, max_attempts=max_attempts)
        if is_port_available(host, port):
            logger.info("Found available port", available_port=port)
            return port
        port += 1

    logger.error("Could not find an available port", start_port=start_port, attempts=max_attempts)
    raise RuntimeError(
        f"Could not find an available port starting from {start_port} "
        f"after {max_attempts} attempts on host {host}"
    )

def get_free_port_pair(
    host: Optional[str] = None,
    start_port: Optional[int] = None,
    max_attempts: int = 20
) -> Tuple[int, int]:
    """
    Find two consecutive available ports.
    
    Useful for services that need two related ports (e.g., UI server and MCP proxy).
    
    Args:
        host: The host address to check
        start_port: The starting port number
        max_attempts: Maximum number of port pairs to check
        
    Returns:
        Tuple[int, int]: A pair of available ports
        
    Raises:
        RuntimeError: If no available port pair could be found
    """
    settings = get_settings()
    host = host or settings.mcp_server_host
    start_port = start_port or settings.min_port
    
    logger.info("Searching for available port pair", start_port=start_port, host=host)
    
    for attempt in range(max_attempts):
        first_port = start_port + (attempt * 2)
        second_port = first_port + 1
        
        logger.debug(
            "Attempting port pair", 
            first_port=first_port, 
            second_port=second_port,
            attempt=attempt + 1
        )
        
        if is_port_available(host, first_port) and is_port_available(host, second_port):
            logger.info(
                "Found available port pair", 
                first_port=first_port, 
                second_port=second_port
            )
            return first_port, second_port
    
    logger.error(
        "Could not find available port pair", 
        start_port=start_port, 
        attempts=max_attempts
    )
    raise RuntimeError(
        f"Could not find available port pair starting from {start_port} "
        f"after {max_attempts} attempts on host {host}"
    )

def find_and_terminate_process_by_port(port: int) -> bool:
    """
    Find and terminate a process using a specific port.
    
    This is a fallback for manual process termination if automatic port selection
    isn't sufficient.
    
    Args:
        port: The port number to check
        
    Returns:
        bool: True if a process was found and terminated, False otherwise
    """
    logger.warning("Attempting to find and terminate process on port", port=port)
    
    try:
        # Try to import psutil - this is an optional dependency
        import psutil
    except ImportError:
        logger.error("Could not import psutil - cannot terminate process")
        return False
    
    # Find connections using this port
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            connections = proc.connections()
            for conn in connections:
                if conn.laddr.port == port:
                    logger.warning(
                        "Found process using port", 
                        port=port, 
                        pid=proc.pid, 
                        name=proc.name()
                    )
                    proc.terminate()
                    logger.info("Terminated process", pid=proc.pid)
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    
    logger.info("No process found using port", port=port)
    return False 