import * as vscode from 'vscode';
import { CharPrefixExtension } from './CharPrefixExtension';

// This method is called when the extension is activated
export function activate(context: vscode.ExtensionContext): void {
    // Create and activate the extension
    const extension = new CharPrefixExtension();
    
    // Add to subscriptions to ensure proper disposal
    context.subscriptions.push(extension);
    
    // Activate the extension
    extension.activate();
    
    console.log('Character Prefix extension has been activated');
}

// This method is called when the extension is deactivated
export function deactivate(): void {
    console.log('Character Prefix extension has been deactivated');
} 