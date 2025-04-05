import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Collected context type
 */
export interface VSCodeContext {
    editor: EditorContext;
    workspace: WorkspaceContext;
    git?: GitContext;
}

/**
 * Editor context
 */
export interface EditorContext {
    documentText: string;
    selections: Array<{
        start: vscode.Position;
        end: vscode.Position;
        text: string;
    }>;
    fileName: string | undefined;
    languageId: string | undefined;
    lineCount: number;
    currentFile?: {
        path: string;
        language: string;
        content: string;
        selectionRange?: vscode.Range;
        selectionText?: string;
    };
    visibleFiles?: Array<{
        path: string;
        language: string;
        isActive: boolean;
    }>;
    cursorPosition?: vscode.Position;
}

/**
 * Workspace context
 */
export interface WorkspaceContext {
    rootPath?: string;
    workspaceFolders: string[];
    openFiles: string[];
    recentFiles: string[];
}

/**
 * Git context
 */
export interface GitContext {
    branch: string;
    uncommittedChanges: Array<{
        file: string;
        status: string;
    }>;
    recent?: {
        commits: Array<{
            hash: string;
            message: string;
            author: string;
            date: string;
        }>;
    };
}

/**
 * Context collection options
 */
export interface ContextCollectionOptions {
    includeGit: boolean;
    includeOpenFiles: boolean;
    includeWorkspaceFolders: boolean;
    includeRecentFiles: boolean;
    maxRecentFiles: number;
    maxGitCommits: number;
}

/**
 * Context Manager for VSCode integration with Gemini tokenizer
 * Collects and formats editor context for analysis
 */
export class VsCodeContextManager implements vscode.Disposable {
    private disposables: vscode.Disposable[] = [];
    private maxContextLines: number = 1000;
    
    constructor() {
        // Add any listeners needed
    }
    
    /**
     * Collect the current editor context
     * @returns The current editor context or undefined if no editor is active
     */
    public collectCurrentContext(): EditorContext | undefined {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return undefined;
        }
        
        const document = editor.document;
        const selections = editor.selections;
        
        // Get text from each selection
        const selectionInfo = selections.map(selection => {
            return {
                start: selection.start,
                end: selection.end,
                text: document.getText(new vscode.Range(selection.start, selection.end))
            };
        });
        
        // Create full context
        return {
            documentText: this.truncateIfNeeded(document.getText()),
            selections: selectionInfo,
            fileName: document.fileName,
            languageId: document.languageId,
            lineCount: document.lineCount
        };
    }
    
    /**
     * Get selected text from active editor
     * @returns The selected text or empty string if no selection
     */
    public getSelectedText(): string {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return '';
        }
        
        const document = editor.document;
        const selection = editor.selection;
        
        if (selection.isEmpty) {
            return '';
        }
        
        return document.getText(selection);
    }
    
    /**
     * Get surrounding context around the cursor
     * @param lineCount Number of lines to include before and after cursor
     * @returns Context string or empty string if not available
     */
    public getCursorContext(lineCount: number = 5): string {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return '';
        }
        
        const document = editor.document;
        const position = editor.selection.active;
        
        // Calculate the range of lines to include
        const startLine = Math.max(0, position.line - lineCount);
        const endLine = Math.min(document.lineCount - 1, position.line + lineCount);
        
        // Get the text within the range
        const range = new vscode.Range(
            new vscode.Position(startLine, 0),
            new vscode.Position(endLine, document.lineAt(endLine).text.length)
        );
        
        return document.getText(range);
    }
    
    /**
     * Truncate text if it's too long
     * @param text Text to potentially truncate
     * @returns Truncated text
     */
    private truncateIfNeeded(text: string): string {
        const lines = text.split('\n');
        if (lines.length <= this.maxContextLines) {
            return text;
        }
        
        // Take first half and last half of the maximum allowed lines
        const halfMax = Math.floor(this.maxContextLines / 2);
        const firstHalf = lines.slice(0, halfMax);
        const secondHalf = lines.slice(lines.length - halfMax);
        
        return [...firstHalf, '...', ...secondHalf].join('\n');
    }
    
    /**
     * Configure the context manager
     * @param maxLines Maximum lines to include in document context
     */
    public configure(maxLines: number): void {
        this.maxContextLines = maxLines;
    }
    
    /**
     * Dispose resources
     */
    public dispose(): void {
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
        this.disposables = [];
    }
}

