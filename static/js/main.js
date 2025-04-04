document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initThemeToggle();
    initParticles();
    initClipboard();
    initCodeEditor();
    initCollapsibles();
    initBubbles();
    initTooltips();
    initDragAndDrop();
    initRealTimeStatus();
    initKeyboardShortcuts();
    initTabSwitching();
    initNotifications();
    initAnimations();
    
    // Log initialization
    console.log('Enhanced Developer Toolkit initialized successfully!');
});

/**
 * Initialize the theme toggle functionality
 */
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    
    // Check for saved theme preference or use system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme based on saved preference or system preference
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        htmlElement.classList.add('dark');
    } else {
        htmlElement.classList.remove('dark');
    }
    
    // Handle theme toggle clicks
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            htmlElement.classList.toggle('dark');
            
        // Save preference
            localStorage.setItem('theme', 
                htmlElement.classList.contains('dark') ? 'dark' : 'light'
            );
            
            // Advanced effect on toggle
            const lightning = document.createElement('div');
            lightning.classList.add('theme-switch-flash');
            document.body.appendChild(lightning);
            
            setTimeout(() => {
                lightning.remove();
            }, 500);
        });
    }
}

/**
 * Initialize the particles.js library for background effects
 */
function initParticles() {
    if (window.particlesJS && document.getElementById('particles-js')) {
        particlesJS('particles-js', {
            "particles": {
                "number": { "value": 40, "density": { "enable": true, "value_area": 800 } },
                "color": { "value": "#4ade80" },
                "shape": { "type": "circle" },
                "opacity": { "value": 0.5, "random": true },
                "size": { "value": 3, "random": true },
                "line_linked": {
                    "enable": true,
                    "distance": 150,
                    "color": "#4ade80",
                    "opacity": 0.2,
                    "width": 1
                },
                "move": {
                    "enable": true,
                    "speed": 1,
                    "direction": "none",
                    "random": true,
                    "straight": false,
                    "out_mode": "out",
                    "bounce": false
                }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": { "enable": true, "mode": "repulse" },
                    "onclick": { "enable": true, "mode": "push" },
                    "resize": true
                }
            },
            "retina_detect": true
        });
    }
}

/**
 * Initialize clipboard functionality for copy buttons
 */
function initClipboard() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.dataset.clipboardTarget;
            const target = document.querySelector(targetId);
            
            if (target) {
                // Create a temporary textarea element to copy from
                const textarea = document.createElement('textarea');
                textarea.value = target.textContent;
                textarea.setAttribute('readonly', '');
                textarea.style.position = 'absolute';
                textarea.style.left = '-9999px';
                document.body.appendChild(textarea);
                
                // Select and copy the text
                textarea.select();
                document.execCommand('copy');
                
                // Clean up
                document.body.removeChild(textarea);
                
                // Visual feedback
                const icon = this.querySelector('i');
                const originalClass = icon.className;
                icon.className = 'bi bi-check';
                
                    setTimeout(() => {
                    icon.className = originalClass;
                    }, 2000);
                
                // Show notification
                showNotification('Copied to clipboard', 'success');
            }
        });
    });
}

/**
 * Initialize the code editor with syntax highlighting and analysis
 */
