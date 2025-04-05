import * as vscode from 'vscode';
// Use require syntax for axios to avoid TypeScript esModuleInterop issues
const axios = require('axios');

// Define a more compatible interface that matches the actual axios implementation
interface AxiosResponse<T = any> {
    status: number;
    data: T;
}

/**
 * Status of the MCP connection
 */
export type McpConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'error';

/**
 * Event fired when the MCP connection status changes
 */
export interface McpStatusChangeEvent {
    status: McpConnectionStatus;
    details?: string;
}

/**
 * Manages connection to the MCP server
 */
export class McpConnection implements vscode.Disposable {
    private status: McpConnectionStatus = 'disconnected';
    private statusDetails?: string;
    private url: string = 'http://localhost:8000/mcp';
    private authRequired: boolean = false;
    private username: string = '';
    private apiKey: string = '';
    private client: any; // Use any type for axios client to avoid type conflicts
    
    private readonly _onStatusChanged = new vscode.EventEmitter<McpStatusChangeEvent>();
    public readonly onStatusChanged = this._onStatusChanged.event;
    
    private disposables: vscode.Disposable[] = [];
    
    /**
     * Create a new MCP connection
     */
    constructor() {
        this.client = axios.create({
            timeout: 5000
        });
        
        // Add the event emitter to disposables
        this.disposables.push(this._onStatusChanged);
        
        // Load settings from VS Code configuration
        this.loadConfiguration();
    }
    
    /**
     * Load configuration from VS Code settings
     */
    private loadConfiguration(): void {
        const config = vscode.workspace.getConfiguration('chimera');
        
        const url = config.get<string>('mcpUrl');
        if (url) {
            this.url = url;
        }
        
        const authRequired = config.get<boolean>('authRequired');
        if (authRequired !== undefined) {
            this.authRequired = authRequired;
            
            if (this.authRequired) {
                const username = config.get<string>('username');
                if (username) {
                    this.username = username;
                }
                
                // Load API key from secrets storage
                vscode.commands.executeCommand<string | undefined>('chimera.loadApiKey')
                    .then((apiKey) => {
                        if (apiKey) {
                            this.apiKey = apiKey;
                        }
                    });
            }
        }
    }
    
    /**
     * Get the current connection status
     */
    public getStatus(): McpConnectionStatus {
        return this.status;
    }
    
    /**
     * Get the current connection status details
     */
    public getStatusDetails(): string | undefined {
        return this.statusDetails;
    }
    
    /**
     * Set the MCP server URL
     * 
     * @param url The URL of the MCP server
     */
    public setUrl(url: string): void {
        this.url = url;
    }
    
    /**
     * Set whether authentication is required
     * 
     * @param required Whether authentication is required
     */
    public setAuthRequired(required: boolean): void {
        this.authRequired = required;
    }
    
    /**
     * Set the credentials for MCP authentication
     * 
     * @param username The username
     * @param apiKey The API key
     */
    public setCredentials(username: string, apiKey: string): void {
        this.username = username;
        this.apiKey = apiKey;
    }
    
    /**
     * Update the connection status and fire an event
     * 
     * @param status The new status
     * @param details Optional status details
     */
    private updateStatus(status: McpConnectionStatus, details?: string): void {
        this.status = status;
        this.statusDetails = details;
        
        // Fire the status changed event
        this._onStatusChanged.fire({
            status,
            details
        });
    }
    
    /**
     * Get the headers for API requests
     */
    private getHeaders(): Record<string, string> {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json'
        };
        
        if (this.authRequired && this.username && this.apiKey) {
            headers['X-MCP-Username'] = this.username;
            headers['X-MCP-API-Key'] = this.apiKey;
        }
        
        return headers;
    }
    
    /**
     * Connect to the MCP server
     */
    public async connect(): Promise<boolean> {
        try {
            this.updateStatus('connecting', 'Connecting to MCP server...');
            
            const response = await this.client.get(`${this.url}/status`, {
                headers: this.getHeaders()
            });
            
            if (response.status === 200 && response.data?.status === 'ok') {
                this.updateStatus('connected', `Connected to MCP server at ${this.url}`);
                return true;
            } else {
                this.updateStatus('error', `Failed to connect: ${response.data?.message || 'Unknown error'}`);
                return false;
            }
        } catch (error: any) {
            this.updateStatus('error', `Connection error: ${error.message || 'Unknown error'}`);
            return false;
        }
    }
    
    /**
     * Disconnect from the MCP server
     */
    public disconnect(): void {
        this.updateStatus('disconnected', 'Disconnected from MCP server');
    }
    
    /**
     * Test a connection to the MCP server
     * 
     * @param url The URL to test
     * @param authRequired Whether authentication is required
     * @param username The username (if auth required)
     * @param apiKey The API key (if auth required)
     */
    public async testConnection(
        url: string,
        authRequired: boolean,
        username?: string,
        apiKey?: string
    ): Promise<string> {
        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json'
            };
            
            if (authRequired && username && apiKey) {
                headers['X-MCP-Username'] = username;
                headers['X-MCP-API-Key'] = apiKey;
            }
            
            const response = await axios.get(`${url}/status`, {
                headers,
                timeout: 5000
            });
            
            // Type check: ensure response.data is an object with a status property
            const responseData = response.data as {status?: string; message?: string} | null;
            
            if (response.status === 200 && responseData && responseData.status === 'ok') {
                return 'Connection successful';
            } else {
                throw new Error(responseData?.message || 'Unknown error');
            }
        } catch (error: any) {
            throw new Error(`Connection failed: ${error.message || 'Unknown error'}`);
        }
    }
    
    /**
     * Send a command to the MCP server
     * 
     * @param command The command to send
     * @param data The command data
     */
    public async sendCommand<T>(command: string, data?: any): Promise<T> {
        try {
            if (this.status !== 'connected') {
                // Try to connect first
                const connected = await this.connect();
                if (!connected) {
                    throw new Error('Not connected to MCP server');
                }
            }
            
            const response = await this.client.post(`${this.url}/command`, {
                command,
                data
            }, {
                headers: this.getHeaders()
            });
            
            if (response.status === 200) {
                return response.data as T;
            } else {
                const errorMessage = (response.data as {message?: string})?.message || 'Unknown error';
                throw new Error(errorMessage);
            }
        } catch (error: any) {
            this.updateStatus('error', `Command error: ${error.message || 'Unknown error'}`);
            throw error;
        }
    }
    
    /**
     * Check if the connection is currently connected
     */
    public isConnected(): boolean {
        return this.status === 'connected';
    }

    /**
     * Get the current MCP server URL
     */
    public getUrl(): string {
        return this.url;
    }

    /**
     * Check if authentication is required
     */
    public isAuthRequired(): boolean {
        return this.authRequired;
    }

    /**
     * Get information about the MCP server
     */
    public async getMcpInfo(): Promise<Record<string, string>> {
        try {
            if (this.status !== 'connected') {
                throw new Error('Not connected to MCP server');
            }
            
            const response = await this.client.get(`${this.url}/info`, {
                headers: this.getHeaders()
            });
            
            if (response.status === 200) {
                return response.data as Record<string, string>;
            } else {
                const errorMessage = (response.data as {message?: string})?.message || 'Unknown error';
                throw new Error(errorMessage);
            }
        } catch (error: any) {
            throw new Error(`Failed to get MCP info: ${error.message || 'Unknown error'}`);
        }
    }
    
    /**
     * Dispose the MCP connection
     */
    public dispose(): void {
        // Dispose all disposables
        this.disposables.forEach(d => d.dispose());
        this.disposables = [];
    }
} 