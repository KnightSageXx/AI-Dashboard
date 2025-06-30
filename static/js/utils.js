/**
 * utils.js - Utility functions for the AI Dashboard
 */

// Centralized error handling utility
const ErrorHandler = {
    /**
     * Display an error message in a container
     * @param {HTMLElement} container - The container to display the error in
     * @param {Error|string} error - The error object or message
     * @param {Function} retryCallback - Optional callback function for retry button
     * @param {string} retryButtonText - Optional text for retry button
     */
    showError: function(container, error, retryCallback = null, retryButtonText = 'Retry') {
        if (!container) return;
        
        const errorMessage = error instanceof Error ? error.message : error;
        
        let html = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2" aria-hidden="true"></i>
                ${errorMessage}
        `;
        
        if (retryCallback) {
            html += `
                <button class="btn btn-sm btn-outline-danger ms-2" id="error-retry-btn" aria-label="${retryButtonText}">
                    <i class="fas fa-sync-alt" aria-hidden="true"></i> ${retryButtonText}
                </button>
            `;
        }
        
        html += `</div>`;
        
        container.innerHTML = html;
        container.setAttribute('aria-busy', 'false');
        
        // Update screen reader status
        this.updateScreenReaderStatus(`Error: ${errorMessage}`);
        
        if (retryCallback) {
            document.getElementById('error-retry-btn')?.addEventListener('click', retryCallback);
        }
    },
    
    /**
     * Display a loading indicator in a container
     * @param {HTMLElement} container - The container to display the loading indicator in
     * @param {string} message - Optional loading message
     * @param {boolean} useSmallSpinner - Whether to use a small spinner
     */
    showLoading: function(container, message = 'Loading...', useSmallSpinner = false) {
        if (!container) return;
        
        const spinnerClass = useSmallSpinner ? 'spinner-border-sm' : '';
        const textClass = useSmallSpinner ? 'ms-2' : 'mt-3';
        
        container.innerHTML = `
            <div class="text-center p-${useSmallSpinner ? '3' : '5'}">
                <div class="spinner-border text-primary ${spinnerClass}" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <${useSmallSpinner ? 'span' : 'p'} class="${textClass}">${message}</${useSmallSpinner ? 'span' : 'p'}>
            </div>
        `;
        
        container.setAttribute('aria-busy', 'true');
        
        // Update screen reader status
        this.updateScreenReaderStatus(`Loading: ${message}`);
    },
    
    /**
     * Display an empty state message in a container
     * @param {HTMLElement} container - The container to display the empty state in
     * @param {string} message - The empty state message
     * @param {string} icon - The icon class to use
     */
    showEmptyState: function(container, message = 'No data available', icon = 'fa-info-circle') {
        if (!container) return;
        
        container.innerHTML = `
            <div class="text-center p-3">
                <i class="fas ${icon} me-2" aria-hidden="true"></i>
                ${message}
            </div>
        `;
        
        container.setAttribute('aria-busy', 'false');
        
        // Update screen reader status
        this.updateScreenReaderStatus(message);
    },
    
    /**
     * Handle fetch API errors with normalized response format
     * @param {Response} response - The fetch response object
     * @returns {Promise} - The response JSON if ok, otherwise throws an error
     */
    handleFetchResponse: async function(response) {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || data.message || "Unknown error");
        }
        
        return data;
    },
    
    /**
     * Update the screen reader status region with a message
     * @param {string} message - The message to announce
     * @private
     */
    updateScreenReaderStatus: function(message) {
        const statusRegion = document.getElementById("status-update-region");
        if (statusRegion) {
            statusRegion.textContent = message;
        }
    },
    
    /**
     * Show a toast notification
     * @param {string} message - The notification message
     * @param {string} type - The notification type (success, error, warning, info)
     * @param {number} duration - The duration in milliseconds
     */
    showToast: function(message, type = 'success', duration = 3000) {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast show bg-${type === 'error' ? 'danger' : type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        // Set toast content
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body text-white">
                ${message}
            </div>
        `;
        
        // Add toast to container
        toastContainer.appendChild(toast);
        
        // Set up close button
        toast.querySelector('.btn-close').addEventListener('click', function() {
            toast.remove();
        });
        
        // Auto-remove after duration
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
};

// Debounce utility function
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Local storage utility
const StorageUtil = {
    /**
     * Save data to local storage
     * @param {string} key - The storage key
     * @param {any} data - The data to store
     * @param {number} expiryMinutes - Optional expiry time in minutes
     */
    save: function(key, data, expiryMinutes = null) {
        const item = {
            data: data,
            timestamp: Date.now()
        };
        
        if (expiryMinutes) {
            item.expiry = Date.now() + (expiryMinutes * 60 * 1000);
        }
        
        localStorage.setItem(key, JSON.stringify(item));
    },
    
    /**
     * Get data from local storage
     * @param {string} key - The storage key
     * @returns {any} - The stored data or null if not found or expired
     */
    get: function(key) {
        const item = localStorage.getItem(key);
        if (!item) return null;
        
        try {
            const parsedItem = JSON.parse(item);
            
            // Check if item has expired
            if (parsedItem.expiry && parsedItem.expiry < Date.now()) {
                localStorage.removeItem(key);
                return null;
            }
            
            return parsedItem.data;
        } catch (e) {
            console.error('Error parsing stored item:', e);
            return null;
        }
    },
    
    /**
     * Remove data from local storage
     * @param {string} key - The storage key
     */
    remove: function(key) {
        localStorage.removeItem(key);
    },
    
    /**
     * Clear all data from local storage
     */
    clear: function() {
        localStorage.clear();
    }
};