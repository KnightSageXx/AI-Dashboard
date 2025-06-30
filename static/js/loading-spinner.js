/**
 * loading-spinner.js - Consistent loading state management for the AI Dashboard
 */

class LoadingSpinner {
    /**
     * Create a new LoadingSpinner instance
     * @param {string} selector - CSS selector for the container element
     * @param {Object} options - Configuration options
     * @param {string} options.size - Size of spinner ('sm', 'md', 'lg')
     * @param {string} options.color - Bootstrap color class ('primary', 'secondary', etc.)
     * @param {string} options.message - Loading message to display
     */
    constructor(selector, options = {}) {
        this.container = document.querySelector(selector);
        this.options = {
            size: options.size || 'md',
            color: options.color || 'primary',
            message: options.message || 'Loading...'
        };
        
        if (!this.container) {
            console.error(`Container element not found: ${selector}`);
        }
        
        // Store original content to restore later
        this.originalContent = null;
    }
    
    /**
     * Show the loading spinner
     * @param {string} message - Optional message to override the default
     */
    show(message = null) {
        if (!this.container) return;
        
        // Store original content if not already stored
        if (this.originalContent === null) {
            this.originalContent = this.container.innerHTML;
        }
        
        // Determine spinner size class
        const spinnerSizeClass = this.options.size === 'sm' ? 'spinner-border-sm' : '';
        const paddingClass = this.options.size === 'sm' ? 'p-2' : 'p-5';
        const displayMessage = message || this.options.message;
        
        // Create spinner HTML
        const spinnerHtml = `
            <div class="text-center ${paddingClass}">
                <div class="spinner-border text-${this.options.color} ${spinnerSizeClass}" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <${this.options.size === 'sm' ? 'span' : 'p'} class="${this.options.size === 'sm' ? 'ms-2' : 'mt-3'}">${displayMessage}</${this.options.size === 'sm' ? 'span' : 'p'}>
            </div>
        `;
        
        // Update container
        this.container.innerHTML = spinnerHtml;
        this.container.classList.remove('d-none');
        this.container.setAttribute('aria-busy', 'true');
    }
    
    /**
     * Hide the loading spinner and restore original content
     */
    hide() {
        if (!this.container) return;
        
        // Restore original content if available
        if (this.originalContent !== null) {
            this.container.innerHTML = this.originalContent;
            this.originalContent = null;
        } else {
            this.container.innerHTML = '';
        }
        
        this.container.setAttribute('aria-busy', 'false');
    }
    
    /**
     * Show an empty state message instead of the spinner
     * @param {string} message - Message to display
     * @param {string} icon - FontAwesome icon class (without 'fa-' prefix)
     */
    showEmptyState(message = 'No data available', icon = 'info-circle') {
        if (!this.container) return;
        
        const emptyStateHtml = `
            <div class="text-center p-3">
                <i class="fas fa-${icon} me-2" aria-hidden="true"></i>
                ${message}
            </div>
        `;
        
        this.container.innerHTML = emptyStateHtml;
        this.container.setAttribute('aria-busy', 'false');
    }
    
    /**
     * Show an error message instead of the spinner
     * @param {string} message - Error message to display
     * @param {Function} retryCallback - Optional callback for retry button
     * @param {string} retryButtonText - Text for retry button
     */
    showError(message = 'An error occurred', retryCallback = null, retryButtonText = 'Retry') {
        if (!this.container) return;
        
        let errorHtml = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2" aria-hidden="true"></i>
                ${message}
        `;
        
        if (retryCallback) {
            errorHtml += `
                <button class="btn btn-sm btn-outline-danger ms-2" id="error-retry-btn">
                    <i class="fas fa-sync-alt" aria-hidden="true"></i> ${retryButtonText}
                </button>
            `;
        }
        
        errorHtml += `</div>`;
        
        this.container.innerHTML = errorHtml;
        this.container.setAttribute('aria-busy', 'false');
        
        if (retryCallback) {
            this.container.querySelector('#error-retry-btn')?.addEventListener('click', retryCallback);
        }
    }
}