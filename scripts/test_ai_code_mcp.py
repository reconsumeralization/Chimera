#!/usr/bin/env python
"""
Test script for the AI Code MCP Tools.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_ai_code_mcp")

# Mock tool classes for testing
class BaseTool:
    """Mock base tool class."""
    
    def validate_params(self, params, required_params):
        """Validate required parameters."""
        missing = [param for param in required_params if param not in params]
        if missing:
            error_msg = f"Missing required parameters: {', '.join(missing)}"
            return False, error_msg
        return True, None

class MockCodeGenerationTool(BaseTool):
    """Mock code generation tool for testing."""
    
    async def execute(self, params):
        """Execute mock code generation."""
        valid, error = self.validate_params(params, ["prompt", "language"])
        if not valid:
            return {"error": error}
        
        prompt = params.get("prompt", "")
        language = params.get("language", "")
        
        logger.info(f"Generating code for: {prompt} in {language}")
        
        # Simulate code generation
        if language.lower() == "python":
            code = "```python\ndef hello_world():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello_world()\n```"
        elif language.lower() == "javascript":
            code = "```javascript\nfunction helloWorld() {\n    console.log('Hello, World!');\n}\n\nhelloWorld();\n```"
        else:
            code = f"// Generated {language} code for: {prompt}"
        
        return {
            "code": code,
            "language": language,
            "model": "mock-model",
            "elapsed_ms": 150
        }

class MockCodeAnalysisTool(BaseTool):
    """Mock code analysis tool for testing."""
    
    async def execute(self, params):
        """Execute mock code analysis."""
        valid, error = self.validate_params(params, ["code"])
        if not valid:
            return {"error": error}
        
        code = params.get("code", "")
        language = params.get("language", "")
        analysis_type = params.get("analysis_type", "general")
        
        logger.info(f"Analyzing {language} code, type: {analysis_type}")
        
        # Simulate analysis based on code content
        if "exec(" in code:
            analysis = "SECURITY ISSUE: This code contains an unsafe exec() call that can lead to remote code execution vulnerabilities."
        elif "add" in code:
            analysis = "The code defines a simple function that adds two numbers. It's correct but could benefit from type annotations and a docstring."
        else:
            analysis = f"Analysis of {language} code complete. No major issues found."
        
        return {
            "analysis": analysis,
            "language": language,
            "analysis_type": analysis_type,
            "model": "mock-model",
            "elapsed_ms": 120
        }

async def test_code_generation():
    """Test the code generation tool."""
    tool = MockCodeGenerationTool()
    
    # Test basic code generation
    logger.info("\n\nTesting code generation...")
    params = {
        "prompt": "Create a simple hello world program",
        "language": "python"
    }
    
    result = await tool.execute(params)
    logger.info(f"Result:\n{json.dumps(result, indent=2)}")
    
    # Test with different language
    logger.info("\n\nTesting code generation with JavaScript...")
    params = {
        "prompt": "Create a simple hello world program",
        "language": "javascript"
    }
    
    result = await tool.execute(params)
    logger.info(f"Result with different language:\n{json.dumps(result, indent=2)}")
    
    return result

async def test_code_analysis():
    """Test the code analysis tool."""
    tool = MockCodeAnalysisTool()
    
    # Test basic code analysis
    logger.info("\n\nTesting code analysis...")
    params = {
        "code": "def add(a, b):\n    return a + b",
        "language": "python",
        "analysis_type": "general"
    }
    
    result = await tool.execute(params)
    logger.info(f"Result:\n{json.dumps(result, indent=2)}")
    
    # Test security analysis
    logger.info("\n\nTesting security analysis...")
    params = {
        "code": "def process_input(user_input):\n    exec(user_input)",
        "language": "python",
        "analysis_type": "security"
    }
    
    result = await tool.execute(params)
    logger.info(f"Security analysis result:\n{json.dumps(result, indent=2)}")
    
    return result

async def main():
    """Run all tests."""
    await test_code_generation()
    await test_code_analysis()

if __name__ == "__main__":
    asyncio.run(main()) 