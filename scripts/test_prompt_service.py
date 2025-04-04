#!/usr/bin/env python3
"""
Test script for the Chimera prompt templates.

This script demonstrates how the prompt templates work by directly filling them
with sample content, without requiring the full context cache infrastructure.
"""

import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chimera_core.prompts import templates


def test_code_explanation_template():
    """Test the code explanation template."""
    print("\nTest 1: Code Explanation Template (Detailed)")
    
    # Create sample context
    context = {
        "code_content": "def add_numbers(a, b):\n    return a + b",
        "language": "python",
        "active_file_path": "/path/to/sample.py",
        "active_file_content": "# Sample file with math functions\n\ndef add_numbers(a, b):\n    return a + b\n\ndef subtract_numbers(a, b):\n    return a - b"
    }
    
    # Fill the detailed template
    filled_detailed = templates.fill_template(templates.CODE_EXPLANATION_DETAILED, context)
    print("\nSystem Prompt:")
    print(filled_detailed["system_prompt"])
    print("\nUser Prompt:")
    print(filled_detailed["user_prompt"])
    
    # Fill the brief template
    print("\nTest 2: Code Explanation Template (Brief)")
    filled_brief = templates.fill_template(templates.CODE_EXPLANATION_BRIEF, context)
    print("\nSystem Prompt:")
    print(filled_brief["system_prompt"])
    print("\nUser Prompt:")
    print(filled_brief["user_prompt"])


def test_code_generation_template():
    """Test the code generation template."""
    print("\nTest 3: Code Generation Template")
    
    # Create sample context files
    context_files = [
        {
            "path": "/path/to/utils.py",
            "content": "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5)+1):\n        if n % i == 0:\n            return False\n    return True",
            "language": "python"
        }
    ]
    
    # Format context files
    formatted_context_files = templates.format_context_files(context_files)
    
    # Create sample context
    context = {
        "generation_request": "Create a function to calculate the factorial of a number",
        "language": "python",
        "active_file_path": "/path/to/math_utils.py",
        "context_files": formatted_context_files,
        "insertion_point_code": "# Insert factorial function here"
    }
    
    # Fill the template
    filled = templates.fill_template(templates.CODE_GENERATION, context)
    print("\nSystem Prompt:")
    print(filled["system_prompt"])
    print("\nUser Prompt:")
    print(filled["user_prompt"])


def test_code_review_template():
    """Test the code review template."""
    print("\nTest 4: Code Review Template")
    
    # Create sample diagnostics
    diagnostics = [
        {
            "line": 5,
            "message": "Variable 'result' might be referenced before assignment",
            "severity": "warning",
            "file_path": "/path/to/sample.py",
            "column": 10,
            "source": "pylint"
        },
        {
            "line": 8,
            "message": "Unused variable 'temp'",
            "severity": "info",
            "file_path": "/path/to/sample.py",
            "column": 5,
            "source": "pylint"
        }
    ]
    
    # Format diagnostics
    formatted_diagnostics = templates.format_diagnostics(diagnostics)
    
    # Create sample context
    context = {
        "code_content": "def process_data(items):\n    result = []\n    for item in items:\n        if item > 0:\n            temp = item * 2\n            if item % 2 == 0:\n                result.append(item * 2)\n            else:\n                result.append(item)\n    return result",
        "language": "python",
        "active_file_path": "/path/to/sample.py",
        "diagnostics": formatted_diagnostics
    }
    
    # Fill the template
    filled = templates.fill_template(templates.CODE_REVIEW, context)
    print("\nSystem Prompt:")
    print(filled["system_prompt"])
    print("\nUser Prompt:")
    print(filled["user_prompt"])
    
    # Test JSON output format
    print("\nTest 5: Code Analysis JSON Template")
    filled_json = templates.fill_template(templates.CODE_ANALYSIS_JSON, context)
    print("\nSystem Prompt:")
    print(filled_json["system_prompt"])
    print("\nUser Prompt:")
    print(filled_json["user_prompt"])


def test_chat_template():
    """Test the chat template."""
    print("\nTest 6: Chat Template")
    
    # Create sample context files
    context_files = [
        {
            "path": "/path/to/app.py",
            "content": "from flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/')\ndef home():\n    return 'Hello, World!'",
            "language": "python"
        }
    ]
    
    # Format context files
    formatted_context_files = templates.format_context_files(context_files)
    
    # Create sample context
    context = {
        "user_query": "How do I add a new route to my Flask application?",
        "active_file_path": "/path/to/app.py",
        "selection_content": "@app.route('/')\ndef home():\n    return 'Hello, World!'",
        "language": "python",
        "diagnostics": "No diagnostics found.",
        "context_files": formatted_context_files
    }
    
    # Fill the template
    filled = templates.fill_template(templates.GENERAL_CODING_ASSISTANT, context)
    print("\nSystem Prompt:")
    print(filled["system_prompt"])
    print("\nUser Prompt:")
    print(filled["user_prompt"])


def test_chimera_themed_html():
    """Test the Chimera-themed HTML template."""
    print("\nTest 7: Chimera-Themed HTML Template")
    
    # Create sample context
    context = {
        "page_type": "Dashboard",
        "content_description": "Create a dashboard showing:  \n- Project stats (number of files, diagnostics)\n- Recent activities\n- Quick access to AI actions (code generation, explanation, etc.)",
        "additional_requirements": "Include a navigation sidebar and a header with the Chimera logo. Add visual indicators for system status."
    }
    
    # Fill the template
    filled = templates.fill_template(templates.CHIMERA_THEMED_HTML, context)
    print("\nSystem Prompt:")
    print(filled["system_prompt"])
    print("\nUser Prompt:")
    print(filled["user_prompt"])


def main():
    """Run the prompt template tests."""
    print("Starting prompt template tests...\n")
    
    # Test code explanation templates
    test_code_explanation_template()
    
    # Test code generation template
    test_code_generation_template()
    
    # Test code review template
    test_code_review_template()
    
    # Test chat template
    test_chat_template()
    
    # Test Chimera-themed HTML template
    test_chimera_themed_html()
    
    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    main() 