import * as vscode from 'vscode';
import * as path from 'path';
import { GeminiTokenizerService } from './tokenizer-service';
import { CharacterPrefixSampler } from './char-prefix-sampler';
import { GeminiProvider, GenerationConfig, GenerationResult } from './gemini-provider';
import { TelemetryTransformer } from './telemetry-transformer';
import { VSCodeContextManager, VSCodeContext } from './vscode-context-manager';

/**
 * Main service for coordinating Gemini functionality
 */
export class GeminiService implements vscode.Disposable {
    private tokenizer: GeminiTokenizerService;
    private sampler: CharacterPrefixSampler;
    private provider: GeminiProvider;
    private telemetryTransformer: TelemetryTransformer;
    private contextManager: VSCodeContextManager;
    private statusBarItem: vscode.StatusBarItem;
    
    private disposables: vscode.Disposable[] = [];
    private isReady: boolean = false;
    
    private readonly _onServiceReady = new vscode.EventEmitter<boolean>();
    public readonly onServiceReady = this._onServiceReady.event;
    
    /**
     * Create a new GeminiService
     */
    constructor() {
        // Get extension context
        const extension = vscode.extensions.getExtension('project-chimera.chimera-dashboard');
        if (!extension) {
            throw new Error('Could not get extension context');
        }
        
        // Initialize components
        this.tokenizer = new GeminiTokenizerService(extension.extensionPath);
        this.sampler = new CharacterPrefixSampler(this.tokenizer);
        this.provider = new GeminiProvider(this.tokenizer, this.sampler);
        this.telemetryTransformer = new TelemetryTransformer();
        this.contextManager = new VSCodeContextManager();
        
        // Create status bar item
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.text = "$(beaker) Gemini: Initializing...";
        this.statusBarItem.tooltip = "Gemini Tokenizer Status";
        this.statusBarItem.command = 'chimera-dashboard.showGeminiPanel';
        this.statusBarItem.show();
        
        // Add all components to disposables
        this.disposables.push(
            this.tokenizer,
            this.sampler,
            this.provider,
            this.telemetryTransformer,
            this.contextManager,
            this.statusBarItem,
            this._onServiceReady
        );
        
        // Initialize service
        this.initialize();
    }
    
    /**
     * Initialize the Gemini service
     */
    private async initialize(): Promise<void> {
        // Show initializing status
        this.updateStatusBar('initializing');
        
        // Wait for the provider to be ready
        this.provider.onReady(ready => {
            this.isReady = ready;
            this.updateStatusBar(ready ? 'ready' : 'error');
            this._onServiceReady.fire(ready);
            
            if (ready) {
                vscode.window.showInformationMessage('Gemini tokenizer ready!');
            } else {
                vscode.window.showErrorMessage('Gemini tokenizer failed to initialize');
            }
        });
        
        // Register command handlers
        this.registerCommands();
    }
    
    /**
     * Register command handlers
     */
    private registerCommands(): void {
        // Register commands related to Gemini functionality
        this.disposables.push(
            vscode.commands.registerCommand('chimera-dashboard.geminiGenerateCompletion', () => 
                this.handleGenerateCompletion()
            ),
            
            vscode.commands.registerCommand('chimera-dashboard.geminiRefactorCode', () => 
                this.handleRefactorCode()
            ),
            
            vscode.commands.registerCommand('chimera-dashboard.geminiGenerateTests', () => 
                this.handleGenerateTests()
            )
        );
    }
    
    /**
     * Update the status bar item
     * 
     * @param status The current status
     */
    private updateStatusBar(status: 'initializing' | 'ready' | 'error' | 'working'): void {
        switch (status) {
            case 'initializing':
                this.statusBarItem.text = "$(sync~spin) Gemini: Initializing...";
                this.statusBarItem.tooltip = "Gemini Tokenizer is initializing";
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
                break;
                
            case 'ready':
                this.statusBarItem.text = "$(beaker) Gemini: Ready";
                this.statusBarItem.tooltip = "Gemini Tokenizer is ready";
                this.statusBarItem.backgroundColor = undefined;
                break;
                
            case 'error':
                this.statusBarItem.text = "$(error) Gemini: Error";
                this.statusBarItem.tooltip = "Gemini Tokenizer encountered an error";
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
                break;
                
            case 'working':
                this.statusBarItem.text = "$(sync~spin) Gemini: Working...";
                this.statusBarItem.tooltip = "Gemini Tokenizer is processing";
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
                break;
        }
    }
    
    /**
     * Handler for generating code completion
     */
    private async handleGenerateCompletion(): Promise<void> {
        if (!this.isReady) {
            vscode.window.showErrorMessage('Gemini service is not ready');
            return;
        }
        
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        
        try {
            // Update status
            this.updateStatusBar('working');
            
            // Get context
            const context = await this.contextManager.collectContext();
            
            // Get current document and cursor position
            const document = editor.document;
            const position = editor.selection.active;
            
            // Get text up to cursor
            const range = new vscode.Range(new vscode.Position(0, 0), position);
            const textUpToCursor = document.getText(range);
            
            // Generate completion
            const result = await this.provider.generateCodeCompletion(
                textUpToCursor,
                document.languageId
            );
            
            // Insert the completion
            if (result.text) {
                editor.edit(editBuilder => {
                    editBuilder.insert(position, result.text);
                });
            }
            
            // Update status
            this.updateStatusBar('ready');
        } catch (error) {
            console.error('Error generating completion:', error);
            vscode.window.showErrorMessage(`Failed to generate completion: ${error}`);
            this.updateStatusBar('error');
        }
    }
    
