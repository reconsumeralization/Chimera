import socket
import logging
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PortChecker")

def is_port_in_use(port, host='127.0.0.1'):
    """Check if a port is in use by attempting to bind to it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except (socket.error, OSError):
            return True

def find_free_port(start_port=9998, max_attempts=20, host='127.0.0.1'):
    """Find an available port starting from start_port."""
    current_port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(current_port, host):
            return current_port
        current_port += 1
    raise RuntimeError(f"Could not find an available port starting from {start_port} after {max_attempts} attempts")

def kill_process_on_port(port, host='127.0.0.1'):
    """Attempt to kill any process using the specified port."""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and (conn.laddr.ip == host or host == '127.0.0.1' and conn.laddr.ip == '0.0.0.0'):
                try:
                    process = psutil.Process(conn.pid)
                    logger.info(f"Killing process {process.name()} (PID: {conn.pid}) that's using port {port}")
                    process.terminate()
                    return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.warning(f"Could not terminate process with PID {conn.pid}")
                    return False
        return False
    except Exception as e:
        logger.error(f"Error while trying to kill process on port {port}: {str(e)}")
        return False

def ensure_port_availability(preferred_port, alternative_start=None, host='127.0.0.1'):
    """
    Ensures a port is available by:
    1. Checking if preferred port is available
    2. If not, attempting to kill the process using it
    3. If still not available, finding another free port
    
    Returns the port that's available for use
    """
    if not is_port_in_use(preferred_port, host):
        logger.info(f"Port {preferred_port} is available")
        return preferred_port
    
    logger.warning(f"Port {preferred_port} is in use")
    
    # Attempt to kill the process using the port
    if kill_process_on_port(preferred_port, host):
        if not is_port_in_use(preferred_port, host):
            logger.info(f"Successfully freed port {preferred_port}")
            return preferred_port
    
    # If we couldn't free the preferred port, find another one
    if alternative_start is None:
        alternative_start = preferred_port + 1
    
    available_port = find_free_port(alternative_start, 50, host)
    logger.info(f"Using alternative port {available_port}")
    return available_port

if __name__ == "__main__":
    # Test the functions
    web_port = ensure_port_availability(9998)
    mcp_port = ensure_port_availability(9999, 10000)
    print(f"Web port: {web_port}")
    print(f"MCP port: {mcp_port}") 