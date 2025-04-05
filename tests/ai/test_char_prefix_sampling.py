"""Integration tests for Character Prefix Conditioning.

This module contains tests for the Character Prefix Conditioning algorithm and
its integration with the AI client.
"""

import unittest
from unittest import mock
import asyncio
from typing import Dict, List, Optional, Tuple

from src.chimera_core.ai.char_prefix_sampling import CharacterPrefixSampler, CharacterTrie
try:
    from src.chimera_core.ai.char_prefix_openai import OpenAICharacterPrefixSampler
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class MockTokenizer:
    """Mock tokenizer for testing the character prefix sampler."""
    
    def __init__(self, vocab: Dict[int, str]):
        """
        Initialize the mock tokenizer.
        
        Args:
            vocab: Dictionary mapping token IDs to their string representations
        """
        self.vocab = vocab
        self.id_to_token = vocab
        self.token_to_id = {token: id for id, token in vocab.items()}
    
    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs to text.
        
        Args:
            token_ids: List of token IDs to decode
            
        Returns:
            Decoded text
        """
        return ''.join(self.vocab.get(token_id, '') for token_id in token_ids)
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text to token IDs (simple implementation for testing).
        
        Args:
            text: Text to encode
            
        Returns:
            List of token IDs
        """
        # This is a very simplified encoding (character-based)
        return [self.token_to_id.get(char, 0) for char in text]


