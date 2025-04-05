#!/usr/bin/env python
"""
Project Chimera Dashboard

A simple GUI for managing Project Chimera services and tools,
designed for accessibility and ease of use.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
from pathlib import Path

# Define color scheme
COLORS = {
    "bg_main": "#1A1A2E",  # Deep midnight blue
    "bg_panel": "#16213E",  # Dark purple-blue
    "text": "#E0E0E0",      # Light silver
    "accent": "#7FFF00",    # Electric/toxic green
    "success": "#39FF14",   # Bright neon green
    "warning": "#FF9D00",   # Bright orange
    "error": "#FF3131",     # Bright red
    "button": "#7700FF",    # Electric purple
    "button_hover": "#9D00FF",  # Brighter purple
    "inactive": "#4F4F4F",  # Dark gray
}

# Get project root directory
PROJECT_ROOT = Path(__file__).resolve().parent

class ChimeraDashboard:
    """Main dashboard application for Project Chimera."""
    
    def __init__(self, root):
        """Initialize the dashboard.
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        self.root.title("Project Chimera Dashboard")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        self.root.configure(bg=COLORS["bg_main"])
        
        # Set application icon if available
        icon_path = PROJECT_ROOT / "static" / "images" / "Chimera.png"
        if icon_path.exists():
            try:
                self.root.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
            except Exception:
                pass  # Ignore if icon can't be loaded
        
        # Track running processes
        self.processes = {}
        
        # Create the UI
        self.create_styles()
        self.create_ui()
        
        # Update service status periodically
        self.update_service_status()
    
    def create_styles(self):
        """Create custom ttk styles for the dashboard."""
        self.style = ttk.Style()
        
        # Configure the main theme
        self.style.configure(
            "TFrame",
            background=COLORS["bg_main"],
        )
        
        # Configure button styles
        self.style.configure(
            "TButton",
            background=COLORS["button"],
            foreground=COLORS["text"],
            font=("Arial", 11, "bold"),
            padding=10,
            relief="flat",
        )
        
        # Configure label styles
        self.style.configure(
            "TLabel",
            background=COLORS["bg_main"],
            foreground=COLORS["text"],
            font=("Arial", 11),
            padding=5,
        )
        
        # Configure heading label style
        self.style.configure(
            "Heading.TLabel",
            font=("Arial", 14, "bold"),
            foreground=COLORS["accent"],
            padding=10,
        )
        
        # Configure status labels
        self.style.configure(
            "Running.TLabel",
            foreground=COLORS["success"],
            font=("Arial", 11, "bold"),
        )
        
        self.style.configure(
            "Stopped.TLabel",
            foreground=COLORS["error"],
            font=("Arial", 11, "bold"),
        )
        
        # Configure separator
        self.style.configure(
            "TSeparator",
            background=COLORS["accent"],
        )
    
    def create_ui(self):
        """Create the user interface."""
        # Main container frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Project Chimera Dashboard",
            style="Heading.TLabel",
        )
        title_label.pack(pady=(0, 10))
        
        # Split into left and right panels
        panel_frame = ttk.Frame(main_frame)
        panel_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for service controls
        left_panel = ttk.Frame(panel_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right panel for output and logs
        right_panel = ttk.Frame(panel_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Create service control panel
        self.create_service_panel(left_panel)
        
        # Create tools panel
        self.create_tools_panel(left_panel)
        
        # Create output panel
        self.create_output_panel(right_panel)
    
    def create_service_panel(self, parent):
        """Create the service control panel.
        
        Args:
            parent: The parent widget
        """
        # Service panel frame
        service_frame = ttk.Frame(parent)
        service_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Service panel heading
        service_heading = ttk.Label(
            service_frame,
            text="Services",
            style="Heading.TLabel",
        )
        service_heading.pack(pady=(0, 5))
        
        # Service status frame
        status_frame = ttk.Frame(service_frame)
        status_frame.pack(fill=tk.X, expand=False, pady=5)
        
        # Web server status
        ttk.Label(status_frame, text="Web Server:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.web_status_label = ttk.Label(status_frame, text="Checking...", style="TLabel")
        self.web_status_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # MCP server status
        ttk.Label(status_frame, text="MCP Servers:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.mcp_status_label = ttk.Label(status_frame, text="Checking...", style="TLabel")
        self.mcp_status_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Service control buttons frame
        control_frame = ttk.Frame(service_frame)
        control_frame.pack(fill=tk.X, expand=False, pady=10)
        
        # Start simple mode button
        start_simple_btn = ttk.Button(
            control_frame,
            text="Start Simplified Mode",
            command=self.start_simplified,
        )
        start_simple_btn.pack(fill=tk.X, pady=5)
        
        # Start full mode button
        start_full_btn = ttk.Button(
            control_frame,
            text="Start Full Mode",
            command=self.start_full,
        )
        start_full_btn.pack(fill=tk.X, pady=5)
        
        # Stop all services button
        stop_btn = ttk.Button(
            control_frame,
            text="Stop All Services",
            command=self.stop_all_services,
        )
        stop_btn.pack(fill=tk.X, pady=5)
    
    def create_tools_panel(self, parent):
        """Create the tools panel.
        
        Args:
            parent: The parent widget
        """
        # Tools panel frame
        tools_frame = ttk.Frame(parent)
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Tools panel heading
        tools_heading = ttk.Label(
            tools_frame,
            text="Maintenance Tools",
            style="Heading.TLabel",
        )
        tools_heading.pack(pady=(0, 5))
        
        # System check button
        check_btn = ttk.Button(
            tools_frame,
            text="Run System Check",
            command=lambda: self.run_tool("check_system.py"),
        )
        check_btn.pack(fill=tk.X, pady=5)
        
        # Quick fix button
        fix_btn = ttk.Button(
            tools_frame,
            text="Run System Quick Fix",
            command=lambda: self.run_tool("check_system.py --fix"),
        )
        fix_btn.pack(fill=tk.X, pady=5)
        
        # MCP fix button
        mcp_fix_btn = ttk.Button(
            tools_frame,
            text="Fix MCP Issues",
            command=lambda: self.run_tool("fix_mcp.py"),
        )
        mcp_fix_btn.pack(fill=tk.X, pady=5)
        
        # Open accessibility guide button
        guide_btn = ttk.Button(
            tools_frame,
            text="Open Accessibility Guide",
            command=self.open_accessibility_guide,
        )
        guide_btn.pack(fill=tk.X, pady=5)
    
    def create_output_panel(self, parent):
        """Create the output panel.
        
        Args:
            parent: The parent widget
        """
        # Output panel frame
        output_frame = ttk.Frame(parent)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        # Output panel heading
        output_heading = ttk.Label(
            output_frame,
            text="Output",
            style="Heading.TLabel",
        )
        output_heading.pack(pady=(0, 5))
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            bg=COLORS["bg_panel"],
            fg=COLORS["text"],
            font=("Consolas", 10),
            wrap=tk.WORD,
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        
        # Clear output button
        clear_btn = ttk.Button(
            output_frame,
            text="Clear Output",
            command=self.clear_output,
        )
        clear_btn.pack(fill=tk.X, pady=5)
    
    def update_service_status(self):
        """Update the service status labels."""
        try:
            # Check web server (port 8000)
            web_running = self.is_port_in_use(8000)
            
            # Check MCP processes
            mcp_running = self.is_process_running("chimera_stdio_mcp")
            
            # Update status labels
            if web_running:
                self.web_status_label.config(text="Running", style="Running.TLabel")
            else:
                self.web_status_label.config(text="Stopped", style="Stopped.TLabel")
            
            if mcp_running:
                self.mcp_status_label.config(text="Running", style="Running.TLabel")
            else:
                self.mcp_status_label.config(text="Stopped", style="Stopped.TLabel")
        
        except Exception as e:
            self.log_output(f"Error checking service status: {e}")
        
        # Schedule next update
        self.root.after(5000, self.update_service_status)
    
    def start_simplified(self):
        """Start the simplified mode (web server only)."""
        self.stop_all_services()
        time.sleep(1)
        
        # Start the easy_start script
        if os.name == "nt":
            script = str(PROJECT_ROOT / "easy_start.bat")
            self.log_output("Starting services in simplified mode (easy_start.bat)...")
            # Use subprocess.Popen to start the script
            try:
                proc = subprocess.Popen(
                    ["cmd", "/c", "start", "cmd", "/k", script],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.log_output("Simplified mode started in a new window.")
            except Exception as e:
                self.log_output(f"Error starting simplified mode: {e}")
        else:
            script = str(PROJECT_ROOT / "easy_start.sh")
            self.log_output("Starting services in simplified mode (easy_start.sh)...")
            try:
                os.chmod(script, 0o755)  # Make executable
                proc = subprocess.Popen(
                    ["x-terminal-emulator", "-e", script],
                    stderr=subprocess.PIPE
                )
                self.log_output("Simplified mode started in a new window.")
            except Exception as e:
                self.log_output(f"Error starting simplified mode: {e}")
    
    def start_full(self):
        """Start the full mode (web server and MCP servers)."""
        self.stop_all_services()
        time.sleep(1)
        
        # Start the full start_chimera script
        if os.name == "nt":
            script = str(PROJECT_ROOT / "start_chimera.bat")
            self.log_output("Starting services in full mode (start_chimera.bat)...")
            try:
                proc = subprocess.Popen(
                    ["cmd", "/c", "start", "cmd", "/k", script],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.log_output("Full mode started in a new window.")
            except Exception as e:
                self.log_output(f"Error starting full mode: {e}")
        else:
            script = str(PROJECT_ROOT / "start_chimera.sh")
            self.log_output("Starting services in full mode (start_chimera.sh)...")
            try:
                os.chmod(script, 0o755)  # Make executable
                proc = subprocess.Popen(
                    ["x-terminal-emulator", "-e", script],
                    stderr=subprocess.PIPE
                )
                self.log_output("Full mode started in a new window.")
            except Exception as e:
                self.log_output(f"Error starting full mode: {e}")
    
    def stop_all_services(self):
        """Stop all running services."""
        self.log_output("Stopping all services...")
        
        try:
            if os.name == "nt":
                # Windows
                subprocess.run(["taskkill", "/f", "/im", "uvicorn.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["taskkill", "/f", "/im", "python.exe", "/fi", "windowtitle eq *chimera*"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                # Linux/Mac
                subprocess.run("pkill -f 'uvicorn'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run("pkill -f 'chimera_stdio_mcp'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.log_output("All services stopped.")
        except Exception as e:
            self.log_output(f"Error stopping services: {e}")
    
    def run_tool(self, tool_cmd):
        """Run a tool and capture its output.
        
        Args:
            tool_cmd: The command to run
        """
        cmd_parts = tool_cmd.split()
        tool_name = cmd_parts[0]
        
        self.log_output(f"Running tool: {tool_cmd}")
        
        # Create and start the thread
        thread = threading.Thread(
            target=self._run_tool_thread,
            args=(tool_cmd,),
            daemon=True
        )
        thread.start()
    
    def _run_tool_thread(self, tool_cmd):
        """Run a tool in a separate thread.
        
        Args:
            tool_cmd: The command to run
        """
        try:
            # Enable console colors on Windows
            if os.name == "nt":
                os.system("color")
            
            # Run the process and capture output
            process = subprocess.Popen(
                [sys.executable] + tool_cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Read output line by line
            for line in iter(process.stdout.readline, ""):
                self.log_output(line.rstrip())
            
            # Wait for process to complete
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                self.log_output(f"Tool completed successfully with return code {return_code}.")
            else:
                self.log_output(f"Tool failed with return code {return_code}.")
        
        except Exception as e:
            self.log_output(f"Error running tool: {e}")
    
    def open_accessibility_guide(self):
        """Open the accessibility guide."""
        guide_path = PROJECT_ROOT / "ACCESSIBILITY.md"
        
        if guide_path.exists():
            self.log_output("Opening accessibility guide...")
            
            # Read the guide content
            try:
                with open(guide_path, "r") as f:
                    content = f.read()
                
                # Show in a new window
                self.show_guide_window(content)
                
            except Exception as e:
                self.log_output(f"Error opening guide: {e}")
        else:
            self.log_output("Accessibility guide not found.")
    
    def show_guide_window(self, content):
        """Show the guide content in a new window.
        
        Args:
            content: The content to display
        """
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Accessibility Guide")
        guide_window.geometry("800x600")
        guide_window.minsize(600, 400)
        guide_window.configure(bg=COLORS["bg_main"])
        
        # Create text widget for content
        text = scrolledtext.ScrolledText(
            guide_window,
            bg=COLORS["bg_panel"],
            fg=COLORS["text"],
            font=("Arial", 11),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Insert content
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = ttk.Button(
            guide_window,
            text="Close",
            command=guide_window.destroy
        )
        close_btn.pack(pady=10)
    
    def clear_output(self):
        """Clear the output text area."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def log_output(self, message):
        """Log a message to the output text area.
        
        Args:
            message: The message to log
        """
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def is_port_in_use(self, port):
        """Check if a port is in use.
        
        Args:
            port: The port to check
            
        Returns:
            bool: True if the port is in use, False otherwise
        """
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def is_process_running(self, process_name):
        """Check if a process is running.
        
        Args:
            process_name: The name of the process to check
            
        Returns:
            bool: True if the process is running, False otherwise
        """
        if os.name == "nt":
            # Windows
            output = subprocess.check_output("tasklist", shell=True).decode()
            return process_name.lower() in output.lower()
        else:
            # Linux/Mac
            try:
                output = subprocess.check_output(["pgrep", "-f", process_name]).decode()
                return bool(output.strip())
            except subprocess.CalledProcessError:
                return False


def main():
    """Main entry point."""
    root = tk.Tk()
    app = ChimeraDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main() 