/**
 * modal-manager.js - Centralized modal management for the AI Dashboard
 * Improved version with better accessibility and memory management
 */

class ModalManager {
    constructor(templateId = "modal-template") {
        this.template = document.getElementById(templateId);
        if (!this.template) {
            console.error(`Modal template with ID "${templateId}" not found`);
            return;
        }
        this.activeModals = [];
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.addEventListener('click', this.handleModalClose.bind(this));
        document.addEventListener('keydown', this.handleKeyboardNavigation.bind(this));
    }

    handleModalClose(e) {
        if (e.target.matches('[data-bs-dismiss="modal"]') || e.target.closest('[data-bs-dismiss="modal"]')) {
            const modal = e.target.closest('.modal');
            if (modal) this.close(modal.id);
        }
    }

    handleKeyboardNavigation(e) {
        if (!this.activeModals.length) return;
        
        const activeModal = this.activeModals[this.activeModals.length - 1];
        
        if (e.key === 'Escape') {
            e.preventDefault();
            this.close(activeModal.id);
        } else if (e.key === 'Tab') {
            this.handleTabKeyInModal(e, activeModal.element);
        }
    }

    open(data) {
        if (!this.template) return null;

        const modal = this.createModalElement(data);
        const modalId = `modal-${Date.now()}`;
        
        this.setupModalAttributes(modal, modalId, data);
        this.setupModalContent(modal, data);
        this.setupModalButtons(modal, data);
        
        document.body.appendChild(modal);
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        this.activeModals.push({
            id: modalId,
            element: modal,
            instance: bsModal,
            onClose: data.onClose
        });
        
        this.setupModalCloseHandler(modal, modalId, data);
        this.setupInitialFocus(modal);
        this.updateScreenReaderStatus(data.message, data.type);
        
        return modal;
    }

    createModalElement(data) {
        const clone = this.template.content.cloneNode(true);
        return clone.querySelector(".modal");
    }

    setupModalAttributes(modal, modalId, data) {
        modal.id = modalId;
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', `${modalId}-title`);
        modal.setAttribute('aria-describedby', `${modalId}-body`);
        modal.setAttribute('aria-label', `${data.type || 'info'} dialog`);
    }

    setupModalContent(modal, data) {
        const title = data.title || "Status Update";
        const titleElement = modal.querySelector(".modal-title");
        titleElement.textContent = title;
        titleElement.id = `${modal.id}-title`;

        const modalBody = modal.querySelector(".modal-body");
        modalBody.id = `${modal.id}-body`;

        if (data.useHtml && data.message) {
            modalBody.innerHTML = data.message;
            this.makeInteractiveElementsAccessible(modalBody);
        } else {
            modalBody.textContent = data.message || "";
        }

        this.applyModalStyling(modal, data.type);
    }

    applyModalStyling(modal, type) {
        const headerElement = modal.querySelector(".modal-header");
        headerElement.classList.remove("bg-success", "bg-danger", "bg-warning", "bg-info", "text-white");
        
        const styleMap = {
            error: ["bg-danger", "text-white"],
            success: ["bg-success", "text-white"],
            warning: ["bg-warning"],
            info: ["bg-info", "text-white"]
        };
        
        const styles = styleMap[type] || styleMap.info;
        headerElement.classList.add(...styles);
    }

    makeInteractiveElementsAccessible(container) {
        container.querySelectorAll('a, button, [role="button"]')
            .forEach(el => {
                if (!el.getAttribute('tabindex')) {
                    el.setAttribute('tabindex', '0');
                }
            });
    }

    setupModalButtons(modal, data) {
        if (!Array.isArray(data.buttons) || !data.buttons.length) return;

        const modalFooter = modal.querySelector('.modal-footer');
        modalFooter.innerHTML = '';
        
        data.buttons.forEach((button, index) => {
            const btnElement = this.createButton(button, index, modal.id);
            modalFooter.appendChild(btnElement);
        });
    }

    createButton(button, index, modalId) {
        const btnElement = document.createElement('button');
        btnElement.type = 'button';
        btnElement.className = `btn btn-${button.type || 'primary'}`;
        btnElement.textContent = button.text || 'Button';
        btnElement.setAttribute('data-button-index', index);
        
        if (button.ariaLabel) {
            btnElement.setAttribute('aria-label', button.ariaLabel);
        }
        
        this.setupButtonClickHandler(btnElement, button, modalId);
        
        return btnElement;
    }

    setupButtonClickHandler(btnElement, button, modalId) {
        if (typeof button.onClick === 'function') {
            btnElement.addEventListener('click', (e) => {
                button.onClick(e, modalId);
                if (button.closeOnClick !== false) {
                    this.close(modalId);
                }
            });
        } else if (button.closeOnClick !== false) {
            btnElement.addEventListener('click', () => this.close(modalId));
        }
    }

    setupModalCloseHandler(modal, modalId, data) {
        modal.addEventListener("hidden.bs.modal", () => {
            this.removeModal(modalId);
            if (typeof data.onClose === "function") {
                data.onClose();
            }
        });
    }