function initCodeEditor() {
    const codeInput = document.getElementById('code-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const aiOutput = document.getElementById('ai-output');

    if (codeInput && analyzeBtn && aiOutput) {
        // Set up event listener for the analyze button
        analyzeBtn.addEventListener('click', function() {
            const code = codeInput.value.trim();
            
            if (!code) {
                showNotification('Please enter some code first', 'warning');
                return;
            }

            // Start loading state
            const btnText = document.getElementById('analyze-btn-text');
            const spinner = document.getElementById('analyze-spinner');
            
            if (btnText) btnText.textContent = 'ANALYZING...';
            if (spinner) spinner.classList.remove('hidden');
            
            analyzeBtn.disabled = true;
            
            // Simulated Tesla effect
            document.body.classList.add('tesla-flash');
            setTimeout(() => {
                document.body.classList.remove('tesla-flash');
            }, 300);
            
            // Make the actual analysis request
            fetch('/analyze', {
                    method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code }) 
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();
            })
            .then(html => {
                // Display the analysis result
                aiOutput.innerHTML = html;
                
                // Apply syntax highlighting to code blocks in the response
                if (window.Prism) {
                    Prism.highlightAllUnder(aiOutput);
                }

                // Reset button state
                if (btnText) btnText.textContent = 'TRANSMUTE CODE';
                if (spinner) spinner.classList.add('hidden');
                analyzeBtn.disabled = false;
                
                // Animation effect on the output
                aiOutput.classList.add('animate__animated', 'animate__fadeIn');
                setTimeout(() => {
                    aiOutput.classList.remove('animate__animated', 'animate__fadeIn');
                }, 1000);
            })
            .catch(error => {
                console.error('Error analyzing code:', error);
                aiOutput.innerHTML = `<div class="p-3 rounded bg-red-500/10 dark:bg-red-500/20 border border-red-500/30">
                    <h4 class="font-semibold text-red-700 dark:text-red-300 mb-1 flex items-center gap-2">
                        <i class="bi bi-exclamation-triangle"></i>
                        <span>Analysis Error</span>
                    </h4>
                    <p class="text-sm text-red-600 dark:text-red-400 mb-1">${error.message}</p>
                </div>`;
                
                // Reset button state
                if (btnText) btnText.textContent = 'TRANSMUTE CODE';
                if (spinner) spinner.classList.add('hidden');
                analyzeBtn.disabled = false;
            });
        });
    }
}

/**
 * Initialize collapsible sections
 */
function initCollapsibles() {
    const collapsibles = document.querySelectorAll('.collapsible-trigger');
    
    collapsibles.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const expanded = this.getAttribute('aria-expanded') === 'true';
            const targetId = this.getAttribute('aria-controls');
            const targetPanel = document.getElementById(targetId);
            const chevron = this.querySelector('.bi-chevron-down');
            
            if (targetPanel) {
                if (expanded) {
                    // Collapse
                    targetPanel.classList.add('hidden');
                    this.setAttribute('aria-expanded', 'false');
                    if (chevron) chevron.classList.remove('rotate-180');
                } else {
                    // Expand
                    targetPanel.classList.remove('hidden');
                    this.setAttribute('aria-expanded', 'true');
                    if (chevron) chevron.classList.add('rotate-180');
                }
            }
        });
    });
}

/**
 * Initialize bubbling beaker effect
 */
function initBubbles() {
    const beakers = document.querySelectorAll('.bubbling-beaker');
    
    beakers.forEach(beaker => {
        const bubblesContainer = document.createElement('div');
        bubblesContainer.classList.add('bubbles-container');
        beaker.appendChild(bubblesContainer);
        
        // Create bubbles
        for (let i = 0; i < 15; i++) {
            const bubble = document.createElement('div');
            bubble.classList.add('bubble');
            bubble.style.left = `${Math.random() * 100}%`;
            bubble.style.width = `${Math.random() * 10 + 5}px`;
            bubble.style.height = bubble.style.width;
            bubble.style.animationDelay = `${Math.random() * 4}s`;
            bubble.style.animationDuration = `${Math.random() * 4 + 3}s`;
            bubblesContainer.appendChild(bubble);
        }
    });
}

/**
 * Initialize tooltips
 */
function initTooltips() {
    const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
    
    tooltipTriggers.forEach(trigger => {
        trigger.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.classList.add('tooltip');
            tooltip.textContent = this.dataset.tooltip;
            
            // Position the tooltip
            document.body.appendChild(tooltip);
            const triggerRect = this.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            
            tooltip.style.top = `${triggerRect.top - tooltipRect.height - 10}px`;
            tooltip.style.left = `${triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2)}px`;
            
            // Add animation class
            setTimeout(() => tooltip.classList.add('tooltip-visible'), 10);
            
            // Store reference to the tooltip
            this._tooltip = tooltip;
        });
        
        trigger.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.classList.remove('tooltip-visible');
                setTimeout(() => {
                    if (this._tooltip && this._tooltip.parentNode) {
                        this._tooltip.parentNode.removeChild(this._tooltip);
                    }
                    this._tooltip = null;
                }, 300);
            }
        });
    });
}

