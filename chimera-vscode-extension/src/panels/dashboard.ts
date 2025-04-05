import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Manages the dashboard webview panel
 */
export class DashboardPanel {
    public static currentPanel: DashboardPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionPath: string;
    private _disposables: vscode.Disposable[] = [];

    /**
     * Get the current panel instance
     */
    public static get instance(): DashboardPanel | undefined {
        return this.currentPanel;
    }

    /**
     * Create or show the dashboard panel
     */
    public static createOrShow(extensionPath: string): DashboardPanel {
        // If we already have a panel, show it
        if (DashboardPanel.currentPanel) {
            DashboardPanel.currentPanel._panel.reveal(vscode.ViewColumn.One);
            return DashboardPanel.currentPanel;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            'chimeraDashboard',
            'Project Chimera Dashboard',
            vscode.ViewColumn.One,
            {
                // Enable JavaScript in the webview
                enableScripts: true,
                
                // Restrict the webview to only load resources from the extension's directory
                localResourceRoots: [
                    vscode.Uri.file(path.join(extensionPath, 'webviews', 'dashboard'))
                ],
                
                // Keep the webview in memory when hidden
                retainContextWhenHidden: true
            }
        );

        DashboardPanel.currentPanel = new DashboardPanel(panel, extensionPath);
        return DashboardPanel.currentPanel;
    }

    /**
     * Create a new Dashboard panel
     */
    private constructor(panel: vscode.WebviewPanel, extensionPath: string) {
        this._panel = panel;
        this._extensionPath = extensionPath;

        // Set the initial HTML content for the webview
        this._updateWebview();

        // Handle messages from the webview
        this._setWebviewMessageListener();

        // Listen for when the panel is disposed
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Update the content if the panel becomes visible
        this._panel.onDidChangeViewState(
            e => {
                if (this._panel.visible) {
                    this._updateWebview();
                }
            },
            null,
            this._disposables
        );
    }

    /**
     * Dispose and clean up the panel's resources
     */
    public dispose() {
        DashboardPanel.currentPanel = undefined;

        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }

    /**
     * Update the webview content
     */
    private _updateWebview() {
        // Get the local path to the webview's HTML file
        const htmlPath = path.join(this._extensionPath, 'webviews', 'dashboard', 'main.html');
        let htmlContent = fs.readFileSync(htmlPath, 'utf8');

        // Get the stylesheet and script URIs
        const styleUri = this._panel.webview.asWebviewUri(
            vscode.Uri.file(path.join(this._extensionPath, 'webviews', 'dashboard', 'style.css'))
        );
        
        const scriptUri = this._panel.webview.asWebviewUri(
            vscode.Uri.file(path.join(this._extensionPath, 'webviews', 'dashboard', 'main.js'))
        );

        // Replace placeholders in the HTML content
        htmlContent = htmlContent
            .replace(/{{{styleUri}}}/g, styleUri.toString())
            .replace(/{{{scriptUri}}}/g, scriptUri.toString());

        this._panel.webview.html = htmlContent;
    }

    /**
     * Set up the webview message listener
     */
    private _setWebviewMessageListener() {
        this._panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'startService':
                        this._startService(message.serviceId);
                        return;
                    
                    case 'stopService':
                        this._stopService(message.serviceId);
                        return;
                    
                    case 'restartService':
                        this._restartService(message.serviceId);
                        return;
                    
                    case 'getServiceStatus':
                        this._getServiceStatus();
                        return;
                    
                    case 'openMcpPanel':
                        this._openMcpPanel();
                        return;
                }
            },
            null,
            this._disposables
        );
    }

    /**
     * Start a service
     */
    private _startService(serviceId: string) {
        // Implementation will be added later
        vscode.window.showInformationMessage(`Starting service: ${serviceId}`);
    }

    /**
     * Stop a service
     */
    private _stopService(serviceId: string) {
        // Implementation will be added later
        vscode.window.showInformationMessage(`Stopping service: ${serviceId}`);
    }

    /**
     * Restart a service
     */
    private _restartService(serviceId: string) {
        // Implementation will be added later
        vscode.window.showInformationMessage(`Restarting service: ${serviceId}`);
    }

    /**
     * Get service status
     */
    private _getServiceStatus() {
        // Simulated service status for now
        const services = [
            { id: 'core', name: 'Core Service', status: 'running' },
            { id: 'mcp', name: 'MCP Server', status: 'stopped' },
            { id: 'api', name: 'API Service', status: 'running' }
        ];

        // Send the status back to the webview
        this._panel.webview.postMessage({
            command: 'serviceStatus',
            services
        });
    }

    /**
     * Open the MCP configuration panel
     */
    private _openMcpPanel() {
        vscode.commands.executeCommand('chimera-dashboard.showMcpPanel');
    }
} 