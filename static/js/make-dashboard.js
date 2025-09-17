/**
 * Make.com Dashboard JavaScript
 * Handles the frontend interface for Make.com workflow automation
 */

class MakeDashboard {
    constructor() {
        this.currentScenarioId = null;
        this.scenarios = [];
        this.templates = [];
        this.bridges = [];
        this.stats = {};
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialData();
        this.setupTabs();
    }
    
    bindEvents() {
        // Button events
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadInitialData());
        document.getElementById('createScenarioBtn').addEventListener('click', () => this.showCreateScenarioModal());
        document.getElementById('createBridgeBtn').addEventListener('click', () => this.showCreateBridgeModal());
        
        // Modal events
        document.getElementById('closeCreateModal').addEventListener('click', () => this.hideModal('createScenarioModal'));
        document.getElementById('cancelCreate').addEventListener('click', () => this.hideModal('createScenarioModal'));
        document.getElementById('closeDetailsModal').addEventListener('click', () => this.hideModal('scenarioDetailsModal'));
        document.getElementById('closeTestModal').addEventListener('click', () => this.hideModal('testScenarioModal'));
        document.getElementById('cancelTest').addEventListener('click', () => this.hideModal('testScenarioModal'));
        
        // Form events
        document.getElementById('createScenarioForm').addEventListener('submit', (e) => this.handleCreateScenario(e));
        document.getElementById('executeTest').addEventListener('click', () => this.executeScenarioTest());
        
        // Filter events
        document.getElementById('categoryFilter').addEventListener('change', (e) => this.filterScenarios(e.target.value));
        
