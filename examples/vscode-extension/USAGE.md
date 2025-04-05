# Using the Character Prefix Code Completion Extension

This guide explains how to effectively use the Character Prefix Code Completion extension with the Project Chimera API.

## Setup & Connection

Before using the extension, you need to ensure it's properly connected to your Chimera server:

1. **Configure API Settings**
   - Open VS Code settings (File > Preferences > Settings or Ctrl+,)
   - Search for "Character Prefix"
   - Set the following options:
     - `characterPrefix.apiUrl`: The URL of your running Chimera API server (e.g., "http://localhost:8000")
     - `characterPrefix.apiKey`: Your API key if authentication is required
     - `characterPrefix.modelType`: Your preferred model ("openai" or "gemini")

2. **Start your Chimera Server**
   - Make sure your Project Chimera server is running with the Character Prefix Conditioning API available
   - The server should expose the endpoint `/api/ai/generate/char_prefix`

## Using Character Prefix Completion

### Method 1: Command Palette

1. Position your cursor where you want to insert code
2. Press `Ctrl+Shift+P` to open the Command Palette
3. Type "Character Prefix" and select "Character Prefix: Complete with Prefix"
4. Enter your desired character prefix (e.g., "def factorial")
5. Wait for the code to be generated and inserted at your cursor position

### Method 2: Auto-Completion

1. Start typing in a supported language file (JavaScript, TypeScript, Python, etc.)
2. When VS Code shows completion suggestions, look for "Character Prefix Completion..."
3. Select this option to trigger the character prefix completion flow
4. Enter your desired character prefix
5. Wait for the code to be generated and inserted at your cursor position

## Switching Models

You can easily switch between OpenAI and Gemini models:

1. Press `Ctrl+Shift+P` to open the Command Palette
2. Type "Character Prefix" and select "Character Prefix: Switch Model Type"
3. Select your desired model ("openai" or "gemini")
4. You'll see a notification confirming the model change

## Tips for Effective Use

- **Be Specific**: More specific character prefixes yield better results
- **Include Function Signatures**: For function completions, include the function signature in your prefix
- **Context Awareness**: The extension sends the text before your cursor as context to help the model understand what you're trying to do
- **Language Support**: The extension supports multiple programming languages, and the completion request includes the language identifier to help the API generate appropriate code

## Troubleshooting

If you encounter issues:

1. **Check Chimera Server**: Ensure your Chimera server is running and accessible
2. **Verify API URL**: Make sure the API URL is correctly configured
3. **Check Logs**: Look for error messages in the VS Code Developer Console (Help > Toggle Developer Tools)
4. **API Key**: If your server requires authentication, verify your API key is valid

## Advanced Configuration

For advanced users who want to modify extension behavior:

1. The extension is written in TypeScript and can be found in the `src` directory
2. Key files:
   - `extension.ts`: The main entry point
   - `CharPrefixExtension.ts`: The core implementation 