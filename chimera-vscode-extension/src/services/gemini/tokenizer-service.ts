import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Token representation
 */
export interface Token {
    id: number;
    text: string;
    probability?: number; // Optional because not always available
}

/**
 * Tokenization result interface
 */
export interface TokenizationResult {
    tokens: Token[];
    cached: boolean;
}

/**
 * Token cache interface
 */
interface TokenCache {
    [key: string]: Token[];
}

/**
 * Gemini tokenizer wrapper with caching capabilities
 */
export class GeminiTokenizerService implements vscode.Disposable {
    private tokenCache: TokenCache = {};
    private maxCacheItems: number = 1000;
    private cacheEnabled: boolean = true;
    private disposables: vscode.Disposable[] = [];
    private _isReady: boolean = false;
    private mcpProcess?: vscode.Disposable;
    private readonly tokenizerPath: string;

    // For testing/dev mode when tokenizer not available
    private readonly devMode: boolean = false;
    
    // Event emitter for tokenizer ready state
    private readonly _onTokenizerReady = new vscode.EventEmitter<boolean>();
    public readonly onTokenizerReady = this._onTokenizerReady.event;

    constructor(private readonly extensionPath: string) {
        this.tokenizerPath = this.resolveTokenizerPath();
        this.initializeTokenizer();
        
        // Add event emitter to disposables
        this.disposables.push(this._onTokenizerReady);
    }

    /**
     * Resolves the path to the tokenizer binary or script
     */
    private resolveTokenizerPath(): string {
        // Default paths for different platforms
        let binPath = '';
        
        if (process.platform === 'win32') {
            binPath = path.join(this.extensionPath, 'bin', 'tokenizer', 'tokenizer.exe');
        } else if (process.platform === 'darwin') {
            binPath = path.join(this.extensionPath, 'bin', 'tokenizer', 'tokenizer-macos');
        } else {
            binPath = path.join(this.extensionPath, 'bin', 'tokenizer', 'tokenizer-linux');
        }
        
        // Check if the file exists
        if (fs.existsSync(binPath)) {
            return binPath;
        }
        
        // If binary doesn't exist, use Python script
        const scriptPath = path.join(this.extensionPath, 'scripts', 'tokenizer', 'tokenize.py');
        if (fs.existsSync(scriptPath)) {
            return scriptPath;
        }
        
        // If neither exists, enter dev mode
        vscode.window.showWarningMessage('Gemini tokenizer not found. Running in development mode with mock data.');
        return '';
    }

