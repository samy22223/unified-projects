/**
 * Notification System
 * Handles all types of notifications and alerts
 */

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.maxNotifications = 10;
    }

    initialize() {
        this.container = document.getElementById('notifications');
        if (!this.container) {
            this.createContainer();
        }
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notifications';
        this.container.className = 'notifications-container';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', options = {}) {
        const notification = this.createNotification(message, type, options);
        this.addNotification(notification);
        this.displayNotification(notification);
        
        // Auto-remove after specified duration
        const duration = options.duration || 5000;
        setTimeout(() => {
            this.removeNotification(notification.id);
        }, duration);
        
        return notification.id;
    }

    createNotification(message, type, options = {}) {
        const notification = {
            id: Date.now() + Math.random(),
            message,
            type,
            timestamp: new Date(),
            persistent: options.persistent || false,
            actions: options.actions || [],
            icon: options.icon || this.getDefaultIcon(type)
        };
        
        return notification;
    }

    addNotification(notification) {
        this.notifications.unshift(notification);
        
        // Keep only max notifications
        if (this.notifications.length > this.maxNotifications) {
            this.notifications = this.notifications.slice(0, this.maxNotifications);
        }
    }

    displayNotification(notification) {
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification ${notification.type}`;
        notificationElement.id = `notification-${notification.id}`;
        
        const actionsHtml = notification.actions.map(action => 
            `<button class="notification-action" onclick="${action.handler}">${action.label}</button>`
        ).join('');
        
        notificationElement.innerHTML = `
            <div class="notification-header">
                <div class="notification-title">
                    <i class="fas fa-${notification.icon}"></i>
                    ${notification.type.charAt(0).toUpperCase() + notification.type.slice(1)}
                </div>
                <button class="notification-close" onclick="window.notificationManager.removeNotification(${notification.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-message">${notification.message}</div>
            ${actionsHtml ? `<div class="notification-actions">${actionsHtml}</div>` : ''}
        `;
        
        this.container.appendChild(notificationElement);
        
        // Trigger animation
        setTimeout(() => {
            notificationElement.classList.add('show');
        }, 100);
        
        // Store reference for removal
        notification.element = notificationElement;
    }

    removeNotification(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification) return;
        
        if (notification.element) {
            notification.element.classList.remove('show');
            setTimeout(() => {
                if (notification.element.parentNode) {
                    notification.element.parentNode.removeChild(notification.element);
                }
            }, 300);
        }
        
        // Remove from array
        this.notifications = this.notifications.filter(n => n.id !== id);
    }

    getDefaultIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Specialized notification methods
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', options);
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    // System notifications
    showAgentStatus(agentName, status, details = '') {
        const messages = {
            'online': `${agentName} is now online`,
            'offline': `${agentName} went offline`,
            'error': `${agentName} encountered an error`,
            'busy': `${agentName} is processing tasks`,
            'idle': `${agentName} is idle`
        };
        
        const types = {
            'online': 'success',
            'offline': 'error',
            'error': 'error',
            'busy': 'info',
            'idle': 'info'
        };
        
        const message = details ? `${messages[status]}: ${details}` : messages[status];
        return this.show(message, types[status]);
    }

    showTaskUpdate(taskName, status, details = '') {
        const messages = {
            'started': `Task "${taskName}" started`,
            'completed': `Task "${taskName}" completed successfully`,
            'failed': `Task "${taskName}" failed`,
            'cancelled': `Task "${taskName}" was cancelled`
        };
        
        const types = {
            'started': 'info',
            'completed': 'success',
            'failed': 'error',
            'cancelled': 'warning'
        };
        
        const message = details ? `${messages[status]}: ${details}` : messages[status];
        return this.show(message, types[status]);
    }

    showSystemAlert(type, message, details = '') {
        const fullMessage = details ? `${message}: ${details}` : message;
        return this.show(fullMessage, type, { persistent: true });
    }

    // Bulk operations
    clearAll() {
        this.notifications.forEach(notification => {
            this.removeNotification(notification.id);
        });
        this.notifications = [];
    }

    clearByType(type) {
        const toRemove = this.notifications.filter(n => n.type === type);
        toRemove.forEach(notification => {
            this.removeNotification(notification.id);
        });
    }

    // Notification history
    getHistory() {
        return [...this.notifications];
    }

    exportHistory() {
        return JSON.stringify(this.notifications, null, 2);
    }

    // Sound notifications (optional)
    enableSound() {
        this.soundEnabled = true;
    }

    disableSound() {
        this.soundEnabled = false;
    }

    playNotificationSound(type) {
        if (!this.soundEnabled) return;
        
        // Create audio context for notification sounds
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Different frequencies for different notification types
        const frequencies = {
            'success': 800,
            'error': 400,
            'warning': 600,
            'info': 500
        };
        
        oscillator.frequency.setValueAtTime(frequencies[type] || 500, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start();
        oscillator.stop(audioContext.currentTime + 0.5);
    }

    // Desktop notifications
    async requestPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }
        return false;
    }

    showDesktopNotification(title, options = {}) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification(title, {
                body: options.body || '',
                icon: options.icon || '/assets/images/logo.png',
                badge: options.badge || '/assets/images/badge.png',
                ...options
            });
            
            if (options.onClick) {
                notification.onclick = options.onClick;
            }
            
            return notification;
        }
    }

    // Toast notifications (alternative style)
    showToast(message, type = 'info', duration = 3000) {
        return this.show(message, type, {
            duration,
            style: 'toast'
        });
    }

    // Progress notifications
    showProgress(message, type = 'info') {
        const notificationId = this.show(message, type, { persistent: true });
        
        return {
            id: notificationId,
            update: (progress, newMessage) => {
                this.updateProgress(notificationId, progress, newMessage);
            },
            complete: (finalMessage) => {
                this.completeProgress(notificationId, finalMessage || 'Completed');
            }
        };
    }

    updateProgress(id, progress, message) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification) return;
        
        const element = notification.element;
        if (element) {
            const progressBar = element.querySelector('.progress-bar') || document.createElement('div');
            progressBar.className = 'progress-bar';
            progressBar.innerHTML = `<div class="progress-fill" style="width: ${progress}%"></div>`;
            
            if (!element.querySelector('.progress-bar')) {
                element.appendChild(progressBar);
            } else {
                element.querySelector('.progress-fill').style.width = `${progress}%`;
            }
            
            if (message) {
                element.querySelector('.notification-message').textContent = message;
            }
        }
    }

    completeProgress(id, finalMessage) {
        this.updateProgress(id, 100, finalMessage);
        setTimeout(() => {
            this.removeNotification(id);
        }, 1000);
    }
}

// Export for global use
window.NotificationManager = NotificationManager;
