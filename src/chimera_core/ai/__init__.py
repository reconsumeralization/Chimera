"""AI utilities for Project Chimera.

This package provides specialized AI-related utilities for Project Chimera,
including implementations of advanced algorithms like Character Prefix Conditioning.
"""

from .char_prefix_sampling import CharacterPrefixSampler, CharacterTrie

# Import OpenAI-specific implementations if available
try:
    from .char_prefix_openai import OpenAICharacterPrefixSampler, integrate_with_openai_client
    HAS_OPENAI_INTEGRATION = True
except ImportError:
    HAS_OPENAI_INTEGRATION = False

# Import Gemini-specific implementations if available
try:
    from .char_prefix_gemini import GeminiCharacterPrefixSampler, integrate_with_gemini, GeminiTokenizerWrapper
    HAS_GEMINI_INTEGRATION = True
except ImportError:
    HAS_GEMINI_INTEGRATION = False

# Make everything importable from src.chimera_core.ai
__all__ = [
    "CharacterPrefixSampler", 
    "CharacterTrie",
    "HAS_OPENAI_INTEGRATION",
    "HAS_GEMINI_INTEGRATION"
]

if HAS_OPENAI_INTEGRATION:
    __all__.extend(["OpenAICharacterPrefixSampler", "integrate_with_openai_client"])

if HAS_GEMINI_INTEGRATION:
    __all__.extend(["GeminiCharacterPrefixSampler", "integrate_with_gemini", "GeminiTokenizerWrapper"]) 