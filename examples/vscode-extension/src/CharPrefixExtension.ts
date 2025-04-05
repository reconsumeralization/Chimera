import * as vscode from 'vscode';
import axios from 'axios';

/**
 * Character Prefix Extension for VS Code
 * 
 * This extension provides code completion with character prefix conditioning
 * using the Project Chimera API.
 */
export class CharPrefixExtension implements vscode.Disposable {
    private _chimeraApiUrl: string;
    private _apiKey: string;
    private _modelType: 'openai' | 'gemini';
    private _disposables: vscode.Disposable[] = [];

    constructor() {
        // Get configuration
        const config = vscode.workspace.getConfiguration('characterPrefix');
        this._chimeraApiUrl = config.get<string>('apiUrl') || 'http://localhost:8000';
        this._apiKey = config.get<string>('apiKey') || '';
        this._modelType = config.get<'openai' | 'gemini'>('modelType') || 'openai';

        // Register commands
        this.registerCommands();

        // Listen for configuration changes
        vscode.workspace.onDidChangeConfiguration((e: vscode.ConfigurationChangeEvent) => {
            if (e.affectsConfiguration('characterPrefix')) {
                const config = vscode.workspace.getConfiguration('characterPrefix');
                this._chimeraApiUrl = config.get<string>('apiUrl') || 'http://localhost:8000';
                this._apiKey = config.get<string>('apiKey') || '';
                this._modelType = config.get<'openai' | 'gemini'>('modelType') || 'openai';
                vscode.window.showInformationMessage(`Character Prefix settings updated. Using model: ${this._modelType}`);
            }
        }, this, this._disposables);
    }

    // Getters for readonly properties
    get chimeraApiUrl(): string {
        return this._chimeraApiUrl;
    }

    get apiKey(): string {
        return this._apiKey;
    }

    get modelType(): 'openai' | 'gemini' {
        return this._modelType;
    }

    /**
     * Register commands
     */
    private registerCommands(): void {
        this._disposables.push(
            vscode.commands.registerTextEditorCommand('characterPrefix.completeWithPrefix', async (editor: vscode.TextEditor) => {
                const position = editor.selection.active;
                const linePrefix = editor.document.lineAt(position.line).text.substring(0, position.character);
                
                const prefix = await vscode.window.showInputBox({
                    placeHolder: 'Enter character prefix',
                    prompt: 'Enter a character prefix for code completion',
                    value: '',
                });

                if (!prefix) {
                    return;
                }

                vscode.window.withProgress({ 
                    location: vscode.ProgressLocation.Notification,
                    title: `Generating code with prefix "${prefix}"...`,
                    cancellable: true
                }, async (progress: vscode.Progress<{ message?: string; increment?: number }>, token: vscode.CancellationToken) => {
                    try {
                        const generatedCode = await this.generateWithCharPrefix(
                            linePrefix,
                            prefix,
                            editor.document.languageId
                        );

                        if (generatedCode && !token.isCancellationRequested) {
                            editor.edit((editBuilder: vscode.TextEditorEdit) => {
                                editBuilder.insert(position, generatedCode);
                            });
                        }
                    } catch (error) {
                        vscode.window.showErrorMessage(`Error generating code: ${error}`);
                    }
                    return Promise.resolve();
                });
            }),

            vscode.commands.registerCommand('characterPrefix.switchModelType', async () => {
                const selected = await vscode.window.showQuickPick(
                    ['openai', 'gemini'],
                    { placeHolder: 'Select model type' }
                );

                if (!selected) {
                    return;
                }

                const config = vscode.workspace.getConfiguration('characterPrefix');
                await config.update('modelType', selected, vscode.ConfigurationTarget.Global);
                this._modelType = selected as 'openai' | 'gemini';
                vscode.window.showInformationMessage(`Switched model type to ${selected}`);
            })
        );

        // Register completion provider
        this._disposables.push(
            vscode.languages.registerCompletionItemProvider(
                ['javascript', 'typescript', 'python', 'java', 'csharp', 'cpp', 'go', 'rust', 'php'],
                {
                    provideCompletionItems: (document: vscode.TextDocument, position: vscode.Position) => {
                        const linePrefix = document.lineAt(position.line).text.substring(0, position.character);
                        
                        // Create completion item
                        const item = new vscode.CompletionItem(
                            'Character Prefix Completion...',
                            vscode.CompletionItemKind.Snippet
                        );
                        item.detail = 'Generate code with a character prefix constraint';
                        item.documentation = new vscode.MarkdownString(
                            'Generates code completion that starts with a specific character prefix ' +
                            `using the ${this._modelType} model.`
                        );
                        
                        // Command to execute when selecting this completion
                        item.command = {
                            command: 'characterPrefix.completeWithPrefix',
                            title: 'Complete with Prefix'
                        };
                        
                        return [item];
                    }
                }
            )
        );
    }

    /**
     * Generate code with character prefix constraint
     */
    private async generateWithCharPrefix(
        context: string,
        prefix: string,
        language: string
    ): Promise<string> {
        try {
            const response = await axios.post(
                `${this._chimeraApiUrl}/api/ai/generate/char_prefix`,
                {
                    context: context,
                    prefix: prefix,
                    language: language,
                    max_tokens: 100,
                    model_type: this._modelType
                },
                {
                    headers: this._apiKey ? { 'Authorization': `Bearer ${this._apiKey}` } : {}
                }
            );

            return response.data.completion;
        } catch (error) {
            console.error('Error generating with character prefix:', error);
            throw new Error(`Failed to generate with prefix: ${error}`);
        }
    }

    /**
     * Activate the extension
     */
    public activate(): void {
        vscode.window.showInformationMessage('Character Prefix extension activated!');
    }

    /**
     * Dispose of resources
     */
    public dispose(): void {
        this._disposables.forEach(d => d.dispose());
        this._disposables = [];
    }
}

/**
 * Activate the extension
 */
export function activate(context: vscode.ExtensionContext): CharPrefixExtension {
    const extension = new CharPrefixExtension();
    return extension;
}

/**
 * Deactivate the extension
 */
export function deactivate(): void {
    // Nothing to do
} 