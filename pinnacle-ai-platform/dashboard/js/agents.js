/**
 * AI Agents Management Module
 * Handles agent-specific functionality and interactions
 */

class AgentManager {
    constructor() {
        this.agents = {};
        this.activeAgents = new Set();
    }

    async loadAgents() {
        try {
            const response = await fetch('/api/v1/agents', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                }
            });
            
            if (response.ok) {
                this.agents = await response.json();
                this.updateAgentDisplays();
            }
        } catch (error) {
            console.error('Failed to load agents:', error);
        }
    }

    updateAgentDisplays() {
        // Update agent status indicators
        Object.values(this.agents).forEach(agent => {
            this.updateAgentStatus(agent);
        });
    }

    updateAgentStatus(agent) {
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

    async startAgent(agentType) {
        try {
            const response = await fetch(`/api/v1/agents/${agentType}/start`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                }
            });
            
            if (response.ok) {
                this.showNotification(`${agentType} agent started successfully`, 'success');
                await this.loadAgents(); // Refresh agent data
            } else {
                this.showNotification(`Failed to start ${agentType} agent`, 'error');
            }
        } catch (error) {
            console.error(`Failed to start ${agentType}:`, error);
            this.showNotification(`Error starting ${agentType} agent`, 'error');
        }
    }

    async stopAgent(agentType) {
        try {
            const response = await fetch(`/api/v1/agents/${agentType}/stop`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                }
            });
            
            if (response.ok) {
                this.showNotification(`${agentType} agent stopped successfully`, 'success');
                await this.loadAgents(); // Refresh agent data
            } else {
                this.showNotification(`Failed to stop ${agentType} agent`, 'error');
            }
        } catch (error) {
            console.error(`Failed to stop ${agentType}:`, error);
            this.showNotification(`Error stopping ${agentType} agent`, 'error');
        }
    }

    showNotification(message, type) {
        if (window.dashboard) {
            window.dashboard.showNotification(message, type);
        }
    }
}

// Export for global use
window.AgentManager = AgentManager;
