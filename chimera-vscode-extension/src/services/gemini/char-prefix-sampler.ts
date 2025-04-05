import * as vscode from 'vscode';
import { GeminiTokenizerService, Token } from './tokenizer-service';

/**
 * CharacterPrefixSampler - Analyzes the probability distribution of tokens after given prefixes.
 * 
 * This service is useful for:
 * - Analyzing how the model predicts tokens after different character prefixes
 * - Understanding tokenization patterns for different character sequences
 * - Exploring common completions for different character contexts
 */
export class CharacterPrefixSampler implements vscode.Disposable {
    private readonly disposables: vscode.Disposable[] = [];
    
    constructor(private readonly tokenizer: GeminiTokenizerService) {}
    
    /**
     * Sample tokens that follow the given character prefix
     * @param prefix The character prefix to analyze
     * @param count Number of top tokens to return
     * @returns A Promise resolving to an array of predicted tokens with probabilities
     */
    public async sampleNextTokens(prefix: string, count: number = 10): Promise<Token[]> {
        if (!this.tokenizer.isReady) {
            throw new Error('Tokenizer service is not ready');
        }
        
        // Generate the top predicted tokens after the prefix
        const tokens = await this.tokenizer.generateNextTokens(prefix, count);
        
        return tokens;
    }
    
    /**
     * Sample a single next token based on the context
     * @param context The current text context
     * @param temperature The sampling temperature (0-1)
     * @returns A Promise resolving to the next token
     */
    public async sampleNextToken(context: string, temperature: number = 0.7): Promise<Token> {
        if (!this.tokenizer.isReady) {
            throw new Error('Tokenizer service is not ready');
        }
        
        // Get next token predictions
        const tokens = await this.tokenizer.generateNextTokens(context, 10);
        
        if (tokens.length === 0) {
            throw new Error('No token predictions available');
        }
        
        // If temperature is very low, just return the top token
        if (temperature < 0.01) {
            return tokens[0];
        }
        
        // Apply temperature to adjust probabilities
        // Higher temperature = more randomness
        const totalProb = tokens.reduce((sum, token) => sum + (token.probability || 0), 0);
        let cumulativeProb = 0;
        
        // Adjust probabilities based on temperature
        const adjustedTokens = tokens.map(token => {
            const prob = Math.pow((token.probability || 0) / totalProb, 1 / temperature);
            cumulativeProb += prob;
            return {
                ...token,
                cumulativeProb
            };
        });
        
        // Normalize the cumulative probabilities
        for (const token of adjustedTokens) {
            token.cumulativeProb! /= cumulativeProb;
        }
        
        // Sample based on the adjusted probabilities
        const random = Math.random();
        for (const token of adjustedTokens) {
            if (random <= token.cumulativeProb!) {
                return token;
            }
        }
        
        // Fallback to the highest probability token
        return tokens[0];
    }
    
    /**
     * Generate a sequence of tokens based on the prompt
     * @param prompt The initial prompt text
     * @param maxTokens Maximum number of tokens to generate
     * @param temperature The sampling temperature (0-1)
     * @returns A Promise resolving to an array of generated tokens
     */
    public async generateTokens(
        prompt: string,
        maxTokens: number = 100,
        temperature: number = 0.7
    ): Promise<Token[]> {
        if (!this.tokenizer.isReady) {
            throw new Error('Tokenizer service is not ready');
        }
        
        const generatedTokens: Token[] = [];
        let currentContext = prompt;
        
        // Generate tokens one by one
        for (let i = 0; i < maxTokens; i++) {
            try {
                // Sample the next token
                const nextToken = await this.sampleNextToken(currentContext, temperature);
                
                // Add to results
                generatedTokens.push(nextToken);
                
                // Update context
                currentContext += nextToken.text;
                
            } catch (error) {
                console.error('Error generating token:', error);
                break;
            }
        }
        
        return generatedTokens;
    }
    
