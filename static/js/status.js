/**
 * status.js - Handles status updates and refreshing for the AI Dashboard
 */

// Status refresh function
function refreshStatus() {
    fetch('/api/status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Update the status card
            const statusHtml = `
                <div class="provider-status provider-${data.current_provider}">
                    <h5>
                        <span class="status-indicator status-active"></span>
                        Current Provider: <strong>${data.current_provider.toUpperCase()}</strong>
                    </h5>
                    <p class="mb-1">Model: <span class="badge bg-info">${data.current_model}</span></p>
                    ${data.current_provider === 'openrouter' ? `
                        <p class="mb-1">Active Key: <code class="api-key-masked">${data.active_key}</code></p>
                        <p class="mb-1">Last Used: ${data.last_used ? new Date(data.last_used).toLocaleString() : 'Never'}</p>
                        <p class="mb-1">Error Count: <span class="badge ${data.error_count > 0 ? 'bg-danger' : 'bg-success'}"><i class="fas ${data.error_count > 0 ? 'fa-exclamation-triangle' : 'fa-check'}"></i> ${data.error_count}</span></p>
                        <p class="mb-0">Keys: <span class="badge bg-primary">${data.active_keys}/${data.total_keys}</span> active</p>
                    ` : ''}
                    ${data.current_provider === 'ollama' ? `
                        <p class="mb-0">Running locally on your machine</p>
                    ` : ''}
                    ${data.current_provider === 'phind' ? `
                        <p class="mb-0">Running in browser</p>
                    ` : ''}
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">Last checked: ${new Date(data.last_check).toLocaleString()}</small>
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="auto-rotate-switch" ${data.auto_rotate ? 'checked' : ''}>
                        <label class="form-check-label" for="auto-rotate-switch">Auto-rotate</label>
                    </div>
                </div>
            `;
            
            document.getElementById('status-card').innerHTML = statusHtml;
            
            // Set up the auto-rotate switch
            document.getElementById('auto-rotate-switch').addEventListener('change', function(e) {
                updateAutoRotate(e.target.checked);
            });
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            ErrorHandler.showError(
                document.getElementById('status-card'),
                `Error fetching status: ${error.message}`,
                refreshStatus
            );
        });
}

// Recent logs refresh function
function refreshRecentLogs() {
    // Show loading indicator
    const logsContainer = document.getElementById('recent-logs');
    if (logsContainer) {
        ErrorHandler.showLoading(logsContainer, 'Loading logs...', true);
    }
    
    fetch('/api/logs?limit=10')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Check if there's an error flag in the response
            if (data.error) {
                throw new Error(data.logs && data.logs.length > 0 ? data.logs[0] : 'Unknown error');
            }
            
            const logs = data.logs || [];
            
            let logsHtml = '';
            
            if (logs.length === 0) {
                ErrorHandler.showEmptyState(logsContainer, 'No recent logs');
                return;
            } else {
                logs.forEach(log => {
                    const logClass = log.includes('ERROR') ? 'log-error' : 
                                    log.includes('WARNING') ? 'log-warning' : 'log-info';
                    
                    logsHtml += `<div class="log-entry ${logClass}">${log}</div>`;
                });
            }
            
            if (logsContainer) {
                logsContainer.innerHTML = logsHtml;
                // Scroll to the bottom of the logs
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
            if (logsContainer) {
                ErrorHandler.showError(
                    logsContainer,
                    `Error fetching logs: ${error.message}`,
                    refreshRecentLogs,
                    'Retry'
                );
            }
        });
}

// Helper function to update auto-rotate setting
function updateAutoRotate(enabled) {
    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ auto_rotate: enabled })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error updating auto-rotate setting:', data.error);
            showStatusModal('Error', `Failed to update auto-rotate setting: ${data.error}`);
        } else {
            console.log('Auto-rotate setting updated successfully');
        }
    })
    .catch(error => {
        console.error('Error updating auto-rotate setting:', error);
        showStatusModal('Error', `Failed to update auto-rotate setting: ${error.message}`);
    });
}