/**
 * VS Code context manager for Gemini integration
 */
export class VSCodeContextManager implements vscode.Disposable {
    private disposables: vscode.Disposable[] = [];
    private defaultOptions: ContextCollectionOptions = {
        includeGit: true,
        includeOpenFiles: true,
        includeWorkspaceFolders: true,
        includeRecentFiles: true,
        maxRecentFiles: 10,
        maxGitCommits: 5
    };
    
    /**
     * Create a new VSCodeContextManager
     */
    constructor() {
        // Nothing to initialize here
    }
    
    /**
     * Collect context from VS Code
     * 
     * @param options Context collection options
     */
    public async collectContext(
        options: Partial<ContextCollectionOptions> = {}
    ): Promise<VSCodeContext> {
        // Merge options with defaults
        const mergedOptions: ContextCollectionOptions = {
            ...this.defaultOptions,
            ...options
        };
        
        // Collect editor context
        const editorContext = await this.collectEditorContext();
        
        // Collect workspace context
        const workspaceContext = await this.collectWorkspaceContext(mergedOptions);
        
        // Collect git context if enabled
        let gitContext: GitContext | undefined;
        if (mergedOptions.includeGit) {
            gitContext = await this.collectGitContext(mergedOptions);
        }
        
        return {
            editor: editorContext,
            workspace: workspaceContext,
            git: gitContext
        };
    }
    
    /**
     * Collect context from the editor
     */
    private async collectEditorContext(): Promise<EditorContext> {
        const activeEditor = vscode.window.activeTextEditor;
        const visibleEditors = vscode.window.visibleTextEditors;
        
        // Get current file context if there's an active editor
        let currentFile: EditorContext['currentFile'] | undefined;
        let cursorPosition: vscode.Position | undefined;
        let documentText = '';
        let fileName = undefined;
        let languageId = undefined;
        let lineCount = 0;
        let selections: Array<{
            start: vscode.Position;
            end: vscode.Position;
            text: string;
        }> = [];
        
        if (activeEditor) {
            const document = activeEditor.document;
            const selection = activeEditor.selection;
            
            documentText = document.getText();
            fileName = document.fileName;
            languageId = document.languageId;
            lineCount = document.lineCount;
            
            // Get all selections
            selections = activeEditor.selections.map(sel => ({
                start: sel.start,
                end: sel.end,
                text: document.getText(new vscode.Range(sel.start, sel.end))
            }));
            
            currentFile = {
                path: document.fileName,
                language: document.languageId,
                content: document.getText(),
                selectionRange: selection && !selection.isEmpty ? selection : undefined,
                selectionText: selection && !selection.isEmpty ? document.getText(selection) : undefined
            };
            
            cursorPosition = activeEditor.selection.active;
        }
        
        // Get visible files
        const visibleFiles = visibleEditors.map(editor => ({
            path: editor.document.fileName,
            language: editor.document.languageId,
            isActive: editor === activeEditor
        }));
        
        return {
            documentText,
            selections,
            fileName,
            languageId,
            lineCount,
            currentFile,
            visibleFiles,
            cursorPosition
        };
    }
    
    /**
     * Collect context from the workspace
     * 
     * @param options Context collection options
     */
    private async collectWorkspaceContext(options: ContextCollectionOptions): Promise<WorkspaceContext> {
        const workspaceFolders: string[] = options.includeWorkspaceFolders ?
            (vscode.workspace.workspaceFolders?.map(folder => folder.uri.fsPath) || []) : [];
        
        // Get root path
        const rootPath = workspaceFolders.length > 0 ? workspaceFolders[0] : undefined;
        
        // Get open files
        const openFiles: string[] = options.includeOpenFiles ?
            vscode.workspace.textDocuments
                .filter(doc => !doc.isUntitled && doc.uri.scheme === 'file')
                .map(doc => doc.fileName) : [];
        
        // Get recent files (mock implementation)
        const recentFiles: string[] = options.includeRecentFiles ?
            await this.getRecentFiles(options.maxRecentFiles) : [];
        
        return {
            rootPath,
            workspaceFolders,
            openFiles,
            recentFiles
        };
    }
    
