/**
 * App Manager
 * Main application functionality and initialization
 */
const AppManager = {
    /**
     * Initialize the application
     */
    init() {
        // Set up connection status check
        this.setupConnectionCheck();
        // Initialize UI components
        this.initUI();
        // Set up event handlers
        this.bindEvents();
        
        console.log('Enhanced Developer\'s Toolkit initialized');
    },

    /**
     * Initialize UI components
     */
    initUI() {
        // Show the main content
        this.showMainContent();
        
        // Initialize the navigation
        this.initNavigation();
    },

    /**
     * Set up periodic MCP connection check
     */
    setupConnectionCheck() {
        // Check for MCP connection status indicator
        const connectionStatus = document.getElementById('connection-status');
        if (connectionStatus) {
            // Initial check
            this.checkMCPConnection();
            
            // Schedule periodic checks
            setInterval(() => this.checkMCPConnection(), 5000);
        }
    },

    /**
     * Check MCP connection status
     */
    checkMCPConnection() {
        const connectionStatus = document.getElementById('connection-status');
        if (!connectionStatus) return;
        
        fetch('/mcp-status')
            .then(response => response.json())
            .then(data => {
                if (data.connected) {
                    connectionStatus.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i> Connected';
                    connectionStatus.classList.remove('text-danger');
                    connectionStatus.classList.add('text-success');
                } else {
                    connectionStatus.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i> Disconnected';
                    connectionStatus.classList.remove('text-success');
                    connectionStatus.classList.add('text-danger');
                }
            })
            .catch(() => {
                connectionStatus.innerHTML = '<i class="bi bi-exclamation-triangle-fill text-warning"></i> Unknown';
                connectionStatus.classList.remove('text-success', 'text-danger');
                connectionStatus.classList.add('text-warning');
            });
    },

    /**
     * Initialize navigation elements
     */
    initNavigation() {
        // Set up navigation handling
        const navLinks = document.querySelectorAll('.nav-link');
        if (navLinks.length > 0) {
            navLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    const target = e.currentTarget.getAttribute('href');
                    if (target && target.startsWith('#')) {
                        e.preventDefault();
                        this.navigateTo(target.substring(1));
                    }
                });
            });
            
            // Load the initial view based on hash
            const hash = window.location.hash.substring(1) || 'dashboard';
            this.navigateTo(hash);
        }
    },

    /**
     * Navigate to a specific view
     * @param {string} viewId - ID of the view to navigate to
     */
    navigateTo(viewId) {
        // Update the URL hash
        window.location.hash = viewId;
        
        // Highlight active navigation item
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            const linkTarget = link.getAttribute('href');
            if (linkTarget === `#${viewId}`) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
        
        // Load the view content
        this.loadView(viewId);
    },

    /**
     * Load a view into the main content area
     * @param {string} viewId - ID of the view to load
     */
    loadView(viewId) {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) return;
        
        // Show loading state
        mainContent.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Loading ${viewId}...</p>
            </div>
        `;
        
        // Fetch the view content
        fetch(`/${viewId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load ${viewId}`);
                }
                return response.text();
            })
            .then(html => {
                mainContent.innerHTML = html;
                // Initialize view-specific features
                this.initView(viewId);
            })
            .catch(error => {
                console.error(`Error loading view ${viewId}:`, error);
                mainContent.innerHTML = `
                    <div class="alert alert-danger m-5" role="alert">
                        <h4 class="alert-heading">Error Loading View</h4>
                        <p>Failed to load the ${viewId} view. Please try again later.</p>
                        <hr>
                        <p class="mb-0">${error.message}</p>
                    </div>
                `;
            });
    },

    /**
     * Initialize view-specific features
     * @param {string} viewId - ID of the view
     */
    initView(viewId) {
        // Initialize specific view functionality based on ID
        switch (viewId) {
            case 'dashboard':
                this.initDashboard();
                break;
            case 'code-analysis':
                this.initCodeAnalysis();
                break;
            case 'terminal':
                this.initTerminal();
                break;
            case 'git':
                this.initGit();
                break;
            case 'settings':
                this.initSettings();
                break;
            default:
                // No specific initialization needed
                break;
        }
    },

    /**
     * Initialize dashboard view
     */
    initDashboard() {
        // Dashboard-specific initialization
        console.log('Dashboard view initialized');
        
        // Fetch system info for dashboard
        this.fetchSystemInfo();
    },

    /**
     * Fetch system information for the dashboard
     */
    fetchSystemInfo() {
        const systemInfoContainer = document.getElementById('system-info');
        if (!systemInfoContainer) return;
        
        fetch('/system-info')
            .then(response => response.json())
            .then(data => {
                // Update system info UI
                if (data) {
                    let html = '<div class="card-body">';
                    html += '<h5 class="card-title">System Information</h5>';
                    html += '<ul class="list-group list-group-flush">';
                    
                    if (data.hostname) {
                        html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                            Hostname <span class="badge bg-primary rounded-pill">${data.hostname}</span>
                        </li>`;
                    }
                    
                    if (data.python_version) {
                        html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                            Python Version <span class="badge bg-primary rounded-pill">${data.python_version.split(' ')[0]}</span>
                        </li>`;
                    }
                    
                    if (data.cpu_percent !== undefined) {
                        html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                            CPU Usage <span class="badge bg-primary rounded-pill">${data.cpu_percent}%</span>
                        </li>`;
                    }
                    
                    if (data.memory_percent !== undefined) {
                        html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                            Memory Usage <span class="badge bg-primary rounded-pill">${data.memory_percent.toFixed(1)}%</span>
                        </li>`;
                    }
                    
                    if (data.limited_info) {
                        html += `<li class="list-group-item">
                            <div class="alert alert-warning mb-0 py-2" role="alert">
                                <small>${data.limited_info}</small>
                            </div>
                        </li>`;
                    }
                    
                    html += '</ul></div>';
                    systemInfoContainer.innerHTML = html;
                }
            })
            .catch(error => {
                console.error('Error fetching system info:', error);
                systemInfoContainer.innerHTML = `
                    <div class="card-body">
                        <div class="alert alert-danger mb-0" role="alert">
                            Failed to load system information
                        </div>
                    </div>
                `;
            });
    },

    /**
     * Initialize code analysis view
     */
    initCodeAnalysis() {
        console.log('Code Analysis view initialized');
        // Code analysis view-specific initialization
    },

    /**
     * Initialize terminal view
     */
    initTerminal() {
        console.log('Terminal view initialized');
        // Terminal view-specific initialization
    },

    /**
     * Initialize git view
     */
    initGit() {
        console.log('Git view initialized');
        // Git view-specific initialization
    },

    /**
     * Initialize settings view
     */
    initSettings() {
        console.log('Settings view initialized');
        
        // Get setting form elements
        const settingsForm = document.getElementById('settings-form');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings(new FormData(settingsForm));
            });
        }
    },

    /**
     * Save user settings
     * @param {FormData} formData - Form data from settings form
     */
    saveSettings(formData) {
        // Convert FormData to JSON object
        const settings = {};
        for (const [key, value] of formData.entries()) {
            settings[key] = value === 'on' ? true : value;
        }
        
        // Save settings via API
        fetch('/save-settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success notification
                if (typeof showNotification === 'function') {
                    showNotification('Settings saved successfully', 'success');
                } else {
                    alert('Settings saved successfully');
                }
            } else {
                throw new Error(data.error || 'Failed to save settings');
            }
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            // Show error notification
            if (typeof showNotification === 'function') {
                showNotification('Failed to save settings: ' + error.message, 'error');
            } else {
                alert('Failed to save settings: ' + error.message);
            }
        });
    },

    /**
     * Show the main content (hide loading screen)
     */
    showMainContent() {
        const loadingScreen = document.getElementById('loading-screen');
        const mainContainer = document.getElementById('main-container');
        
        if (loadingScreen) {
            loadingScreen.classList.add('fade-out');
            setTimeout(() => {
                loadingScreen.style.display = 'none';
                if (mainContainer) {
                    mainContainer.classList.add('fade-in');
                }
            }, 500);
        }
    },

    /**
     * Set up global event handlers
     */
    bindEvents() {
        // Handle window resize
        window.addEventListener('resize', () => {
            // Adjust UI for responsive layout if needed
        });
        
        // Handle connection retry
        const retryButton = document.getElementById('retry-connection');
        if (retryButton) {
            retryButton.addEventListener('click', () => {
                this.checkMCPConnection();
            });
        }
    }
};

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    if (typeof AppManager !== 'undefined') {
        AppManager.init();
    }
}); 