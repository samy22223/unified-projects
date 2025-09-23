/**
 * Charts and Data Visualization Module
 * Handles all chart creation and updates using Chart.js
 */

class ChartManager {
    constructor() {
        this.charts = {};
        this.chartData = {};
    }

    initialize() {
        // Set Chart.js defaults
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
        this.createSystemLoadChart();
    }

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
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(107, 114, 128, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(107, 114, 128, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
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
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
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
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(107, 114, 128, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(107, 114, 128, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
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
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(107, 114, 128, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(107, 114, 128, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                },
                interaction: {
                    intersect: false
                }
            }
        });
    }

    createSystemLoadChart() {
        const ctx = document.getElementById('systemLoadChart');
        if (!ctx) return;

        this.charts.systemLoad = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true
                }, {
                    label: 'Memory Usage',
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
                },
                interaction: {
                    mode: 'index',
                    intersect: false
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
        this.charts.agentPerformance.update('none');
    }

    updateTaskDistributionChart(tasks) {
        if (!this.charts.taskDistribution) return;

        const completed = tasks.filter(t => t.status === 'completed').length;
        const inProgress = tasks.filter(t => t.status === 'in_progress').length;
        const failed = tasks.filter(t => t.status === 'failed').length;
        const queued = tasks.filter(t => t.status === 'queued').length;

        this.charts.taskDistribution.data.datasets[0].data = [completed, inProgress, failed, queued];
        this.charts.taskDistribution.update('none');
    }

    updatePerformanceChart(agents) {
        if (!this.charts.performance) return;

        const performanceData = [
            agents.autopilot?.performance || 0,
            agents.fabricai?.performance || 0,
            agents.builderx?.performance || 0,
            agents.insighor?.performance || 0,
            agents.connector?.performance || 0
        ];

        this.charts.performance.data.datasets[0].data = performanceData;
        this.charts.performance.update('none');
    }

    updateTrendChart(data) {
        if (!this.charts.trend) return;

        const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString());
        const loadData = data.map(d => d.system_load);

        this.charts.trend.data.labels = labels;
        this.charts.trend.data.datasets[0].data = loadData;
        this.charts.trend.update('none');
    }

    updateSystemLoadChart(data) {
        if (!this.charts.systemLoad) return;

        const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString());
        const cpuData = data.map(d => d.cpu_usage);
        const memoryData = data.map(d => d.memory_usage);

        this.charts.systemLoad.data.labels = labels;
        this.charts.systemLoad.data.datasets[0].data = cpuData;
        this.charts.systemLoad.data.datasets[1].data = memoryData;
        this.charts.systemLoad.update('none');
    }

    // Utility methods for chart data management
    addChartData(chartName, data) {
        if (!this.chartData[chartName]) {
            this.chartData[chartName] = [];
        }

        this.chartData[chartName].push(data);

        // Keep only last 50 data points
        if (this.chartData[chartName].length > 50) {
            this.chartData[chartName] = this.chartData[chartName].slice(-50);
        }
    }

    getChartData(chartName) {
        return this.chartData[chartName] || [];
    }

    clearChartData(chartName) {
        this.chartData[chartName] = [];
    }

    exportChartData(chartName, format = 'json') {
        const data = this.getChartData(chartName);
        
        if (format === 'csv') {
            return this.convertToCSV(data);
        }
        
        return JSON.stringify(data, null, 2);
    }

    convertToCSV(data) {
        if (data.length === 0) return '';
        
        const headers = Object.keys(data[0]);
        const csvRows = [
            headers.join(','),
            ...data.map(row => headers.map(header => row[header]).join(','))
        ];
        
        return csvRows.join('\n');
    }
}

// Export for global use
window.ChartManager = ChartManager;
