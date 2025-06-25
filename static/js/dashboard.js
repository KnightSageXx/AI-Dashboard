/**
 * AI Control Dashboard JavaScript
 * Main entry point that initializes all dashboard functionality
 */

// Auto-refresh status every 30 seconds
let statusRefreshInterval;

// Initialize the dashboard
function initDashboard() {
    // Initial load
    refreshStatus();
    refreshApiKeys();
    refreshRecentLogs();
    
    // Set up event handlers
    setupEventHandlers();
    
    // Set up auto-refresh
    statusRefreshInterval = setInterval(function() {
        refreshStatus();
        refreshApiKeys();
        refreshRecentLogs();
    }, 30000); // 30 seconds
}

// Set up event handlers for all buttons and inputs
function setupEventHandlers() {
    // OpenRouter Actions
    document.getElementById('btn-rotate-key')?.addEventListener('click', rotateApiKey);
    document.getElementById('btn-test-key')?.addEventListener('click', testApiKey);
    document.getElementById('btn-switch-openrouter')?.addEventListener('click', switchToOpenRouter);
    
    // Fallback Actions
    document.getElementById('btn-switch-ollama')?.addEventListener('click', switchToOllama);
    document.getElementById('btn-switch-phind')?.addEventListener('click', launchPhind);
    
    // Advanced Actions
    document.getElementById('btn-temp-email')?.addEventListener('click', createTempEmail);
    
    // API Key Management
    document.getElementById('btn-add-key')?.addEventListener('click', addApiKey);
    
    // Add key on Enter key press
    document.getElementById('new-api-key')?.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            addApiKey();
        }
    });
    
    // Model Selector
    document.getElementById('model-selector')?.addEventListener('change', function() {
        updateModel(this.value);
    });
}

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the dashboard page
    if (document.getElementById('status-card')) {
        initDashboard();
    }
    
    // Check if we're on the logs page
    if (document.getElementById('full-logs')) {
        initLogsPage();
    }
});