"""Custom exceptions for Chimera Core."""

class ChimeraError(Exception):
    """Base exception for all Chimera errors."""
    
    def __init__(self, message: str):
        """Initialize ChimeraError.
        
        Args:
            message: Error message
        """
        self.message = message
        super().__init__(self.message)

class DatabaseError(ChimeraError):
    """Exception raised for database errors."""
    pass

class NotFoundError(ChimeraError):
    """Exception raised when a resource is not found."""
    pass

class ValidationError(ChimeraError):
    """Exception raised for validation errors."""
    pass

class ConfigurationError(ChimeraError):
    """Exception raised for configuration errors."""
    pass

class ServiceError(ChimeraError):
    """Exception raised for service errors."""
    pass

class AuthenticationError(ChimeraError):
    """Exception raised for authentication errors."""
    pass

class AuthorizationError(ChimeraError):
    """Exception raised for authorization errors."""
    pass 