#!/usr/bin/env python
"""Test script for verifying that the AI client is working correctly."""
import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from src.chimera_core.services.ai_client import AIClient
from src.chimera_core.config import get_settings

# Set up logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


async def test_ai_client():
    """Test the AI client with a simple query."""
    logger.info("Testing AI client")
    
    # Get settings
    settings = get_settings()
    
    # Check if API key is set
    api_key = settings.api_key or os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        logger.error("No API key found. Set GOOGLE_API_KEY environment variable or configure api_key in settings.")
        return
    
    # Create AI client
    client = AIClient(api_key=api_key)
    
    logger.info("AI client created", model=client.model)
    
    try:
        # Test a simple query
        prompt = "What are the main benefits of using TypeScript over JavaScript?"
        
        logger.info("Sending query to AI model", prompt=prompt)
        
        response = await client.call_llm(prompt=prompt)
        
        logger.info("Received response from AI model", response_length=len(response))
        logger.info("Response preview", preview=response[:200] + "..." if len(response) > 200 else response)
        
        # Test code generation
        code_prompt = "Write a function that calculates the factorial of a number recursively in Python"
        
        logger.info("Testing code generation", prompt=code_prompt)
        
        code = await client.generate_code(prompt=code_prompt, language="python")
        
        logger.info("Generated code", code=code)
        
        # Test code explanation
        code_to_explain = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""
        
        logger.info("Testing code explanation")
        
        explanation = await client.explain_code(code=code_to_explain, explanation_type="brief")
        
        logger.info("Code explanation", explanation=explanation)
        
    except Exception as e:
        logger.error("Error testing AI client", error=str(e))
    
    finally:
        # Close the client
        await client.close()
        
        logger.info("AI client test completed")


async def main():
    """Main entry point for the test script."""
    logger.info("Starting AI client test")
    
    await test_ai_client()
    
    logger.info("All tests completed")


if __name__ == "__main__":
    asyncio.run(main()) 