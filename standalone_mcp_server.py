import http.server
import socketserver
import webbrowser
import threading
import time
import os
import socket
import logging
import sys
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)] # Explicitly output to stdout
)
logger = logging.getLogger("DevToolkitServer")

# Constants
DEFAULT_PORT = 9998
MAX_PORT_ATTEMPTS = 10
HOST = "127.0.0.1"
INDEX_FILENAME = "index.html" # Name of the HTML file

def is_port_available(host: str, port: int) -> bool:
    """Check if a host/port combination is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Set a short timeout to avoid long waits on occupied ports
        s.settimeout(0.1)
        try:
            # Try to bind exclusively (SO_REUSEADDR=False is default)
            s.bind((host, port))
            return True
        except (socket.error, OSError):
            # OSError can occur on some systems e.g., "address already in use"
            return False

def find_available_port(host: str = HOST, start_port: int = DEFAULT_PORT) -> int:
    """Find an available port starting from start_port."""
    port = start_port
    for attempt in range(MAX_PORT_ATTEMPTS):
        logger.debug(f"Attempting to bind to {host}:{port} (Attempt {attempt + 1}/{MAX_PORT_ATTEMPTS})")
        if is_port_available(host, port):
            logger.info(f"Found available port: {port}")
            return port
        port += 1
    raise RuntimeError(f"Could not find an available port starting from {start_port} after {MAX_PORT_ATTEMPTS} attempts on host {host}")

class DevToolkitHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve index.html for root and handle logging."""

    def __init__(self, *args, **kwargs):
        # Serve files from the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=script_dir, **kwargs)

    def log_message(self, format: str, *args) -> None:
        """Override to use our logger instead of writing to stderr."""
        logger.info(format % args)

    def do_GET(self) -> None:
        """Serve index.html for '/' or fall back to default file serving."""
        if self.path == "/":
            # Rewrite root path to serve the specific index file
            self.path = f"/{INDEX_FILENAME}"
            # Check if index.html exists before serving
            filepath = os.path.join(self.directory, INDEX_FILENAME)
            if not os.path.exists(filepath):
                self.send_error(404, f"File Not Found: {INDEX_FILENAME}")
                return

        # Let SimpleHTTPRequestHandler handle serving the file (or 404)
        super().do_GET()

    def do_HEAD(self) -> None:
        """Handle HEAD requests similarly to GET."""
        if self.path == "/":
            self.path = f"/{INDEX_FILENAME}"
        super().do_HEAD()


def run_web_server(host: str, port: int, server_ready_event: threading.Event, stop_event: threading.Event) -> None:
    """Run the web server until stop_event is set."""
    Handler = DevToolkitHandler
    httpd = None
    try:
        # Use ThreadingHTTPServer for better responsiveness if needed,
        # but TCPServer is often fine for simple local use.
        # httpd = socketserver.ThreadingTCPServer((host, port), Handler)
        httpd = socketserver.TCPServer((host, port), Handler)
        # Disable Nagle's algorithm for potentially slightly lower latency
        httpd.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # Allow address reuse quickly after shutdown
        httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        logger.info(f"Serving HTTP on {host} port {port}...")
        logger.info(f"Access the toolkit at: http://{host}:{port}/")

        # Signal that the server is ready
        server_ready_event.set()

        # Serve until the stop event is set
        while not stop_event.is_set():
            httpd.handle_request() # Handle one request at a time

        logger.info("Stop event received, shutting down server...")

    except OSError as e:
        logger.error(f"Could not start server on {host}:{port}. Error: {e}")
        # Signal readiness anyway so main thread doesn't hang forever
        server_ready_event.set()
    except Exception as e:
        logger.error(f"An unexpected error occurred in the web server: {e}", exc_info=True)
        server_ready_event.set() # Signal to unblock main thread
    finally:
        if httpd:
            logger.info("Closing server socket.")
            httpd.server_close() # Close the server socket


def main():
    """Main function to set up and run the server."""
    port = -1
    httpd_thread = None
    server_ready = threading.Event()
    stop_server = threading.Event()

    try:
        # 1. Find an available port
        port = find_available_port(HOST, DEFAULT_PORT)

        # 2. Start the web server in a separate thread
        httpd_thread = threading.Thread(
            target=run_web_server,
            args=(HOST, port, server_ready, stop_server),
            daemon=True # Still daemon, so it exits if main thread crashes
        )
        httpd_thread.start()

        # 3. Wait for the server thread to signal it's ready (or failed)
        logger.info("Waiting for server to start...")
        ready = server_ready.wait(timeout=5.0) # Wait up to 5 seconds
        if not ready:
            logger.error("Server did not start within the timeout period.")
            raise RuntimeError("Server failed to start")
        # Check if thread is still alive (it might have exited due to an error)
        if not httpd_thread.is_alive():
             raise RuntimeError("Server thread terminated unexpectedly during startup.")
        logger.info("Server reported as ready.")

        # 4. Open the web page in a browser using the correct port
        server_url = f"http://{HOST}:{port}/"
        try:
            logger.info(f"Attempting to open browser at {server_url}")
            webbrowser.open(server_url)
        except Exception as e: # Catch broader exceptions from webbrowser
            logger.warning(f"Could not automatically open web browser: {e}")
            logger.info(f"Please open this URL manually: {server_url}")

        # 5. Keep the main thread alive, waiting for KeyboardInterrupt
        logger.info("Server running. Press Ctrl+C to stop.")
        while httpd_thread.is_alive():
            # Sleep briefly to avoid busy-waiting, join with timeout allows checking
            httpd_thread.join(timeout=0.5)

    except RuntimeError as e:
        logger.error(f"Failed to start or run the server: {e}")
        # No need to signal stop if it failed early
    except KeyboardInterrupt:
        logger.info("Ctrl+C received. Initiating shutdown...")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main thread: {e}", exc_info=True)
    finally:
        # 6. Signal the server thread to stop and wait for it
        if httpd_thread and httpd_thread.is_alive():
            logger.info("Signaling server thread to stop...")
            stop_server.set()
            logger.info("Waiting for server thread to finish...")
            httpd_thread.join(timeout=5.0) # Wait for graceful shutdown
            if httpd_thread.is_alive():
                logger.warning("Server thread did not stop gracefully after 5 seconds.")
            else:
                logger.info("Server thread finished.")
        logger.info("Application shut down.")
        sys.exit(0 if port != -1 else 1) # Exit with error code if server never started properly

if __name__ == "__main__":
    main()