"""
Unit tests for AI routes.

This module contains tests for the AI-related API routes.
"""

import json
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from src.chimera_core.api.app import create_app


class TestAIRoutes(unittest.TestCase):
    """Test case for AI routes."""
    
    def setUp(self):
        """Set up test client and mocks."""
        self.app = create_app()
        self.client = TestClient(self.app)
        
        # Setup mocks for all dependencies
        self.ai_client_mock = mock.MagicMock()
        self.context_cache_mock = mock.MagicMock()
        self.prompt_service_mock = mock.MagicMock()
        
        # Override dependencies
        self.app.dependency_overrides = {
            "get_ai_client": lambda: self.ai_client_mock,
            "get_context_cache_service": lambda: self.context_cache_mock,
            "get_prompt_service": lambda: self.prompt_service_mock,
            "APIKey": lambda: None,  # Skip API key validation
        }
    
    def tearDown(self):
        """Clean up after tests."""
        self.app.dependency_overrides.clear()
    
    def test_generate_with_prefix(self):
        """Test the /ai/generate/prefix endpoint."""
        # Setup mocks
        self.ai_client_mock.generate_with_char_prefix.return_value = "def calculate_sum(a, b):\n    return a + b"
        self.prompt_service_mock.create_code_generation_prompt.return_value = {"system": "sys", "user": "user"}
        self.context_cache_mock.query_context.return_value = None
        
        # Make request
        response = self.client.post(
            "/ai/generate/prefix",
            json={
                "prompt": "Write a function to calculate the sum of two numbers",
                "language": "python",
                "prefix": "def calculate_sum",
                "temperature": 0.5
            }
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], "def calculate_sum(a, b):\n    return a + b")
        self.assertEqual(data["language"], "python")
        self.assertEqual(data["prefix"], "def calculate_sum")
        
        # Verify AI client was called correctly
        self.ai_client_mock.generate_with_char_prefix.assert_called_once()
        call_args = self.ai_client_mock.generate_with_char_prefix.call_args[1]
        self.assertEqual(call_args["prompt"], "Write a function to calculate the sum of two numbers")
        self.assertEqual(call_args["prefix"], "def calculate_sum")
        self.assertEqual(call_args["language"], "python")
        self.assertEqual(call_args["temperature"], 0.5)
        self.assertEqual(call_args["stream"], False)
    
    def test_generate_with_prefix_stream(self):
        """Test the /ai/generate/prefix/stream endpoint."""
        # Setup mock for streaming response
        async def mock_stream():
            yield "def "
            yield "calculate_sum"
            yield "(a, b):"
            yield "\n    return a + b"
        
        self.ai_client_mock.generate_with_char_prefix.return_value = mock_stream()
        self.prompt_service_mock.create_code_generation_prompt.return_value = {"system": "sys", "user": "user"}
        
        # Make request
        response = self.client.post(
            "/ai/generate/prefix/stream",
            json={
                "prompt": "Write a function to calculate the sum of two numbers",
                "language": "python",
                "prefix": "def calculate_sum",
                "temperature": 0.5
            }
        )
        
        # Verify response is streaming
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/event-stream")
        
        # Verify AI client was called correctly
        self.ai_client_mock.generate_with_char_prefix.assert_called_once()
        call_args = self.ai_client_mock.generate_with_char_prefix.call_args[1]
        self.assertEqual(call_args["prompt"], "Write a function to calculate the sum of two numbers")
        self.assertEqual(call_args["prefix"], "def calculate_sum")
        self.assertEqual(call_args["language"], "python")
        self.assertEqual(call_args["temperature"], 0.5)
        self.assertEqual(call_args["stream"], True)
    
    def test_generate_with_prefix_error(self):
        """Test error handling in the /ai/generate/prefix endpoint."""
        # Setup mock to raise an exception
        self.ai_client_mock.generate_with_char_prefix.side_effect = Exception("Test error")
        
        # Make request
        response = self.client.post(
            "/ai/generate/prefix",
            json={
                "prompt": "Write a function to calculate the sum of two numbers",
                "language": "python",
                "prefix": "def calculate_sum"
            }
        )
        
        # Verify error response
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Test error", data["detail"])


if __name__ == "__main__":
    unittest.main() 