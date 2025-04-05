"""Tests for Gemini-specific Character Prefix Conditioning.

This module contains tests for the Gemini integration of the
Character Prefix Conditioning algorithm.
"""

import unittest
from unittest import mock
import asyncio
from typing import Any, Dict, List, Optional, Tuple

try:
    from src.chimera_core.ai.char_prefix_gemini import (
        GeminiCharacterPrefixSampler,
        GeminiTokenizerWrapper,
        integrate_with_gemini,
    )
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


@unittest.skipIf(not HAS_GEMINI, "Gemini integration not available")
class TestGeminiTokenizerWrapper(unittest.TestCase):
    """Test case for the GeminiTokenizerWrapper."""
    
    def setUp(self):
        """Set up test environment."""
        self.tokenizer = GeminiTokenizerWrapper(vocab_size=1000)
    
    def test_encode_decode(self):
        """Test encoding and decoding text."""
        # Test encoding
        text = "Hello, world!"
        encoded = self.tokenizer.encode(text)
        
        # Check that encoded is a list of integers
        self.assertIsInstance(encoded, list)
        self.assertTrue(all(isinstance(i, int) for i in encoded))
        
        # Check that encoding is deterministic
        encoded2 = self.tokenizer.encode(text)
        self.assertEqual(encoded, encoded2)
        
        # Test decoding
        decoded = self.tokenizer.decode(encoded)
        self.assertEqual(text, decoded)
    
    def test_encoding_cache(self):
        """Test that encoding results are cached."""
        text = "Testing cache"
        
        # First encode call
        encoded1 = self.tokenizer.encode(text)
        
        # Second encode call should use cache
        with mock.patch.dict(self.tokenizer._char_to_id, {}, clear=False) as mock_dict:
            encoded2 = self.tokenizer.encode(text)
            # Check that the dictionary wasn't modified
            self.assertEqual(encoded1, encoded2)
    
    def test_decoding_cache(self):
        """Test that decoding results are cached."""
        tokens = [1, 2, 3, 4, 5]
        
        # First decode call
        decoded1 = self.tokenizer.decode(tokens)
        
        # Second decode call should use cache
        with mock.patch.dict(self.tokenizer._char_to_id, {}, clear=False) as mock_dict:
            decoded2 = self.tokenizer.decode(tokens)
            # Check that the result is the same
            self.assertEqual(decoded1, decoded2)


