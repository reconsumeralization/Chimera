import asyncio
import json
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_client")

async def read_json():
    """Read a JSON message from stdin."""
    try:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            raise EOFError("End of input")
        line = line.strip()
        if line:
            logger.debug(f"Received raw input: {line}")
            return json.loads(line)
    except Exception as e:
        logger.error(f"Error reading input: {e}")
        raise

async def write_json(obj):
    """Write a JSON message to stdout."""
    try:
        json_str = json.dumps(obj) + "\n"
        logger.debug(f"Sending: {json_str.strip()}")
        await asyncio.get_event_loop().run_in_executor(None, sys.stdout.write, json_str)
        await asyncio.get_event_loop().run_in_executor(None, sys.stdout.flush)
    except Exception as e:
        logger.error(f"Error writing output: {e}")
        raise

async def main():
    """Run the test client."""
    logger.info("Starting test client...")
    
    # Send initialization message
    init_msg = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "initialize",
        "params": {}
    }
    
    await write_json(init_msg)
    logger.info("Sent initialization message")
    
    # Read initialization response
    init_response = await read_json()
    logger.info(f"Received initialization response: {init_response}")
    
    # Send ping message
    ping_msg = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "ping",
        "params": {}
    }
    
    await write_json(ping_msg)
    logger.info("Sent ping message")
    
    # Read ping response
    ping_response = await read_json()
    logger.info(f"Received ping response: {ping_response}")
    
    # Test git operations
    git_msg = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "git-operations",
        "params": {
            "operation": "status"
        }
    }
    
    await write_json(git_msg)
    logger.info("Sent git operations message")
    
    # Read git response
    git_response = await read_json()
    logger.info(f"Received git response: {git_response}")
    
    logger.info("Test completed successfully")

if __name__ == "__main__":
    asyncio.run(main()) 