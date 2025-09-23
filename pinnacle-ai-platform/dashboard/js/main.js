/**
 * Pinnacle AI Platform Dashboard - Main JavaScript
 * Handles dashboard initialization, routing, and core functionality
 */

class PinnacleDashboard {
    constructor() {
        this.currentPage = 'overview';
        this.isAuthenticated = false;
        this.user = null;
        this.sidebarCollapsed = false;
        this.websocket = null;
        this.charts = {};
        this.agents = {};
        this.notifications = [];

        this.init();
    }

    async init() {
        console.log('🚀 Initializing Pinnacle AI Dashboard...');

        // Initialize components
        await this.initializeAuth();
        this.initializeUI();
        this.initializeEventListeners();
        this.initializeCharts();
        this.initializeWebSocket();

        // Load initial data
        await this.loadDashboardData();

        console.log('✅ Dashboard initialized successfully');
    }

    async initializeAuth() {
        // Check if user is already authenticated
        const token = localStorage.getItem('pinnacle_auth_token');
        if (token) {
            try {
                const response = await fetch('/api/v1/auth/verify', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const userData = await response.json();
                    this.user = userData;
                    this.isAuthenticated = true;
                    this.showDashboard();
                } else {
                    localStorage.removeItem('pinnacle_auth_token');
                    this.showAuthModal();
                }
            } catch (error) {
                console.error('Auth verification failed:', error);
                this.showAuthModal();
            }
        } else {
            this.showAuthModal();
        }
    }

    initializeUI() {
        // Set up responsive sidebar
        this.handleResponsiveSidebar();

        // Initialize tooltips
        this.initializeTooltips();

        // Initialize search functionality
        this.initializeSearch();

        // Set up page visibility
        this.showPage('overview');
    }

