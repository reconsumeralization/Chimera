"""MCP client for communication with the client-side."""
import json
import asyncio
import structlog
import uuid
from typing import Any, Dict, Optional

logger = structlog.get_logger(__name__)

# Global state for tracking pending requests
_request_futures: Dict[str, asyncio.Future] = {}
_request_timeout = 60.0  # Default timeout in seconds

class MCPError(Exception):
    """Error occurred during MCP communication."""
    
    def __init__(self, message: str, code: Optional[int] = None):
        super().__init__(message)
        self.code = code

def set_timeout(timeout_seconds: float) -> None:
    """
    Set the timeout for MCP requests.
    
    Args:
        timeout_seconds: Timeout in seconds
    """
    global _request_timeout
    _request_timeout = timeout_seconds

async def send_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a request to the client and wait for a response.
    
    Args:
        method: The MCP method to call (e.g., "sampling/createMessage")
        params: Parameters for the method
        
    Returns:
        Dict: The response from the client
        
    Raises:
        MCPError: If an error occurs during MCP communication
        asyncio.TimeoutError: If the request times out
    """
    # Generate a unique ID for this request
    request_id = str(uuid.uuid4())
    
    # Create the JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }
    
    # Create a future to receive the response
    future = asyncio.get_running_loop().create_future()
    _request_futures[request_id] = future
    
    try:
        # Serialize and send the request
        request_json = json.dumps(request)
        logger.debug("Sending MCP request", method=method, id=request_id)
        
        # In an actual implementation, this would write to stdout or another channel
        # Here we'll use a placeholder for the actual writing mechanism
        await _write_request(request_json)
        
        # Wait for the response with a timeout
        return await asyncio.wait_for(future, _request_timeout)
    
    except asyncio.TimeoutError:
        logger.warning("MCP request timed out", method=method, id=request_id)
        _request_futures.pop(request_id, None)
        raise
    
    except Exception as e:
        logger.exception("Error sending MCP request", method=method, id=request_id, error=str(e))
        _request_futures.pop(request_id, None)
        raise MCPError(f"Error sending request: {str(e)}")
    
    finally:
        # Clean up the future if not already done
        if request_id in _request_futures:
            if not _request_futures[request_id].done():
                _request_futures[request_id].cancel()
            _request_futures.pop(request_id, None)

async def _write_request(request_json: str) -> None:
    """
    Write the request to the client.
    
    This function should be implemented to match the specific communication 
    channel used by the MCP implementation.
    
    Args:
        request_json: Serialized JSON-RPC request
    """
    # In a real implementation, this would write to stdout or other channel
    # For example:
    # print(request_json, flush=True)
    
    # For now, raise an error indicating this needs to be implemented
    raise NotImplementedError(
        "The _write_request function must be implemented to match the "
        "specific communication channel used by the MCP implementation."
    )

def handle_response(response_json: str) -> None:
    """
    Handle a response received from the client.
    
    This function should be called when a response is received from the client.
    It will resolve the appropriate future with the response.
    
    Args:
        response_json: Serialized JSON-RPC response
    """
    try:
        # Parse the response
        response = json.loads(response_json)
        
        # Check if it's a valid JSON-RPC response
        if "jsonrpc" not in response or response["jsonrpc"] != "2.0":
            logger.warning("Invalid JSON-RPC response", response=response)
            return
        
        # Get the request ID
        request_id = response.get("id")
        if not request_id:
            logger.warning("Response missing ID", response=response)
            return
        
        # Find the corresponding future
        future = _request_futures.get(request_id)
        if not future:
            logger.warning("No pending request matching response ID", id=request_id)
            return
        
        # Check for error
        if "error" in response:
            error = response["error"]
            error_message = error.get("message", "Unknown error")
            error_code = error.get("code")
            logger.warning("MCP error response", id=request_id, error=error_message, code=error_code)
            future.set_exception(MCPError(error_message, error_code))
        
        # Set the result
        elif "result" in response:
            logger.debug("MCP response received", id=request_id)
            future.set_result(response["result"])
        
        else:
            logger.warning("Invalid response format", id=request_id, response=response)
            future.set_exception(MCPError("Invalid response format: missing result and error"))
        
        # Remove the future
        _request_futures.pop(request_id, None)
    
    except json.JSONDecodeError:
        logger.exception("Error parsing JSON response", response_json=response_json)
    
    except Exception as e:
        logger.exception("Error handling response", error=str(e))

def initialize(server_instance: Any) -> None:
    """
    Initialize the MCP client with a reference to the server.
    
    This should be called during server initialization to provide the
    necessary context for sending/receiving messages.
    
    Args:
        server_instance: The ChimeraMCP server instance or other object
                         providing access to the communication channel
    """
    # Implementation depends on the specifics of the server class
    # This function would typically store a reference to the server and
    # customize the _write_request function to use the server's communication channel
    pass 