        // Close modals when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.hideModal(e.target.id);
            }
        });
    }
    
    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                
                // Update active tab button
                tabButtons.forEach(btn => btn.classList.remove('active', 'border-blue-500', 'text-blue-600'));
                button.classList.add('active', 'border-blue-500', 'text-blue-600');
                
                // Show corresponding tab content
                tabContents.forEach(content => content.classList.add('hidden'));
                document.getElementById(`${tabName}-tab`).classList.remove('hidden');
                
                // Load tab-specific data
                this.loadTabData(tabName);
            });
        });
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadStats(),
                this.loadScenarios(),
                this.loadTemplates(),
                this.loadBridges()
            ]);
            this.updateDashboard();
        } catch (error) {
            this.showNotification('Error loading data: ' + error.message, 'error');
        }
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/make/stats');
            const data = await response.json();
            
            if (data.success) {
                this.stats = data.stats;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    async loadScenarios() {
        try {
            const response = await fetch('/api/make/scenarios');
            const data = await response.json();
            
            if (data.success) {
                this.scenarios = data.scenarios;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error loading scenarios:', error);
        }
    }
    
    async loadTemplates() {
        try {
            const response = await fetch('/api/make/templates');
            const data = await response.json();
            
            if (data.success) {
                this.templates = Object.values(data.templates);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error loading templates:', error);
        }
    }
    
    async loadBridges() {
        try {
            const response = await fetch('/api/make/bridges');
            const data = await response.json();
            
            if (data.success) {
                this.bridges = data.bridges;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error loading bridges:', error);
        }
    }
    
    updateDashboard() {
        this.updateStats();
        this.renderScenarios();
        this.renderTemplates();
        this.renderBridges();
    }
    
    updateStats() {
        document.getElementById('totalScenarios').textContent = this.stats.scenarios?.total || 0;
        document.getElementById('activeScenarios').textContent = this.stats.scenarios?.active || 0;
        document.getElementById('totalExecutions').textContent = this.stats.executions?.total || 0;
        document.getElementById('successRate').textContent = (this.stats.executions?.success_rate || 0) + '%';
    }
    
    renderScenarios(filter = '') {
        const container = document.getElementById('scenariosContainer');
        let filteredScenarios = this.scenarios;
        
        if (filter) {
            filteredScenarios = this.scenarios.filter(scenario => scenario.category === filter);
        }
        
        if (filteredScenarios.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <i class="fas fa-robot text-gray-300 text-4xl mb-4"></i>
                    <p class="text-gray-500">No scenarios found. Create your first scenario to get started!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = filteredScenarios.map(scenario => `
            <div class="bg-white overflow-hidden shadow rounded-lg card-hover">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-medium text-gray-900 truncate">${scenario.name}</h3>
                        <div class="flex items-center">
                            <span class="status-dot ${scenario.enabled ? 'status-active' : 'status-inactive'}"></span>
                            <span class="text-sm text-gray-500">${scenario.enabled ? 'Active' : 'Inactive'}</span>
                        </div>
                    </div>
                    
                    <p class="text-sm text-gray-600 mb-4">${scenario.description || 'No description'}</p>
                    
                    <div class="flex items-center justify-between text-sm text-gray-500 mb-4">
                        <span><i class="fas fa-tag mr-1"></i>${scenario.category}</span>
                        <span><i class="fas fa-calendar mr-1"></i>${new Date(scenario.created_at).toLocaleDateString()}</span>
                    </div>
                    
                    <div class="grid grid-cols-3 gap-2 text-center text-sm mb-4">
                        <div>
                            <div class="text-lg font-semibold text-blue-600">${scenario.total_executions}</div>
                            <div class="text-gray-500">Executions</div>
                        </div>
                        <div>
                            <div class="text-lg font-semibold text-green-600">${scenario.successful_executions}</div>
                            <div class="text-gray-500">Success</div>
                        </div>
                        <div>
                            <div class="text-lg font-semibold text-purple-600">${scenario.success_rate.toFixed(1)}%</div>
                            <div class="text-gray-500">Rate</div>
                        </div>
                    </div>
                    
                    <div class="flex space-x-2">
                        <button onclick="dashboard.viewScenarioDetails('${scenario.scenario_id}')" 
                                class="flex-1 btn btn-outline btn-sm">
                            <i class="fas fa-eye mr-1"></i> View
                        </button>
                        <button onclick="dashboard.testScenario('${scenario.scenario_id}')" 
                                class="flex-1 btn btn-primary btn-sm">
                            <i class="fas fa-play mr-1"></i> Test
                        </button>
                        <button onclick="dashboard.toggleScenario('${scenario.scenario_id}', ${!scenario.enabled})" 
                                class="btn ${scenario.enabled ? 'btn-outline' : 'btn-primary'} btn-sm">
                            <i class="fas fa-${scenario.enabled ? 'pause' : 'play'} mr-1"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    renderTemplates() {
        const container = document.getElementById('templatesContainer');
        
        if (this.templates.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <i class="fas fa-layer-group text-gray-300 text-4xl mb-4"></i>
                    <p class="text-gray-500">No templates available.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.templates.map(template => `
            <div class="bg-white overflow-hidden shadow rounded-lg card-hover">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-medium text-gray-900">${template.name}</h3>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            ${template.complexity_level}
                        </span>
                    </div>
                    
                    <p class="text-sm text-gray-600 mb-4">${template.description}</p>
                    
                    <div class="flex items-center justify-between text-sm text-gray-500 mb-4">
                        <span><i class="fas fa-tag mr-1"></i>${template.category}</span>
                        <span><i class="fas fa-cog mr-1"></i>${template.estimated_operations} ops</span>
                    </div>
                    
                    <div class="mb-4">
                        <div class="text-sm text-gray-700 mb-2">Event Types:</div>
                        <div class="flex flex-wrap gap-1">
                            ${template.trigger_events.map(event => `
                                <span class="inline-flex items-center px-2 py-1 rounded-md text-xs bg-gray-100 text-gray-800">
                                    ${event.replace(/_/g, ' ')}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <div class="text-sm text-gray-700 mb-2">Required Integrations:</div>
                        <div class="flex flex-wrap gap-1">
                            ${template.required_integrations.map(integration => `
                                <span class="inline-flex items-center px-2 py-1 rounded-md text-xs bg-green-100 text-green-800">
                                    ${integration}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                    
                    <button onclick="dashboard.useTemplate('${template.template_id}')" 
                            class="w-full btn btn-primary">
                        <i class="fas fa-magic mr-1"></i> Use Template
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    renderBridges() {
        const container = document.getElementById('bridgesContainer');
        
        if (this.bridges.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-link text-gray-300 text-4xl mb-4"></i>
                    <p class="text-gray-500">No automation bridges configured. Create your first bridge to connect internal workflows with Make.com scenarios!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.bridges.map(bridge => `
            <div class="bg-white overflow-hidden shadow rounded-lg card-hover">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-medium text-gray-900">${bridge.name}</h3>
                        <div class="flex items-center">
                            <span class="status-dot ${bridge.enabled ? 'status-active' : 'status-inactive'}"></span>
                            <span class="text-sm text-gray-500">${bridge.enabled ? 'Enabled' : 'Disabled'}</span>
                        </div>
                    </div>
                    
                    <p class="text-sm text-gray-600 mb-4">${bridge.description || 'No description'}</p>
                    
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <div class="text-sm text-gray-700 font-medium">Internal Trigger</div>
                            <div class="text-sm text-gray-600">${bridge.internal_trigger_type}</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-700 font-medium">Make.com Scenarios</div>
                            <div class="text-sm text-gray-600">${bridge.make_scenario_ids.length} connected</div>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-3 gap-2 text-center text-sm mb-4">
                        <div>
                            <div class="text-lg font-semibold text-blue-600">${bridge.total_executions}</div>
                            <div class="text-gray-500">Executions</div>
                        </div>
                        <div>
                            <div class="text-lg font-semibold text-green-600">${bridge.successful_executions}</div>
                            <div class="text-gray-500">Success</div>
                        </div>
                        <div>
                            <div class="text-lg font-semibold text-purple-600">${bridge.success_rate.toFixed(1)}%</div>
                            <div class="text-gray-500">Rate</div>
                        </div>
                    </div>
                    
                    <div class="flex space-x-2">
                        <button onclick="dashboard.viewBridgeDetails('${bridge.bridge_id}')" 
                                class="flex-1 btn btn-outline btn-sm">
                            <i class="fas fa-eye mr-1"></i> View
                        </button>
                        <button onclick="dashboard.editBridge('${bridge.bridge_id}')" 
                                class="flex-1 btn btn-primary btn-sm">
                            <i class="fas fa-edit mr-1"></i> Edit
                        </button>
                        <button onclick="dashboard.toggleBridge('${bridge.bridge_id}', ${!bridge.enabled})" 
                                class="btn ${bridge.enabled ? 'btn-outline' : 'btn-primary'} btn-sm">
                            <i class="fas fa-${bridge.enabled ? 'pause' : 'play'} mr-1"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    loadTabData(tabName) {
        switch(tabName) {
            case 'activity':
                this.loadRecentActivity();
                break;
            case 'scenarios':
                // Already loaded
                break;
            case 'templates':
                // Already loaded
                break;
            case 'bridges':
                // Already loaded
                break;
        }
    }
    
    async loadRecentActivity() {
        // This would load recent execution data and render charts/logs
        // For now, we'll create a simple mock chart
        const ctx = document.getElementById('activityChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Successful Executions',
                    data: [12, 19, 3, 5, 2, 3, 8],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Failed Executions',
                    data: [1, 2, 0, 1, 0, 0, 2],
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                }]
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
    
    // Modal Methods
    showModal(modalId) {
        document.getElementById(modalId).classList.add('show');
    }
    
    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('show');
    }
    
    showCreateScenarioModal() {
        this.showModal('createScenarioModal');
    }
    
    showCreateBridgeModal() {
        // This would show a create bridge modal (not implemented in HTML yet)
        this.showNotification('Create Bridge functionality coming soon!', 'info');
    }
    
    // Scenario Methods
    async handleCreateScenario(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const eventTypes = Array.from(document.querySelectorAll('input[name="event_types"]:checked')).map(cb => cb.value);
        
        const scenarioData = {
            name: formData.get('name'),
            description: formData.get('description'),
            category: formData.get('category'),
            webhook_url: formData.get('webhook_url'),
            event_types: eventTypes
        };
        
        try {
            const response = await fetch('/api/make/scenarios', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(scenarioData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideModal('createScenarioModal');
                this.showNotification('Scenario created successfully!', 'success');
                this.loadScenarios();
                this.renderScenarios();
                // Reset form
                event.target.reset();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            this.showNotification('Error creating scenario: ' + error.message, 'error');
        }
    }
    
    async viewScenarioDetails(scenarioId) {
        const scenario = this.scenarios.find(s => s.scenario_id === scenarioId);
        if (!scenario) return;
        
        document.getElementById('scenarioDetailsTitle').textContent = scenario.name;
        
        const content = document.getElementById('scenarioDetailsContent');
        content.innerHTML = `
            <div class="grid grid-cols-2 gap-6">
                <div>
                    <h4 class="text-lg font-medium text-gray-900 mb-4">Basic Information</h4>
                    <dl class="space-y-2">
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Name</dt>
                            <dd class="text-sm text-gray-900">${scenario.name}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Description</dt>
                            <dd class="text-sm text-gray-900">${scenario.description || 'No description'}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Category</dt>
                            <dd class="text-sm text-gray-900">${scenario.category}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Status</dt>
                            <dd class="text-sm text-gray-900">
                                <span class="status-dot ${scenario.enabled ? 'status-active' : 'status-inactive'}"></span>
                                ${scenario.enabled ? 'Active' : 'Inactive'}
                            </dd>
                        </div>
                    </dl>
                </div>
                
                <div>
                    <h4 class="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h4>
                    <dl class="space-y-2">
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Total Executions</dt>
                            <dd class="text-sm text-gray-900">${scenario.total_executions}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Successful</dt>
                            <dd class="text-sm text-gray-900">${scenario.successful_executions}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Failed</dt>
                            <dd class="text-sm text-gray-900">${scenario.failed_executions}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Success Rate</dt>
                            <dd class="text-sm text-gray-900">${scenario.success_rate.toFixed(1)}%</dd>
                        </div>
                    </dl>
                </div>
            </div>
            
            <div class="mt-6">
                <h4 class="text-lg font-medium text-gray-900 mb-4">Configuration</h4>
                <div class="grid grid-cols-2 gap-6">
                    <div>
                        <dt class="text-sm font-medium text-gray-500 mb-2">Webhook URL</dt>
                        <dd class="text-sm text-gray-900 bg-gray-50 p-2 rounded font-mono break-all">${scenario.webhook_url}</dd>
                    </div>
                    <div>
                        <dt class="text-sm font-medium text-gray-500 mb-2">Event Types</dt>
                        <dd class="flex flex-wrap gap-1">
                            ${scenario.event_types.map(event => `
                                <span class="inline-flex items-center px-2 py-1 rounded-md text-xs bg-blue-100 text-blue-800">
                                    ${event.replace(/_/g, ' ')}
                                </span>
                            `).join('')}
                        </dd>
                    </div>
                </div>
            </div>
        `;
        
        this.showModal('scenarioDetailsModal');
    }
    
    testScenario(scenarioId) {
        this.currentScenarioId = scenarioId;
        const scenario = this.scenarios.find(s => s.scenario_id === scenarioId);
        
        document.getElementById('testScenarioTitle').textContent = `Test: ${scenario.name}`;
        document.getElementById('testPayload').value = JSON.stringify({
            test: true,
            message: "This is a test execution",
            timestamp: new Date().toISOString()
        }, null, 2);
        
        document.getElementById('testResult').classList.add('hidden');
        this.showModal('testScenarioModal');
    }
    
    async executeScenarioTest() {
        if (!this.currentScenarioId) return;
        
        const payload = document.getElementById('testPayload').value;
        let parsedPayload;
        
        try {
            parsedPayload = JSON.parse(payload);
        } catch (error) {
            this.showNotification('Invalid JSON payload', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/make/scenarios/${this.currentScenarioId}/trigger`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(parsedPayload)
            });
            
            const data = await response.json();
            
            const resultDiv = document.getElementById('testResult');
            const contentDiv = document.getElementById('testResultContent');
            
            if (data.success) {
                contentDiv.innerHTML = `
                    <div class="text-green-800">
                        <i class="fas fa-check-circle mr-2"></i>Test executed successfully!
                        <br><strong>Execution ID:</strong> ${data.execution_id}
                    </div>
                `;
                this.showNotification('Test executed successfully!', 'success');
            } else {
                contentDiv.innerHTML = `
                    <div class="text-red-800">
                        <i class="fas fa-exclamation-circle mr-2"></i>Test failed: ${data.error}
                    </div>
                `;
            }
            
            resultDiv.classList.remove('hidden');
            
            // Reload scenarios to update execution counts
            setTimeout(() => {
                this.loadScenarios();
                this.renderScenarios();
            }, 1000);
            
        } catch (error) {
            this.showNotification('Error executing test: ' + error.message, 'error');
        }
    }
    
    async toggleScenario(scenarioId, enabled) {
        try {
            const response = await fetch(`/api/make/scenarios/${scenarioId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Scenario ${enabled ? 'enabled' : 'disabled'} successfully!`, 'success');
                this.loadScenarios();
                this.renderScenarios();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            this.showNotification('Error toggling scenario: ' + error.message, 'error');
        }
    }
    
    useTemplate(templateId) {
        const template = this.templates.find(t => t.template_id === templateId);
        if (!template) return;
        
        // Pre-fill the create scenario form with template data
        document.getElementById('scenarioName').value = template.name;
        document.getElementById('scenarioDescription').value = template.description;
        document.getElementById('scenarioCategory').value = template.category;
        
        // Check the appropriate event types
        const eventTypeCheckboxes = document.querySelectorAll('input[name="event_types"]');
        eventTypeCheckboxes.forEach(cb => {
            cb.checked = template.trigger_events.includes(cb.value);
        });
        
        this.showCreateScenarioModal();
    }
    
    // Bridge Methods
    viewBridgeDetails(bridgeId) {
        this.showNotification('Bridge details view coming soon!', 'info');
    }
    
    editBridge(bridgeId) {
        this.showNotification('Bridge editing coming soon!', 'info');
    }
    
    async toggleBridge(bridgeId, enabled) {
        this.showNotification('Bridge toggle functionality coming soon!', 'info');
    }
    
    // Utility Methods
    filterScenarios(category) {
        this.renderScenarios(category);
    }
    
    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        const colors = {
            success: 'bg-green-100 border-green-500 text-green-700',
            error: 'bg-red-100 border-red-500 text-red-700',
            warning: 'bg-yellow-100 border-yellow-500 text-yellow-700',
            info: 'bg-blue-100 border-blue-500 text-blue-700'
        };
        
        notification.innerHTML = `
            <div class="border-l-4 p-4 ${colors[type]} rounded-r-md shadow-lg">
                <div class="flex">
                    <div class="ml-3">
                        <p class="text-sm">${message}</p>
                    </div>
                    <div class="ml-auto pl-3">
                        <button onclick="this.parentElement.parentElement.parentElement.classList.remove('show')" 
                                class="text-current opacity-50 hover:opacity-75">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        notification.classList.add('show');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }
}

// Custom styles for form elements
const style = document.createElement('style');
style.textContent = `
    .btn {
        @apply px-4 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors;
    }
    .btn-primary {
        @apply bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500;
    }
    .btn-outline {
        @apply bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-500;
    }
    .btn-sm {
        @apply px-3 py-1 text-xs;
    }
    .form-input, .form-textarea, .form-select {
        @apply mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500;
    }
    .form-checkbox {
        @apply h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded;
    }
`;
document.head.appendChild(style);

// Initialize dashboard
const dashboard = new MakeDashboard();