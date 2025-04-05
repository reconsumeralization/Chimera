"""OpenAI-specific implementation of Character Prefix Conditioning.

This module provides integration between the Character Prefix Conditioning algorithm
and the OpenAI API, enabling efficient token sampling with character prefix constraints.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import structlog
import tiktoken
from openai.types.chat import ChatCompletionMessageParam

from .char_prefix_sampling import CharacterPrefixSampler

# Set up logging
logger = structlog.get_logger(__name__)


class OpenAICharacterPrefixSampler:
    """OpenAI-specific implementation of Character Prefix Conditioning Sampler."""
    
    def __init__(
        self,
        client: Any,  # openai.AsyncOpenAI client
        model: str,
        tokenizer: Optional[Any] = None  # tiktoken tokenizer
    ):
        """
        Initialize the OpenAI Character Prefix Sampler.
        
        Args:
            client: The OpenAI AsyncOpenAI client
            model: The model name to use
            tokenizer: Optional tiktoken tokenizer (created if not provided)
        """
        self.client = client
        self.model = model
        
        # Initialize tokenizer if not provided
        if tokenizer is None:
            try:
                self.tokenizer = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fall back to cl100k_base for new models
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
                logger.warning(
                    "Model-specific tokenizer not found, using cl100k_base",
                    model=model
                )
        else:
            self.tokenizer = tokenizer
        
        # Create the character prefix sampler
        self.vocab_size = self.tokenizer.n_vocab
        self.sampler = None  # Lazy initialization
        
        logger.info(
            "OpenAI Character Prefix Sampler initialized",
            model=model,
            vocab_size=self.vocab_size
        )
    
    def _lazy_init_sampler(self):
        """Lazily initialize the character prefix sampler."""
        if self.sampler is None:
            # Use a closure to capture the client and call logprobs API
            async def lm_call(tokens: List[int], params: Optional[Dict[str, Any]] = None) -> List[Tuple[int, float]]:
                # Convert tokens to text for the prompt
                messages = params.get("messages", [])
                
                # Add the current tokens as assistant message if any
                if tokens:
                    token_text = self.tokenizer.decode(tokens)
                    # Find the last assistant message or add a new one
                    assistant_idx = -1
                    for i, msg in enumerate(messages):
                        if msg["role"] == "assistant":
                            assistant_idx = i
                    
                    if assistant_idx >= 0:
                        messages[assistant_idx]["content"] = token_text
                    else:
                        messages.append({"role": "assistant", "content": token_text})
                
                try:
                    # Call the OpenAI API with logprobs
                    completion = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0,  # Use 0 to get most likely tokens
                        max_tokens=1,  # Just need the next token
                        logprobs=True,
                        top_logprobs=100  # Get more logprobs for better filtering
                    )
                    
                    # Extract the logprobs
                    choice = completion.choices[0]
                    
                    # Convert logprobs to token probabilities
                    # Structure depends on the API version, adjust as needed
                    token_probs = []
                    
                    # Try to get logprobs from the response
                    # This may need adaptation based on the exact API structure
                    logprobs = getattr(choice, "logprobs", None)
                    if logprobs and hasattr(logprobs, "content"):
                        content_logprobs = logprobs.content[0]
                        top_logprobs = content_logprobs.top_logprobs
                        
                        for entry in top_logprobs:
                            token = entry.token
                            logprob = entry.logprob
                            
                            # Convert token to token_id
                            try:
                                token_id = self.tokenizer.encode(token)[0]
                                # Convert logprob to prob
                                prob = 2 ** logprob  # or math.exp(logprob) for natural log
                                token_probs.append((token_id, prob))
                            except Exception as e:
                                logger.warning("Error processing token", token=token, error=str(e))
                    
                    # If no valid logprobs, use a uniform distribution
                    if not token_probs:
                        logger.warning("No valid logprobs found, using uniform distribution")
                        # Use a small subset for efficiency
                        token_ids = list(range(min(1000, self.vocab_size)))
                        token_probs = [(tid, 1.0 / len(token_ids)) for tid in token_ids]
                    
                    return token_probs
                
                except Exception as e:
                    logger.error("Error calling OpenAI API", error=str(e))
                    # Return a uniform distribution as fallback
                    token_ids = list(range(min(1000, self.vocab_size)))
                    return [(tid, 1.0 / len(token_ids)) for tid in token_ids]
            
            # Initialize the sampler with our tokenizer and LM call function
            self.sampler = CharacterPrefixSampler(
                tokenizer=self,  # Use this class as tokenizer adapter
                lm_call=lm_call,
                vocab_size=self.vocab_size
            )
    
    # Tokenizer adapter methods
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        return self.tokenizer.encode(text)
    
    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs to text."""
        return self.tokenizer.decode(token_ids)
    
    async def sample_with_prefix(
        self,
        messages: List[Dict[str, str]],
        prefix: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: Optional[int] = 40,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Sample completion with character prefix constraint.
        
        Args:
            messages: List of message dictionaries for the chat completion
            prefix: Character prefix to constrain generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling probability threshold
            top_k: Top-k sampling parameter
            stop_sequences: Optional sequences that terminate generation
            
        Returns:
            Generated text starting with the prefix
        """
        # Initialize sampler if needed
        self._lazy_init_sampler()
        
        # Convert messages to the format expected by the sampler
        # We'll need to convert to OpenAI's ChatCompletionMessageParam format
        chat_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
        
        # Sample tokens using the character prefix sampler
        token_ids = await self.sampler.sample_with_prefix(
            prefix=prefix,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop_sequences=stop_sequences,
            lm_params={"messages": chat_messages}
        )
        
        # Decode the tokens to text
        generated_text = self.tokenizer.decode(token_ids)
        
        # Ensure the generated text starts with the prefix
        # This should always be true due to the algorithm, but double-check
        if not generated_text.startswith(prefix):
            logger.warning(
                "Generated text does not start with prefix despite algorithm",
                prefix=prefix,
                generated_text=generated_text[:min(20, len(generated_text))]
            )
            # Force the prefix
            generated_text = prefix + generated_text
        
        return generated_text


async def integrate_with_openai_client(
    client: Any,
    messages: List[Dict[str, str]],
    prefix: str,
    model: str,
    max_tokens: int = 500,
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: Optional[int] = 40
) -> str:
    """
    Integrate Character Prefix Conditioning with OpenAI client.
    
    Args:
        client: The OpenAI AsyncOpenAI client
        messages: The messages for the chat completion
        prefix: The character prefix to constrain generation
        model: The model to use
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Nucleus sampling probability threshold
        top_k: Top-k sampling parameter
        
    Returns:
        Generated text starting with the prefix
    """
    # Create the sampler
    sampler = OpenAICharacterPrefixSampler(
        client=client,
        model=model
    )
    
    # Sample with prefix
    result = await sampler.sample_with_prefix(
        messages=messages,
        prefix=prefix,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k
    )
    
    return result 