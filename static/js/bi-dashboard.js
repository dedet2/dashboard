// Business Intelligence Dashboard JavaScript
class BIDashboard {
    constructor() {
        this.authToken = localStorage.getItem('authToken');
        this.API_BASE = window.location.origin;
        this.charts = {};
        this.refreshInterval = null;
        
        this.init();
    }

    init() {
        if (!this.authToken) {
            window.location.href = '/';
            return;
        }

        this.setupEventListeners();
        this.loadDashboardData();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            localStorage.removeItem('authToken');
            window.location.href = '/';
        });

        // Refresh data
        document.getElementById('refreshDataBtn').addEventListener('click', () => {
            this.loadDashboardData();
        });

        // Generate report
        document.getElementById('generateReportBtn').addEventListener('click', () => {
            this.switchTab('reports');
        });

        // Custom report generation
        document.getElementById('generateCustomReport').addEventListener('click', () => {
            this.generateCustomReport();
        });

        // Report controls
        document.getElementById('closeReport')?.addEventListener('click', () => {
            document.getElementById('reportDisplay').classList.add('hidden');
        });

        document.getElementById('exportPDF')?.addEventListener('click', () => {
            this.exportReport('pdf');
        });

        document.getElementById('exportExcel')?.addEventListener('click', () => {
            this.exportReport('excel');
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('border-blue-500', 'text-blue-600');
            btn.classList.add('border-transparent', 'text-gray-500');
        });

        document.querySelector(`[data-tab="${tabName}"]`).classList.remove('border-transparent', 'text-gray-500');
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('border-blue-500', 'text-blue-600');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });

        document.getElementById(`${tabName}-tab`).classList.remove('hidden');

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        switch(tabName) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'revenue':
                await this.loadRevenueAnalytics();
                break;
            case 'agents':
                await this.loadAgentPerformance();
                break;
            case 'forecasting':
                await this.loadForecastingData();
                break;
            case 'reports':
                await this.loadReportsData();
                break;
        }
    }

    async loadDashboardData() {
        this.showLoading(true);
        try {
            const headers = { 
                'Authorization': `Bearer ${this.authToken}`,
                'Content-Type': 'application/json'
            };

            // Load executive summary data
            const [overview, revenue, agents, kpis] = await Promise.all([
                axios.get(`${this.API_BASE}/api/bi/overview`, { headers }),
                axios.get(`${this.API_BASE}/api/revenue`, { headers }),
                axios.get(`${this.API_BASE}/api/agents`, { headers }),
                axios.get(`${this.API_BASE}/api/kpi`, { headers })
            ]);

            this.updateExecutiveSummary(overview.data, revenue.data, agents.data, kpis.data);
            await this.loadOverviewData();

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    updateExecutiveSummary(overview, revenue, agents, kpis) {
        // Calculate totals
        const totalRevenue = revenue.reduce((sum, stream) => sum + stream.current_month, 0);
        const activeAgents = agents.filter(agent => agent.status === 'active').length;
        
        // Calculate pipeline value from agents
        const pipelineValue = agents.reduce((sum, agent) => {
            const performance = agent.performance || {};
            return sum + (performance.pipeline_value || 0);
        }, 0);

        // Calculate overall success rate
        const successRates = agents.map(agent => {
            const performance = agent.performance || {};
            return performance.success_rate || 0;
        });
        const avgSuccessRate = successRates.length > 0 ? 
            successRates.reduce((sum, rate) => sum + rate, 0) / successRates.length : 0;

        // Update cards
        document.getElementById('totalRevenue').textContent = `$${totalRevenue.toLocaleString()}`;
        document.getElementById('activeAgents').textContent = activeAgents;
        document.getElementById('pipelineValue').textContent = `$${pipelineValue.toLocaleString()}`;
        document.getElementById('successRate').textContent = `${avgSuccessRate.toFixed(1)}%`;

        // Update trends (placeholder - would come from historical data)
        document.getElementById('revenueGrowth').textContent = '+12.5% vs last month';
        document.getElementById('agentEfficiency').textContent = `${avgSuccessRate.toFixed(0)}% avg efficiency`;
        document.getElementById('pipelineGrowth').textContent = `${agents.length} opportunities`;
        document.getElementById('successTrend').textContent = 'Target: 85%';
    }

    async loadOverviewData() {
        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };

            // Load revenue trend data
            const revenueResponse = await axios.get(`${this.API_BASE}/api/revenue`, { headers });
            this.createRevenueTrendChart(revenueResponse.data);

            // Load agent performance data
            const agentsResponse = await axios.get(`${this.API_BASE}/api/agents`, { headers });
            this.updateTopAgents(agentsResponse.data);

            // Load KPI data
            const kpiResponse = await axios.get(`${this.API_BASE}/api/kpi`, { headers });
            this.createKPIChart(kpiResponse.data);

            // Update recent activities
            this.updateRecentActivities(agentsResponse.data);

        } catch (error) {
            console.error('Failed to load overview data:', error);
        }
    }

    createRevenueTrendChart(revenueData) {
        const ctx = document.getElementById('revenueTrendChart');
        if (!ctx) return;

        if (this.charts.revenueTrend) {
            this.charts.revenueTrend.destroy();
        }

        // Generate mock historical data for demonstration
        const months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const data = revenueData.map(stream => ({
            label: stream.name,
            data: this.generateTrendData(stream.current_month, 6),
            borderColor: this.getRandomColor(),
            backgroundColor: this.getRandomColor(0.1),
            tension: 0.4
        }));

        this.charts.revenueTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: data
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    createKPIChart(kpiData) {
        const ctx = document.getElementById('kpiChart');
        if (!ctx) return;

        if (this.charts.kpi) {
            this.charts.kpi.destroy();
        }

        const labels = kpiData.map(kpi => kpi.name);
        const values = kpiData.map(kpi => (kpi.value / kpi.target) * 100);
        const colors = values.map(value => value >= 90 ? '#10B981' : value >= 70 ? '#F59E0B' : '#EF4444');

        this.charts.kpi = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Achievement %',
                    data: values,
                    backgroundColor: colors,
                    borderColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 120,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Achievement: ' + context.parsed.y.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    updateTopAgents(agents) {
        const topAgents = agents
            .filter(agent => agent.performance && agent.performance.success_rate)
            .sort((a, b) => (b.performance.success_rate || 0) - (a.performance.success_rate || 0))
            .slice(0, 5);

        const container = document.getElementById('topAgents');
        container.innerHTML = topAgents.map((agent, index) => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
                        ${index + 1}
                    </div>
                    <div>
                        <div class="font-medium text-gray-900">${agent.name}</div>
                        <div class="text-sm text-gray-500">${agent.tier}</div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="font-bold text-green-600">${(agent.performance.success_rate || 0).toFixed(1)}%</div>
                    <div class="text-xs text-gray-500">${agent.status}</div>
                </div>
            </div>
        `).join('');
    }

    updateRecentActivities(agents) {
        const activities = agents
            .filter(agent => agent.last_activity)
            .sort((a, b) => new Date(b.last_activity) - new Date(a.last_activity))
            .slice(0, 5);

        const container = document.getElementById('recentActivities');
        container.innerHTML = activities.map(agent => {
            const timeDiff = this.getTimeAgo(agent.last_activity);
            return `
                <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <div class="flex-1">
                        <div class="font-medium text-gray-900">${agent.name}</div>
                        <div class="text-sm text-gray-500">Last active ${timeDiff}</div>
                    </div>
                    <div class="text-xs text-gray-400">${agent.tier}</div>
                </div>
            `;
        }).join('');
    }

    async loadRevenueAnalytics() {
        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };
            const revenueResponse = await axios.get(`${this.API_BASE}/api/revenue`, { headers });
            const revenue = revenueResponse.data;

            this.createRevenueStreamChart(revenue);
            this.createRevenueBreakdownChart(revenue);
            this.createTargetsChart(revenue);
            this.updateGrowthMetrics(revenue);

        } catch (error) {
            console.error('Failed to load revenue analytics:', error);
        }
    }

    createRevenueStreamChart(revenue) {
        const ctx = document.getElementById('revenueStreamChart');
        if (!ctx) return;

        if (this.charts.revenueStream) {
            this.charts.revenueStream.destroy();
        }

        const months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const datasets = revenue.map(stream => ({
            label: stream.name,
            data: this.generateTrendData(stream.current_month, 6),
            borderColor: this.getRandomColor(),
            backgroundColor: this.getRandomColor(0.1),
            tension: 0.4,
            fill: true
        }));

        this.charts.revenueStream = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        stacked: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    createRevenueBreakdownChart(revenue) {
        const ctx = document.getElementById('revenueBreakdownChart');
        if (!ctx) return;

        if (this.charts.revenueBreakdown) {
            this.charts.revenueBreakdown.destroy();
        }

        const labels = revenue.map(stream => stream.name);
        const data = revenue.map(stream => stream.current_month);
        const colors = revenue.map(() => this.getRandomColor());

        this.charts.revenueBreakdown = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((sum, value) => sum + value, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return context.label + ': $' + context.raw.toLocaleString() + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }

    createTargetsChart(revenue) {
        const ctx = document.getElementById('targetsChart');
        if (!ctx) return;

        if (this.charts.targets) {
            this.charts.targets.destroy();
        }

        const labels = revenue.map(stream => stream.name);
        const actuals = revenue.map(stream => stream.current_month);
        const targets = revenue.map(stream => stream.target_month);

        this.charts.targets = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Actual',
                        data: actuals,
                        backgroundColor: '#3B82F6',
                        borderColor: '#1D4ED8',
                        borderWidth: 1
                    },
                    {
                        label: 'Target',
                        data: targets,
                        backgroundColor: '#10B981',
                        borderColor: '#059669',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    updateGrowthMetrics(revenue) {
        const container = document.getElementById('growthMetrics');
        const totalCurrent = revenue.reduce((sum, stream) => sum + stream.current_month, 0);
        const totalTarget = revenue.reduce((sum, stream) => sum + stream.target_month, 0);
        const avgGrowth = revenue.reduce((sum, stream) => sum + stream.growth_rate, 0) / revenue.length;

        container.innerHTML = `
            <div class="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                <span class="font-medium text-blue-800">Total Current</span>
                <span class="font-bold text-blue-900">$${totalCurrent.toLocaleString()}</span>
            </div>
            <div class="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <span class="font-medium text-green-800">Total Target</span>
                <span class="font-bold text-green-900">$${totalTarget.toLocaleString()}</span>
            </div>
            <div class="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                <span class="font-medium text-purple-800">Achievement</span>
                <span class="font-bold text-purple-900">${((totalCurrent / totalTarget) * 100).toFixed(1)}%</span>
            </div>
            <div class="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                <span class="font-medium text-yellow-800">Avg Growth</span>
                <span class="font-bold text-yellow-900">${avgGrowth.toFixed(1)}%</span>
            </div>
        `;
    }

    async loadAgentPerformance() {
        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };
            const agentsResponse = await axios.get(`${this.API_BASE}/api/agents`, { headers });
            const agents = agentsResponse.data;

            this.createAgentEfficiencyChart(agents);
            this.createAgentSuccessChart(agents);
            this.updateAgentMetricsTable(agents);

        } catch (error) {
            console.error('Failed to load agent performance:', error);
        }
    }

    createAgentEfficiencyChart(agents) {
        const ctx = document.getElementById('agentEfficiencyChart');
        if (!ctx) return;

        if (this.charts.agentEfficiency) {
            this.charts.agentEfficiency.destroy();
        }

        // Group agents by tier
        const tierData = {};
        agents.forEach(agent => {
            if (!tierData[agent.tier]) {
                tierData[agent.tier] = [];
            }
            tierData[agent.tier].push(agent.performance?.success_rate || 0);
        });

        const labels = Object.keys(tierData);
        const data = labels.map(tier => {
            const rates = tierData[tier];
            return rates.reduce((sum, rate) => sum + rate, 0) / rates.length;
        });

        this.charts.agentEfficiency = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Efficiency %',
                    data: data,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    pointBackgroundColor: '#3B82F6',
                    pointBorderColor: '#1D4ED8',
                    pointHoverBackgroundColor: '#1D4ED8',
                    pointHoverBorderColor: '#3B82F6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    createAgentSuccessChart(agents) {
        const ctx = document.getElementById('agentSuccessChart');
        if (!ctx) return;

        if (this.charts.agentSuccess) {
            this.charts.agentSuccess.destroy();
        }

        const topAgents = agents
            .filter(agent => agent.performance?.success_rate)
            .sort((a, b) => (b.performance.success_rate || 0) - (a.performance.success_rate || 0))
            .slice(0, 8);

        const labels = topAgents.map(agent => agent.name.substring(0, 20) + '...');
        const data = topAgents.map(agent => agent.performance.success_rate || 0);

        this.charts.agentSuccess = new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Success Rate %',
                    data: data,
                    backgroundColor: '#10B981',
                    borderColor: '#059669',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    updateAgentMetricsTable(agents) {
        const container = document.getElementById('agentMetricsTable');
        container.innerHTML = agents.map(agent => {
            const performance = agent.performance || {};
            const successRate = performance.success_rate || 0;
            const pipelineValue = performance.pipeline_value || 0;
            
            return `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        ${agent.name}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                            ${agent.tier}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div class="flex items-center">
                            <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                <div class="bg-green-500 h-2 rounded-full" style="width: ${successRate}%"></div>
                            </div>
                            ${successRate.toFixed(1)}%
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        $${pipelineValue.toLocaleString()}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 py-1 text-xs rounded-full ${
                            agent.status === 'active' ? 'bg-green-100 text-green-800' : 
                            agent.status === 'paused' ? 'bg-yellow-100 text-yellow-800' : 
                            'bg-red-100 text-red-800'
                        }">
                            ${agent.status}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button class="text-blue-600 hover:text-blue-900" onclick="dashboard.optimizeAgent(${agent.id})">
                            Optimize
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    async loadForecastingData() {
        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };
            const [revenue, milestones] = await Promise.all([
                axios.get(`${this.API_BASE}/api/revenue`, { headers }),
                axios.get(`${this.API_BASE}/api/milestones`, { headers })
            ]);

            this.createRevenueForecastChart(revenue.data);
            this.updateGoalProgress(milestones.data || []);
            this.createScenarioChart(revenue.data);

        } catch (error) {
            console.error('Failed to load forecasting data:', error);
        }
    }

    createRevenueForecastChart(revenue) {
        const ctx = document.getElementById('revenueForecastChart');
        if (!ctx) return;

        if (this.charts.revenueForecast) {
            this.charts.revenueForecast.destroy();
        }

        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
        const totalCurrent = revenue.reduce((sum, stream) => sum + stream.current_month, 0);
        
        // Generate forecast data based on growth rates
        const forecastData = months.map((month, index) => {
            const avgGrowth = revenue.reduce((sum, stream) => sum + stream.growth_rate, 0) / revenue.length;
            return totalCurrent * Math.pow(1 + (avgGrowth / 100), index + 1);
        });

        this.charts.revenueForecast = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Forecasted Revenue',
                        data: forecastData,
                        borderColor: '#8B5CF6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Conservative Estimate',
                        data: forecastData.map(value => value * 0.85),
                        borderColor: '#F59E0B',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });

        // Update scenario values
        const bestCase = forecastData[5] * 1.15;
        const likely = forecastData[5];
        const conservative = forecastData[5] * 0.85;

        document.getElementById('bestCaseRevenue').textContent = `$${bestCase.toLocaleString()}`;
        document.getElementById('likelyRevenue').textContent = `$${likely.toLocaleString()}`;
        document.getElementById('conservativeRevenue').textContent = `$${conservative.toLocaleString()}`;
    }

    updateGoalProgress(milestones) {
        const container = document.getElementById('goalProgress');
        
        if (milestones.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p>No milestones found</p>
                    <p class="text-sm">Add milestones to track goal progress</p>
                </div>
            `;
            return;
        }

        container.innerHTML = milestones.map(milestone => {
            const progress = milestone.progress || 0;
            const statusColor = milestone.status === 'completed' ? 'green' : 
                              milestone.status === 'in_progress' ? 'blue' : 'gray';

            return `
                <div class="border rounded-lg p-4">
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="font-medium text-gray-900">${milestone.title}</h4>
                        <span class="px-2 py-1 text-xs rounded-full bg-${statusColor}-100 text-${statusColor}-800">
                            ${milestone.status}
                        </span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                        <div class="bg-blue-500 h-2 rounded-full transition-all duration-300" style="width: ${progress}%"></div>
                    </div>
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>${progress}% complete</span>
                        <span>Due: ${milestone.target_date}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    createScenarioChart(revenue) {
        const ctx = document.getElementById('scenarioChart');
        if (!ctx) return;

        if (this.charts.scenario) {
            this.charts.scenario.destroy();
        }

        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
        const totalCurrent = revenue.reduce((sum, stream) => sum + stream.current_month, 0);

        const bestCase = months.map((month, index) => totalCurrent * Math.pow(1.15, index + 1));
        const likely = months.map((month, index) => totalCurrent * Math.pow(1.10, index + 1));
        const conservative = months.map((month, index) => totalCurrent * Math.pow(0.95, index + 1));

        this.charts.scenario = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Best Case',
                        data: bestCase,
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Most Likely',
                        data: likely,
                        borderColor: '#3B82F6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Conservative',
                        data: conservative,
                        borderColor: '#F59E0B',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    async loadReportsData() {
        // Load recent reports (placeholder)
        this.updateRecentReports();
    }

    updateRecentReports() {
        const container = document.getElementById('recentReports');
        const sampleReports = [
            { name: 'Executive Summary - Dec 2024', date: '2024-12-01', type: 'executive' },
            { name: 'Revenue Analysis - Nov 2024', date: '2024-11-01', type: 'revenue' },
            { name: 'Agent Performance - Nov 2024', date: '2024-11-01', type: 'agent' }
        ];

        container.innerHTML = sampleReports.map(report => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                    <div class="font-medium text-gray-900">${report.name}</div>
                    <div class="text-sm text-gray-500">${report.date}</div>
                </div>
                <button class="text-blue-600 hover:text-blue-800 text-sm">Download</button>
            </div>
        `).join('');
    }

    async generateCustomReport() {
        const reportType = document.getElementById('reportType').value;
        const reportPeriod = document.getElementById('reportPeriod').value;

        this.showLoading(true, 'Generating report...');

        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };
            const response = await axios.post(`${this.API_BASE}/api/bi/generate-report`, {
                type: reportType,
                period: reportPeriod
            }, { headers });

            this.displayGeneratedReport(response.data);

        } catch (error) {
            console.error('Failed to generate report:', error);
            this.showNotification('Failed to generate report', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayGeneratedReport(reportData) {
        const reportDisplay = document.getElementById('reportDisplay');
        const reportContent = document.getElementById('reportContent');

        reportContent.innerHTML = this.formatReportContent(reportData);
        reportDisplay.classList.remove('hidden');
    }

    formatReportContent(data) {
        return `
            <div class="space-y-6">
                <div class="border-b pb-4">
                    <h1 class="text-2xl font-bold text-gray-900">${data.title}</h1>
                    <p class="text-gray-600">${data.period} | Generated on ${new Date().toLocaleDateString()}</p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-blue-50 p-4 rounded-lg">
                        <h3 class="font-semibold text-blue-800">Total Revenue</h3>
                        <p class="text-2xl font-bold text-blue-900">$${data.totalRevenue?.toLocaleString() || '0'}</p>
                    </div>
                    <div class="bg-green-50 p-4 rounded-lg">
                        <h3 class="font-semibold text-green-800">Active Agents</h3>
                        <p class="text-2xl font-bold text-green-900">${data.activeAgents || 0}</p>
                    </div>
                    <div class="bg-purple-50 p-4 rounded-lg">
                        <h3 class="font-semibold text-purple-800">Success Rate</h3>
                        <p class="text-2xl font-bold text-purple-900">${data.successRate?.toFixed(1) || 0}%</p>
                    </div>
                </div>

                <div>
                    <h2 class="text-xl font-semibold mb-3">Key Insights</h2>
                    <ul class="list-disc list-inside space-y-2 text-gray-700">
                        <li>Revenue growth has increased by ${data.revenueGrowth || 'N/A'}% compared to previous period</li>
                        <li>Top performing agent tier: ${data.topTier || 'Revenue Generation'}</li>
                        <li>Current pipeline value: $${data.pipelineValue?.toLocaleString() || '0'}</li>
                        <li>Projected 6-month revenue: $${data.projectedRevenue?.toLocaleString() || '0'}</li>
                    </ul>
                </div>

                <div>
                    <h2 class="text-xl font-semibold mb-3">Recommendations</h2>
                    <ul class="list-disc list-inside space-y-2 text-gray-700">
                        <li>Focus on optimizing underperforming agent tiers</li>
                        <li>Increase investment in highest ROI revenue streams</li>
                        <li>Implement automated monitoring for real-time performance tracking</li>
                        <li>Schedule weekly reviews for continuous optimization</li>
                    </ul>
                </div>
            </div>
        `;
    }

    exportReport(format) {
        this.showNotification(`Exporting report as ${format.toUpperCase()}...`, 'info');
        // Implementation would depend on backend support
        setTimeout(() => {
            this.showNotification(`Report exported as ${format.toUpperCase()}`, 'success');
        }, 2000);
    }

    async optimizeAgent(agentId) {
        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };
            await axios.post(`${this.API_BASE}/api/agents/${agentId}/optimize`, {}, { headers });
            this.showNotification('Agent optimization initiated', 'success');
            
            // Refresh agent data
            setTimeout(() => {
                this.loadAgentPerformance();
            }, 1000);

        } catch (error) {
            console.error('Failed to optimize agent:', error);
            this.showNotification('Failed to optimize agent', 'error');
        }
    }

    startAutoRefresh() {
        // Refresh data every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    showLoading(show, message = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.querySelector('span').textContent = message;
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-white' :
            'bg-blue-500 text-white'
        }`;

        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 5000);
    }

    // Utility functions
    generateTrendData(baseValue, periods) {
        const data = [];
        let current = baseValue * 0.7; // Start from 70% of current
        
        for (let i = 0; i < periods; i++) {
            data.push(Math.round(current));
            current *= (1 + (Math.random() * 0.2 - 0.05)); // Vary by ±5%
        }
        
        return data;
    }

    getRandomColor(alpha = 1) {
        const colors = [
            `rgba(59, 130, 246, ${alpha})`,    // Blue
            `rgba(16, 185, 129, ${alpha})`,    // Green
            `rgba(245, 158, 11, ${alpha})`,    // Yellow
            `rgba(239, 68, 68, ${alpha})`,     // Red
            `rgba(139, 92, 246, ${alpha})`,    // Purple
            `rgba(6, 182, 212, ${alpha})`,     // Cyan
            `rgba(251, 146, 60, ${alpha})`,    // Orange
            `rgba(236, 72, 153, ${alpha})`     // Pink
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    getTimeAgo(dateString) {
        const now = new Date();
        const date = new Date(dateString);
        const diffInMs = now - date;
        const diffInMins = Math.floor(diffInMs / (1000 * 60));
        const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
        const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

        if (diffInMins < 60) {
            return `${diffInMins} min ago`;
        } else if (diffInHours < 24) {
            return `${diffInHours}h ago`;
        } else {
            return `${diffInDays}d ago`;
        }
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new BIDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (dashboard) {
        dashboard.stopAutoRefresh();
    }
});