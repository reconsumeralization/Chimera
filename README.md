# Project Chimera

Project Chimera is a context-aware AI coding assistant that provides intelligent code generation, explanation, and analysis by understanding your project's context.

## Features

- **Context-Aware AI**: Chimera understands your code in context, providing more relevant assistance.
- **Code Generation**: Generate code snippets, functions, or entire components with context-aware assistance.
- **Code Explanation**: Get detailed or brief explanations of any code snippet or function.
- **Code Analysis**: Identify potential issues, bugs, and improvement opportunities.
- **Test Generation**: Automatically generate comprehensive test cases for your functions.
- **Rule Engine**: Define custom rules to automate repetitive tasks and enforce coding standards.

## Getting Started

### Prerequisites

- Python 3.9+
- pip for package installation
- OpenAI API key or other supported LLM provider keys

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/project-chimera.git
   cd project-chimera
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up configuration:
   ```bash
   cp .env.sample .env
   ```
   Edit the `.env` file with your settings, especially your AI provider API key.

### Running the API Server

Start the API server with:

```bash
python scripts/run_api.py
```

The server will be available at http://localhost:8000 by default.

## Architecture

Chimera is built with a modular architecture:

- **ContextCacheService**: Manages code context and provides relevant information to the AI.
- **PromptService**: Creates intelligent, context-aware prompts for different AI tasks.
- **AIClient**: Handles communication with LLM providers (OpenAI, Vertex AI, etc.).
- **RuleEngineService**: Evaluates rules against code context and automates actions.
- **DatabaseService**: Handles persistence for contexts, rules, and other data.

## API Endpoints

The API provides several endpoints for interacting with Chimera:

- `/ai/generate`: Generate code based on a prompt and context
- `/ai/explain`: Explain code with optional context
- `/ai/analyze`: Analyze code for issues and improvements
- `/ai/chat`: Chat with the AI about code
- `/ai/test`: Generate tests for code
- `/context/`: Manage context snapshots
- `/rules/`: Manage and evaluate rules

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 