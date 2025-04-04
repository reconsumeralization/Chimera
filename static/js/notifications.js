/**
 * Notifications Module
 * Handles displaying toast notifications throughout the application
 */

// Store for notification settings
const NotificationSettings = {
    duration: 5000,    // Default duration in ms
    position: 'top-right', // Default position
    maxNotifications: 3,   // Maximum concurrent notifications
    enabled: true      // Whether notifications are enabled
};

// Queue for managing notifications
let notificationQueue = [];
let activeNotifications = 0;

/**
 * Initialize the notifications system
 */
function initNotifications() {
    // Create container for notifications if it doesn't exist
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = `notification-container ${NotificationSettings.position}`;
        document.body.appendChild(container);
    }
    
    console.log('Notifications system initialized');
}

/**
 * Show a notification
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (info, success, warning, error)
 * @param {object} options - Additional options (duration, closable)
 */
function showNotification(message, type = 'info', options = {}) {
    if (!NotificationSettings.enabled) return;
    
    // Add to queue if we're at max notifications
    if (activeNotifications >= NotificationSettings.maxNotifications) {
        notificationQueue.push({ message, type, options });
        return;
    }
    
    // Create notification
    createNotification(message, type, options);
}

/**
 * Create and show a notification element
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (info, success, warning, error)
 * @param {object} options - Additional options (duration, closable)
 */
function createNotification(message, type = 'info', options = {}) {
    // Get container
    const container = document.getElementById('notification-container');
    if (!container) {
        console.error('Notification container not found');
        return;
    }
    
    // Increment active count
    activeNotifications++;
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} animate__animated animate__fadeIn`;
    
    // Get appropriate icon
    let icon = 'info-circle';
    switch (type) {
        case 'success':
            icon = 'check-circle';
            break;
        case 'warning':
            icon = 'exclamation-triangle';
            break;
        case 'error':
            icon = 'exclamation-circle';
            break;
    }
    
    // Set inner HTML
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="bi bi-${icon}"></i>
        </div>
        <div class="notification-content">
            <div class="notification-message">${message}</div>
        </div>
        ${options.closable !== false ? '<button class="notification-close"><i class="bi bi-x"></i></button>' : ''}
    `;
    
    // Add close button functionality
    const closeButton = notification.querySelector('.notification-close');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            closeNotification(notification);
        });
    }
    
    // Add to container
    container.appendChild(notification);
    
    // Set timeout to auto-remove
    const duration = options.duration || NotificationSettings.duration;
    if (duration > 0) {
        setTimeout(() => {
            closeNotification(notification);
        }, duration);
    }
    
    // Add progress bar if needed
    if (duration > 0 && options.showProgress !== false) {
        const progressBar = document.createElement('div');
        progressBar.className = 'notification-progress';
        notification.appendChild(progressBar);
        
        // Animate progress bar
        setTimeout(() => {
            progressBar.style.width = '0';
            progressBar.style.transition = `width ${duration}ms linear`;
        }, 10);
    }
    
    return notification;
}

/**
 * Close a notification
 * @param {HTMLElement} notification - The notification element to close
 */
function closeNotification(notification) {
    if (!notification || notification.classList.contains('closing')) return;
    
    notification.classList.add('closing');
    notification.classList.remove('animate__fadeIn');
    notification.classList.add('animate__fadeOut');
    
    // Remove after animation
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
        
        // Decrement active count
        activeNotifications--;
        
        // Process queue if needed
        processNotificationQueue();
    }, 500); // Animation duration
}

/**
 * Process the notification queue
 */
function processNotificationQueue() {
    if (notificationQueue.length > 0 && activeNotifications < NotificationSettings.maxNotifications) {
        const { message, type, options } = notificationQueue.shift();
        createNotification(message, type, options);
    }
}

/**
 * Update notification settings
 * @param {object} settings - New settings
 */
function updateNotificationSettings(settings = {}) {
    // Update settings
    Object.assign(NotificationSettings, settings);
    
    // Update container position if needed
    const container = document.getElementById('notification-container');
    if (container) {
        // Remove all position classes
        container.className = container.className.replace(/top-right|top-left|bottom-right|bottom-left/g, '');
        // Add new position class
        container.className += ` ${NotificationSettings.position}`;
    }
}