    /**
     * Initialize the tokenizer process
     */
    private async initializeTokenizer(): Promise<void> {
        try {
            if (this.devMode || !this.tokenizerPath) {
                // Mock initialization for dev mode
                this._isReady = true;
                this._onTokenizerReady.fire(true);
                vscode.window.showInformationMessage('Gemini tokenizer initialized in development mode.');
                return;
            }
            
            // Start tokenizer process
            // For now, we'll consider it immediately ready, but in a real implementation
            // you'd need to handle startup and checking if it's responsive
            
            this._isReady = true;
            this._onTokenizerReady.fire(true);
            
            // Log successful initialization
            console.log('Gemini tokenizer initialized successfully');
        } catch (error: unknown) {
            console.error('Failed to initialize Gemini tokenizer:', error);
            const errorMessage = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Failed to initialize Gemini tokenizer: ${errorMessage}`);
            this._onTokenizerReady.fire(false);
        }
    }

    /**
     * Check if the tokenizer service is ready for use
     */
    public get isReady(): boolean {
        return this._isReady;
    }

    /**
     * Configure the tokenizer cache
     */
    public configureCache(enabled: boolean, maxItems: number): void {
        this.cacheEnabled = enabled;
        this.maxCacheItems = maxItems;
        
        // If cache disabled, clear it
        if (!enabled) {
            this.clearCache();
        }
        
        // If max items reduced, trim cache
        if (enabled && Object.keys(this.tokenCache).length > maxItems) {
            this.trimCache();
        }
    }

    /**
     * Clear the tokenizer cache
     */
    public clearCache(): void {
        this.tokenCache = {};
    }

    /**
     * Trim the cache to match the maximum allowed items
     */
    private trimCache(): void {
        const keys = Object.keys(this.tokenCache);
        const itemsToRemove = keys.length - this.maxCacheItems;
        
        if (itemsToRemove <= 0) {
            return;
        }
        
        // Simple approach: remove oldest keys (first entries in the object)
        // A more sophisticated approach might use LRU cache
        const keysToRemove = keys.slice(0, itemsToRemove);
        for (const key of keysToRemove) {
            delete this.tokenCache[key];
        }
    }

    /**
     * Tokenize text into tokens
     */
    public async tokenize(text: string): Promise<TokenizationResult> {
        // Check if service is ready
        if (!this._isReady) {
            throw new Error('Gemini tokenizer service is not ready.');
        }
        
        // Check cache if enabled
        if (this.cacheEnabled && this.tokenCache[text]) {
            return {
                tokens: this.tokenCache[text],
                cached: true
            };
        }
        
        try {
            let tokens: Token[];
            
            if (this.devMode) {
                // Generate mock tokens in dev mode
                tokens = this.generateMockTokens(text);
            } else {
                // Real tokenization logic would go here
                // This would involve calling the MCP tokenizer process
                tokens = await this.callTokenizerProcess(text);
            }
            
            // Cache the result if caching is enabled
            if (this.cacheEnabled) {
                // Check if cache is full
                if (Object.keys(this.tokenCache).length >= this.maxCacheItems) {
                    this.trimCache();
                }
                
                this.tokenCache[text] = tokens;
            }
            
            return {
                tokens,
                cached: false
            };
        } catch (error: unknown) {
            console.error('Tokenization failed:', error);
            const errorMessage = error instanceof Error ? error.message : String(error);
            throw new Error(`Failed to tokenize text: ${errorMessage}`);
        }
    }

    /**
     * Generate likely next tokens given a prompt
     */
    public async generateNextTokens(prompt: string, count: number = 5): Promise<Token[]> {
        // Check if service is ready
        if (!this._isReady) {
            throw new Error('Gemini tokenizer service is not ready.');
        }
        
        try {
            if (this.devMode) {
                // Generate mock next tokens in dev mode
                return this.generateMockNextTokens(prompt, count);
            } else {
                // Real next token prediction logic would go here
                // This would involve calling the MCP tokenizer process with appropriate flags
                return await this.callTokenizerProcessForNextTokens(prompt, count);
            }
        } catch (error: unknown) {
            console.error('Next token prediction failed:', error);
            const errorMessage = error instanceof Error ? error.message : String(error);
            throw new Error(`Failed to predict next tokens: ${errorMessage}`);
        }
    }

    /**
     * Analyze frequency of tokens across multiple samples
     */
    public async analyzeTokenFrequency(samples: string[]): Promise<any> {
        if (!this._isReady) {
            throw new Error('Gemini tokenizer service is not ready.');
        }
        
        try {
            // Tokenize all samples
            const allTokens: Token[][] = [];
            
            for (const sample of samples) {
                const result = await this.tokenize(sample);
                allTokens.push(result.tokens);
            }
            
            // Compute token frequencies
            const tokenFrequency: { [tokenId: number]: { count: number, text: string } } = {};
            let totalTokens = 0;
            
            for (const tokens of allTokens) {
                for (const token of tokens) {
                    if (!tokenFrequency[token.id]) {
                        tokenFrequency[token.id] = { count: 0, text: token.text };
                    }
                    tokenFrequency[token.id].count++;
                    totalTokens++;
                }
            }
            
            // Calculate statistics
            const uniqueTokens = Object.keys(tokenFrequency).length;
            const avgTokensPerSample = totalTokens / samples.length;
            
            // Sort tokens by frequency
            const sortedTokens = Object.entries(tokenFrequency)
                .map(([id, { count, text }]) => ({
                    id: parseInt(id),
                    text,
                    frequency: count,
                    percentage: (count / totalTokens) * 100
                }))
                .sort((a, b) => b.frequency - a.frequency);
            
            // Return the top 50 tokens and summary statistics
            return {
                summary: {
                    sampleCount: samples.length,
                    uniqueTokens,
                    avgTokensPerSample
                },
                topTokens: sortedTokens.slice(0, 50)
            };
        } catch (error: unknown) {
            console.error('Token frequency analysis failed:', error);
            const errorMessage = error instanceof Error ? error.message : String(error);
            throw new Error(`Failed to analyze token frequency: ${errorMessage}`);
        }
    }

    /**
     * Mock implementation for tokenization (dev mode only)
     */
    private generateMockTokens(text: string): Token[] {
        const tokens: Token[] = [];
        const words = text.split(/(\s+|\b|[.,!?;])/g).filter(word => word.length > 0);
        
        let tokenId = 1000; // Starting from arbitrary ID
        
        for (const word of words) {
            tokens.push({
                id: tokenId++,
                text: word,
                probability: Math.random()
            });
        }
        
        return tokens;
    }

    /**
     * Mock implementation for next token prediction (dev mode only)
     */
    private generateMockNextTokens(_unused: string, count: number): Token[] {
        const mockNextTokens: Token[] = [];
        const possibleNextWords = [
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'will', 'would', 
            'could', 'can', 'should', 'may', 'might', 'must', 'have', 'has', 'had'
        ];
        
        for (let i = 0; i < count; i++) {
            const randomIdx = Math.floor(Math.random() * possibleNextWords.length);
            mockNextTokens.push({
                id: 2000 + i,
                text: possibleNextWords[randomIdx],
                probability: Math.random()
            });
        }
        
        // Sort by probability
        return mockNextTokens.sort((a, b) => (b.probability || 0) - (a.probability || 0));
    }

    /**
     * Call the actual tokenizer process
     * In a real implementation, this would use the MCP to invoke the tokenizer
     */
    private async callTokenizerProcess(text: string): Promise<Token[]> {
        // This is a placeholder for the actual implementation
        // In a real implementation, this would call the MCP to tokenize text
        return this.generateMockTokens(text); // For now, use mock implementation
    }

    /**
     * Call the actual tokenizer process for next token prediction
     * In a real implementation, this would use the MCP to get predicted tokens
     */
    private async callTokenizerProcessForNextTokens(prompt: string, count: number): Promise<Token[]> {
        // This is a placeholder for the actual implementation
        // In a real implementation, this would call the MCP to predict next tokens
        return this.generateMockNextTokens(prompt, count); // For now, use mock implementation
    }

    /**
     * Dispose of resources
     */
    public dispose(): void {
        this.mcpProcess?.dispose();
        
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
        
        this.disposables = [];
    }
} 