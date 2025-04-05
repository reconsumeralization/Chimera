# Project Chimera

Project Chimera is a context-aware AI coding assistant that provides intelligent code generation, explanation, and analysis by understanding your project's context.

## Features

- **Context-Aware AI**: Chimera understands your code in context, providing more relevant assistance.
- **Code Generation**: Generate code snippets, functions, or entire components with context-aware assistance.
- **Code Explanation**: Get detailed or brief explanations of any code snippet or function.
- **Code Analysis**: Identify potential issues, bugs, and improvement opportunities.
- **Test Generation**: Automatically generate comprehensive test cases for your functions.
- **Rule Engine**: Define custom rules to automate repetitive tasks and enforce coding standards.

## Quick Start

This project includes unified startup scripts that work across multiple environments:

### Windows Users

Run the batch file by double-clicking `start_chimera.bat` or from a command prompt:

```
start_chimera.bat
```

### Linux/Mac/WSL Users

Run the bash script:

```
chmod +x start_chimera.sh
./start_chimera.sh
```

### Git Bash Users (Windows)

Run the bash script:

```
chmod +x start_chimera.sh
./start_chimera.sh
```

## Startup Script Features

- Automatically detects and adapts to your environment (Windows, WSL, Git Bash)
- Activates the Python virtual environment
- Creates any missing schema files needed for proper operation
- Starts all required services:
  - Web Server (FastAPI) on port 8000
  - Code Analysis Server
  - Tools Server
- Handles graceful shutdown with Ctrl+C

## Troubleshooting

If you encounter errors:

1. Make sure you've run the setup script first (`setup.bat` or `setup.sh`)
2. Check that your virtual environment is correctly installed
3. Verify Python dependencies are installed: `pip install -r requirements.txt`
4. If you get import errors, the startup scripts will attempt to create missing files

## Accessing Services

Once started, access the web interface at:
- http://localhost:8000

## Stopping Services

Press Ctrl+C in the terminal window to gracefully stop all services.

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