/**
 * Initialize drag and drop for the code editor
 */
function initDragAndDrop() {
    const codeInput = document.getElementById('code-input');
    
    if (codeInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            codeInput.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            codeInput.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            codeInput.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            codeInput.classList.add('border-toxic-500', 'dark:border-toxic-400');
        }
        
        function unhighlight() {
            codeInput.classList.remove('border-toxic-500', 'dark:border-toxic-400');
        }
        
        codeInput.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length) {
                const file = files[0];
                const reader = new FileReader();
                
                reader.readAsText(file);
                reader.onloadend = function() {
                    codeInput.value = reader.result;
                    showNotification(`File "${file.name}" loaded successfully`, 'success');
                };
            }
        }
    }
}

/**
 * Initialize real-time MCP connection status checking
 */
function initRealTimeStatus() {
    // Periodic connection check (every 10 seconds)
    const statusInterval = setInterval(checkMCPStatus, 10000);
    checkMCPStatus(); // Initial check
    
    function checkMCPStatus() {
        const statusElement = document.getElementById('mcp-status');
        
        if (!statusElement) return;
        
        fetch('/api/mcp-status', { method: 'GET' })
            .then(response => response.json())
            .then(data => {
                if (data.connected) {
                    statusElement.innerHTML = '<span class="text-green-500"><i class="bi bi-check-circle-fill"></i> Connected</span>';
                } else {
                    statusElement.innerHTML = '<span class="text-red-500"><i class="bi bi-x-circle-fill"></i> Disconnected</span>';
                }
            })
            .catch(() => {
                statusElement.innerHTML = '<span class="text-yellow-500"><i class="bi bi-question-circle-fill"></i> Unknown</span>';
            });
    }
}

/**
 * Initialize keyboard shortcuts
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to analyze code
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const analyzeBtn = document.getElementById('analyze-btn');
            if (analyzeBtn && !analyzeBtn.disabled) {
                analyzeBtn.click();
                e.preventDefault();
            }
        }
        
        // Ctrl/Cmd + / to toggle theme
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            const themeToggle = document.getElementById('theme-toggle');
            if (themeToggle) {
                themeToggle.click();
                e.preventDefault();
            }
        }
    });
}

/**
 * Initialize tab switching functionality
 */
function initTabSwitching() {
    const tabTriggers = document.querySelectorAll('[data-tab]');
    const tabContents = document.querySelectorAll('[data-tab-content]');
    
    tabTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Update active state on triggers
            tabTriggers.forEach(t => {
                if (t.getAttribute('data-tab') === tabId) {
                    t.classList.add('active-tab');
                } else {
                    t.classList.remove('active-tab');
                }
            });
            
            // Show/hide tab contents
            tabContents.forEach(content => {
                if (content.getAttribute('data-tab-content') === tabId) {
                    content.classList.remove('hidden');
                } else {
                    content.classList.add('hidden');
                }
            });
        });
    });
}

/**
 * Show a notification message
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, warning, error, info)
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.classList.add('notification', `notification-${type}`);
    
    // Icon based on type
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    if (type === 'error') icon = 'x-circle';
    
    // Set content
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="bi bi-${icon}"></i>
        </div>
        <div class="notification-content">
            ${message}
        </div>
        <button class="notification-close">
            <i class="bi bi-x"></i>
        </button>
    `;
    
    // Add to DOM
    const container = document.getElementById('notification-container') || createNotificationContainer();
    container.appendChild(notification);
    
    // Auto-remove after delay
    setTimeout(() => {
        notification.classList.add('notification-hide');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            
            // Remove container if empty
            if (container.children.length === 0) {
                container.parentNode.removeChild(container);
            }
        }, 500);
    }, 5000);
    
    // Close button
    const closeBtn = notification.querySelector('.notification-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            notification.classList.add('notification-hide');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                
                // Remove container if empty
                if (container.children.length === 0) {
                    container.parentNode.removeChild(container);
                }
            }, 500);
        });
    }
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('notification-show');
    }, 10);
}

/**
 * Create a container for notifications
 */
function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notification-container';
    document.body.appendChild(container);
    return container;
} 