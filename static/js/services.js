// --- API Service Classes ---

class CodeAnalysisService {
    static async analyzeCode(filePath) {
        try {
            const response = await fetch('/api/analyze-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path: filePath }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error analyzing code:', error);
            throw error;
        }
    }
}

class TerminalService {
    static async executeCommand(command, cwd = null) {
        try {
            const response = await fetch('/api/execute-command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command, cwd }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error executing command:', error);
            throw error;
        }
    }
}

class FileSystemService {
    static async listDirectory(path) {
        try {
            const response = await fetch('/api/list-directory', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error listing directory:', error);
            throw error;
        }
    }

    static async readFile(path) {
        try {
            const response = await fetch('/api/read-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error reading file:', error);
            throw error;
        }
    }

    static async writeFile(path, content) {
        try {
            const response = await fetch('/api/write-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path, content }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error writing file:', error);
            throw error;
        }
    }
}

class GitService {
    static async getStatus(path = '.') {
        try {
            const response = await fetch('/api/git-operations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ operation: 'status', path }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error getting git status:', error);
            throw error;
        }
    }

    static async getBranches(path = '.') {
        try {
            const response = await fetch('/api/git-operations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ operation: 'branch', path }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error getting git branches:', error);
            throw error;
        }
    }

    static async getLog(path = '.') {
        try {
            const response = await fetch('/api/git-operations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ operation: 'log', path }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error getting git log:', error);
            throw error;
        }
    }
}

class ProjectMetricsService {
    static async getMetrics(path = '.') {
        try {
            const response = await fetch(`/api/project-metrics?path=${encodeURIComponent(path)}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error getting project metrics:', error);
            throw error;
        }
    }
}

class SystemInfoService {
    static async getInfo() {
        try {
            const response = await fetch('/api/system-info');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error getting system info:', error);
            throw error;
        }
    }
}

// --- UI Update Functions ---

function updateCodeAnalysis(filePath) {
    CodeAnalysisService.analyzeCode(filePath)
        .then(data => {
            // Update code analysis UI
            const issuesList = document.getElementById('issues-list');
            const metricsList = document.getElementById('metrics-list');
            
            // Clear existing content
            issuesList.innerHTML = '';
            metricsList.innerHTML = '';
            
            // Add issues
            data.issues.forEach(issue => {
                const issueElement = document.createElement('div');
                issueElement.className = `alert alert-${issue.type === 'warning' ? 'warning' : 'info'}`;
                issueElement.textContent = `Line ${issue.line}: ${issue.message}`;
                issuesList.appendChild(issueElement);
            });
            
            // Add metrics
            Object.entries(data.metrics).forEach(([key, value]) => {
                const metricElement = document.createElement('div');
                metricElement.className = 'metric-item';
                metricElement.innerHTML = `<strong>${key}:</strong> ${value}`;
                metricsList.appendChild(metricElement);
            });
        })
        .catch(error => {
            console.error('Error updating code analysis:', error);
            // Show error in UI
            const errorElement = document.createElement('div');
            errorElement.className = 'alert alert-danger';
            errorElement.textContent = `Error analyzing code: ${error.message}`;
            document.getElementById('issues-list').appendChild(errorElement);
        });
}

function updateTerminal(command) {
    TerminalService.executeCommand(command)
        .then(data => {
            // Update terminal UI
            const terminalOutput = document.getElementById('terminal-output');
            const outputLine = document.createElement('div');
            outputLine.className = 'terminal-line';
            outputLine.innerHTML = `
                <span class="prompt">$</span>
                <span class="command">${data.command}</span>
                <div class="output">${data.stdout}</div>
                ${data.stderr ? `<div class="error">${data.stderr}</div>` : ''}
            `;
            terminalOutput.appendChild(outputLine);
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        })
        .catch(error => {
            console.error('Error executing command:', error);
            // Show error in UI
            const terminalOutput = document.getElementById('terminal-output');
            const errorLine = document.createElement('div');
            errorLine.className = 'terminal-line error';
            errorLine.textContent = `Error: ${error.message}`;
            terminalOutput.appendChild(errorLine);
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        });
}

function updateFileSystem(path) {
    FileSystemService.listDirectory(path)
        .then(data => {
            // Update file system UI
            const fileList = document.getElementById('file-list');
            fileList.innerHTML = '';
            
            data.items.forEach(item => {
                const itemElement = document.createElement('div');
                itemElement.className = `file-item ${item.type}`;
                itemElement.innerHTML = `
                    <i class="bi ${item.type === 'directory' ? 'bi-folder' : 'bi-file'}"></i>
                    <span class="name">${item.name}</span>
                    ${item.size ? `<span class="size">${formatSize(item.size)}</span>` : ''}
                    <span class="modified">${formatDate(item.modified)}</span>
                `;
                fileList.appendChild(itemElement);
            });
        })
        .catch(error => {
            console.error('Error listing directory:', error);
            // Show error in UI
            const fileList = document.getElementById('file-list');
            const errorElement = document.createElement('div');
            errorElement.className = 'alert alert-danger';
            errorElement.textContent = `Error listing directory: ${error.message}`;
            fileList.appendChild(errorElement);
        });
}

function updateGitStatus(path) {
    GitService.getStatus(path)
        .then(data => {
            // Update git status UI
            const statusList = document.getElementById('git-status-list');
            statusList.innerHTML = '';
            
            // Add branch info
            const branchElement = document.createElement('div');
            branchElement.className = 'git-branch';
            branchElement.innerHTML = `<i class="bi bi-git"></i> Branch: ${data.branch}`;
            statusList.appendChild(branchElement);
            
            // Add changes
            data.changes.forEach(change => {
                const changeElement = document.createElement('div');
                changeElement.className = 'git-change';
                changeElement.innerHTML = `
                    <span class="status">${change.status}</span>
                    <span class="file">${change.file}</span>
                `;
                statusList.appendChild(changeElement);
            });
        })
        .catch(error => {
            console.error('Error getting git status:', error);
            // Show error in UI
            const statusList = document.getElementById('git-status-list');
            const errorElement = document.createElement('div');
            errorElement.className = 'alert alert-danger';
            errorElement.textContent = `Error getting git status: ${error.message}`;
            statusList.appendChild(errorElement);
        });
}

function updateProjectMetrics(path) {
    ProjectMetricsService.getMetrics(path)
        .then(data => {
            // Update project metrics UI
            const metricsContainer = document.getElementById('project-metrics');
            metricsContainer.innerHTML = `
                <div class="metric-group">
                    <h4>Files and Directories</h4>
                    <p>Total Files: ${data.files}</p>
                    <p>Total Directories: ${data.directories}</p>
                    <p>Total Lines: ${data.total_lines}</p>
                </div>
                <div class="metric-group">
                    <h4>Languages</h4>
                    ${Object.entries(data.languages).map(([ext, stats]) => `
                        <p>${ext}: ${stats.files} files, ${stats.lines} lines</p>
                    `).join('')}
                </div>
                <div class="metric-group">
                    <h4>Largest Files</h4>
                    ${data.largest_files.map(file => `
                        <p>${file.path}: ${formatSize(file.size)}, ${file.lines} lines</p>
                    `).join('')}
                </div>
            `;
        })
        .catch(error => {
            console.error('Error getting project metrics:', error);
            // Show error in UI
            const metricsContainer = document.getElementById('project-metrics');
            const errorElement = document.createElement('div');
            errorElement.className = 'alert alert-danger';
            errorElement.textContent = `Error getting project metrics: ${error.message}`;
            metricsContainer.appendChild(errorElement);
        });
}

function updateSystemInfo() {
    SystemInfoService.getInfo()
        .then(data => {
            // Update system info UI
            const systemInfo = document.getElementById('system-info');
            systemInfo.innerHTML = `
                <div class="info-group">
                    <h4>System</h4>
                    <p>Platform: ${data.platform}</p>
                    <p>Python Version: ${data.python_version}</p>
                    <p>CPU Cores: ${data.cpu_count}</p>
                </div>
                <div class="info-group">
                    <h4>Memory</h4>
                    <p>Total: ${formatSize(data.memory_total)}</p>
                    <p>Available: ${formatSize(data.memory_available)}</p>
                </div>
                <div class="info-group">
                    <h4>Disk</h4>
                    ${Object.entries(data.disk_usage).map(([path, usage]) => `
                        <p>${path}: ${formatSize(usage.total)} total, ${formatSize(usage.free)} free (${usage.percent}% used)</p>
                    `).join('')}
                </div>
            `;
        })
        .catch(error => {
            console.error('Error getting system info:', error);
            // Show error in UI
            const systemInfo = document.getElementById('system-info');
            const errorElement = document.createElement('div');
            errorElement.className = 'alert alert-danger';
            errorElement.textContent = `Error getting system info: ${error.message}`;
            systemInfo.appendChild(errorElement);
        });
}

// --- Utility Functions ---

function formatSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// --- Event Listeners ---

document.addEventListener('DOMContentLoaded', () => {
    // Initialize UI with current data
    updateSystemInfo();
    updateProjectMetrics();
    
    // Set up event listeners for UI interactions
    const terminalInput = document.getElementById('terminal-input');
    if (terminalInput) {
        terminalInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                const command = terminalInput.value.trim();
                if (command) {
                    updateTerminal(command);
                    terminalInput.value = '';
                }
            }
        });
    }
    
    const filePathInput = document.getElementById('file-path-input');
    if (filePathInput) {
        filePathInput.addEventListener('change', () => {
            updateCodeAnalysis(filePathInput.value);
        });
    }
    
    const gitRefreshButton = document.getElementById('git-refresh');
    if (gitRefreshButton) {
        gitRefreshButton.addEventListener('click', () => {
            updateGitStatus();
        });
    }
}); 