    setupInitialFocus(modal) {
        setTimeout(() => {
            const focusable = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusable.length > 0) {
                focusable[0].focus();
            }
        }, 100);
    }

    close(modalId) {
        const modalInfo = this.activeModals.find(m => m.id === modalId);
        if (modalInfo) {
            modalInfo.instance.hide();
        }
    }

    closeAll() {
        [...this.activeModals].forEach(modalInfo => {
            modalInfo.instance.hide();
        });
    }

    alert(data) {
        return this.open({
            title: data.title || "Alert",
            message: data.message || "",
            type: data.type || "info",
            useHtml: data.useHtml || false,
            onClose: data.onClose,
            buttons: [{
                text: data.buttonText || "OK",
                type: data.buttonType || "primary",
                onClick: data.onClose || (() => {}),
                ariaLabel: "Close alert"
            }]
        });
    }

    confirm(data) {
        return this.open({
            title: data.title || "Confirmation",
            message: data.message || "Are you sure?",
            type: data.type || "warning",
            useHtml: data.useHtml || false,
            onClose: data.onClose,
            buttons: [
                {
                    text: data.cancelText || "No",
                    type: data.cancelType || "secondary",
                    onClick: data.onCancel || (() => {}),
                    ariaLabel: "Cancel action"
                },
                {
                    text: data.confirmText || "Yes",
                    type: data.confirmType || "primary",
                    onClick: data.onConfirm || (() => {}),
                    ariaLabel: "Confirm action"
                }
            ]
        });
    }

    prompt(data) {
        const inputId = `prompt-input-${Date.now()}`;
        const inputHtml = this.createPromptInputHtml(inputId, data);
        
        return this.createPromptModal(data, inputId, inputHtml);
    }

    createPromptInputHtml(inputId, data) {
        return `
            <div class="form-group mt-3">
                <label for="${inputId}" class="form-label">${data.message || "Please enter a value:"}</label>
                <input type="${data.inputType || "text"}" class="form-control" 
                       id="${inputId}" 
                       value="${data.defaultValue || ""}" 
                       placeholder="${data.placeholder || ""}" 
                       aria-describedby="${inputId}-help">
                ${data.helpText ? `<div id="${inputId}-help" class="form-text">${data.helpText}</div>` : ""}
            </div>
        `;
    }

    createPromptModal(data, inputId, inputHtml) {
        const modalElement = this.open({
            title: data.title || "Input Required",
            message: inputHtml,
            type: data.type || "info",
            useHtml: true,
            onClose: data.onClose,
            buttons: this.createPromptButtons(data, inputId)
        });

        this.setupPromptBehavior(modalElement, inputId);
        return modalElement;
    }

    createPromptButtons(data, inputId) {
        return [
            {
                text: data.cancelText || "Cancel",
                type: data.cancelType || "secondary",
                onClick: data.onCancel || (() => {}),
                ariaLabel: "Cancel input"
            },
            {
                text: data.submitText || "Submit",
                type: data.submitType || "primary",
                onClick: () => this.handlePromptSubmit(inputId, data),
                ariaLabel: "Submit input"
            }
        ];
    }

    handlePromptSubmit(inputId, data) {
        const inputElement = document.getElementById(inputId);
        if (inputElement && typeof data.onSubmit === "function") {
            data.onSubmit(inputElement.value);
        }
    }

    setupPromptBehavior(modalElement, inputId) {
        setTimeout(() => {
            const inputElement = document.getElementById(inputId);
            if (!inputElement) return;

            inputElement.focus();
            inputElement.select();
            
            inputElement.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    const submitButton = modalElement.querySelector('.btn-primary');
                    submitButton?.click();
                }
            });
        }, 150);
    }

    removeModal(modalId) {
        const index = this.activeModals.findIndex(modal => modal.id === modalId);
        if (index === -1) return;

        const modal = this.activeModals[index];
        modal.element.remove();
        
        if (typeof modal.onClose === "function") {
            modal.onClose();
        }
        
        this.activeModals.splice(index, 1);
        this.manageFocusAfterClose();
    }

    manageFocusAfterClose() {
        if (this.activeModals.length > 0) {
            const lastModal = this.activeModals[this.activeModals.length - 1].element;
            const focusable = lastModal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusable.length > 0) {
                focusable[0].focus();
            }
        } else {
            document.body.focus();
        }
    }

    updateScreenReaderStatus(message, type) {
        const statusRegion = document.getElementById("status-update-region");
        if (statusRegion) {
            statusRegion.textContent = `${type ? type + ": " : ""}${message}`;
        }
    }

    handleTabKeyInModal(event, modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (event.shiftKey && document.activeElement === firstElement) {
            lastElement.focus();
            event.preventDefault();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
            firstElement.focus();
            event.preventDefault();
        }
    }
}

// Create a singleton instance
const modalManager = new ModalManager();