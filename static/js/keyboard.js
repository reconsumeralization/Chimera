// --- Keyboard Shortcuts Management ---

class KeyboardManager {
    static init() {
        // Initialize keyboard shortcuts
        this.initializeShortcuts();
        
        // Initialize command palette
        this.initializeCommandPalette();
        
        // Initialize keyboard navigation
        this.initializeNavigation();
    }

    static initializeShortcuts() {
        // Global shortcuts
        document.addEventListener('keydown', (event) => {
            // Check if target is an input or textarea
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                return;
            }

            // Ctrl/Cmd + K: Open command palette
            if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
                event.preventDefault();
                this.openCommandPalette();
            }

            // Ctrl/Cmd + /: Toggle theme
            if ((event.ctrlKey || event.metaKey) && event.key === '/') {
                event.preventDefault();
                ThemeManager.toggle();
            }

            // Ctrl/Cmd + Shift + P: Open settings
            if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'p') {
                event.preventDefault();
                window.location.href = '/settings';
            }

            // Ctrl/Cmd + Shift + D: Open dashboard
            if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'd') {
                event.preventDefault();
                window.location.href = '/dashboard';
            }

            // Ctrl/Cmd + Shift + T: Open terminal
            if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 't') {
                event.preventDefault();
                window.location.href = '/terminal';
            }

            // Ctrl/Cmd + Shift + G: Open git
            if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'g') {
                event.preventDefault();
                window.location.href = '/git';
            }

            // Ctrl/Cmd + Shift + A: Open code analysis
            if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'a') {
                event.preventDefault();
                window.location.href = '/code-analysis';
            }
        });
    }

    static initializeCommandPalette() {
        // Create command palette container if it doesn't exist
        if (!document.getElementById('command-palette')) {
            const container = document.createElement('div');
            container.id = 'command-palette';
            container.className = 'command-palette';
            container.innerHTML = `
                <div class="command-palette-content">
                    <div class="command-palette-header">
                        <input type="text" class="command-palette-input" placeholder="Type a command or search...">
                        <button class="command-palette-close">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                    <div class="command-palette-list"></div>
                </div>
            `;
            document.body.appendChild(container);

            // Add event listeners
            const input = container.querySelector('.command-palette-input');
            const closeButton = container.querySelector('.command-palette-close');
            const list = container.querySelector('.command-palette-list');

            input.addEventListener('input', () => {
                this.filterCommands(input.value);
            });

            input.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') {
                    this.closeCommandPalette();
                }
            });

            closeButton.addEventListener('click', () => {
                this.closeCommandPalette();
            });

            // Initialize commands
            this.commands = [
                {
                    name: 'Toggle Theme',
                    shortcut: 'Ctrl/Cmd + /',
                    action: () => ThemeManager.toggle()
                },
                {
                    name: 'Open Settings',
                    shortcut: 'Ctrl/Cmd + Shift + P',
                    action: () => window.location.href = '/settings'
                },
                {
                    name: 'Open Dashboard',
                    shortcut: 'Ctrl/Cmd + Shift + D',
                    action: () => window.location.href = '/dashboard'
                },
                {
                    name: 'Open Terminal',
                    shortcut: 'Ctrl/Cmd + Shift + T',
                    action: () => window.location.href = '/terminal'
                },
                {
                    name: 'Open Git',
                    shortcut: 'Ctrl/Cmd + Shift + G',
                    action: () => window.location.href = '/git'
                },
                {
                    name: 'Open Code Analysis',
                    shortcut: 'Ctrl/Cmd + Shift + A',
                    action: () => window.location.href = '/code-analysis'
                }
            ];

            // Render initial commands
            this.renderCommands(this.commands);
        }
    }

    static initializeNavigation() {
        // Handle keyboard navigation
        document.addEventListener('keydown', (event) => {
            // Check if target is an input or textarea
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                return;
            }

            // Arrow keys for navigation
            switch (event.key) {
                case 'ArrowLeft':
                    if (event.altKey) {
                        window.history.back();
                    }
                    break;
                case 'ArrowRight':
                    if (event.altKey) {
                        window.history.forward();
                    }
                    break;
            }
        });
    }

    static openCommandPalette() {
        const palette = document.getElementById('command-palette');
        palette.classList.add('active');
        const input = palette.querySelector('.command-palette-input');
        input.value = '';
        input.focus();
    }

    static closeCommandPalette() {
        const palette = document.getElementById('command-palette');
        palette.classList.remove('active');
    }

    static filterCommands(query) {
        const filteredCommands = this.commands.filter(command => 
            command.name.toLowerCase().includes(query.toLowerCase())
        );
        this.renderCommands(filteredCommands);
    }

    static renderCommands(commands) {
        const list = document.querySelector('.command-palette-list');
        list.innerHTML = commands.map(command => `
            <div class="command-palette-item" onclick="KeyboardManager.executeCommand('${command.name}')">
                <span class="command-name">${command.name}</span>
                <span class="command-shortcut">${command.shortcut}</span>
            </div>
        `).join('');
    }

    static executeCommand(name) {
        const command = this.commands.find(cmd => cmd.name === name);
        if (command) {
            command.action();
            this.closeCommandPalette();
        }
    }
}

// --- Initialize Keyboard Manager ---
document.addEventListener('DOMContentLoaded', () => {
    KeyboardManager.init();
}); 