    /**
     * Analyze probabilities for multiple character prefixes and compare them
     * @param prefixes Array of character prefixes to analyze
     * @param count Number of top tokens to return for each prefix
     * @returns A Promise resolving to a map of prefix -> predicted tokens
     */
    public async compareCharacterPrefixes(
        prefixes: string[], 
        count: number = 5
    ): Promise<Map<string, Token[]>> {
        if (!this.tokenizer.isReady) {
            throw new Error('Tokenizer service is not ready');
        }
        
        const results = new Map<string, Token[]>();
        
        // Process each prefix
        for (const prefix of prefixes) {
            const tokens = await this.sampleNextTokens(prefix, count);
            results.set(prefix, tokens);
        }
        
        return results;
    }
    
    /**
     * Find common completions across different prefixes
     * @param prefixes Array of character prefixes to analyze
     * @param count Number of common tokens to return
     * @returns A Promise resolving to an array of common predicted tokens
     */
    public async findCommonCompletions(
        prefixes: string[], 
        count: number = 10
    ): Promise<Token[]> {
        if (!this.tokenizer.isReady) {
            throw new Error('Tokenizer service is not ready');
        }
        
        // Get predictions for each prefix
        const allPredictions = await this.compareCharacterPrefixes(prefixes, count * 2);
        
        // Track token text and aggregated scores
        const tokenScores: Map<string, { count: number, avgProb: number, tokenIds: number[] }> = new Map();
        
        // Process all predictions
        for (const tokens of allPredictions.values()) {
            for (const token of tokens) {
                const probability = token.probability || 0;
                const existingData = tokenScores.get(token.text);
                
                if (existingData) {
                    // Update existing entry
                    existingData.count++;
                    existingData.avgProb = (existingData.avgProb * (existingData.count - 1) + probability) / existingData.count;
                    if (!existingData.tokenIds.includes(token.id)) {
                        existingData.tokenIds.push(token.id);
                    }
                } else {
                    // Create new entry
                    tokenScores.set(token.text, {
                        count: 1,
                        avgProb: probability,
                        tokenIds: [token.id]
                    });
                }
            }
        }
        
        // Sort tokens by occurrence count and then by average probability
        const sortedTokens = Array.from(tokenScores.entries())
            .sort((a, b) => {
                // First sort by count (descending)
                if (b[1].count !== a[1].count) {
                    return b[1].count - a[1].count;
                }
                // Then by probability (descending)
                return b[1].avgProb - a[1].avgProb;
            })
            .slice(0, count)
            .map(([text, data]) => ({
                id: data.tokenIds[0], // Use the first token ID
                text,
                probability: data.avgProb
            }));
        
        return sortedTokens;
    }
    
    /**
     * Analyze how character combinations affect tokenization
     * @param baseText The base text to analyze
     * @param chars Array of characters to append to the base text
     * @returns A Promise resolving to an analysis of tokenization patterns
     */
    public async analyzeCharacterCombinations(
        baseText: string, 
        chars: string[]
    ): Promise<{ character: string, tokenCount: number, tokens: Token[] }[]> {
        if (!this.tokenizer.isReady) {
            throw new Error('Tokenizer service is not ready');
        }
        
        const results: { character: string, tokenCount: number, tokens: Token[] }[] = [];
        
        // First, tokenize the base text
        const baseResult = await this.tokenizer.tokenize(baseText);
        
        // Then tokenize each combination
        for (const char of chars) {
            const combinedText = baseText + char;
            const combinedResult = await this.tokenizer.tokenize(combinedText);
            
            results.push({
                character: char,
                tokenCount: combinedResult.tokens.length,
                tokens: combinedResult.tokens
            });
        }
        
        // Sort by token count (ascending)
        return results.sort((a, b) => a.tokenCount - b.tokenCount);
    }
    
    /**
     * Dispose resources
     */
    public dispose(): void {
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }
} 