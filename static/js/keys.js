/**
 * keys.js - Handles API key management for the AI Dashboard
 */

// API Keys refresh function
function refreshApiKeys() {
    // We'll use the config data from the server to populate this
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.current_provider === 'openrouter') {
                // Make another request to get the full config with all keys
                return fetch('/api/status?full=true')
                    .then(response => response.json());
            }
            return data;
        })
        .then(data => {
            // Get the API keys from the config
            const apiKeys = data.providers?.openrouter?.api_keys || [];
            
            // Build the table rows
            let tableHtml = '';
            
            if (apiKeys.length === 0) {
                tableHtml = `
                    <tr>
                        <td colspan="5" class="text-center">No API keys found</td>
                    </tr>
                `;
            } else {
                apiKeys.forEach(key => {
                    // Mask the key for display
                    const keyStr = key.key;
                    let maskedKey = '';
                    if (keyStr.length > 8) {
                        maskedKey = `${keyStr.substring(0, 4)}...${keyStr.substring(keyStr.length - 4)}`;
                    } else {
                        maskedKey = '****';
                    }
                    
                    tableHtml += `
                        <tr>
                            <td><code class="api-key-masked">${maskedKey}</code></td>
                            <td>
                                <span class="status-indicator ${key.is_active ? 'status-active' : 'status-inactive'}"></span>
                                ${key.is_active ? 'Active' : 'Inactive'}
                            </td>
                            <td>${key.last_used ? new Date(key.last_used).toLocaleString() : 'Never'}</td>
                            <td>
                                <span class="badge ${key.error_count > 0 ? 'bg-danger' : 'bg-success'}">
                                    ${key.error_count}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary me-1 btn-activate-key" data-key="${keyStr}" ${key.is_active ? 'disabled' : ''}>
                                    <i class="fas fa-check"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger btn-remove-key" data-key="${keyStr}" ${key.is_active ? 'disabled' : ''}>
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                });
            }
            
            document.getElementById('api-keys-table').innerHTML = tableHtml;
            
            // Set up event handlers for the new buttons
            document.querySelectorAll('.btn-activate-key').forEach(button => {
                button.addEventListener('click', function() {
                    activateKey(this.getAttribute('data-key'));
                });
            });
            
            document.querySelectorAll('.btn-remove-key').forEach(button => {
                button.addEventListener('click', function() {
                    removeKey(this.getAttribute('data-key'));
                });
            });
        })
        .catch(error => {
            console.error('Error fetching API keys:', error);
            document.getElementById('api-keys-table').innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-danger">
                        Error fetching API keys: ${error.message}
                    </td>
                </tr>
            `;
        });
}

// Add a new API key
function addApiKey() {
    const apiKeyInput = document.getElementById('new-api-key');
    const apiKey = apiKeyInput.value.trim();
    
    if (!apiKey) {
        showStatusModal('Error', 'Please enter an API key');
        return;
    }
    
    // Validate API key format (sk-or-xxxxx)
    if (!validateApiKey(apiKey)) {
        showStatusModal('Error', 'Invalid API key format. Key should start with "sk-or-"');
        return;
    }
    
    showStatusModal('Adding API Key', 'Please wait...');
    
    fetch('/api/add_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ key: apiKey })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            apiKeyInput.value = '';
            refreshApiKeys();
            refreshStatus(); // Update the status display
        }
    })
    .catch(error => {
        showStatusModal('Error', `Failed to add API key: ${error.message}`);
    });
}

// Validate API key format
function validateApiKey(key) {
    return key.startsWith('sk-or-');
}

// Rotate to the next API key
function rotateApiKey() {
    showStatusModal('Rotating API Key', 'Please wait...');
    
    fetch('/api/rotate', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshStatus();
            refreshApiKeys();
        }
    })
    .catch(error => {
        showStatusModal('Error', `Failed to rotate API key: ${error.message}`);
    });
}

// Test the current API key
function testApiKey() {
    showStatusModal('Testing API Key', 'Please wait...');
    
    fetch('/api/test', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal(data.success ? 'Success' : 'Error', data.message);
            refreshStatus();
        }
    })
    .catch(error => {
        showStatusModal('Error', `Failed to test API key: ${error.message}`);
    });
}

// Helper function to activate a specific key
function activateKey(apiKey) {
    showStatusModal('Activating Key', 'Please wait...');
    
    fetch('/api/activate_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ key: apiKey })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshStatus();
            refreshApiKeys();
        }
    })
    .catch(error => {
        showStatusModal('Error', `Failed to activate key: ${error.message}`);
    });
}

// Helper function to remove a key
function removeKey(apiKey) {
    if (!confirm('Are you sure you want to remove this API key?')) {
        return;
    }
    
    showStatusModal('Removing Key', 'Please wait...');
    
    fetch('/api/remove_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ key: apiKey })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshApiKeys();
            refreshStatus(); // Update the status display
        }
    })
    .catch(error => {
        showStatusModal('Error', `Failed to remove key: ${error.message}`);
    });
}