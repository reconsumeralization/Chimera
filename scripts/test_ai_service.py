#!/usr/bin/env python
"""Test script for verifying the AI service integration with other services."""
import asyncio
import json
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from src.chimera_core.factory import init_services, close_services

# Set up logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


async def test_ai_with_context_cache():
    """Test AI client integration with context cache."""
    logger.info("Testing AI client integration with context cache")
    
    # Initialize services
    factory = await init_services()
    
    # Get services
    ai_client = factory.get_service("ai_client")
    context_cache = factory.get_service("context_cache")
    
    if not ai_client or not context_cache:
        logger.error("Failed to get required services")
        return
    
    try:
        # Create a simple context query
        query_text = "What is this code doing?"
        code_to_explain = """
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result
"""
        
        logger.info("Explaining code with AI client", query=query_text)
        
        # Call AI client to explain the code
        explanation = await ai_client.explain_code(
            code=code_to_explain,
            explanation_type="detailed"
        )
        
        logger.info("AI explanation", explanation=explanation)
        
        # Now test the code generation capability
        prompt = "Write a function to find the nth Fibonacci number using dynamic programming"
        language = "python"
        
        logger.info("Generating code with AI client", prompt=prompt, language=language)
        
        # Call AI client to generate code
        code = await ai_client.generate_code(
            prompt=prompt,
            language=language
        )
        
        logger.info("Generated code", code=code)
        
        # Test integration with rule engine (if available)
        rule_engine = factory.get_service("rule_engine")
        if rule_engine:
            logger.info("Testing integration with rule engine")
            
            # This would normally involve evaluating rules against a context
            # and using AI to generate suggestions based on rule matches
            pass
        
    except Exception as e:
        logger.error("Error testing AI integration", error=str(e))
    
    finally:
        # Close services
        await close_services()
        
        logger.info("AI integration test completed")


async def main():
    """Main entry point for the test script."""
    logger.info("Starting AI integration test")
    
    await test_ai_with_context_cache()
    
    logger.info("All tests completed")


if __name__ == "__main__":
    asyncio.run(main()) 