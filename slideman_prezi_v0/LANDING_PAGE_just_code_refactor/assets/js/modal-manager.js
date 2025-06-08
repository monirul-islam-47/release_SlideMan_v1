// Modal and Overlay Management System

class ModalManager {
    constructor() {
        this.activeModals = new Set();
        this.escapeKeyHandler = this.handleEscapeKey.bind(this);
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return false;

        modal.classList.add('active');
        this.activeModals.add(modalId);
        
        // Add escape key listener if first modal
        if (this.activeModals.size === 1) {
            document.addEventListener('keydown', this.escapeKeyHandler);
        }
        
        // Focus management
        this.trapFocus(modal);
        
        return true;
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return false;

        modal.classList.remove('active');
        this.activeModals.delete(modalId);
        
        // Remove escape key listener if no active modals
        if (this.activeModals.size === 0) {
            document.removeEventListener('keydown', this.escapeKeyHandler);
        }
        
        return true;
    }

    hideAllModals() {
        this.activeModals.forEach(modalId => {
            this.hideModal(modalId);
        });
    }

    toggleModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return false;

        if (modal.classList.contains('active')) {
            return this.hideModal(modalId);
        } else {
            return this.showModal(modalId);
        }
    }

    handleEscapeKey(event) {
        if (event.key === 'Escape') {
            // Close the most recently opened modal
            const lastModal = Array.from(this.activeModals).pop();
            if (lastModal) {
                this.hideModal(lastModal);
            }
        }
    }

    trapFocus(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });

        firstElement.focus();
    }
}

// Create global modal manager instance
window.modalManager = new ModalManager();

// Overlay management functions
function toggleOverlays() {
    const container = document.getElementById('overlaysContainer');
    if (container) {
        container.classList.toggle('active');
    }
}

function showOverlay(overlayId) {
    return window.modalManager.showModal(overlayId);
}

function hideOverlay(overlayId) {
    return window.modalManager.hideModal(overlayId);
}

// Assistant overlay management
function toggleAssistantOverlay() {
    const overlay = document.getElementById('assistantOverlay');
    if (overlay) {
        overlay.classList.toggle('active');
    }
}

// Tooltip management
function showTooltip(element, text, position = 'top') {
    let tooltip = document.getElementById('globalTooltip');
    if (!tooltip) {
        tooltip = createGlobalTooltip();
    }

    tooltip.textContent = text;
    tooltip.className = `tooltip tooltip-${position}`;
    
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let left, top;
    switch(position) {
        case 'top':
            left = rect.left + (rect.width - tooltipRect.width) / 2;
            top = rect.top - tooltipRect.height - 8;
            break;
        case 'bottom':
            left = rect.left + (rect.width - tooltipRect.width) / 2;
            top = rect.bottom + 8;
            break;
        case 'left':
            left = rect.left - tooltipRect.width - 8;
            top = rect.top + (rect.height - tooltipRect.height) / 2;
            break;
        case 'right':
            left = rect.right + 8;
            top = rect.top + (rect.height - tooltipRect.height) / 2;
            break;
    }
    
    tooltip.style.left = Math.max(8, left) + 'px';
    tooltip.style.top = Math.max(8, top) + 'px';
    tooltip.classList.add('active');
}

function hideTooltip() {
    const tooltip = document.getElementById('globalTooltip');
    if (tooltip) {
        tooltip.classList.remove('active');
    }
}

function createGlobalTooltip() {
    const tooltip = document.createElement('div');
    tooltip.id = 'globalTooltip';
    tooltip.className = 'tooltip';
    tooltip.style.cssText = `
        position: fixed;
        background: var(--bg-panel);
        color: var(--text-primary);
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        z-index: 10000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s ease;
        border: 1px solid var(--border);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;
    document.body.appendChild(tooltip);
    
    // Add CSS for active state
    const style = document.createElement('style');
    style.textContent = `
        .tooltip.active {
            opacity: 1 !important;
        }
    `;
    document.head.appendChild(style);
    
    return tooltip;
}

// Initialize modal system
document.addEventListener('DOMContentLoaded', function() {
    // Close modals when clicking outside
    document.addEventListener('click', function(event) {
        // Check if click is on a modal backdrop
        if (event.target.classList.contains('modal-overlay')) {
            const modal = event.target.querySelector('.modal');
            if (modal) {
                const modalId = event.target.id;
                window.modalManager.hideModal(modalId);
            }
        }
    });
});