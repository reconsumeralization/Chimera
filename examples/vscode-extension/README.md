# Character Prefix Code Completion Extension

This VS Code extension demonstrates how to integrate the Project Chimera Character Prefix Conditioning algorithm into a development environment. It allows you to generate code completions that are guaranteed to start with a specific character prefix, providing more precise and accurate code suggestions.

## Features

- **Character Prefix Completion**: Generate code completions that start with a specific character prefix
- **Multiple Model Support**: Switch between OpenAI and Gemini models for character prefix conditioning
- **VS Code Integration**: Seamlessly integrated into VS Code's completion system

## Requirements

- VS Code 1.60.0 or higher
- Project Chimera server running (with Character Prefix Conditioning API endpoints)
- API key for authentication (if required by your Chimera server)

## Installation

1. Clone this repository
2. Run `npm install` to install dependencies
3. Run `npm run compile` to compile the TypeScript code
4. Press F5 to launch the extension in a new VS Code window

## Usage

1. Configure the extension in VS Code settings:
   - Set `characterPrefix.apiUrl` to your Chimera server URL
   - Set `characterPrefix.apiKey` to your API key (if needed)
   - Choose your preferred model with `characterPrefix.modelType` (openai or gemini)

2. Access character prefix completion in two ways:
   - Command: Press Ctrl+Shift+P and type "Character Prefix: Complete with Prefix"
   - Auto-completion: Type and wait for VS Code to show completions, then select "Character Prefix Completion..."

3. Switch between models:
   - Press Ctrl+Shift+P and type "Character Prefix: Switch Model Type"
   - Select "openai" or "gemini" from the dropdown

## How It Works

This extension connects to a Project Chimera server running the Character Prefix Conditioning API. When you request a completion with a specific prefix, it sends your request to the server, which uses one of two approaches:

1. **OpenAI Integration**: Uses the OpenAI logprobs feature to get token probabilities and efficiently filters them using a character-based Trie.

2. **Gemini Integration**: Uses multiple candidate generation to approximate token probabilities and efficiently filter them.

Both approaches guarantee that the generated completion starts with your specified character prefix, providing precise control over code generation.

## Extension Settings

* `characterPrefix.apiUrl`: URL of the Chimera API server (default: "http://localhost:8000")
* `characterPrefix.apiKey`: API key for authentication with the Chimera API
* `characterPrefix.modelType`: Model type to use (openai or gemini, default: openai)

## Known Issues

- The streaming mode is not yet supported in this example
- Error handling could be improved for better user feedback

## Development

To modify this extension:

1. Edit files in the `src` directory
2. Run `npm run compile` to compile your changes
3. Press F5 to debug the extension in a new VS Code window

## License

This extension is part of Project Chimera and is available under the same license. 