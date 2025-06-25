/**
 * actions.js - Handles provider switching and other actions for the AI Dashboard
 */

// Switch to OpenRouter provider
function switchToOpenRouter() {
    showStatusModal('Switching Provider', 'Switching to OpenRouter...');
    
    fetch('/api/switch/openrouter', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshStatus();
        }
    })
    .catch(error => {
        showStatusModal('Error', `Failed to switch to OpenRouter: ${error.message}`);
    });
}

// Switch to Ollama provider
function switchToOllama() {
    showStatusModal('Switching Provider', 'Switching to Ollama...');
    
    fetch('/api/switch/ollama', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshStatus();
        }
    })
    .catch(error => {
        showStatusModal('Error', `Failed to switch to Ollama: ${error.message}`);
    });
}

// Launch Phind in browser
function launchPhind() {
    showStatusModal('Switching Provider', 'Launching Phind in browser...');
    
    fetch('/api/launch/phind', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshStatus();
        }
    })
    .catch(error => {
        showStatusModal('Error', `Failed to launch Phind: ${error.message}`);
    });
}

// Create Temp Email and get new OpenRouter API key
function createTempEmail() {
    showStatusModal('Creating Account', 'Starting browser automation to create a new OpenRouter account. This may take a few minutes...');
    
    fetch('/api/temp_email', {
        method: 'POST'
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
        showStatusModal('Error', `Failed to create temp email: ${error.message}`);
    });
}

// Update the model selection
function updateModel(modelId) {
    if (!modelId) return;
    
    showStatusModal('Updating Model', 'Please wait...');
    
    fetch('/api/update_model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ model_id: modelId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshStatus();
        }
    })
    .catch(error => {
        showStatusModal('Error', `Failed to update model: ${error.message}`);
    });
}

// Helper function to show status modal
function showStatusModal(title, message) {
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    document.getElementById('statusModalTitle').textContent = title;
    document.getElementById('statusModalBody').textContent = message;
    modal.show();
}