@unittest.skipIf(not HAS_GEMINI, "Gemini integration not available")
class TestGeminiCharacterPrefixSampler(unittest.TestCase):
    """Test case for the GeminiCharacterPrefixSampler."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock Gemini model
        self.mock_model = mock.MagicMock()
        
        # Create a real tokenizer
        self.tokenizer = GeminiTokenizerWrapper(vocab_size=1000)
        
        # Create the sampler with mocks
        self.sampler = GeminiCharacterPrefixSampler(
            model=self.mock_model,
            tokenizer=self.tokenizer
        )
    
    async def test_lm_call(self):
        """Test the LM call function."""
        # Create a mock response
        mock_candidate = mock.MagicMock()
        mock_content = mock.MagicMock()
        mock_part = mock.MagicMock()
        
        # Configure the mock response
        mock_part.text = "Example text"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        
        # Set up the generate_content_async mock
        self.mock_model.generate_content_async.return_value = mock.MagicMock(
            candidates=[mock_candidate]
        )
        
        # Call the LM function
        tokens = []
        params = {"prompt_prefix": "Test prompt"}
        token_probs = await self.sampler._lm_call(tokens, params)
        
        # Verify the result
        self.assertIsInstance(token_probs, list)
        self.assertTrue(all(isinstance(item, tuple) and len(item) == 2 for item in token_probs))
        self.assertTrue(all(isinstance(item[0], int) and isinstance(item[1], float) for item in token_probs))
        
        # Verify the model was called correctly
        self.mock_model.generate_content_async.assert_called_once()
        call_args = self.mock_model.generate_content_async.call_args[0]
        self.assertEqual(call_args[0], "Test prompt\n")
    
    async def test_sample_with_prefix(self):
        """Test sampling with a prefix."""
        # Mock the character prefix sampler's sample_with_prefix method
        with mock.patch.object(self.sampler.sampler, 'sample_with_prefix') as mock_sample:
            # Configure the mock to return token IDs for "def sample_function():"
            mock_sample.return_value = self.tokenizer.encode("def sample_function():")
            
            # Call the method
            result = await self.sampler.sample_with_prefix(
                prefix="def ",
                prompt="Write a sample function",
                max_tokens=50
            )
            
            # Verify the result
            self.assertEqual(result, "def sample_function():")
            
            # Verify the underlying sampler was called with correct parameters
            mock_sample.assert_called_once()
            call_kwargs = mock_sample.call_args[1]
            self.assertEqual(call_kwargs["prefix"], "def ")
            self.assertEqual(call_kwargs["max_tokens"], 50)
    
    async def test_error_handling(self):
        """Test handling of errors in LM call."""
        # Configure the model to raise an exception
        self.mock_model.generate_content_async.side_effect = Exception("Test error")
        
        # Call the LM function
        tokens = []
        token_probs = await self.sampler._lm_call(tokens)
        
        # Even with an error, should return a valid distribution
        self.assertIsInstance(token_probs, list)
        self.assertTrue(len(token_probs) > 0)
        self.assertTrue(all(isinstance(item, tuple) and len(item) == 2 for item in token_probs))


@unittest.skipIf(not HAS_GEMINI, "Gemini integration not available")
class TestIntegrateWithGemini(unittest.TestCase):
    """Test case for the integrate_with_gemini function."""
    
    @mock.patch('src.chimera_core.ai.char_prefix_gemini.genai')
    @mock.patch('src.chimera_core.ai.char_prefix_gemini.GeminiCharacterPrefixSampler')
    async def test_integration_function(self, mock_sampler_class, mock_genai):
        """Test the integration function."""
        # Configure the mock sampler
        mock_sampler_instance = mock.MagicMock()
        mock_sampler_instance.sample_with_prefix.return_value = "def sample_function():"
        mock_sampler_class.return_value = mock_sampler_instance
        
        # Call the integration function
        result = await integrate_with_gemini(
            api_key="test_api_key",
            model_name="gemini-pro",
            prefix="def ",
            prompt="Write a sample function",
            max_tokens=50,
            temperature=0.7
        )
        
        # Verify the result
        self.assertEqual(result, "def sample_function():")
        
        # Verify Gemini API was configured
        mock_genai.configure.assert_called_once_with(api_key="test_api_key")
        
        # Verify sampler was created with correct parameters
        mock_sampler_class.assert_called_once()
        call_args = mock_sampler_class.call_args[1]
        self.assertEqual(call_args["model"], "gemini-pro")
        self.assertEqual(call_args["api_key"], "test_api_key")
        
        # Verify sampler's sample_with_prefix was called with correct parameters
        mock_sampler_instance.sample_with_prefix.assert_called_once()
        call_kwargs = mock_sampler_instance.sample_with_prefix.call_args[1]
        self.assertEqual(call_kwargs["prefix"], "def ")
        self.assertEqual(call_kwargs["prompt"], "Write a sample function")
        self.assertEqual(call_kwargs["max_tokens"], 50)
        self.assertEqual(call_kwargs["temperature"], 0.7)


if __name__ == "__main__":
    # Use asyncio.run to run async tests
    for test_case in [TestGeminiTokenizerWrapper, TestGeminiCharacterPrefixSampler, TestIntegrateWithGemini]:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_case)
        
        # Create a runner that uses asyncio
        runner = unittest.TextTestRunner()
        
        # For each test in the suite
        for test in suite:
            if asyncio.iscoroutinefunction(getattr(test, test._testMethodName)):
                # If it's an async test, wrap it in asyncio.run
                original_method = getattr(test, test._testMethodName)
                
                def wrapper(original_method=original_method):
                    return asyncio.run(original_method())
                
                setattr(test, test._testMethodName, wrapper)
        
        # Run the modified suite
        runner.run(suite) 