/**
 * logs.js - Handles log viewing and filtering for the AI Dashboard
 */

// Load logs from the server
function loadLogs(logFile = 'status.log', limit = 100) {
    fetch(`/api/logs?file=${logFile}&limit=${limit}`)
        .then(response => response.json())
        .then(data => {
            const logs = data.logs || [];
            const logFiles = data.log_files || [];
            
            // Update log file selector if it exists
            const logFileSelector = document.getElementById('log-file-selector');
            if (logFileSelector) {
                let options = '';
                logFiles.forEach(file => {
                    options += `<option value="${file}" ${file === logFile ? 'selected' : ''}>${file}</option>`;
                });
                logFileSelector.innerHTML = options;
            }
            
            // Update logs container
            const logsContainer = document.getElementById('full-logs');
            if (!logsContainer) return;
            
            if (logs.length === 0) {
                logsContainer.innerHTML = `
                    <div class="text-center p-5">
                        <i class="fas fa-info-circle fa-2x mb-3 text-muted"></i>
                        <p>No logs available.</p>
                    </div>
                `;
            } else {
                let logsHtml = '';
                logs.forEach(log => {
                    const logClass = log.includes('ERROR') ? 'log-error' : 
                                   log.includes('WARNING') ? 'log-warning' : 'log-info';
                    
                    logsHtml += `<div class="log-entry ${logClass}">${log}</div>`;
                });
                logsContainer.innerHTML = logsHtml;
                
                // Scroll to the bottom of the logs
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
            
            // Apply any existing filters
            filterLogs();
        })
        .catch(error => {
            console.error('Error loading logs:', error);
            const logsContainer = document.getElementById('full-logs');
            if (logsContainer) {
                logsContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error loading logs: ${error.message}
                    </div>
                `;
            }
        });
}

// Filter logs based on text input and dropdown selections
function filterLogs() {
    const filterText = document.getElementById('log-filter')?.value.toLowerCase() || '';
    const levelFilter = document.getElementById('log-level-filter')?.value || 'all';
    const componentFilter = document.getElementById('log-component-filter')?.value || 'all';
    
    document.querySelectorAll('.log-entry').forEach(entry => {
        const logText = entry.textContent.toLowerCase();
        const hasFilterText = filterText === '' || logText.includes(filterText);
        const hasLevel = levelFilter === 'all' || entry.textContent.includes(levelFilter);
        const hasComponent = componentFilter === 'all' || entry.textContent.includes(componentFilter);
        
        if (hasFilterText && hasLevel && hasComponent) {
            entry.style.display = '';
        } else {
            entry.style.display = 'none';
        }
    });
}

// Initialize logs page
function initLogsPage() {
    // Get the log file from URL query parameter or use default
    const urlParams = new URLSearchParams(window.location.search);
    const logFile = urlParams.get('file') || 'status.log';
    
    // Load logs
    loadLogs(logFile);
    
    // Set up event handlers
    document.getElementById('btn-refresh-logs')?.addEventListener('click', () => {
        const selectedLogFile = document.getElementById('log-file-selector')?.value || logFile;
        loadLogs(selectedLogFile);
    });
    
    document.getElementById('log-file-selector')?.addEventListener('change', function() {
        loadLogs(this.value);
        // Update URL without reloading the page
        const url = new URL(window.location);
        url.searchParams.set('file', this.value);
        window.history.pushState({}, '', url);
    });
    
    document.getElementById('log-filter')?.addEventListener('input', filterLogs);
    document.getElementById('log-level-filter')?.addEventListener('change', filterLogs);
    document.getElementById('log-component-filter')?.addEventListener('change', filterLogs);
}