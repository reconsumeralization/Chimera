"""Tests for the Character Prefix Conditioning Sampling Algorithm.

This module tests the implementation of the Character Prefix Conditioning algorithm
for efficient autoregressive sampling from a language model conditioned on a
character prefix.
"""

import unittest
from typing import Dict, List, Optional, Tuple
from unittest.mock import MagicMock

from ..char_prefix_sampling import CharacterPrefixSampler, CharacterTrie


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


class TestCharacterTrie(unittest.TestCase):
    """Test case for the CharacterTrie class."""
    
    def test_add_and_get_tokens(self):
        """Test adding tokens to the trie and retrieving them by prefix."""
        trie = CharacterTrie()
        
        # Add some tokens
        trie.add_token(1, "hello")
        trie.add_token(2, "help")
        trie.add_token(3, "world")
        
        # Test retrieving tokens by different prefixes
        self.assertEqual(trie.get_tokens_with_prefix("h"), {1, 2})
        self.assertEqual(trie.get_tokens_with_prefix("he"), {1, 2})
        self.assertEqual(trie.get_tokens_with_prefix("hel"), {1, 2})
        self.assertEqual(trie.get_tokens_with_prefix("hell"), {1})
        self.assertEqual(trie.get_tokens_with_prefix("w"), {3})
        self.assertEqual(trie.get_tokens_with_prefix("z"), set())
    
    def test_empty_trie(self):
        """Test behavior with an empty trie."""
        trie = CharacterTrie()
        self.assertEqual(trie.get_tokens_with_prefix("any"), set())


class TestCharacterPrefixSampler(unittest.TestCase):
    """Test case for the CharacterPrefixSampler class."""
    
    def setUp(self):
        """Set up test environment before each test method."""
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
            8: "defg"
        }
        
        self.tokenizer = MockTokenizer(self.vocab)
        
        # Mock LM call function that returns token probs
        self.lm_call = MagicMock()
        
        # Create the sampler
        self.sampler = CharacterPrefixSampler(
            tokenizer=self.tokenizer,
            lm_call=self.lm_call,
            vocab_size=len(self.vocab)
        )
    
    def test_trie_construction(self):
        """Test that the trie is constructed correctly."""
        # Verify some token sets in the trie
        self.assertIn(1, self.sampler.trie.get_tokens_with_prefix("a"))
        self.assertIn(4, self.sampler.trie.get_tokens_with_prefix("a"))
        self.assertIn(6, self.sampler.trie.get_tokens_with_prefix("a"))
        
        self.assertIn(2, self.sampler.trie.get_tokens_with_prefix("b"))
        self.assertIn(5, self.sampler.trie.get_tokens_with_prefix("b"))
        
        self.assertIn(7, self.sampler.trie.get_tokens_with_prefix("d"))
        self.assertIn(8, self.sampler.trie.get_tokens_with_prefix("d"))
    
    def test_sampling_with_prefix(self):
        """Test sampling with a character prefix constraint."""
        # Configure LM mock to return token probabilities
        # For empty sequence, return probs for all tokens
        self.lm_call.side_effect = [
            # First call: LM predicts all tokens with equal probability
            [(i, 1.0/len(self.vocab)) for i in range(len(self.vocab))],
            # Second call (after selecting 'a'): LM predicts 'b' with high probability
            [(i, 0.1) for i in range(len(self.vocab))],
            # Third call (after selecting 'b'): LM predicts 'c' with high probability
            [(i, 0.1) for i in range(len(self.vocab))]
        ]
        
        # Sample with prefix "ab"
        tokens = self.sampler.sample_with_prefix(
            prefix="ab", 
            max_tokens=3, 
            temperature=1.0
        )
        
        # Check at least one token was generated
        self.assertGreater(len(tokens), 0)
        
        # Check that the generated text starts with "ab"
        generated_text = self.tokenizer.decode(tokens)
        self.assertTrue(generated_text.startswith("ab"), 
                        f"Generated text '{generated_text}' does not start with 'ab'")
        
        # Verify the LM call was made
        self.lm_call.assert_called()


if __name__ == '__main__':
    unittest.main() 