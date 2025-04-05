"""Tests for AIClient service."""

import unittest
from unittest import mock
import pytest
from src.chimera_core.services.ai_client import AIClient

class TestAIClient(unittest.TestCase):
    """Test cases for AIClient."""
    
    @mock.patch("src.chimera_core.services.ai_client.openai")
    def test_init_openai(self, mock_openai):
        """Test initialization with OpenAI model."""
        client = AIClient(api_key="test", model="gpt-4o")
        self.assertEqual(client.model, "gpt-4o")
        self.assertEqual(client.llm_client_type, "openai")


if __name__ == "__main__":
    unittest.main()