// Expose functions globally
window.showNotification = showNotification;
window.updateNotificationSettings = updateNotificationSettings;

// --- Notification Management ---

class NotificationManager {
    static init() {
        // Create notification container if it doesn't exist
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            document.body.appendChild(container);
        }
    }

    static show(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        // Create notification content
        notification.innerHTML = `
            <div class="notification-content">
                <i class="bi ${this.getIcon(type)}"></i>
                <span class="message">${message}</span>
            </div>
            <button class="close-button" onclick="NotificationManager.close(this.parentElement)">
                <i class="bi bi-x"></i>
            </button>
        `;
        
        // Add to container
        container.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        });
        
        // Auto close after duration
        if (duration > 0) {
            setTimeout(() => {
                this.close(notification);
            }, duration);
        }
        
        return notification;
    }

    static close(notification) {
        // Animate out
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        
        // Remove after animation
        setTimeout(() => {
            notification.remove();
        }, 300);
    }

    static getIcon(type) {
        switch (type) {
            case 'success':
                return 'bi-check-circle';
            case 'error':
                return 'bi-x-circle';
            case 'warning':
                return 'bi-exclamation-triangle';
            case 'info':
            default:
                return 'bi-info-circle';
        }
    }

    static success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    static error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    static warning(message, duration = 5000) {
        return this.show(message, 'warning', duration);
    }

    static info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }

    static confirm(message, onConfirm, onCancel) {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = 'notification notification-confirm';
        
        // Create notification content
        notification.innerHTML = `
            <div class="notification-content">
                <i class="bi bi-question-circle"></i>
                <span class="message">${message}</span>
            </div>
            <div class="notification-actions">
                <button class="confirm-button" onclick="NotificationManager.handleConfirm(this.parentElement.parentElement, true)">
                    <i class="bi bi-check"></i> Confirm
                </button>
                <button class="cancel-button" onclick="NotificationManager.handleConfirm(this.parentElement.parentElement, false)">
                    <i class="bi bi-x"></i> Cancel
                </button>
            </div>
        `;
        
        // Add to container
        container.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        });
        
        // Store callbacks
        notification.dataset.onConfirm = onConfirm ? onConfirm.toString() : '';
        notification.dataset.onCancel = onCancel ? onCancel.toString() : '';
        
        return notification;
    }

    static handleConfirm(notification, confirmed) {
        const callback = confirmed ? 
            eval(notification.dataset.onConfirm) : 
            eval(notification.dataset.onCancel);
            
        if (typeof callback === 'function') {
            callback();
        }
        
        this.close(notification);
    }

    static prompt(message, defaultValue = '', onConfirm, onCancel) {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = 'notification notification-prompt';
        
        // Create notification content
        notification.innerHTML = `
            <div class="notification-content">
                <i class="bi bi-question-circle"></i>
                <span class="message">${message}</span>
            </div>
            <div class="notification-input">
                <input type="text" value="${defaultValue}" placeholder="Enter your response...">
            </div>
            <div class="notification-actions">
                <button class="confirm-button" onclick="NotificationManager.handlePrompt(this.parentElement.parentElement, true)">
                    <i class="bi bi-check"></i> Confirm
                </button>
                <button class="cancel-button" onclick="NotificationManager.handlePrompt(this.parentElement.parentElement, false)">
                    <i class="bi bi-x"></i> Cancel
                </button>
            </div>
        `;
        
        // Add to container
        container.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        });
        
        // Focus input
        const input = notification.querySelector('input');
        input.focus();
        
        // Handle enter key
        input.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                this.handlePrompt(notification, true);
            }
        });
        
        // Store callbacks
        notification.dataset.onConfirm = onConfirm ? onConfirm.toString() : '';
        notification.dataset.onCancel = onCancel ? onCancel.toString() : '';
        
        return notification;
    }

    static handlePrompt(notification, confirmed) {
        const input = notification.querySelector('input');
        const value = input.value;
        
        const callback = confirmed ? 
            eval(notification.dataset.onConfirm) : 
            eval(notification.dataset.onCancel);
            
        if (typeof callback === 'function') {
            callback(confirmed ? value : null);
        }
        
        this.close(notification);
    }
}

// --- Initialize Notification Manager ---
document.addEventListener('DOMContentLoaded', () => {
    NotificationManager.init();
}); 