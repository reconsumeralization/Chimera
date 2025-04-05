# Character Prefix Conditioning

## Overview

Character Prefix Conditioning is an algorithm implemented in Project Chimera that enables efficient autoregressive sampling from a language model conditioned on a character prefix constraint. This is particularly useful for code completion scenarios where you need to ensure generated code starts with specific characters (function signature, variable name, etc.) regardless of token boundaries.

The algorithm works by efficiently filtering the language model's output distribution to only include tokens that can potentially satisfy the character prefix constraint, making it more efficient than naive approaches.

## Theory

The algorithm addresses the challenge of sampling from a conditional distribution:

```
q(s) = p(s | repr(s) starts with P)
```

Where:
- `p(s)` is the base language model distribution over token sequences
- `repr(s)` is the character representation of the token sequence `s`
- `P` is the character prefix constraint

At each step of autoregressive generation, the algorithm:
1. Determines whether the character prefix has been satisfied
2. If not yet satisfied, identifies valid tokens that could continue the prefix
3. Filters and renormalizes the model's probability distribution to valid tokens
4. Samples from the constrained distribution

## Usage

### Basic API Usage

#### OpenAI

```python
from src.chimera_core.services.ai_client import AIClient

# Initialize your AI client
ai_client = AIClient(...)  # OpenAI client

# Generate code with a character prefix constraint
result = await ai_client.generate_with_char_prefix(
    prompt="Write a function to calculate the factorial of a number",
    prefix="def factorial",
    language="python",
    temperature=0.7
)
```

#### Gemini

```python
from src.chimera_core.services.ai_client import AIClient

# Initialize your AI client with Gemini configuration
ai_client = AIClient(
    api_key="your-gemini-api-key",
    model="gemini-pro",
    llm_client_type="gemini"
)

# Generate code with a character prefix constraint
result = await ai_client.generate_with_char_prefix(
    prompt="Write a function to calculate the factorial of a number",
    prefix="def factorial",
    language="python",
    temperature=0.7
)
```

### Direct Usage with Model-Specific Implementations

#### OpenAI Direct Integration

```python
from src.chimera_core.ai import integrate_with_openai_client
import openai

client = openai.AsyncOpenAI(api_key="your-openai-api-key")

result = await integrate_with_openai_client(
    client=client,
    messages=[
        {"role": "system", "content": "You are a coding assistant."},
        {"role": "user", "content": "Write a factorial function in Python"}
    ],
    prefix="def factorial",
    model="gpt-4",
    temperature=0.7
)
```

#### Gemini Direct Integration

```python
from src.chimera_core.ai import integrate_with_gemini

result = await integrate_with_gemini(
    api_key="your-gemini-api-key",
    model_name="gemini-pro",
    prefix="def factorial",
    prompt="Write a factorial function in Python",
    temperature=0.7
)
```

### REST API Endpoint

The Character Prefix Conditioning is available via the REST API:

#### Non-streaming Endpoint

```
POST /ai/generate/prefix
```

Request body:
```json
{
  "prompt": "Write a function to calculate the factorial of a number",
  "prefix": "def factorial",
  "language": "python",
  "temperature": 0.7
}
```

Response:
```json
{
  "code": "def factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    else:\n        return n * factorial(n - 1)",
  "language": "python",
  "prefix": "def factorial"
}
```

#### Streaming Endpoint

```
POST /ai/generate/prefix/stream
```

With the same request body, returns a Server-Sent Events stream with the generated text.

## Architecture

### Core Components

1. **CharacterTrie**: A trie data structure that maps character sequences to sets of token IDs, enabling efficient lookup of tokens that start with a specific character prefix.

2. **CharacterPrefixSampler**: The main algorithm implementation that:
   - Builds a character trie from the tokenizer's vocabulary
   - Filters valid tokens based on the remaining prefix
   - Renormalizes probability distributions
   - Handles sampling with temperature/top-p/top-k parameters

3. **Model-Specific Implementations**:

   - **OpenAI Integration**:
     - Uses tiktoken for tokenization
     - Integrates with the OpenAI Chat Completions API
     - Handles token probability extraction from the logprobs feature

   - **Gemini Integration**:
     - Uses a custom tokenizer approximation (GeminiTokenizerWrapper)
     - Works with Gemini's candidate generation approach
     - Approximates token probabilities from multiple candidates

### Implementation Details

The implementation follows these key principles:

1. **Efficiency**:
   - Only one LM call per generated token
   - Efficient trie-based filtering of valid tokens
   - Lazy initialization of resource-intensive components

2. **Correctness**:
   - Guarantees generated text starts with the specified prefix
   - Handles multi-token character sequences correctly
   - Properly applies temperature and sampling strategies

3. **Robustness**:
   - Graceful handling of impossible prefixes
   - Fallbacks when specialized integrations aren't available
   - Comprehensive logging

## Model-Specific Considerations

### OpenAI Approach

The OpenAI implementation:
- Uses the logprobs feature to get token probabilities
- Works with the standard OpenAI Chat Completions API
- Relies on tiktoken for accurate tokenization

### Gemini Approach

Since Gemini doesn't expose token probabilities directly in its API, the implementation:
1. Generates multiple candidates (with diversity) to approximate the token distribution
2. Assigns probabilities to tokens based on candidate order
3. Uses a character-level tokenization approximation
4. Provides graceful fallbacks for error cases

## Technical Considerations

1. **Token Boundaries**: Character prefixes may not align with token boundaries, which is the primary challenge this algorithm addresses.

2. **Resource Usage**: The trie structure requires memory proportional to vocabulary size times average token length, but the computational cost during generation is minimal.

3. **API Limitations**: Different LLM providers have varying support for logprobs/token probabilities. The implementation handles these differences.

4. **Tokenizer Differences**: OpenAI and Gemini use different tokenizers, so the implementation adapts to each model's characteristics.

## Testing

The implementation includes comprehensive unit and integration tests:

1. **Unit Tests**: Test the trie structure and core algorithm
2. **Integration Tests**: Test the end-to-end generation process
3. **Mock Tests**: Test the model-specific implementations with mocked API responses

Run the tests using:

```bash
python -m unittest discover -s tests/ai
```

## Future Improvements

1. **Caching**: Add caching of the trie structure for repeated generations with similar prefixes

2. **Additional Integrations**: Support for other LLM providers (Anthropic, Local models, etc.)

3. **Multi-prefix Constraints**: Allow specifying multiple required character sequences at different positions

4. **Character Edit Distance**: Allow approximate prefix matching using edit distance

5. **Improved Gemini Tokenization**: Work with Google to get access to the actual Gemini tokenizer for better accuracy 