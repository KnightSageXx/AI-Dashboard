/**
 * actions.js - Handles provider switching and other actions for the AI Dashboard
 */

// Switch to OpenRouter provider
function switchToOpenRouter() {
    showStatusModal('Switching Provider', 'Switching to OpenRouter...');
    
    fetch('/api/switch/openrouter', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshStatus();
        }
    })
    .catch(error => {
        console.error('Error switching to OpenRouter:', error);
        ErrorHandler.showToast(`Failed to switch to OpenRouter: ${error.message}`, 'error');
        showStatusModal('Error', `Failed to switch to OpenRouter: ${error.message}`);
    });
}

// Switch to Ollama provider
function switchToOllama() {
    showStatusModal('Switching Provider', 'Switching to Ollama...');
    
    fetch('/api/switch/ollama', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshStatus();
        }
    })
    .catch(error => {
        console.error('Error switching to Ollama:', error);
        ErrorHandler.showToast(`Failed to switch to Ollama: ${error.message}`, 'error');
        showStatusModal('Error', `Failed to switch to Ollama: ${error.message}`);
    });
}

// Launch Phind in browser
function launchPhind() {
    showStatusModal('Switching Provider', 'Launching Phind in browser...');
    
    fetch('/api/launch/phind', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            showStatusModal('Error', data.error);
        } else {
            showStatusModal('Success', data.message);
            refreshStatus();
        }
    })
    .catch(error => {
        console.error('Error launching Phind:', error);
        ErrorHandler.showToast(`Failed to launch Phind: ${error.message}`, 'error');
        showStatusModal('Error', `Failed to launch Phind: ${error.message}`);
    });
}

// Create Temp Email and get new OpenRouter API key
function createTempEmail() {
    showStatusModal('Creating Account', 'Starting browser automation to create a new OpenRouter account. This may take a few minutes...');
    
    fetch('/api/temp_email', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
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
        console.error('Error creating temp email:', error);
        ErrorHandler.showToast(`Failed to create temp email: ${error.message}`, 'error');
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
        console.error('Error updating model:', error);
        ErrorHandler.showToast(`Failed to update model: ${error.message}`, 'error');
        showStatusModal('Error', `Failed to update model: ${error.message}`);
    });
}

/**
 * Show a status modal with the given title and message
 * @param {string} title - The modal title
 * @param {string} message - The modal message
 * @param {Function} onClose - Optional callback when modal is closed
 * @param {boolean} useHtml - Whether to use HTML content for the message
 */
function showStatusModal(title, message, onClose, useHtml = false) {
    // Determine the modal type based on the title
    let type = 'info';
    if (title.toLowerCase().includes('error')) {
        type = 'error';
    } else if (title.toLowerCase().includes('success')) {
        type = 'success';
    } else if (title.toLowerCase().includes('warning')) {
        type = 'warning';
    }
    
    // Use the modalManager to show the modal
    modalManager.open({
        title: title,
        message: message,
        type: type,
        useHtml: useHtml,
        onClose: onClose
    });
}