class TestCharPrefixIntegration(unittest.TestCase):
    """Integration tests for Character Prefix Conditioning."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a simple vocabulary for testing
        self.vocab = {
            0: "<pad>",
            1: "a",
            2: "b",
            3: "c",
            4: "ab",
            5: "bc",
            6: "abc",
            7: "def",
            8: "defg",
            9: "function",
            10: " ",
            11: "(",
            12: ")"
        }
        
        self.tokenizer = MockTokenizer(self.vocab)
        
        # Mock LM call function with realistic behavior
        async def mock_lm_call(tokens: List[int], params: Optional[Dict] = None) -> List[Tuple[int, float]]:
            # Return token probabilities based on the context
            # Simple model: higher probability for tokens that make sense based on prefix
            probs = [(i, 0.01) for i in range(len(self.vocab))]
            
            # No context, uniform distribution
            if not tokens:
                return probs
            
            # Simple "language model" behavior: increased probabilities for common sequences
            last_token = tokens[-1]
            
            # After "a", "b" is more likely
            if last_token == 1:  # "a"
                probs[2] = (2, 0.5)  # "b" more likely
            
            # After "ab", "c" is more likely
            elif last_token == 4:  # "ab"
                probs[3] = (3, 0.6)  # "c" more likely
                
            # After "function", space is likely
            elif last_token == 9:  # "function"
                probs[10] = (10, 0.8)  # " " more likely
                
            # After space, "(" is likely
            elif last_token == 10:  # " "
                probs[11] = (11, 0.7)  # "(" more likely
            
            return probs
        
        self.mock_lm_call = mock_lm_call
        
        # Create the sampler
        self.sampler = CharacterPrefixSampler(
            tokenizer=self.tokenizer,
            lm_call=self.mock_lm_call,
            vocab_size=len(self.vocab)
        )
    
    async def test_sample_with_simple_prefix(self):
        """Test sampling with a simple character prefix."""
        # Sample with prefix "a"
        tokens = await self.sampler.sample_with_prefix(
            prefix="a",
            max_tokens=5,
            temperature=1.0
        )
        
        # Check that the generated text starts with "a"
        generated_text = self.tokenizer.decode(tokens)
        self.assertTrue(generated_text.startswith("a"), 
                        f"Generated text '{generated_text}' does not start with 'a'")
    
    async def test_sample_with_multi_token_prefix(self):
        """Test sampling with a prefix that requires multiple tokens."""
        # Sample with prefix "abc"
        tokens = await self.sampler.sample_with_prefix(
            prefix="abc",
            max_tokens=5,
            temperature=1.0
        )
        
        # Check that the generated text starts with "abc"
        generated_text = self.tokenizer.decode(tokens)
        self.assertTrue(generated_text.startswith("abc"), 
                        f"Generated text '{generated_text}' does not start with 'abc'")
    
    async def test_function_prefix(self):
        """Test sampling with a prefix typical for code generation."""
        # Sample with prefix "function("
        tokens = await self.sampler.sample_with_prefix(
            prefix="function(",
            max_tokens=10,
            temperature=1.0
        )
        
        # Check that the generated text starts with "function("
        generated_text = self.tokenizer.decode(tokens)
        self.assertTrue(generated_text.startswith("function("), 
                        f"Generated text '{generated_text}' does not start with 'function('")
    
    async def test_impossible_prefix(self):
        """Test sampling with a prefix that cannot be generated."""
        # Sample with prefix that doesn't match any token or combination
        tokens = await self.sampler.sample_with_prefix(
            prefix="impossible_prefix",
            max_tokens=5,
            temperature=1.0
        )
        
        # Should return empty or minimal tokens if impossible
        self.assertLessEqual(len(tokens), 1)
    
    async def test_temperature_effect(self):
        """Test that temperature affects sampling variance."""
        # With temperature near 0, should consistently pick highest probability
        tokens_cold = await self.sampler.sample_with_prefix(
            prefix="a",
            max_tokens=5,
            temperature=0.01
        )
        
        # Run it a few times to ensure it's stable
        for _ in range(3):
            tokens_cold_repeat = await self.sampler.sample_with_prefix(
                prefix="a",
                max_tokens=5,
                temperature=0.01
            )
            # With nearly zero temperature, should get consistent results
            self.assertEqual(self.tokenizer.decode(tokens_cold),
                             self.tokenizer.decode(tokens_cold_repeat))


# Only run these if OpenAI integration is available
@unittest.skipIf(not HAS_OPENAI, "OpenAI integration not available")
class TestOpenAIIntegration(unittest.TestCase):
    """Tests for OpenAI-specific Character Prefix Conditioning implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock OpenAI client
        self.openai_client_mock = mock.MagicMock()
        self.model = "gpt-4"
        
        # Mock tiktoken behavior
        self.tiktoken_mock = mock.MagicMock()
        self.tiktoken_mock.n_vocab = 50000
        self.tiktoken_mock.encode.return_value = [1000, 1001, 1002]
        self.tiktoken_mock.decode.return_value = "test text"
        
        # Create sampler with mocks
        self.sampler = OpenAICharacterPrefixSampler(
            client=self.openai_client_mock,
            model=self.model,
            tokenizer=self.tiktoken_mock
        )
    
    async def test_openai_integration(self):
        """Test the OpenAI-specific implementation."""
        # Mock the OpenAI API response
        completion_mock = mock.MagicMock()
        choice_mock = mock.MagicMock()
        logprobs_mock = mock.MagicMock()
        
        # Setup the nested structure
        completion_mock.choices = [choice_mock]
        choice_mock.logprobs = logprobs_mock
        
        # This structure will change based on OpenAI API version
        content_logprobs = mock.MagicMock()
        top_logprobs_entry = mock.MagicMock()
        top_logprobs_entry.token = "test"
        top_logprobs_entry.logprob = -2.0  # log2 probability
        
        content_logprobs.top_logprobs = [top_logprobs_entry]
        logprobs_mock.content = [content_logprobs]
        
        # Configure the mock to return the mocked response
        self.openai_client_mock.chat.completions.create = mock.AsyncMock(return_value=completion_mock)
        
        # Now test the OpenAI integration
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a Python function."}
        ]
        
        # Mock the CharacterPrefixSampler.sample_with_prefix method
        with mock.patch('src.chimera_core.ai.char_prefix_sampling.CharacterPrefixSampler.sample_with_prefix') as mock_sample:
            # Configure the mock to return token IDs
            mock_sample.return_value = [1000, 1001, 1002]
            
            # Call the method
            result = await self.sampler.sample_with_prefix(
                messages=messages,
                prefix="def ",
                max_tokens=100
            )
            
            # Verify result
            self.assertEqual(result, "test text")
            
            # Verify the OpenAI API was called
            self.openai_client_mock.chat.completions.create.assert_called()
    
    @mock.patch('src.chimera_core.ai.char_prefix_openai.tiktoken')
    async def test_integrate_with_openai_client(self, mock_tiktoken):
        """Test the convenience function for integrating with OpenAI client."""
        from src.chimera_core.ai.char_prefix_openai import integrate_with_openai_client
        
        # Configure the tiktoken mock
        mock_encoding = mock.MagicMock()
        mock_encoding.n_vocab = 50000
        mock_encoding.encode.return_value = [1000]
        mock_encoding.decode.return_value = "def sample_function():"
        
        mock_tiktoken.encoding_for_model.return_value = mock_encoding
        
        # Mock OpenAI client
        openai_client_mock = mock.MagicMock()
        
        # Mock the sampler's sample_with_prefix method
        with mock.patch('src.chimera_core.ai.char_prefix_sampling.CharacterPrefixSampler.sample_with_prefix') as mock_sample:
            mock_sample.return_value = [1000, 1001, 1002]
            
            # Call the integration function
            result = await integrate_with_openai_client(
                client=openai_client_mock,
                messages=[{"role": "user", "content": "Write a function"}],
                prefix="def ",
                model="gpt-4"
            )
            
            # As the function will create an OpenAICharacterPrefixSampler and call sample_with_prefix,
            # the result should come from the mocked sample_with_prefix which returns tokens that
            # the mocked tokenizer turns into "def sample_function():"
            self.assertEqual(result, "def sample_function():")


if __name__ == "__main__":
    # Use asyncio.run to run async tests
    for test_case in [TestCharPrefixIntegration, TestOpenAIIntegration]:
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