"""Gemini-specific implementation of Character Prefix Conditioning.

This module provides integration between the Character Prefix Conditioning algorithm
and the Google Gemini API, enabling efficient token sampling with character prefix constraints.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from functools import lru_cache
from collections import OrderedDict
import logging
import math

import structlog

try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel
    from google.generativeai.types import GenerationConfig
    HAS_GEMINI_SDK = True
except ImportError:
    HAS_GEMINI_SDK = False

from .char_prefix_sampling import CharacterPrefixSampler, TokenizerInterface

# Set up logging
logger = structlog.get_logger(__name__)


class GeminiTokenizerWrapper(TokenizerInterface):
    """
    Tokenizer wrapper for Gemini API that simulates tokenization for probability estimation.
    Since Gemini doesn't expose its tokenizer, this implements character-based tokenization
    with efficient caching.
    """
    def __init__(self, vocab_size: int = 50000, cache_size: int = 1000):
        """
        Initialize the tokenizer wrapper.
        
        Args:
            vocab_size: Estimated vocabulary size for the model
            cache_size: Maximum number of entries to cache
        """
        self.vocab_size = vocab_size
        self._char_to_id = {}  # Cache for character to token ID mapping
        self._encoding_cache = OrderedDict()  # LRU cache for text to token IDs (ordered for LRU behavior)
        self._decoding_cache = {}  # Cache for token ID to character mapping
        self._max_cache_entries = cache_size
        
        # Create initial decoders for common characters to improve initial performance
        for char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_(){}[]:;,. \n\t":
            token_id = hash(char) % self.vocab_size
            self._char_to_id[char] = token_id
            self._decoding_cache[token_id] = char
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text to token IDs with LRU caching for better performance.
        
        Args:
            text: The text to encode
            
        Returns:
            List of token IDs
        """
        # Quick cache lookup
        if text in self._encoding_cache:
            # Move to end (most recently used)
            result = self._encoding_cache.pop(text)
            self._encoding_cache[text] = result
            return result.copy()  # Return copy to prevent cache modification
        
        # Check for cached prefixes to optimize encoding
        best_prefix = ""
        prefix_result = []
        
        # Only check for longest cached prefixes to avoid overhead
        # on very large caches
        check_limit = 10  # Only check top 10 most recently used entries
        for i, cached_text in enumerate(reversed(self._encoding_cache)):
            if i >= check_limit:
                break
                
            if text.startswith(cached_text) and len(cached_text) > len(best_prefix):
                best_prefix = cached_text
                prefix_result = self._encoding_cache[cached_text].copy()
        
        if best_prefix:
            # We found a cached prefix - just encode the remaining part
            remaining_text = text[len(best_prefix):]
            remaining_ids = self._encode_uncached(remaining_text)
            
            # Combine results
            result = prefix_result + remaining_ids
            self._add_to_cache(text, result)
            return result.copy()
        
        # No cached prefix found, encode the full text
        result = self._encode_uncached(text)
        self._add_to_cache(text, result)
        return result.copy()
    
    def _encode_uncached(self, text: str) -> List[int]:
        """
        Encode text without using the cache.
        
        Args:
            text: The text to encode
            
        Returns:
            List of token IDs
        """
        token_ids = []
        for char in text:
            if char not in self._char_to_id:
                # Assign a deterministic hash-based ID to each new character
                self._char_to_id[char] = hash(char) % self.vocab_size
                self._decoding_cache[self._char_to_id[char]] = char
            token_ids.append(self._char_to_id[char])
        return token_ids
    
    def _add_to_cache(self, text: str, token_ids: List[int]) -> None:
        """
        Add an entry to the cache with LRU eviction.
        
        Args:
            text: The text to cache
            token_ids: The token IDs to cache
        """
        # If cache is full, remove the oldest entry (first in OrderedDict)
        if len(self._encoding_cache) >= self._max_cache_entries:
            self._encoding_cache.popitem(last=False)
        
        # Add new entry (will be at the end - most recently used)
        self._encoding_cache[text] = token_ids
    
    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs to text.
        
        Args:
            token_ids: The token IDs to decode
            
        Returns:
            Decoded text
        """
        return "".join(self._decoding_cache.get(token_id, "") for token_id in token_ids)
    
    def get_vocab_size(self) -> int:
        """
        Get the vocabulary size.
        
        Returns:
            Vocabulary size
        """
        return self.vocab_size


class GeminiCharacterPrefixSampler:
    """
    Character prefix sampler implementation for Gemini API.
    This provides token probability approximation for Gemini models
    which don't natively expose token probabilities.
    """
    
    def __init__(self, model, candidates_per_step: int = 10):
        """
        Initialize the Gemini character prefix sampler.
        
        Args:
            model: The Gemini language model
            candidates_per_step: Number of candidates to generate per step for probability approximation
        """
        self.model = model
        self.tokenizer = GeminiTokenizerWrapper()
        self.candidates_per_step = candidates_per_step
        
        # Create the base CharacterPrefixSampler with our optimized tokenizer and LM call
        self.sampler = CharacterPrefixSampler(
            tokenizer=self.tokenizer,
            lm_call=self._lm_call,
            vocab_size=self.tokenizer.vocab_size
        )
    
    async def _lm_call(self, tokens: List[int], params: Optional[Dict[str, Any]] = None) -> List[Tuple[int, float]]:
        """
        Approximate next token probabilities using a nested fallback strategy:
        1. Try native token probabilities if available (future API support)
        2. Use parallel candidate generation as primary implementation
        3. Fall back to emergency distribution if all else fails
        
        Args:
            tokens: Current token sequence
            params: Additional parameters for generation
            
        Returns:
            List of (token_id, probability) tuples
        """
        try:
            # 1. Try native token probabilities if available (future API support)
            if hasattr(self.model, 'get_token_probabilities'):
                try:
                    logger.info("Using native token probabilities from Gemini")
                    native_probs = await self.model.get_token_probabilities(
                        self.tokenizer.decode(tokens),
                        **params if params else {}
                    )
                    if native_probs and len(native_probs) > 0:
                        return native_probs
                    logger.warning("Native token probabilities returned empty result, falling back")
                except Exception as e:
                    logger.warning(f"Native token probabilities failed: {e}, falling back to candidate generation")
            
            # 2. Use parallel candidate generation (our primary implementation)
            # Convert tokens to text
            prompt = self.tokenizer.decode(tokens) if tokens else ""
            prompt_prefix = params.get("prompt_prefix", "") if params else ""
            
            if prompt_prefix:
                prompt = f"{prompt_prefix}\n{prompt}"
            
            # Configure generation parameters for better diversity
            generation_config = {
                "temperature": 0.9,  # Higher temperature for better exploration
                "top_p": 0.98,       # Higher top_p for more diversity
                "top_k": 60,         # More tokens to consider
                "candidate_count": 1,
                "max_output_tokens": 1
            }
            
            # Generate multiple candidates in parallel for better performance
            num_parallel = max(10, self.candidates_per_step)
            
            # Create tasks for parallel generation
            async def generate_candidate():
                try:
                    return await self.model.generate_content_async(
                        prompt, 
                        generation_config=GenerationConfig(**generation_config)
                    )
                except Exception as e:
                    logger.error("Error generating candidate", error=str(e))
                    return None
            
            # Run candidates in parallel
            tasks = [generate_candidate() for _ in range(num_parallel)]
            candidates_responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process candidates with weighted frequency analysis
            token_counts = {}
            valid_candidates = 0
            
            for i, candidate in enumerate(candidates_responses):
                # Skip exceptions or None responses
                if isinstance(candidate, Exception) or candidate is None:
                    logger.warning("Candidate generation failed", index=i)
                    continue
                
                # Extract text from candidate
                if hasattr(candidate, "candidates") and candidate.candidates:
                    for j, cand in enumerate(candidate.candidates):
                        if hasattr(cand, "content") and cand.content and cand.content.parts:
                            text = cand.content.parts[0].text
                            if text:
                                # Try different prefix lengths for better subword tokenization handling
                                found_token = False
                                for prefix_len in range(1, min(4, len(text) + 1)):
                                    first_token_ids = self.tokenizer.encode(text[:prefix_len])
                                    if first_token_ids:
                                        token_id = first_token_ids[0]
                                        # Apply exponential decay weighting based on position
                                        weight = math.exp(-0.5 * (i + j))
                                        token_counts[token_id] = token_counts.get(token_id, 0) + weight
                                        valid_candidates += 1
                                        found_token = True
                                        break
                                
                                # Log if we couldn't extract a token
                                if not found_token and text:
                                    logger.debug(f"Could not extract token from text: '{text[:10]}...'")
            
            # Convert to probability distribution
            token_probs = []
            if token_counts:
                total_weight = sum(token_counts.values())
                token_probs = [(token_id, count/total_weight) for token_id, count in token_counts.items()]
            
            if token_probs and len(token_probs) > 0:
                logger.debug("Generated token probabilities", 
                            num_tokens=len(token_probs), 
                            valid_candidates=valid_candidates)
                return token_probs
            
            # 3. Fall back to emergency distribution if candidate generation didn't produce results
            logger.warning("Candidate generation produced no valid tokens, using emergency fallback")
            return self._fallback_distribution()
            
        except Exception as e:
            # 3. Fall back to emergency distribution on any exception
            logger.error("Error in Gemini LM call", error=str(e), exc_info=True)
            return self._fallback_distribution()
    
    def _fallback_distribution(self) -> List[Tuple[int, float]]:
        """
        Provide a targeted fallback distribution focused on common code characters
        with differential weighting for spaces and punctuation.
        
        Returns:
            List of (token_id, probability) tuples
        """
        # Focus on common code characters for better fallback distribution
        common_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_(){}[]:;,. \n\t"
        
        # Special characters that should have higher weights
        high_priority_chars = " \n\t.,;:()"
        
        tokens = []
        for char in common_chars:
            # Assign appropriate weights based on character type
            if char in high_priority_chars:
                weight = 3.0  # Spaces and common punctuation
            elif char in "{}[]()":
                weight = 2.5  # Brackets and parentheses
            elif char in "_":
                weight = 2.0  # Underscore for variable names
            else:
                weight = 1.0  # Default weight
            
            token_ids = self.tokenizer.encode(char)
            if token_ids:
                tokens.append((token_ids[0], weight))
        
        # Normalize probabilities
        total = sum(weight for _, weight in tokens)
        if total == 0:  # Safeguard against empty tokens list
            # Last resort fallback - use first 30 token IDs with uniform distribution
            return [(i, 1.0/30) for i in range(30)]
            
        return [(tid, weight/total) for tid, weight in tokens]
    
    async def sample_with_prefix(
        self,
        prefix: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: Optional[float] = 0.9,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        lm_params: Optional[Dict[str, Any]] = None
    ) -> List[int]:
        """
        Sample a token sequence conditioned on a character prefix.
        
        Args:
            prefix: Character prefix constraint for generation
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling probability threshold
            top_k: Top-k sampling parameter
            stop_sequences: Optional sequences that terminate generation
            lm_params: Additional parameters for the language model call
            
        Returns:
            List of token IDs forming the generated sequence
        """
        # Set up adaptive candidate count based on prefix complexity
        if lm_params is None:
            lm_params = {}
            
        if 'candidates_per_step' not in lm_params:
            # Calculate prefix complexity factors
            prefix_length_factor = min(len(prefix) / 2, 5)  # Cap at 5
            special_chars = sum(1 for c in prefix if not c.isalnum())
            complexity_factor = 1 + (prefix_length_factor + special_chars) / 10
            
            # Base count is 10, can go up to ~25 for complex prefixes
            adaptive_count = max(10, int(10 * complexity_factor))
            
            # Store the adapted count in parameters
            lm_params['candidates_per_step'] = adaptive_count
            self.candidates_per_step = adaptive_count
            
            logger.info(f"Using adaptive candidate count: {adaptive_count} for prefix '{prefix}'")
        
        # Delegate to the base sampler
        return await self.sampler.sample_with_prefix(
            prefix=prefix,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop_sequences=stop_sequences,
            lm_params=lm_params
        )


async def integrate_with_gemini(
    api_key: str,
    model_name: str,
    prefix: str,
    prompt: str = "",
    max_tokens: int = 100,
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: int = 40
) -> str:
    """
    Integrate Character Prefix Conditioning with Gemini.
    
    Args:
        api_key: Google AI Studio API key
        model_name: The Gemini model to use
        prefix: The character prefix to constrain generation
        prompt: Optional prompt to guide generation
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Nucleus sampling probability threshold
        top_k: Top-k sampling parameter
        
    Returns:
        Generated text starting with the prefix
    """
    # Configure Gemini API
    genai.configure(api_key=api_key)
    
    # Create the sampler
    sampler = GeminiCharacterPrefixSampler(
        model=model_name,
        api_key=api_key
    )
    
    # Sample with prefix
    result = await sampler.sample_with_prefix(
        prefix=prefix,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k
    )
    
    return result 