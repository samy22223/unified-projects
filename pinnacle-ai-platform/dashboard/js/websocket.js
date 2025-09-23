/**
 * WebSocket Manager
 * Handles real-time communication with the backend
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 5000;
        this.eventListeners = {};
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.onConnected();
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.onDisconnected();
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectInterval);
        } else {
            console.log('Max reconnection attempts reached');
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected');
        }
    }

    handleMessage(data) {
        // Emit event for other modules to listen to
        this.emit(data.type, data);
        
        // Handle system messages
        switch (data.type) {
            case 'agent_status_update':
                this.handleAgentStatusUpdate(data.agent);
                break;
            case 'task_update':
                this.handleTaskUpdate(data.task);
                break;
            case 'system_stats_update':
                this.handleSystemStatsUpdate(data.stats);
                break;
            case 'notification':
                this.handleNotification(data);
                break;
        }
    }

    handleAgentStatusUpdate(agent) {
        // Update UI elements
        this.updateAgentStatusDisplay(agent);
        
        // Update charts if needed
        if (window.dashboard && window.dashboard.charts.agentPerformance) {
            window.dashboard.updateAgentPerformanceChart(window.dashboard.agents);
        }
    }

    handleTaskUpdate(task) {
        // Update task counters
        this.updateTaskCounters(task);
        
        // Add to activity feed
        this.addToActivityFeed(task);
    }

    handleSystemStatsUpdate(stats) {
        // Update system statistics displays
        this.updateSystemStats(stats);
    }

    handleNotification(data) {
        if (window.dashboard) {
            window.dashboard.showNotification(data.message, data.level || 'info');
        }
    }

    updateAgentStatusDisplay(agent) {
        const statusElement = document.getElementById(`${agent.type}Status`);
        if (statusElement) {
            const indicator = statusElement.querySelector('.status-indicator');
            const text = statusElement.querySelector('.status-text');
            
            if (indicator) {
                indicator.className = `status-indicator ${agent.status === 'error' ? 'error' : agent.status === 'warning' ? 'warning' : ''}`;
            }
            
            if (text) {
                text.textContent = agent.status || 'Unknown';
            }
        }
    }

    updateTaskCounters(task) {
        const activeTasksElement = document.getElementById('activeTasks');
        if (activeTasksElement) {
            const currentTasks = parseInt(activeTasksElement.textContent) || 0;
            const newCount = task.status === 'active' ? currentTasks + 1 : Math.max(0, currentTasks - 1);
            activeTasksElement.textContent = newCount;
        }
    }

    updateSystemStats(stats) {
        if (stats.system_load !== undefined) {
            const loadElement = document.getElementById('systemLoad');
            const loadBar = document.getElementById('systemLoadBar');
            
            if (loadElement) {
                loadElement.textContent = `${stats.system_load}%`;
            }
            
            if (loadBar) {
                loadBar.style.width = `${Math.min(stats.system_load, 100)}%`;
            }
        }
        
        if (stats.total_agents !== undefined) {
            const agentsElement = document.getElementById('totalAgents');
            if (agentsElement) {
                agentsElement.textContent = stats.total_agents;
            }
        }
    }

    addToActivityFeed(activity) {
        if (window.dashboard) {
            window.dashboard.addRecentActivity({
                type: 'task',
                title: `Task ${activity.status}: ${activity.name}`,
                time: new Date().toLocaleTimeString()
            });
        }
    }

    onConnected() {
        if (window.dashboard) {
            window.dashboard.showNotification('Connected to real-time updates', 'success');
        }
    }

    onDisconnected() {
        if (window.dashboard) {
            window.dashboard.showNotification('Lost connection to real-time updates', 'warning');
        }
    }

    // Event system
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }

    off(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => callback(data));
        }
    }
}

// Export for global use
window.WebSocketManager = WebSocketManager;