    initializeEventListeners() {
        // Sidebar navigation
        document.querySelectorAll('.sidebar-menu li[data-page]').forEach(item => {
            item.addEventListener('click', (e) => {
                const page = e.currentTarget.getAttribute('data-page');
                this.navigateToPage(page);
            });
        });

        // Menu toggle
        document.querySelector('.menu-toggle').addEventListener('click', () => {
            this.toggleSidebar();
        });

        // Auth form submissions
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            this.handleLogin(e);
        });

        document.getElementById('registerForm').addEventListener('submit', (e) => {
            this.handleRegister(e);
        });

        // Window resize
        window.addEventListener('resize', () => {
            this.handleResponsiveSidebar();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }

    initializeCharts() {
        // Initialize Chart.js defaults
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.plugins.legend.display = true;
        Chart.defaults.color = 'rgba(241, 245, 249, 0.8)';
        Chart.defaults.borderColor = 'rgba(107, 114, 128, 0.5)';

        // Create initial charts
        this.createAgentPerformanceChart();
        this.createTaskDistributionChart();
        this.createPerformanceChart();
        this.createTrendChart();
    }

    initializeWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('🔗 WebSocket connected');
                this.showNotification('Connected to real-time updates', 'success');
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.showNotification('Lost connection to real-time updates', 'warning');

                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    this.initializeWebSocket();
                }, 5000);
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
        }
    }

    async loadDashboardData() {
        if (!this.isAuthenticated) return;

        try {
            // Load system stats
            await this.loadSystemStats();

            // Load agents data
            await this.loadAgentsData();

            // Load recent activity
            await this.loadRecentActivity();

            // Load system status
            await this.loadSystemStatus();

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        }
    }

    async loadSystemStats() {
        try {
            const response = await fetch('/api/v1/dashboard/stats', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                }
            });

            if (response.ok) {
                const stats = await response.json();

                // Update UI with stats
                document.getElementById('totalAgents').textContent = stats.total_agents || 0;
                document.getElementById('activeTasks').textContent = stats.active_tasks || 0;
                document.getElementById('systemLoad').textContent = `${stats.system_load || 0}%`;
                document.getElementById('uptime').textContent = this.formatUptime(stats.uptime || 0);

                // Update progress bar
                const loadBar = document.getElementById('systemLoadBar');
                if (loadBar) {
                    loadBar.style.width = `${Math.min(stats.system_load || 0, 100)}%`;
                }

                // Update trends
                document.getElementById('agentsTrend').textContent = `${stats.agents_trend || 0}%`;
                document.getElementById('tasksTrend').textContent = `${stats.tasks_trend || 0}%`;
            }
        } catch (error) {
            console.error('Failed to load system stats:', error);
        }
    }

    async loadAgentsData() {
        try {
            const response = await fetch('/api/v1/agents', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                }
            });

            if (response.ok) {
                const agents = await response.json();
                this.agents = agents;

                // Update agents grid
                this.updateAgentsGrid(agents);

                // Update agent performance chart
                this.updateAgentPerformanceChart(agents);
            }
        } catch (error) {
            console.error('Failed to load agents data:', error);
        }
    }

    async loadRecentActivity() {
        try {
            const response = await fetch('/api/v1/dashboard/activity', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                }
            });

            if (response.ok) {
                const activities = await response.json();
                this.updateActivityList(activities);
            }
        } catch (error) {
            console.error('Failed to load recent activity:', error);
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/v1/dashboard/status', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                }
            });

            if (response.ok) {
                const status = await response.json();
                this.updateSystemStatus(status);
            }
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    }

    navigateToPage(pageId) {
        this.showPage(pageId);
        this.updateActiveMenuItem(pageId);
    }

    showPage(pageId) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });

        // Show selected page
        const targetPage = document.getElementById(`${pageId}Page`);
        if (targetPage) {
            targetPage.classList.add('active');
            this.currentPage = pageId;
        }

        // Update page title
        this.updatePageTitle(pageId);
    }

    updatePageTitle(pageId) {
        const titles = {
            'overview': 'Dashboard Overview',
            'agents': 'AI Agent Management',
            'monitoring': 'System Monitoring',
            'tasks': 'Task History',
            'autopilot': 'AutoPilot Agent',
            'fabricai': 'FabricAI Agent',
            'builderx': 'BuilderX Agent',
            'insighor': 'Insightor Agent',
            'connector': 'Connector Agent',
            'accounts': 'Account Management',
            'fabric': 'Fabric Workspace',
            'orchestration': 'AI Orchestration',
            'tools': 'Tools Builder',
            'models': 'AI Models',
            'preferences': 'User Preferences',
            'notifications': 'Notifications'
        };

        const title = titles[pageId] || 'Dashboard';
        document.getElementById('pageTitle').textContent = title;
    }

    updateActiveMenuItem(pageId) {
        // Remove active class from all menu items
        document.querySelectorAll('.sidebar-menu li').forEach(item => {
            item.classList.remove('active');
        });

        // Add active class to current item
        const activeItem = document.querySelector(`[data-page="${pageId}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }

    toggleSidebar() {
        this.sidebarCollapsed = !this.sidebarCollapsed;
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');

        if (this.sidebarCollapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        }
    }

    handleResponsiveSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');

        if (window.innerWidth <= 768) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        }
    }

    initializeTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        tooltipElements.forEach(element => {
            element.classList.add('tooltip');
        });
    }

    initializeSearch() {
        const searchInput = document.querySelector('.search-box input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }
    }

    handleSearch(query) {
        if (query.length < 2) return;

        // Simple search implementation
        console.log('Searching for:', query);

        // In a real implementation, this would filter content or make API calls
        this.showNotification(`Searching for: ${query}`, 'info');
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-box input');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape to close modals/dropdowns
        if (e.key === 'Escape') {
            this.closeAuthModal();
        }
    }

    async handleLogin(e) {
        e.preventDefault();

        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;

        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('pinnacle_auth_token', data.token);
                this.user = data.user;
                this.isAuthenticated = true;
                this.showDashboard();
                this.showNotification('Successfully logged in!', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.message || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Login failed. Please try again.', 'error');
        }
    }

    async handleRegister(e) {
        e.preventDefault();

        const name = document.getElementById('registerName').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('registerConfirmPassword').value;

        if (password !== confirmPassword) {
            this.showNotification('Passwords do not match', 'error');
            return;
        }

        try {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, email, password })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('pinnacle_auth_token', data.token);
                this.user = data.user;
                this.isAuthenticated = true;
                this.showDashboard();
                this.showNotification('Account created successfully!', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.message || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showNotification('Registration failed. Please try again.', 'error');
        }
    }

    showAuthModal() {
        document.getElementById('authModal').classList.add('show');
        document.getElementById('dashboard').style.display = 'none';
    }

    closeAuthModal() {
        document.getElementById('authModal').classList.remove('show');
    }

    showDashboard() {
        document.getElementById('authModal').classList.remove('show');
        document.getElementById('dashboard').style.display = 'flex';

        // Update user info
        if (this.user) {
            document.getElementById('userName').textContent = this.user.name || 'Admin User';
            document.getElementById('userRole').textContent = this.user.role || 'Administrator';
        }
    }

    logout() {
        localStorage.removeItem('pinnacle_auth_token');
        this.isAuthenticated = false;
        this.user = null;
        this.showAuthModal();
        this.showNotification('Logged out successfully', 'info');
    }

    showLoginForm() {
        document.getElementById('loginForm').style.display = 'flex';
        document.getElementById('registerForm').style.display = 'none';
        document.querySelectorAll('.auth-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelector('.auth-tab').classList.add('active');
    }

    showRegisterForm() {
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('registerForm').style.display = 'flex';
        document.querySelectorAll('.auth-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelector('.auth-tab:last-child').classList.add('active');
    }

    showNotification(message, type = 'info') {
        const notificationsContainer = document.getElementById('notifications');

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-header">
                <span class="notification-title">${type.charAt(0).toUpperCase() + type.slice(1)}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-message">${message}</div>
        `;

        notificationsContainer.appendChild(notification);

        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);

        this.notifications.push({ message, type, timestamp: Date.now() });
    }

    handleWebSocketMessage(data) {
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
                this.showNotification(data.message, data.level || 'info');
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    handleAgentStatusUpdate(agent) {
        // Update agent in local data
        this.agents[agent.id] = agent;

        // Update UI
        this.updateAgentStatus(agent);

        // Update charts if needed
        this.updateAgentPerformanceChart(this.agents);
    }

    handleTaskUpdate(task) {
        // Update task counters
        const activeTasksElement = document.getElementById('activeTasks');
        if (activeTasksElement) {
            const currentTasks = parseInt(activeTasksElement.textContent) || 0;
            activeTasksElement.textContent = task.status === 'active' ? currentTasks + 1 : Math.max(0, currentTasks - 1);
        }

        // Add to recent activity
        this.addRecentActivity({
            type: 'task',
            title: `Task ${task.status}: ${task.name}`,
            time: new Date().toLocaleTimeString()
        });
    }

    handleSystemStatsUpdate(stats) {
        // Update system stats in UI
        if (stats.system_load !== undefined) {
            document.getElementById('systemLoad').textContent = `${stats.system_load}%`;
            const loadBar = document.getElementById('systemLoadBar');
            if (loadBar) {
                loadBar.style.width = `${Math.min(stats.system_load, 100)}%`;
            }
        }

        if (stats.total_agents !== undefined) {
            document.getElementById('totalAgents').textContent = stats.total_agents;
        }

        if (stats.active_tasks !== undefined) {
            document.getElementById('activeTasks').textContent = stats.active_tasks;
        }
    }

    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    // Chart creation methods
    createAgentPerformanceChart() {
        const ctx = document.getElementById('agentPerformanceChart');
        if (!ctx) return;

        this.charts.agentPerformance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Agent Performance',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    createTaskDistributionChart() {
        const ctx = document.getElementById('taskDistributionChart');
        if (!ctx) return;

        this.charts.taskDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'In Progress', 'Failed', 'Queued'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        'rgb(16, 185, 129)',
                        'rgb(59, 130, 246)',
                        'rgb(239, 68, 68)',
                        'rgb(107, 114, 128)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    createPerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        this.charts.performance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['AutoPilot', 'FabricAI', 'BuilderX', 'Insightor', 'Connector'],
                datasets: [{
                    label: 'Performance Score',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: 'rgba(59, 130, 246, 0.8)'
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    createTrendChart() {
        const ctx = document.getElementById('trendChart');
        if (!ctx) return;

        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'System Load',
                    data: [],
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    updateAgentPerformanceChart(agents) {
        if (!this.charts.agentPerformance) return;

        const agentData = Object.values(agents || {});
        const labels = agentData.map(agent => agent.name || agent.id);
        const performanceData = agentData.map(agent => agent.performance || Math.random() * 100);

        this.charts.agentPerformance.data.labels = labels;
        this.charts.agentPerformance.data.datasets[0].data = performanceData;
        this.charts.agentPerformance.update();
    }

    updateActivityList(activities) {
        const activityList = document.getElementById('activityList');
        if (!activityList) return;

        activityList.innerHTML = '';

        activities.forEach(activity => {
            const activityItem = document.createElement('div');
            activityItem.className = 'activity-item';

            activityItem.innerHTML = `
                <div class="activity-icon">
                    <i class="fas fa-${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-time">${activity.time}</div>
                </div>
            `;

            activityList.appendChild(activityItem);
        });
    }

    updateSystemStatus(status) {
        const statusGrid = document.getElementById('systemStatus');
        if (!statusGrid) return;

        statusGrid.innerHTML = '';

        Object.entries(status).forEach(([key, value]) => {
            const statusItem = document.createElement('div');
            statusItem.className = 'status-item';

            statusItem.innerHTML = `
                <span class="status-indicator ${value.status === 'error' ? 'error' : value.status === 'warning' ? 'warning' : ''}"></span>
                <span>${key}: ${value.status}</span>
            `;

            statusGrid.appendChild(statusItem);
        });
    }

    getActivityIcon(type) {
        const icons = {
            'task': 'tasks',
            'agent': 'robot',
            'system': 'server',
            'user': 'user'
        };
        return icons[type] || 'info-circle';
    }

    addRecentActivity(activity) {
        const activityList = document.getElementById('activityList');
        if (!activityList) return;

        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';

        activityItem.innerHTML = `
            <div class="activity-icon">
                <i class="fas fa-${this.getActivityIcon(activity.type)}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">${activity.title}</div>
                <div class="activity-time">${activity.time}</div>
            </div>
        `;

        // Add to beginning of list
        activityList.insertBefore(activityItem, activityList.firstChild);

        // Keep only last 10 activities
        while (activityList.children.length > 10) {
            activityList.removeChild(activityList.lastChild);
        }
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

    updateAgentsGrid(agents) {
        const agentsGrid = document.getElementById('agentsGrid');
        if (!agentsGrid) return;

        agentsGrid.innerHTML = '';

        Object.values(agents).forEach(agent => {
            const agentCard = document.createElement('div');
            agentCard.className = 'card';
            agentCard.innerHTML = `
                <div class="card-header">
                    <h4>${agent.name || agent.id}</h4>
                    <span class="badge badge-${agent.status === 'ready' ? 'success' : agent.status === 'busy' ? 'primary' : 'secondary'}">
                        ${agent.status || 'unknown'}
                    </span>
                </div>
                <div class="card-body">
                    <p>Type: ${agent.type}</p>
                    <p>Tasks: ${agent.task_count || 0}</p>
                    <p>Success Rate: ${agent.success_rate || 0}%</p>
                </div>
            `;

            agentsGrid.appendChild(agentCard);
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PinnacleDashboard();
});

// Global functions for HTML onclick handlers
function showLoginForm() {
    window.dashboard.showLoginForm();
}

function showRegisterForm() {
    window.dashboard.showRegisterForm();
}

function closeAuthModal() {
    window.dashboard.closeAuthModal();
}

function logout() {
    window.dashboard.logout();
}

function toggleSidebar() {
    window.dashboard.toggleSidebar();
}

// Agent control functions
function startAgent(agentType) {
    window.dashboard.showNotification(`${agentType} agent started`, 'success');
}

function pauseAgent(agentType) {
    window.dashboard.showNotification(`${agentType} agent paused`, 'warning');
}

function stopAgent(agentType) {
    window.dashboard.showNotification(`${agentType} agent stopped`, 'error');
}

// Workspace functions
function generateDesign() {
    window.dashboard.showNotification('Generating design...', 'info');
}

function exportDesign() {
    window.dashboard.showNotification('Design exported successfully', 'success');
}

function buildProject() {
    window.dashboard.showNotification('Building project...', 'info');
}

function deployProject() {
    window.dashboard.showNotification('Project deployed successfully', 'success');
}

function createNewAgent() {
    window.dashboard.showNotification('Create agent modal would open here', 'info');
}</content>
</edit_file>