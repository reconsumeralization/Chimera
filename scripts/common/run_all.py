#!/usr/bin/env python
"""
Run both the MCP and UI servers together.

This script starts both servers in separate processes and handles graceful shutdown.
"""

import os
import sys
import argparse
import asyncio
import signal
import subprocess
from pathlib import Path

# Add the project root directory to the Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.chimera_core.config import get_settings
from src.chimera_core.utils.network import get_free_port_pair


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Chimera services")
    parser.add_argument(
        "--ui-port",
        type=int,
        help="Port for the UI server (default: auto-detect)"
    )
    parser.add_argument(
        "--mcp-port",
        type=int,
        help="Port for the MCP server (default: auto-detect)"
    )
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Don't start the UI server"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open the browser when starting the UI"
    )
    parser.add_argument(
        "--enable-data-collection",
        action="store_true",
        help="Enable data collection"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Log level (default: from settings)"
    )
    return parser.parse_args()


async def run_servers():
    """Run the MCP and UI servers in separate processes."""
    args = parse_args()
    settings = get_settings()
    
    # Find available ports if not specified
    ui_port = args.ui_port
    mcp_port = args.mcp_port
    
    if ui_port is None and mcp_port is None:
        # Find two consecutive available ports
        try:
            ui_port, mcp_port = get_free_port_pair(
                host=settings.ui_server_host,
                start_port=settings.ui_server_port
            )
            print(f"Found available ports: UI={ui_port}, MCP={mcp_port}")
        except RuntimeError as e:
            print(f"Error finding available ports: {e}")
            return 1
    
    # Prepare common arguments
    log_level_arg = f"--log-level={args.log_level}" if args.log_level else ""
    data_collection_arg = "--enable-data-collection" if args.enable_data_collection else ""
    
    # Start the MCP server
    mcp_cmd = [
        sys.executable,
        str(script_dir / "run_mcp_server.py"),
        f"--port={mcp_port}" if mcp_port else "",
        log_level_arg,
        data_collection_arg
    ]
    mcp_cmd = [arg for arg in mcp_cmd if arg]  # Remove empty strings
    
    print(f"Starting MCP server: {' '.join(mcp_cmd)}")
    mcp_process = subprocess.Popen(mcp_cmd)
    
    # If requested, also start the UI server
    ui_process = None
    if not args.no_ui:
        # Wait a moment for MCP server to start
        await asyncio.sleep(1)
        
        no_browser_arg = "--no-browser" if args.no_browser else ""
        ui_cmd = [
            sys.executable,
            str(script_dir / "run_ui_server.py"),
            f"--port={ui_port}" if ui_port else "",
            no_browser_arg,
            log_level_arg
        ]
        ui_cmd = [arg for arg in ui_cmd if arg]  # Remove empty strings
        
        print(f"Starting UI server: {' '.join(ui_cmd)}")
        ui_process = subprocess.Popen(ui_cmd)
    
    # Set up signal handler for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        print("Received shutdown signal, stopping servers...")
        if ui_process:
            ui_process.terminate()
        mcp_process.terminate()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    # Wait for processes to complete
    try:
        mcp_status = None
        ui_status = None
        
        while True:
            if ui_process and ui_status is None:
                ui_status = ui_process.poll()
                if ui_status is not None:
                    print(f"UI server exited with status {ui_status}")
            
            if mcp_status is None:
                mcp_status = mcp_process.poll()
                if mcp_status is not None:
                    print(f"MCP server exited with status {mcp_status}")
                    # If MCP exits, also terminate UI
                    if ui_process and ui_status is None:
                        ui_process.terminate()
            
            if (ui_status is not None or ui_process is None) and mcp_status is not None:
                break
            
            await asyncio.sleep(0.5)
        
        return max(0, ui_status or 0, mcp_status or 0)
    
    except KeyboardInterrupt:
        signal_handler()
        return 0


def main():
    """Main entry point."""
    try:
        exit_code = asyncio.run(run_servers())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 