// --- MCP Availability Check ---

class MCPChecker {
    static async checkMCPAvailability() {
        try {
            // Try to fetch basic system info to check if MCP is available
            const response = await fetch('/api/system-info');
            
            if (response.ok) {
                const data = await response.json();
                // MCP is available - show success notification
                NotificationManager.success(`Connected to MCP. System: ${data.os_name}`, 5000);
                
                // Apply matrix effect to terminal elements
                document.querySelectorAll('.terminal, .terminal-output').forEach(el => {
                    el.classList.add('matrix-bg');
                });
                
                // Add neon class to important elements
                document.querySelectorAll('h1, h2, h3').forEach(el => {
                    el.classList.add('neon-text');
                });
                
                return true;
            } else {
                throw new Error('MCP responded with status: ' + response.status);
            }
        } catch (error) {
            // MCP is not available - show warning notification
            NotificationManager.warning('MCP connection unavailable. Limited functionality.', 8000);
            console.warn('MCP check failed:', error);
            return false;
        }
    }
    
    static enhanceUIWithMCPFeatures() {
        // Apply fancy effects to MCP-related UI components
        document.querySelectorAll('[data-mcp-feature]').forEach(element => {
            element.classList.add('border-glow');
            
            // Add cyberpunk tooltip
            const featureName = element.getAttribute('data-mcp-feature');
            element.setAttribute('data-tooltip', `Enhanced MCP Feature: ${featureName}`);
            
            // Add click effect
            element.addEventListener('click', () => {
                AnimationManager.addGlitchAnimation(element);
            });
        });
    }
    
    static disableUnavailableFeatures() {
        // Find and disable UI elements that require MCP
        document.querySelectorAll('[data-requires-mcp="true"]').forEach(element => {
            element.classList.add('disabled');
            element.setAttribute('data-tooltip', 'Requires MCP connection');
            
            // If it's a button or link, disable click
            if (element.tagName === 'BUTTON' || element.tagName === 'A') {
                element.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    NotificationManager.warning('This feature requires active MCP connection');
                    AnimationManager.addShakeAnimation(element);
                });
            }
        });
    }
}

// Initialize on document load
document.addEventListener('DOMContentLoaded', async () => {
    // Check MCP connection with a small delay to let other systems initialize
    setTimeout(async () => {
        const mcpAvailable = await MCPChecker.checkMCPAvailability();
        
        if (mcpAvailable) {
            MCPChecker.enhanceUIWithMCPFeatures();
        } else {
            MCPChecker.disableUnavailableFeatures();
        }
    }, 2000);
}); 