    /**
     * Handler for refactoring code
     */
    private async handleRefactorCode(): Promise<void> {
        if (!this.isReady) {
            vscode.window.showErrorMessage('Gemini service is not ready');
            return;
        }
        
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        
        try {
            // Get selected code
            const selection = editor.selection;
            if (selection.isEmpty) {
                vscode.window.showInformationMessage('Please select code to refactor');
                return;
            }
            
            const selectedText = editor.document.getText(selection);
            
            // Get refactoring instructions
            const instructions = await vscode.window.showInputBox({
                prompt: 'Enter refactoring instructions',
                placeHolder: 'e.g., "Make this code more efficient", "Add error handling", etc.'
            });
            
            if (!instructions) {
                return; // User cancelled
            }
            
            // Update status
            this.updateStatusBar('working');
            
            // Get context
            const context = await this.contextManager.collectContext();
            
            // Prepare prompt for refactoring
            const prompt = `
Refactor the following ${editor.document.languageId} code:

\`\`\`${editor.document.languageId}
${selectedText}
\`\`\`

Instructions: ${instructions}

Refactored code (keep the same language and only output the code, no explanations):
\`\`\`${editor.document.languageId}
`;
            
            // Generate refactored code
            const config: Partial<GenerationConfig> = {
                temperature: 0.2, // Lower temperature for refactoring
                stopSequences: ['```']
            };
            
            const result = await this.provider.generateText(prompt, config);
            
            // Extract just the code
            let refactoredCode = result.text.trim();
            
            // Replace the selected text
            editor.edit(editBuilder => {
                editBuilder.replace(selection, refactoredCode);
            });
            
            // Update status
            this.updateStatusBar('ready');
        } catch (error) {
            console.error('Error refactoring code:', error);
            vscode.window.showErrorMessage(`Failed to refactor code: ${error}`);
            this.updateStatusBar('error');
        }
    }
    
    /**
     * Handler for generating tests
     */
    private async handleGenerateTests(): Promise<void> {
        if (!this.isReady) {
            vscode.window.showErrorMessage('Gemini service is not ready');
            return;
        }
        
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        
        try {
            // Get selected code
            const selection = editor.selection;
            const selectedText = selection.isEmpty ? 
                editor.document.getText() : editor.document.getText(selection);
            
            // Update status
            this.updateStatusBar('working');
            
            // Get context
            const context = await this.contextManager.collectContext();
            
            // Determine test framework based on language
            let testFramework = 'pytest';
            const language = editor.document.languageId;
            
            if (language === 'javascript' || language === 'typescript') {
                testFramework = 'jest';
            } else if (language === 'csharp') {
                testFramework = 'xunit';
            } else if (language === 'java') {
                testFramework = 'junit';
            }
            
            // Prepare prompt for test generation
            const prompt = `
Generate tests for the following ${language} code using ${testFramework}:

\`\`\`${language}
${selectedText}
\`\`\`

Generate comprehensive tests for this code. Include:
1. Tests for normal operation
2. Tests for edge cases
3. Tests for error conditions

Only output the test code in \`\`\`${language} code blocks, no explanations:
\`\`\`${language}
`;
            
            // Generate tests
            const config: Partial<GenerationConfig> = {
                temperature: 0.2, // Lower temperature for test generation
                maxTokens: 1000,
                stopSequences: ['```']
            };
            
            const result = await this.provider.generateText(prompt, config);
            
            // Extract just the code
            const testCode = result.text.trim();
            
            // Create a new file for the tests
            const currentFile = editor.document.fileName;
            const fileExtension = path.extname(currentFile);
            const baseName = path.basename(currentFile, fileExtension);
            const testFileName = `${baseName}.test${fileExtension}`;
            const testFileUri = vscode.Uri.file(path.join(path.dirname(currentFile), testFileName));
            
            // Create the test file
            const workspaceEdit = new vscode.WorkspaceEdit();
            workspaceEdit.createFile(testFileUri, { overwrite: false, ignoreIfExists: true });
            await vscode.workspace.applyEdit(workspaceEdit);
            
            // Open the test file and insert the generated tests
            const testDocument = await vscode.workspace.openTextDocument(testFileUri);
            const testEditor = await vscode.window.showTextDocument(testDocument);
            
            testEditor.edit(editBuilder => {
                const firstLine = testDocument.lineAt(0);
                const lastLine = testDocument.lineAt(testDocument.lineCount - 1);
                const textRange = new vscode.Range(firstLine.range.start, lastLine.range.end);
                editBuilder.replace(textRange, testCode);
            });
            
            // Update status
            this.updateStatusBar('ready');
        } catch (error) {
            console.error('Error generating tests:', error);
            vscode.window.showErrorMessage(`Failed to generate tests: ${error}`);
            this.updateStatusBar('error');
        }
    }
    
    /**
     * Get the tokenizer service
     */
    public getTokenizer(): GeminiTokenizerService {
        return this.tokenizer;
    }
    
    /**
     * Get the Gemini provider
     */
    public getProvider(): GeminiProvider {
        return this.provider;
    }
    
    /**
     * Get the context manager
     */
    public getContextManager(): VSCodeContextManager {
        return this.contextManager;
    }
    
    /**
     * Check if the service is ready
     */
    public getIsReady(): boolean {
        return this.isReady;
    }
    
    /**
     * Dispose the Gemini service
     */
    public dispose(): void {
        // Dispose all disposables
        this.disposables.forEach(d => d.dispose());
        this.disposables = [];
    }
} 