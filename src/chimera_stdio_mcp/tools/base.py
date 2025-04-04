"""Base class for all MCP tools."""
import abc
import structlog
from typing import Any, Dict, List, Optional, Tuple, Union, ClassVar

logger = structlog.get_logger(__name__)

class BaseTool(abc.ABC):
    """Base class for all MCP tools.
    
    Each tool implementation should:
    1. Extend this class
    2. Set the TOOL_NAME class variable
    3. Implement the execute method
    4. Register in the tool registry
    """
    
    # Class variables to be overridden by subclasses
    TOOL_NAME: ClassVar[str] = ""
    DESCRIPTION: ClassVar[str] = ""
    
    def __init__(self):
        """Initialize the tool."""
        if not self.TOOL_NAME:
            raise ValueError(f"Tool {self.__class__.__name__} must define TOOL_NAME")
        
        self.log = logger.bind(tool=self.TOOL_NAME)
        self.log.debug("Initialized tool")
    
    @abc.abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the given parameters.
        
        Args:
            params: Dictionary of parameters for the tool
            
        Returns:
            Dictionary with the tool execution results
        """
        pass
    
    def validate_params(self, params: Dict[str, Any], required_params: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate that all required parameters are present.
        
        Args:
            params: Parameters to validate
            required_params: List of required parameter names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        missing = [param for param in required_params if param not in params]
        if missing:
            error_msg = f"Missing required parameters: {', '.join(missing)}"
            self.log.warning(error_msg, missing_params=missing)
            return False, error_msg
        return True, None
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get the JSON schema for this tool.
        
        This can be overridden by subclasses to provide a custom schema,
        but the default implementation extracts info from class variables.
        
        Returns:
            Dictionary containing the tool's JSON schema
        """
        return {
            "name": cls.TOOL_NAME,
            "description": cls.DESCRIPTION,
            # Subclasses should override to provide parameters schema
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        } 