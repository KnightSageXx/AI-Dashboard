/**
 * api-client.js - Centralized API client for the AI Dashboard
 */

class ApiClient {
    /**
     * Create a new API client instance
     * @param {Object} options - Configuration options
     * @param {string} options.baseUrl - Base URL for API requests (defaults to current origin)
     * @param {number} options.timeout - Request timeout in milliseconds
     */
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || '';
        this.timeout = options.timeout || 30000; // 30 seconds default timeout
    }
    
    /**
     * Make a fetch request with standardized error handling
     * @param {string} endpoint - API endpoint to call
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} - Parsed response data
     */
    async fetch(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            return this.handleResponse(data);
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error(`Request timeout after ${this.timeout}ms`);
            }
            throw error;
        }
    }
    
    /**
     * Handle API response with consistent error handling
     * @param {Object} data - Response data
     * @returns {Object} - Processed response data
     * @private
     */
    handleResponse(data) {
        // Normalize response format
        if (!data.success && (data.error || data.message)) {
            throw new Error(data.error || data.message || "Unknown error");
        }
        
        return data;
    }
    
    /**
     * Make a GET request
     * @param {string} endpoint - API endpoint
     * @param {Object} params - Query parameters
     * @returns {Promise<Object>} - Parsed response data
     */
    async get(endpoint, params = {}) {
        const url = new URL(`${this.baseUrl}${endpoint}`, window.location.origin);
        
        // Add query parameters
        Object.keys(params).forEach(key => {
            url.searchParams.append(key, params[key]);
        });
        
        return this.fetch(url.toString().replace(window.location.origin, ''), {
            method: 'GET'
        });
    }
    
    /**
     * Make a POST request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request body data
     * @returns {Promise<Object>} - Parsed response data
     */
    async post(endpoint, data = {}) {
        return this.fetch(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    /**
     * Get dashboard status
     * @param {boolean} full - Whether to get full status including all keys
     * @returns {Promise<Object>} - Status data
     */
    async getStatus(full = false) {
        return this.get('/api/status', { full: full ? 'true' : 'false' });
    }
    
    /**
     * Get logs
     * @param {Object} options - Log options
     * @param {string} options.file - Log file name
     * @param {number} options.limit - Maximum number of logs to return
     * @returns {Promise<Object>} - Logs data
     */
    async getLogs(options = {}) {
        return this.get('/api/logs', options);
    }
    
    /**
     * Add a new API key
     * @param {string} key - API key to add
     * @returns {Promise<Object>} - Response data
     */
    async addKey(key) {
        return this.post('/api/add_key', { key });
    }
    
    /**
     * Activate an API key
     * @param {string} key - API key to activate
     * @returns {Promise<Object>} - Response data
     */
    async activateKey(key) {
        return this.post('/api/activate_key', { key });
    }
    
    /**
     * Remove an API key
     * @param {string} key - API key to remove
     * @returns {Promise<Object>} - Response data
     */
    async removeKey(key) {
        return this.post('/api/remove_key', { key });
    }
    
    /**
     * Rotate to the next API key
     * @returns {Promise<Object>} - Response data
     */
    async rotateKey() {
        return this.post('/api/rotate');
    }
    
    /**
     * Test the current API key
     * @returns {Promise<Object>} - Response data
     */
    async testKey() {
        return this.post('/api/test');
    }
    
    /**
     * Update settings
     * @param {Object} settings - Settings to update
     * @returns {Promise<Object>} - Response data
     */
    async updateSettings(settings) {
        return this.post('/api/settings', settings);
    }
    
    /**
     * Update the model
     * @param {string} modelId - Model ID to use
     * @returns {Promise<Object>} - Response data
     */
    async updateModel(modelId) {
        return this.post('/api/update_model', { model_id: modelId });
    }
    
    /**
     * Switch to a provider
     * @param {string} provider - Provider to switch to (openrouter, ollama, phind)
     * @returns {Promise<Object>} - Response data
     */
    async switchProvider(provider) {
        return this.post(`/api/switch/${provider}`);
    }
    
    /**
     * Create a temporary email
     * @returns {Promise<Object>} - Response data
     */
    async createTempEmail() {
        return this.post('/api/temp_email');
    }
}

// Create a singleton instance
const apiClient = new ApiClient();