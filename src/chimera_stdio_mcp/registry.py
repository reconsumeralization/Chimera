"""Registry for MCP tools."""
import structlog
from typing import Dict, List, Type, Any

from .tools.base import BaseTool

logger = structlog.get_logger(__name__)

class ToolRegistry:
    """Registry for MCP tools.
    
    This class manages the registration and retrieval of MCP tools.
    """
    
    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}
        self.log = logger.bind(component="ToolRegistry")
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool class.
        
        Args:
            tool_class: The tool class to register
        """
        tool_name = tool_class.TOOL_NAME
        if not tool_name:
            raise ValueError(f"Tool class {tool_class.__name__} has no TOOL_NAME defined")
        
        if tool_name in self._tools:
            self.log.warning(
                f"Tool {tool_name} is already registered. Overwriting.",
                tool_name=tool_name,
                existing_class=self._tools[tool_name].__name__,
                new_class=tool_class.__name__
            )
        
        self._tools[tool_name] = tool_class
        self.log.debug(f"Registered tool {tool_name}", tool_class=tool_class.__name__)
    
    def get_tool(self, tool_name: str) -> BaseTool:
        """Get a tool instance by name.
        
        Args:
            tool_name: The name of the tool to retrieve
            
        Returns:
            An instance of the requested tool
            
        Raises:
            KeyError: If the tool is not registered
        """
        if tool_name not in self._tools:
            self.log.error(f"Tool {tool_name} not found", available_tools=list(self._tools.keys()))
            raise KeyError(f"Tool {tool_name} not found")
        
        # Create instance if not already created
        if tool_name not in self._instances:
            tool_class = self._tools[tool_name]
            
            # Handle special case for FileManagerTool
            if tool_name == "fileManager":
                # Get workspace path from environment or use current directory
                from chimera_core.config import get_settings
                workspace_path = get_settings().workspace_path
                self._instances[tool_name] = tool_class(base_path=workspace_path)
                self.log.debug(f"Created instance of FileManagerTool with base_path: {workspace_path}")
            else:
                self._instances[tool_name] = tool_class()
                self.log.debug(f"Created instance of tool {tool_name}")
        
        return self._instances[tool_name]
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get instances of all registered tools.
        
        Returns:
            List of all tool instances
        """
        # Ensure all tools are instantiated
        for tool_name, tool_class in self._tools.items():
            if tool_name not in self._instances:
                # Handle special case for FileManagerTool
                if tool_name == "fileManager":
                    # Get workspace path from environment or use current directory
                    from chimera_core.config import get_settings
                    workspace_path = get_settings().workspace_path
                    self._instances[tool_name] = tool_class(base_path=workspace_path)
                    self.log.debug(f"Created instance of FileManagerTool with base_path: {workspace_path}")
                else:
                    self._instances[tool_name] = tool_class()
                    self.log.debug(f"Created instance of tool {tool_name}")
        
        return list(self._instances.values())
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get JSON schemas for all registered tools.
        
        Returns:
            List of tool schemas
        """
        return [tool_class.get_schema() for tool_class in self._tools.values()]
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._instances.clear()
        self.log.debug("Cleared all registered tools")


# Create a global tool registry instance
registry = ToolRegistry() 