/**
 * LinkedIn Sales Navigator Automation Dashboard JavaScript
 * Handles the frontend interface for LinkedIn campaign management, 
 * lead pipeline tracking, and automation performance monitoring
 */

class LinkedInDashboard {
    constructor() {
        this.authToken = localStorage.getItem('authToken');
        this.API_BASE = window.location.origin;
        this.charts = {};
        this.refreshInterval = null;
        this.currentCampaign = null;
        this.campaigns = [];
        this.priorityLeads = [];
        this.activeAlerts = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupTabs();
        
        if (!this.authToken) {
            // Don't redirect, just don't load data - let the template handle login
            console.warn('No auth token found, waiting for authentication');
            return;
        }
        
        this.loadDashboardData();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.linkedin-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
        
        // Campaign management
        document.getElementById('createCampaignBtn')?.addEventListener('click', () => {
            this.showCreateCampaignModal();
        });
        
        document.getElementById('refreshLinkedInBtn')?.addEventListener('click', () => {
            this.loadDashboardData();
        });
        
        // Campaign selection
        document.getElementById('campaignSelect')?.addEventListener('change', (e) => {
            this.currentCampaign = e.target.value;
            this.loadCampaignData(this.currentCampaign);
        });
        
        // Lead actions
        document.getElementById('discoverLeadsBtn')?.addEventListener('click', () => {
            this.showDiscoverLeadsModal();
        });
        
        document.getElementById('processAutomationBtn')?.addEventListener('click', () => {
            this.processAutomation();
        });
        
        // Modal events
        document.getElementById('closeCampaignModal')?.addEventListener('click', () => {
            this.hideModal('createCampaignModal');
        });
        
        document.getElementById('closeLeadDiscoveryModal')?.addEventListener('click', () => {
            this.hideModal('leadDiscoveryModal');
        });
        
        document.getElementById('closeLeadDetailsModal')?.addEventListener('click', () => {
            this.hideModal('leadDetailsModal');
        });
        
        // Form submissions
        document.getElementById('createCampaignForm')?.addEventListener('submit', (e) => {
            this.handleCreateCampaign(e);
        });
        
        document.getElementById('discoverLeadsForm')?.addEventListener('submit', (e) => {
            this.handleDiscoverLeads(e);
        });
        
        // Alert acknowledgments
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('acknowledge-alert-btn')) {
                const alertId = e.target.dataset.alertId;
                this.acknowledgeAlert(alertId);
            }
        });
        
        // Lead actions
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('qualify-lead-btn')) {
                const leadId = e.target.dataset.leadId;
                this.qualifyLead(leadId);
            } else if (e.target.classList.contains('connect-lead-btn')) {
                const leadId = e.target.dataset.leadId;
                this.showConnectModal(leadId);
            } else if (e.target.classList.contains('message-lead-btn')) {
                const leadId = e.target.dataset.leadId;
                this.showMessageModal(leadId);
            } else if (e.target.classList.contains('view-lead-btn')) {
                const leadId = e.target.dataset.leadId;
                this.showLeadDetails(leadId);
            }
        });
    }
    
    setupTabs() {
        const tabButtons = document.querySelectorAll('.linkedin-tab-btn');
        const tabContents = document.querySelectorAll('.linkedin-tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                
                // Update active tab button
                tabButtons.forEach(btn => {
                    btn.classList.remove('border-blue-500', 'text-blue-600');
                    btn.classList.add('border-transparent', 'text-gray-500');
                });
                
                button.classList.remove('border-transparent', 'text-gray-500');
                button.classList.add('border-blue-500', 'text-blue-600');
                
                // Update active tab content
                tabContents.forEach(content => {
                    content.classList.add('hidden');
                });
                
                document.getElementById(`${tabName}Tab`)?.classList.remove('hidden');
                
                // Load tab-specific data
                this.loadTabData(tabName);
            });
        });
    }
    
    switchTab(tabName) {
        // This method is called by setupTabs, but we can add additional logic here
        if (tabName === 'analytics') {
            this.loadAnalyticsData();
        } else if (tabName === 'pipeline') {
            this.loadPipelineData();
        } else if (tabName === 'workflows') {
            this.loadWorkflowData();
        }
    }
    
    loadTabData(tabName) {
        switch (tabName) {
            case 'overview':
                this.loadDashboardOverview();
                break;
            case 'campaigns':
                this.loadCampaignsData();
                break;
            case 'leads':
                this.loadLeadsData();
                break;
            case 'pipeline':
                this.loadPipelineData();
                break;
            case 'analytics':
                this.loadAnalyticsData();
                break;
            case 'workflows':
                this.loadWorkflowData();
                break;
        }
    }
    
    async loadDashboardData() {
        // Check if authenticated before making any API calls
        if (!this.authToken) {
            console.warn('No auth token available, skipping data load');
            return;
        }
        
        try {
            this.showLoading();
            
            // Load all dashboard data in parallel
            await Promise.all([
                this.loadDashboardOverview(),
                this.loadCampaignsData(),
                this.loadPriorityLeads(),
                this.loadActiveAlerts()
            ]);
            
            this.hideLoading();
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
            this.hideLoading();
        }
    }
    
    async loadDashboardOverview() {
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/analytics/dashboard`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.updateDashboardSummary(data.analytics.summary);
                this.updatePipelineBreakdown(data.analytics.pipeline_breakdown);
                this.updateRecentActivity(data.analytics.recent_activity);
            } else {
                throw new Error(data.error || 'Failed to load dashboard overview');
            }
        } catch (error) {
            console.error('Error loading dashboard overview:', error);
        }
    }
    
    async loadCampaignsData() {
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/campaigns`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.campaigns = data.campaigns;
                this.updateCampaignsTable(data.campaigns);
                this.updateCampaignSelect(data.campaigns);
            } else {
                throw new Error(data.error || 'Failed to load campaigns');
            }
        } catch (error) {
            console.error('Error loading campaigns:', error);
        }
    }
    
    async loadCampaignData(campaignId) {
        if (!campaignId) return;
        
        try {
            const [campaignResponse, leadsResponse] = await Promise.all([
                fetch(`${this.API_BASE}/api/linkedin/campaigns/${campaignId}`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                }),
                fetch(`${this.API_BASE}/api/linkedin/campaigns/${campaignId}/leads`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                })
            ]);
            
            const campaignData = await campaignResponse.json();
            const leadsData = await leadsResponse.json();
            
            if (campaignData.success && leadsData.success) {
                this.updateCampaignDetails(campaignData.campaign);
                this.updateLeadsTable(leadsData.leads);
            }
        } catch (error) {
            console.error('Error loading campaign data:', error);
        }
    }
    
    async loadPriorityLeads() {
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/pipeline/priority-leads?limit=10`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.priorityLeads = data.priority_leads;
                this.updatePriorityLeadsTable(data.priority_leads);
            }
        } catch (err) {
            console.error('Error loading priority leads:', err);
        }
    }
    
    async loadActiveAlerts() {
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/pipeline/alerts`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.activeAlerts = data.alerts;
                this.updateAlertsPanel(data.alerts);
            }
        } catch (error) {
            console.error('Error loading active alerts:', error);
        }
    }
    
    async loadPipelineData() {
        try {
            const [metricsResponse, funnelResponse, trendsResponse] = await Promise.all([
                fetch(`${this.API_BASE}/api/linkedin/pipeline/metrics${this.currentCampaign ? `?campaign_id=${this.currentCampaign}` : ''}`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                }),
                fetch(`${this.API_BASE}/api/linkedin/pipeline/funnel${this.currentCampaign ? `?campaign_id=${this.currentCampaign}` : ''}`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                }),
                fetch(`${this.API_BASE}/api/linkedin/pipeline/trends${this.currentCampaign ? `?campaign_id=${this.currentCampaign}` : ''}`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                })
            ]);
            
            const metricsData = await metricsResponse.json();
            const funnelData = await funnelResponse.json();
            const trendsData = await trendsResponse.json();
            
            if (metricsData.success) {
                this.updatePipelineMetrics(metricsData.metrics);
            }
            
            if (funnelData.success) {
                this.renderConversionFunnel(funnelData.funnel);
            }
            
            if (trendsData.success) {
                this.renderPipelineTrends(trendsData.trends);
            }
        } catch (error) {
            console.error('Error loading pipeline data:', error);
        }
    }
    
    async loadAnalyticsData() {
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/analytics/performance${this.currentCampaign ? `?campaign_id=${this.currentCampaign}` : ''}`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.renderAnalyticsCharts(data.performance);
            }
        } catch (error) {
            console.error('Error loading analytics data:', error);
        }
    }
    
    async loadWorkflowData() {
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/workflows/analytics${this.currentCampaign ? `?campaign_id=${this.currentCampaign}` : ''}`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.updateWorkflowAnalytics(data.analytics);
            }
        } catch (error) {
            console.error('Error loading workflow data:', error);
        }
    }
    
    // === UI UPDATE METHODS ===
    
    updateDashboardSummary(summary) {
        document.getElementById('totalLeads').textContent = summary.total_leads || 0;
        document.getElementById('qualifiedLeads').textContent = summary.qualified_leads || 0;
        document.getElementById('activeCampaigns').textContent = summary.active_campaigns || 0;
        document.getElementById('responseRate').textContent = `${(summary.response_rate || 0).toFixed(1)}%`;
        document.getElementById('conversionRate').textContent = `${(summary.qualification_rate || 0).toFixed(1)}%`;
        document.getElementById('revenuePipeline').textContent = `$${(summary.revenue_pipeline || 0).toLocaleString()}`;
    }
    
    updatePipelineBreakdown(breakdown) {
        const container = document.getElementById('pipelineBreakdown');
        if (!container) return;
        
        const stages = [
            { key: 'discovery', label: 'Discovery', color: 'bg-gray-100 text-gray-800' },
            { key: 'qualification', label: 'Qualification', color: 'bg-blue-100 text-blue-800' },
            { key: 'outreach', label: 'Outreach', color: 'bg-yellow-100 text-yellow-800' },
            { key: 'engagement', label: 'Engagement', color: 'bg-orange-100 text-orange-800' },
            { key: 'nurturing', label: 'Nurturing', color: 'bg-purple-100 text-purple-800' },
            { key: 'qualified', label: 'Qualified', color: 'bg-green-100 text-green-800' },
            { key: 'opportunity', label: 'Opportunity', color: 'bg-indigo-100 text-indigo-800' },
            { key: 'converted', label: 'Converted', color: 'bg-emerald-100 text-emerald-800' }
        ];
        
        container.innerHTML = stages.map(stage => {
            const count = breakdown[stage.key] || 0;
            return `
                <div class="bg-white p-4 rounded-lg shadow">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-gray-600">${stage.label}</p>
                            <p class="text-2xl font-bold text-gray-900">${count}</p>
                        </div>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${stage.color}">
                            ${stage.label}
                        </span>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateCampaignsTable(campaigns) {
        const tbody = document.getElementById('campaignsTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = campaigns.map(campaign => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">${campaign.name}</div>
                    <div class="text-sm text-gray-500">${campaign.description || ''}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${this.getStatusColor(campaign.status)}">
                        ${campaign.status}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${campaign.total_prospects || 0}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${campaign.connections_sent || 0}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${campaign.responses_received || 0}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${((campaign.responses_received || 0) / Math.max(campaign.messages_sent || 1, 1) * 100).toFixed(1)}%
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="linkedInDashboard.selectCampaign('${campaign.campaign_id}')" class="text-blue-600 hover:text-blue-900">View</button>
                </td>
            </tr>
        `).join('');
    }
    
    updateLeadsTable(leads) {
        const tbody = document.getElementById('leadsTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = leads.map(lead => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10">
                            <img class="h-10 w-10 rounded-full" src="${lead.profile_image_url || '/static/images/default-avatar.png'}" alt="">
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${lead.full_name}</div>
                            <div class="text-sm text-gray-500">${lead.current_title || ''}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${lead.current_company || ''}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${this.getPriorityColor(lead.priority)}">
                        ${lead.priority}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${this.getStageColor(lead.pipeline_stage)}">
                        ${lead.pipeline_stage}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${(lead.lead_score || 0).toFixed(0)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex space-x-2">
                        <button class="qualify-lead-btn text-blue-600 hover:text-blue-900" data-lead-id="${lead.lead_id}">Qualify</button>
                        <button class="connect-lead-btn text-green-600 hover:text-green-900" data-lead-id="${lead.lead_id}">Connect</button>
                        <button class="view-lead-btn text-indigo-600 hover:text-indigo-900" data-lead-id="${lead.lead_id}">View</button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    
    updatePriorityLeadsTable(priorityLeads) {
        const container = document.getElementById('priorityLeadsContainer');
        if (!container) return;
        
        container.innerHTML = priorityLeads.map(leadData => {
            const lead = leadData.lead;
            return `
                <div class="bg-white p-4 rounded-lg shadow border-l-4 ${this.getPriorityBorder(leadData.priority)}">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center">
                            <img class="h-8 w-8 rounded-full" src="${lead.profile_image_url || '/static/images/default-avatar.png'}" alt="">
                            <div class="ml-3">
                                <p class="text-sm font-medium text-gray-900">${lead.full_name}</p>
                                <p class="text-xs text-gray-500">${lead.current_title} at ${lead.current_company}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${this.getPriorityColor(leadData.priority)}">
                                ${leadData.priority}
                            </span>
                            <p class="text-xs text-gray-500 mt-1">Score: ${(leadData.priority_score || 0).toFixed(0)}</p>
                        </div>
                    </div>
                    <div class="mt-2 flex space-x-2">
                        ${leadData.recommended_actions.slice(0, 2).map(action => `
                            <span class="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">${action}</span>
                        `).join('')}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateAlertsPanel(alerts) {
        const container = document.getElementById('alertsContainer');
        if (!container) return;
        
        if (alerts.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No active alerts</p>';
            return;
        }
        
        container.innerHTML = alerts.map(alert => `
            <div class="bg-white p-4 rounded-lg shadow border-l-4 ${this.getAlertBorder(alert.priority)}">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h4 class="text-sm font-medium text-gray-900">${alert.title}</h4>
                        <p class="text-sm text-gray-600 mt-1">${alert.message}</p>
                        <p class="text-xs text-gray-500 mt-2">${this.formatTimeAgo(alert.created_at)}</p>
                    </div>
                    <button class="acknowledge-alert-btn ml-4 text-blue-600 hover:text-blue-800 text-sm" data-alert-id="${alert.alert_id}">
                        Acknowledge
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    // === CHART RENDERING METHODS ===
    
    renderConversionFunnel(funnelData) {
        const ctx = document.getElementById('conversionFunnelChart');
        if (!ctx) return;
        
        if (this.charts.conversionFunnel) {
            this.charts.conversionFunnel.destroy();
        }
        
        this.charts.conversionFunnel = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: funnelData.stages.map(stage => stage.stage),
                datasets: [{
                    label: 'Leads',
                    data: funnelData.stages.map(stage => stage.count),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Conversion Funnel'
                    }
                }
            }
        });
    }
    
    renderPipelineTrends(trendsData) {
        const ctx = document.getElementById('pipelineTrendsChart');
        if (!ctx) return;
        
        if (this.charts.pipelineTrends) {
            this.charts.pipelineTrends.destroy();
        }
        
        this.charts.pipelineTrends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendsData.daily_data.map(day => day.date),
                datasets: [
                    {
                        label: 'Leads Discovered',
                        data: trendsData.daily_data.map(day => day.leads_discovered),
                        borderColor: 'rgba(59, 130, 246, 1)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Connections Sent',
                        data: trendsData.daily_data.map(day => day.connections_sent),
                        borderColor: 'rgba(16, 185, 129, 1)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Qualified Leads',
                        data: trendsData.daily_data.map(day => day.qualified_leads),
                        borderColor: 'rgba(245, 158, 11, 1)',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Pipeline Trends (30 Days)'
                    }
                }
            }
        });
    }
    
    // === ACTION METHODS ===
    
    async processAutomation() {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.API_BASE}/api/linkedin/pipeline/process`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`Processed ${data.results.leads_processed} leads and triggered ${data.results.workflows_triggered} workflows`);
                this.loadDashboardData(); // Refresh data
            } else {
                throw new Error(data.error || 'Failed to process automation');
            }
        } catch (error) {
            console.error('Error processing automation:', error);
            this.showError('Failed to process automation');
        } finally {
            this.hideLoading();
        }
    }
    
    async qualifyLead(leadId) {
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/leads/${leadId}/qualify`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`Lead qualified: ${data.qualification_result.qualification_level}`);
                this.loadDashboardData(); // Refresh data
            } else {
                throw new Error(data.error || 'Failed to qualify lead');
            }
        } catch (error) {
            console.error('Error qualifying lead:', error);
            this.showError('Failed to qualify lead');
        }
    }
    
    async acknowledgeAlert(alertId) {
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/pipeline/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.loadActiveAlerts(); // Refresh alerts
            } else {
                throw new Error(data.error || 'Failed to acknowledge alert');
            }
        } catch (error) {
            console.error('Error acknowledging alert:', error);
            this.showError('Failed to acknowledge alert');
        }
    }
    
    // === MODAL METHODS ===
    
    showCreateCampaignModal() {
        document.getElementById('createCampaignModal')?.classList.remove('hidden');
    }
    
    showDiscoverLeadsModal() {
        if (!this.currentCampaign) {
            this.showError('Please select a campaign first');
            return;
        }
        document.getElementById('leadDiscoveryModal')?.classList.remove('hidden');
    }
    
    hideModal(modalId) {
        document.getElementById(modalId)?.classList.add('hidden');
    }
    
    // === FORM HANDLERS ===
    
    async handleCreateCampaign(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const campaignData = {
            name: formData.get('name'),
            description: formData.get('description'),
            target_audience: {
                keywords: formData.get('keywords'),
                titles: formData.get('titles')?.split(',').map(t => t.trim()),
                industries: formData.get('industries')?.split(',').map(i => i.trim()),
                locations: formData.get('locations')?.split(',').map(l => l.trim())
            },
            daily_connection_limit: parseInt(formData.get('daily_connection_limit')) || 20,
            daily_message_limit: parseInt(formData.get('daily_message_limit')) || 50
        };
        
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/campaigns`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(campaignData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Campaign created successfully');
                this.hideModal('createCampaignModal');
                this.loadCampaignsData();
                e.target.reset();
            } else {
                throw new Error(data.error || 'Failed to create campaign');
            }
        } catch (error) {
            console.error('Error creating campaign:', error);
            this.showError('Failed to create campaign');
        }
    }
    
    async handleDiscoverLeads(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const searchData = {
            keywords: formData.get('keywords'),
            titles: formData.get('titles')?.split(',').map(t => t.trim()),
            companies: formData.get('companies')?.split(',').map(c => c.trim()),
            industries: formData.get('industries')?.split(',').map(i => i.trim()),
            locations: formData.get('locations')?.split(',').map(l => l.trim()),
            limit: parseInt(formData.get('limit')) || 50
        };
        
        try {
            const response = await fetch(`${this.API_BASE}/api/linkedin/campaigns/${this.currentCampaign}/discover-leads`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(searchData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`Discovered ${data.leads_discovered} new leads`);
                this.hideModal('leadDiscoveryModal');
                this.loadCampaignData(this.currentCampaign);
                e.target.reset();
            } else {
                throw new Error(data.error || 'Failed to discover leads');
            }
        } catch (error) {
            console.error('Error discovering leads:', error);
            this.showError('Failed to discover leads');
        }
    }
    
    // === UTILITY METHODS ===
    
    getStatusColor(status) {
        const colors = {
            'active': 'bg-green-100 text-green-800',
            'paused': 'bg-yellow-100 text-yellow-800',
            'completed': 'bg-blue-100 text-blue-800',
            'draft': 'bg-gray-100 text-gray-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    }
    
    getPriorityColor(priority) {
        const colors = {
            'critical': 'bg-red-100 text-red-800',
            'high': 'bg-orange-100 text-orange-800',
            'medium': 'bg-yellow-100 text-yellow-800',
            'low': 'bg-green-100 text-green-800'
        };
        return colors[priority] || 'bg-gray-100 text-gray-800';
    }
    
    getPriorityBorder(priority) {
        const borders = {
            'critical': 'border-red-500',
            'high': 'border-orange-500',
            'medium': 'border-yellow-500',
            'low': 'border-green-500'
        };
        return borders[priority] || 'border-gray-500';
    }
    
    getStageColor(stage) {
        const colors = {
            'discovery': 'bg-gray-100 text-gray-800',
            'qualification': 'bg-blue-100 text-blue-800',
            'outreach': 'bg-yellow-100 text-yellow-800',
            'engagement': 'bg-orange-100 text-orange-800',
            'nurturing': 'bg-purple-100 text-purple-800',
            'qualified': 'bg-green-100 text-green-800',
            'opportunity': 'bg-indigo-100 text-indigo-800',
            'converted': 'bg-emerald-100 text-emerald-800'
        };
        return colors[stage] || 'bg-gray-100 text-gray-800';
    }
    
    getAlertBorder(priority) {
        const borders = {
            'critical': 'border-red-500',
            'high': 'border-orange-500',
            'medium': 'border-yellow-500',
            'low': 'border-blue-500'
        };
        return borders[priority] || 'border-gray-500';
    }
    
    formatTimeAgo(timestamp) {
        const now = new Date();
        const past = new Date(timestamp);
        const diffMs = now - past;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 60) {
            return `${diffMins} minutes ago`;
        } else if (diffHours < 24) {
            return `${diffHours} hours ago`;
        } else {
            return `${diffDays} days ago`;
        }
    }
    
    showLoading() {
        document.getElementById('loadingSpinner')?.classList.remove('hidden');
    }
    
    hideLoading() {
        document.getElementById('loadingSpinner')?.classList.add('hidden');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    selectCampaign(campaignId) {
        this.currentCampaign = campaignId;
        document.getElementById('campaignSelect').value = campaignId;
        this.loadCampaignData(campaignId);
        this.switchTab('leads');
    }
    
    startAutoRefresh() {
        // Refresh data every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 300000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('linkedin') || 
        document.getElementById('linkedinDashboard')) {
        window.linkedInDashboard = new LinkedInDashboard();
    }
});