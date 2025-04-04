#!/usr/bin/env python3
"""
Test script for the Rule Engine with AI integration.

This script tests the rule engine by creating a sample context snapshot,
initializing the required services, and evaluating rules against the context.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chimera_core.services.ai_client import AIClient
from src.chimera_core.services.rule_engine import RuleEngineService
from src.config.settings import load_settings
from src.schemas.context import (
    ContextSnapshot,
    DiagnosticItem,
    EditorSelection,
    FileData,
)


async def create_test_context() -> ContextSnapshot:
    """Create a test context snapshot with Python files."""
    current_time = datetime.now()
    
    # Create a sample Python file with no type annotations
    python_file1 = FileData(
        path="/path/to/sample.py",
        content="""
def add_numbers(a, b):
    return a + b

def process_data(items):
    result = []
    for item in items:
        if item > 0:
            if item % 2 == 0:
                result.append(item * 2)
            else:
                result.append(item)
    return result
        """,
        language="python",
        last_modified=current_time,
        size_bytes=250,
        is_open=True,
        is_dirty=False,
    )
    
    # Create a sample Python file with SQL query
    python_file2 = FileData(
        path="/path/to/db_utils.py",
        content="""
import sqlite3

def execute_query(db_path, user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = '%s'" % user_id
    cursor.execute(query)
    return cursor.fetchall()
        """,
        language="python",
        last_modified=current_time,
        size_bytes=180,
        is_open=True,
        is_dirty=False,
    )
    
    # Create a sample JavaScript file (should not trigger Python rules)
    js_file = FileData(
        path="/path/to/app.js",
        content="""
function processData(data) {
    return data.map(item => item * 2);
}
        """,
        language="javascript",
        last_modified=current_time,
        size_bytes=80,
        is_open=False,
        is_dirty=False,
    )
    
    # Create a context snapshot
    snapshot = ContextSnapshot(
        timestamp=current_time,
        workspace_root="/path/to/workspace",
        active_file="/path/to/sample.py",
        selections=[
            EditorSelection(
                file_path="/path/to/sample.py",
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=10,
                selected_text="def add_num",
            )
        ],
        files=[python_file1, python_file2, js_file],
        diagnostics=[
            DiagnosticItem(
                file_path="/path/to/sample.py",
                message="Function is missing type annotations",
                severity="warning",
                line=1,
                column=0,
                source="linter",
                code="missing-annotation",
            )
        ],
        metadata={
            "editor": "vscode",
            "language_server_active": True,
        },
    )
    
    return snapshot


async def main():
    """Run the rule engine test."""
    print("Starting rule engine test...")
    
    # Make sure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Load settings
    settings = load_settings()
    print(f"Rules directory: {settings.rules_directory}")
    
    # Create mock OpenAI API key (for testing only - no real API calls will be made)
    os.environ["CHIMERA_AI_API_KEY"] = "sk-mock-key-for-testing"
    
    # Initialize services
    print("\nInitializing AI client...")
    ai_client = AIClient(
        api_key=settings.ai_api_key or os.environ.get("CHIMERA_AI_API_KEY", ""),
        model=settings.ai_model_name,
        api_base=settings.ai_api_base,
        api_version=settings.ai_api_version,
        max_tokens=settings.ai_max_tokens,
        temperature=settings.ai_temperature,
    )
    
    print("\nInitializing rule engine...")
    rule_engine = RuleEngineService(
        rules_dir=settings.rules_directory
    )
    
    # Create a test context
    context = await create_test_context()
    
    print(f"Created test context with {len(context.files)} files")
    print(f"Active file: {context.active_file}")
    print(f"Files: {[file.path for file in context.files]}")
    
    # Evaluate rules
    print("\nEvaluating rules against context...")
    result = await rule_engine.evaluate_rules(context, ai_client)
    
    # Print results
    print(f"\nRule evaluation completed with {result.match_count} matches:")
    
    if result.match_count == 0:
        print("No rules matched the context.")
    else:
        for i, match in enumerate(result.matches, 1):
            print(f"\nMatch {i}:")
            print(f"  Rule: {match.rule_name} (ID: {match.rule_id})")
            print(f"  Rule Set: {match.rule_set_id}")
            print(f"  Priority: {match.priority}")
            print("  Actions:")
            
            for j, action in enumerate(match.actions, 1):
                print(f"    {j}. Type: {action.type}")
                print(f"       Value: {action.value}")
                if action.param:
                    print(f"       Param: {action.param}")
                if action.description:
                    print(f"       Description: {action.description}")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 