    /**
     * Get a list of recent files
     * 
     * @param maxFiles Maximum number of files to return
     */
    private async getRecentFiles(maxFiles: number): Promise<string[]> {
        // In a real implementation, this would use the VS Code API to get recent files
        // For mock purposes, we'll return open files
        return vscode.workspace.textDocuments
            .filter(doc => !doc.isUntitled && doc.uri.scheme === 'file')
            .map(doc => doc.fileName)
            .slice(0, maxFiles);
    }
    
    /**
     * Collect Git context for the workspace
     * 
     * @param options Context collection options
     */
    private async collectGitContext(options: ContextCollectionOptions): Promise<GitContext | undefined> {
        // This is a mock implementation
        // In a real implementation, this would use the Git extension API or spawn git commands
        
        const rootFolder = vscode.workspace.workspaceFolders?.[0];
        if (!rootFolder) {
            return undefined;
        }
        
        // Use the maxGitCommits option to limit the number of commits returned
        const recentCommitsCount = Math.min(options.maxGitCommits, 10);
        
        // Mock Git data
        return {
            branch: 'main',
            uncommittedChanges: [
                {
                    file: 'src/services/gemini/vscode-context-manager.ts',
                    status: 'modified'
                }
            ],
            recent: {
                commits: Array.from({ length: recentCommitsCount }, (_, i) => ({
                    hash: `abc${1234 + i}`,
                    message: i === 0 ? 'Added VS Code context manager' : `Mock commit ${i}`,
                    author: 'Developer',
                    date: new Date().toISOString()
                }))
            }
        };
    }
    
    /**
     * Get file content
     * 
     * @param filePath Path to the file
     */
    public async getFileContent(filePath: string): Promise<string | undefined> {
        try {
            // Try to get from open documents first
            const doc = vscode.workspace.textDocuments.find(doc => 
                doc.fileName === filePath);
            
            if (doc) {
                return doc.getText();
            }
            
            // Otherwise read from disk
            return fs.promises.readFile(filePath, 'utf-8');
        } catch (error) {
            console.error(`Error reading file ${filePath}:`, error);
            return undefined;
        }
    }
    
    /**
     * Find files in the workspace
     * 
     * @param pattern The glob pattern to match
     * @param exclude The glob pattern to exclude
     */
    public async findFiles(pattern: string, exclude?: string): Promise<vscode.Uri[]> {
        return vscode.workspace.findFiles(pattern, exclude);
    }
    
    /**
     * Process the collected context for the Gemini model
     * This formats the context in a way that's most useful for the model
     * 
     * @param context The collected VS Code context
     */
    public processContextForModel(context: VSCodeContext): string {
        // Build a formatted context string for the model
        let result = '';
        
        // Add current file info
        if (context.editor.currentFile) {
            const file = context.editor.currentFile;
            result += `Current file: ${file.path} (${file.language})\n\n`;
            
            if (file.selectionText) {
                result += `Selected code:\n\`\`\`${file.language}\n${file.selectionText}\n\`\`\`\n\n`;
            } else {
                // Include truncated file content (first 1000 chars) if no selection
                const truncatedContent = file.content.length > 1000 
                    ? file.content.substring(0, 1000) + '...' 
                    : file.content;
                result += `File content:\n\`\`\`${file.language}\n${truncatedContent}\n\`\`\`\n\n`;
            }
        }
        
        // Add workspace info
        if (context.workspace.rootPath) {
            result += `Workspace root: ${context.workspace.rootPath}\n`;
        }
        
        // Add Git info
        if (context.git) {
            result += `\nGit branch: ${context.git.branch}\n`;
            
            if (context.git.uncommittedChanges.length > 0) {
                result += 'Uncommitted changes:\n';
                context.git.uncommittedChanges.forEach(change => {
                    result += `- ${change.file} (${change.status})\n`;
                });
            }
        }
        
        return result;
    }
    
    /**
     * Dispose the context manager
     */
    public dispose(): void {
        // Dispose all disposables
        this.disposables.forEach(d => d.dispose());
        this.disposables = [];
    }
} 