/**
 * Character Prefix Code Completion Demo - TypeScript
 * 
 * This file demonstrates how to use the Character Prefix Code Completion extension
 * with both OpenAI and Gemini models for TypeScript code.
 * 
 * Instructions:
 * 1. Position your cursor at the end of a line with '// Complete:'
 * 2. Press Ctrl+Shift+P to open the command palette
 * 3. Type 'Character Prefix' and select 'Character Prefix: Complete with Prefix'
 * 4. Enter the suggested character prefix 
 * 5. Compare results between OpenAI and Gemini models
 */

// DEMO 1: TypeScript Interface
// Complete: interface User {
// Suggested prefix: "interface User {"

// DEMO 2: Arrow Function
// Complete: const calculateTotal = (items: number[]): number => {
// Suggested prefix: "const calculateTotal = (items: number[]): number => {"

// DEMO 3: Class with Generic Type
// Complete: class DataStore<T> implements 
// Suggested prefix: "class DataStore<T> implements "

// DEMO 4: React Component 
// Complete: function UserProfile({ user }: { user: User }): JSX.Element {
// Suggested prefix: "function UserProfile({ user }: { user: User }): JSX.Element {"

// DEMO 5: Async Function with Error Handling
// Complete: async function fetchData(url: string): Promise<
// Suggested prefix: "async function fetchData(url: string): Promise<" 