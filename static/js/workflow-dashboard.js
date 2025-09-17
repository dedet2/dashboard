// Workflow Dashboard JavaScript
// Author: AI Empire Platform
// Description: Frontend functionality for workflow automation dashboard

class WorkflowDashboard {
    constructor() {
        this.baseURL = '/api';
        this.token = localStorage.getItem('token');
        this.currentTab = 'triggers';
        this.charts = {};
        this.init();
    }

    init() {
        // Set default tab
        this.switchTab('triggers');
        this.loadDashboardStats();
        this.setupEventListeners();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            this.refreshCurrentTab();
        }, 30000);
    }

    setupEventListeners() {
        // Form submissions
        document.getElementById('create-trigger-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createTrigger(new FormData(e.target));
        });

        document.getElementById('create-rule-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createRule(new FormData(e.target));
        });
    }

    // API Helper Methods
    async apiRequest(endpoint, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`,
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            this.showNotification('API request failed: ' + error.message, 'error');
            throw error;
        }
    }

    // Tab Management
    switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.add('hidden');
        });

        // Remove active class from all buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('border-blue-500', 'text-blue-600');
            button.classList.add('border-transparent', 'text-gray-500');
        });

        // Show selected tab
        const selectedTab = document.getElementById(`${tabName}-tab`);
        if (selectedTab) {
            selectedTab.classList.remove('hidden');
        }

        // Activate selected button
        const selectedButton = document.querySelector(`[data-tab="${tabName}"]`);
        if (selectedButton) {
            selectedButton.classList.add('border-blue-500', 'text-blue-600');
            selectedButton.classList.remove('border-transparent', 'text-gray-500');
        }

        this.currentTab = tabName;
        this.loadTabContent(tabName);
    }

    async loadTabContent(tabName) {
        this.showLoading();
        
        try {
            switch (tabName) {
                case 'triggers':
                    await this.loadWorkflowTriggers();
                    break;
                case 'rules':
                    await this.loadBusinessRules();
                    break;
                case 'schedules':
                    await this.loadWorkflowSchedules();
                    break;
                case 'executions':
                    await this.loadWorkflowExecutions();
                    break;
                case 'notifications':
                    await this.loadNotificationChannels();
                    break;
                case 'analytics':
                    await this.loadAnalytics();
                    break;
            }
        } catch (error) {
            console.error(`Failed to load ${tabName}:`, error);
        } finally {
            this.hideLoading();
        }
    }

    async refreshCurrentTab() {
        if (this.currentTab) {
            await this.loadTabContent(this.currentTab);
        }
    }

    // Dashboard Statistics
    async loadDashboardStats() {
        try {
            const [triggers, rules, analytics] = await Promise.all([
                this.apiRequest('/workflows/triggers'),
                this.apiRequest('/workflows/rules'),
                this.apiRequest('/workflows/analytics')
            ]);

            const activeTriggers = triggers.filter(t => t.enabled).length;
            const totalRules = rules.length;
            const successRate = analytics.overview?.success_rate || 0;
            const executionsToday = analytics.overview?.total_executions || 0;

            document.getElementById('active-triggers').textContent = activeTriggers;
            document.getElementById('total-rules').textContent = totalRules;
            document.getElementById('success-rate').textContent = `${successRate.toFixed(1)}%`;
            document.getElementById('executions-today').textContent = executionsToday;
        } catch (error) {
            console.error('Failed to load dashboard stats:', error);
        }
    }

    // Workflow Triggers
    async loadWorkflowTriggers() {
        try {
            const triggers = await this.apiRequest('/workflows/triggers');
            this.renderTriggers(triggers);
        } catch (error) {
            console.error('Failed to load triggers:', error);
        }
    }

    renderTriggers(triggers) {
        const container = document.getElementById('triggers-list');
        
        if (triggers.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-bolt text-4xl mb-4"></i>
                    <p>No workflow triggers found. Create your first trigger to get started.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = triggers.map(trigger => `
            <div class="border border-gray-200 rounded-lg p-4 trigger-${trigger.trigger_type}">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center">
                            <h4 class="text-lg font-medium text-gray-900">${trigger.name}</h4>
                            <span class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${trigger.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                ${trigger.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                            <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                ${trigger.trigger_type}
                            </span>
                        </div>
                        <p class="text-sm text-gray-600 mt-1">${trigger.description || 'No description'}</p>
                        <div class="text-sm text-gray-500 mt-2">
                            <span><strong>Event Type:</strong> ${trigger.event_type}</span>
                            ${trigger.priority ? `<span class="ml-4"><strong>Priority:</strong> ${trigger.priority}</span>` : ''}
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="workflowDashboard.testTrigger(${trigger.id})" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-play"></i>
                        </button>
                        <button onclick="workflowDashboard.editTrigger(${trigger.id})" class="text-yellow-600 hover:text-yellow-800">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="workflowDashboard.deleteTrigger(${trigger.id})" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async createTrigger(formData) {
        try {
            const data = {
                name: formData.get('name'),
                description: formData.get('description'),
                trigger_type: formData.get('trigger_type'),
                event_type: formData.get('event_type'),
                enabled: true,
                priority: 5
            };

            await this.apiRequest('/workflows/triggers', {
                method: 'POST',
                body: JSON.stringify(data)
            });

            this.hideCreateTriggerModal();
            this.showNotification('Trigger created successfully!', 'success');
            await this.loadWorkflowTriggers();
            await this.loadDashboardStats();
        } catch (error) {
            this.showNotification('Failed to create trigger: ' + error.message, 'error');
        }
    }

    async deleteTrigger(triggerId) {
        if (!confirm('Are you sure you want to delete this trigger?')) return;

        try {
            await this.apiRequest(`/workflows/triggers/${triggerId}`, {
                method: 'DELETE'
            });

            this.showNotification('Trigger deleted successfully!', 'success');
            await this.loadWorkflowTriggers();
            await this.loadDashboardStats();
        } catch (error) {
            this.showNotification('Failed to delete trigger: ' + error.message, 'error');
        }
    }

    // Business Rules
    async loadBusinessRules() {
        try {
            const [rules, triggers] = await Promise.all([
                this.apiRequest('/workflows/rules'),
                this.apiRequest('/workflows/triggers')
            ]);
            this.renderRules(rules, triggers);
        } catch (error) {
            console.error('Failed to load rules:', error);
        }
    }

    renderRules(rules, triggers) {
        const container = document.getElementById('rules-list');
        
        if (rules.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-list-check text-4xl mb-4"></i>
                    <p>No business rules found. Create your first rule to get started.</p>
                </div>
            `;
            return;
        }

        const triggerMap = triggers.reduce((map, trigger) => {
            map[trigger.id] = trigger;
            return map;
        }, {});

        container.innerHTML = rules.map(rule => {
            const trigger = triggerMap[rule.trigger_id];
            return `
                <div class="border border-gray-200 rounded-lg p-4 bg-white">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="flex items-center">
                                <h4 class="text-lg font-medium text-gray-900">${rule.name}</h4>
                                <span class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${rule.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                    ${rule.enabled ? 'Enabled' : 'Disabled'}
                                </span>
                            </div>
                            <p class="text-sm text-gray-600 mt-1">${rule.description || 'No description'}</p>
                            <div class="text-sm text-gray-500 mt-2">
                                <span><strong>Trigger:</strong> ${trigger ? trigger.name : 'Unknown'}</span>
                                <span class="ml-4"><strong>Actions:</strong> ${rule.actions ? rule.actions.length : 0}</span>
                                ${rule.priority ? `<span class="ml-4"><strong>Priority:</strong> ${rule.priority}</span>` : ''}
                            </div>
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="workflowDashboard.testRule(${rule.id})" class="text-blue-600 hover:text-blue-800">
                                <i class="fas fa-play"></i>
                            </button>
                            <button onclick="workflowDashboard.editRule(${rule.id})" class="text-yellow-600 hover:text-yellow-800">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button onclick="workflowDashboard.deleteRule(${rule.id})" class="text-red-600 hover:text-red-800">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async createRule(formData) {
        try {
            const data = {
                name: formData.get('name'),
                description: formData.get('description'),
                trigger_id: parseInt(formData.get('trigger_id')),
                enabled: true,
                priority: 5,
                conditions: {},
                actions: []
            };

            await this.apiRequest('/workflows/rules', {
                method: 'POST',
                body: JSON.stringify(data)
            });

            this.hideCreateRuleModal();
            this.showNotification('Rule created successfully!', 'success');
            await this.loadBusinessRules();
            await this.loadDashboardStats();
        } catch (error) {
            this.showNotification('Failed to create rule: ' + error.message, 'error');
        }
    }

    async deleteRule(ruleId) {
        if (!confirm('Are you sure you want to delete this rule?')) return;

        try {
            await this.apiRequest(`/workflows/rules/${ruleId}`, {
                method: 'DELETE'
            });

            this.showNotification('Rule deleted successfully!', 'success');
            await this.loadBusinessRules();
            await this.loadDashboardStats();
        } catch (error) {
            this.showNotification('Failed to delete rule: ' + error.message, 'error');
        }
    }

    // Workflow Schedules
    async loadWorkflowSchedules() {
        try {
            const schedules = await this.apiRequest('/schedules');
            this.renderSchedules(schedules);
        } catch (error) {
            console.error('Failed to load schedules:', error);
        }
    }

    renderSchedules(schedules) {
        const container = document.getElementById('schedules-list');
        
        if (schedules.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-calendar-alt text-4xl mb-4"></i>
                    <p>No schedules found. Create your first schedule to automate workflows.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = schedules.map(schedule => `
            <div class="border border-gray-200 rounded-lg p-4 bg-white">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center">
                            <h4 class="text-lg font-medium text-gray-900">${schedule.name}</h4>
                            <span class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${schedule.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                ${schedule.enabled ? 'Active' : 'Inactive'}
                            </span>
                            <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                ${schedule.schedule_type}
                            </span>
                        </div>
                        <p class="text-sm text-gray-600 mt-1">${schedule.description || 'No description'}</p>
                        <div class="text-sm text-gray-500 mt-2">
                            ${schedule.cron_expression ? `<span><strong>Schedule:</strong> ${schedule.cron_expression}</span>` : ''}
                            ${schedule.interval_seconds ? `<span><strong>Interval:</strong> ${schedule.interval_seconds}s</span>` : ''}
                            ${schedule.execution_count ? `<span class="ml-4"><strong>Executions:</strong> ${schedule.execution_count}</span>` : ''}
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="workflowDashboard.executeSchedule(${schedule.id})" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-play"></i>
                        </button>
                        <button onclick="workflowDashboard.viewScheduleHistory(${schedule.id})" class="text-green-600 hover:text-green-800">
                            <i class="fas fa-history"></i>
                        </button>
                        <button onclick="workflowDashboard.deleteSchedule(${schedule.id})" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Workflow Executions
    async loadWorkflowExecutions() {
        try {
            const filter = document.getElementById('execution-filter')?.value || '';
            const params = filter ? `?status=${filter}` : '';
            const executions = await this.apiRequest(`/workflows/executions${params}`);
            this.renderExecutions(executions.executions || []);
        } catch (error) {
            console.error('Failed to load executions:', error);
        }
    }

    renderExecutions(executions) {
        const container = document.getElementById('executions-list');
        
        if (executions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-history text-4xl mb-4"></i>
                    <p>No executions found.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = executions.map(execution => `
            <div class="border border-gray-200 rounded-lg p-4 bg-white">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center">
                            <span class="text-sm font-mono text-gray-600">${execution.execution_id}</span>
                            <span class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium status-${execution.status}">
                                <i class="fas fa-circle mr-1 text-xs"></i>
                                ${execution.status.toUpperCase()}
                            </span>
                        </div>
                        <div class="text-sm text-gray-500 mt-2">
                            <span><strong>Started:</strong> ${new Date(execution.start_time).toLocaleString()}</span>
                            ${execution.end_time ? `<span class="ml-4"><strong>Completed:</strong> ${new Date(execution.end_time).toLocaleString()}</span>` : ''}
                        </div>
                        ${execution.result_data?.error ? `<p class="text-sm text-red-600 mt-2">${execution.result_data.error}</p>` : ''}
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="workflowDashboard.viewExecution('${execution.execution_id}')" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${execution.status === 'failed' ? `<button onclick="workflowDashboard.retryExecution('${execution.execution_id}')" class="text-green-600 hover:text-green-800"><i class="fas fa-redo"></i></button>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Notification Channels
    async loadNotificationChannels() {
        try {
            const channels = await this.apiRequest('/notifications/channels');
            this.renderNotificationChannels(channels);
        } catch (error) {
            console.error('Failed to load notification channels:', error);
        }
    }

    renderNotificationChannels(channels) {
        const container = document.getElementById('notifications-list');
        
        if (channels.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-bell text-4xl mb-4"></i>
                    <p>No notification channels configured. Add channels to receive alerts.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = channels.map(channel => `
            <div class="border border-gray-200 rounded-lg p-4 bg-white">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center">
                            <h4 class="text-lg font-medium text-gray-900">${channel.name}</h4>
                            <span class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${channel.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                ${channel.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                            <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                ${channel.channel_type}
                            </span>
                        </div>
                        <div class="text-sm text-gray-500 mt-2">
                            <span><strong>Priority:</strong> ${channel.priority || 'N/A'}</span>
                            ${channel.rate_limit ? `<span class="ml-4"><strong>Rate Limit:</strong> ${channel.rate_limit}</span>` : ''}
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="workflowDashboard.testNotificationChannel(${channel.id})" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-bell"></i>
                        </button>
                        <button onclick="workflowDashboard.editNotificationChannel(${channel.id})" class="text-yellow-600 hover:text-yellow-800">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="workflowDashboard.deleteNotificationChannel(${channel.id})" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Analytics
    async loadAnalytics() {
        try {
            const analytics = await this.apiRequest('/workflows/analytics');
            this.renderAnalytics(analytics);
        } catch (error) {
            console.error('Failed to load analytics:', error);
        }
    }

    renderAnalytics(analytics) {
        this.renderExecutionTrendsChart(analytics.daily_trends || {});
        this.renderSuccessRateChart(analytics.overview || {});
        this.renderPerformanceMetrics(analytics.overview || {});
    }

    renderExecutionTrendsChart(dailyTrends) {
        const ctx = document.getElementById('execution-trends-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.executionTrends) {
            this.charts.executionTrends.destroy();
        }

        const labels = Object.keys(dailyTrends).sort();
        const successData = labels.map(date => dailyTrends[date]?.successful || 0);
        const failedData = labels.map(date => dailyTrends[date]?.failed || 0);

        this.charts.executionTrends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Successful',
                        data: successData,
                        borderColor: '#10b981',
                        backgroundColor: '#10b98120',
                        tension: 0.1
                    },
                    {
                        label: 'Failed',
                        data: failedData,
                        borderColor: '#ef4444',
                        backgroundColor: '#ef444420',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    renderSuccessRateChart(overview) {
        const ctx = document.getElementById('success-rate-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.successRate) {
            this.charts.successRate.destroy();
        }

        const successRate = overview.success_rate || 0;
        const failureRate = 100 - successRate;

        this.charts.successRate = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Success', 'Failure'],
                datasets: [{
                    data: [successRate, failureRate],
                    backgroundColor: ['#10b981', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    renderPerformanceMetrics(overview) {
        const container = document.getElementById('performance-metrics');
        if (!container) return;

        container.innerHTML = `
            <div class="text-center">
                <div class="text-2xl font-bold text-gray-900">${overview.total_executions || 0}</div>
                <div class="text-sm text-gray-500">Total Executions</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-green-600">${overview.successful_executions || 0}</div>
                <div class="text-sm text-gray-500">Successful</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-red-600">${overview.failed_executions || 0}</div>
                <div class="text-sm text-gray-500">Failed</div>
            </div>
        `;
    }

    // Modal Management
    showCreateTriggerModal() {
        document.getElementById('create-trigger-modal').classList.remove('hidden');
    }

    hideCreateTriggerModal() {
        document.getElementById('create-trigger-modal').classList.add('hidden');
        document.getElementById('create-trigger-form').reset();
    }

    async showCreateRuleModal() {
        // Load triggers for dropdown
        try {
            const triggers = await this.apiRequest('/workflows/triggers');
            const select = document.getElementById('rule-trigger-select');
            select.innerHTML = triggers.map(trigger => 
                `<option value="${trigger.id}">${trigger.name}</option>`
            ).join('');
        } catch (error) {
            console.error('Failed to load triggers for rule modal:', error);
        }

        document.getElementById('create-rule-modal').classList.remove('hidden');
    }

    hideCreateRuleModal() {
        document.getElementById('create-rule-modal').classList.add('hidden');
        document.getElementById('create-rule-form').reset();
    }

    // Utility Methods
    showLoading() {
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Action Methods (placeholder implementations)
    async testTrigger(triggerId) {
        this.showNotification('Testing trigger...', 'info');
        // Implementation would test the trigger
    }

    async testRule(ruleId) {
        this.showNotification('Testing rule...', 'info');
        // Implementation would test the rule
    }

    async executeSchedule(scheduleId) {
        try {
            await this.apiRequest(`/schedules/${scheduleId}/execute`, {
                method: 'POST'
            });
            this.showNotification('Schedule executed successfully!', 'success');
        } catch (error) {
            this.showNotification('Failed to execute schedule: ' + error.message, 'error');
        }
    }

    async retryExecution(executionId) {
        try {
            await this.apiRequest(`/workflows/executions/${executionId}/retry`, {
                method: 'POST'
            });
            this.showNotification('Execution retry initiated!', 'success');
            await this.loadWorkflowExecutions();
        } catch (error) {
            this.showNotification('Failed to retry execution: ' + error.message, 'error');
        }
    }

    // Placeholder methods for future implementation
    editTrigger(triggerId) { this.showNotification('Edit trigger functionality coming soon!', 'info'); }
    editRule(ruleId) { this.showNotification('Edit rule functionality coming soon!', 'info'); }
    viewScheduleHistory(scheduleId) { this.showNotification('Schedule history functionality coming soon!', 'info'); }
    deleteSchedule(scheduleId) { this.showNotification('Delete schedule functionality coming soon!', 'info'); }
    viewExecution(executionId) { this.showNotification('View execution details functionality coming soon!', 'info'); }
    testNotificationChannel(channelId) { this.showNotification('Test notification functionality coming soon!', 'info'); }
    editNotificationChannel(channelId) { this.showNotification('Edit notification channel functionality coming soon!', 'info'); }
    deleteNotificationChannel(channelId) { this.showNotification('Delete notification channel functionality coming soon!', 'info'); }
    showCreateNotificationModal() { this.showNotification('Create notification channel functionality coming soon!', 'info'); }
    showScheduleTemplates() { this.showNotification('Schedule templates functionality coming soon!', 'info'); }
    showCreateScheduleModal() { this.showNotification('Create schedule functionality coming soon!', 'info'); }
}

// Global functions for HTML onclick handlers
function switchTab(tabName) {
    workflowDashboard.switchTab(tabName);
}

function showCreateTriggerModal() {
    workflowDashboard.showCreateTriggerModal();
}

function hideCreateTriggerModal() {
    workflowDashboard.hideCreateTriggerModal();
}

function showCreateRuleModal() {
    workflowDashboard.showCreateRuleModal();
}

function hideCreateRuleModal() {
    workflowDashboard.hideCreateRuleModal();
}

// Initialize dashboard when page loads
let workflowDashboard;
document.addEventListener('DOMContentLoaded', function() {
    workflowDashboard = new WorkflowDashboard();
});