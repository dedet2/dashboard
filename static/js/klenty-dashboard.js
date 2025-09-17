/**
 * Klenty SDRx Outreach Automation Dashboard JavaScript
 * Handles the frontend interface for Klenty email campaign management, 
 * lead nurturing, sequence automation, and outreach performance monitoring
 */

class KlentyDashboard {
    constructor() {
        this.authToken = localStorage.getItem('authToken');
        this.API_BASE = window.location.origin;
        this.charts = {};
        this.refreshInterval = null;
        this.currentCampaign = null;
        this.campaigns = [];
        this.sequences = [];
        this.leads = [];
        this.analytics = {};
        
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
        this.setupTabs();
    }
    
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.klenty-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
        
        // Campaign management
        document.getElementById('createKlentyCampaignBtn')?.addEventListener('click', () => {
            this.showCreateCampaignModal();
        });
        
        document.getElementById('refreshKlentyBtn')?.addEventListener('click', () => {
            this.loadDashboardData();
        });
        
        // Campaign selection
        document.getElementById('klentyCampaignSelect')?.addEventListener('change', (e) => {
            this.currentCampaign = e.target.value;
            this.loadCampaignData(this.currentCampaign);
        });
        
        // Sequence management
        document.getElementById('createSequenceBtn')?.addEventListener('click', () => {
            this.showCreateSequenceModal();
        });
        
        // Lead actions
        document.getElementById('importLeadsBtn')?.addEventListener('click', () => {
            this.showImportLeadsModal();
        });
        
        document.getElementById('sendScheduledEmailsBtn')?.addEventListener('click', () => {
            this.sendScheduledEmails();
        });
        
        // Integration actions
        document.getElementById('syncLinkedInLeadsBtn')?.addEventListener('click', () => {
            this.showSyncLinkedInModal();
        });
        
        document.getElementById('processResponsesBtn')?.addEventListener('click', () => {
            this.processCrossPlatformResponses();
        });
        
        // Modal events
        document.getElementById('closeKlentyCampaignModal')?.addEventListener('click', () => {
            this.hideModal('createKlentyCampaignModal');
        });
        
        document.getElementById('closeSequenceModal')?.addEventListener('click', () => {
            this.hideModal('createSequenceModal');
        });
        
        document.getElementById('closeImportLeadsModal')?.addEventListener('click', () => {
            this.hideModal('importLeadsModal');
        });
        
        document.getElementById('closeSyncLinkedInModal')?.addEventListener('click', () => {
            this.hideModal('syncLinkedInModal');
        });
        
        // Form submissions
        document.getElementById('createKlentyCampaignForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createCampaign();
        });
        
        document.getElementById('createSequenceForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createSequence();
        });
        
        document.getElementById('importLeadsForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.importLeads();
        });
        
        document.getElementById('syncLinkedInForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.syncLinkedInLeads();
        });
    }
    
    setupTabs() {
        // Initialize first tab as active
        this.switchTab('overview');
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.klenty-tab-btn').forEach(btn => {
            btn.classList.remove('border-indigo-500', 'text-indigo-600', 'bg-indigo-50');
            btn.classList.add('border-transparent', 'text-gray-500', 'hover:text-gray-700', 'hover:border-gray-300');
        });
        
        document.querySelector(`[data-tab="${tabName}"]`)?.classList.remove('border-transparent', 'text-gray-500', 'hover:text-gray-700', 'hover:border-gray-300');
        document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('border-indigo-500', 'text-indigo-600', 'bg-indigo-50');
        
        // Show/hide tab content
        document.querySelectorAll('.klenty-tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        document.getElementById(`${tabName}Tab`)?.classList.remove('hidden');
        
        // Load tab-specific data
        this.loadTabData(tabName);
    }
    
    async loadDashboardData() {
        try {
            this.showLoading('dashboard');
            
            // Load overview data
            const overviewResponse = await fetch(`${this.API_BASE}/api/klenty/analytics/dashboard`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (overviewResponse.ok) {
                const overviewData = await overviewResponse.json();
                this.analytics.overview = overviewData;
                this.renderOverview(overviewData);
            }
            
            // Load campaigns
            const campaignsResponse = await fetch(`${this.API_BASE}/api/klenty/campaigns`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (campaignsResponse.ok) {
                const campaignsData = await campaignsResponse.json();
                this.campaigns = campaignsData.campaigns || [];
                this.renderCampaignSelect();
                this.renderCampaignsTable();
            }
            
            this.hideLoading('dashboard');
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
            this.hideLoading('dashboard');
        }
    }
    
    async loadTabData(tabName) {
        switch (tabName) {
            case 'overview':
                this.renderOverview(this.analytics.overview);
                break;
            case 'campaigns':
                await this.loadCampaignsData();
                break;
            case 'sequences':
                await this.loadSequencesData();
                break;
            case 'leads':
                await this.loadLeadsData();
                break;
            case 'analytics':
                await this.loadAnalyticsData();
                break;
            case 'integration':
                await this.loadIntegrationData();
                break;
        }
    }
    
    async loadCampaignData(campaignId) {
        if (!campaignId) return;
        
        try {
            this.showLoading('campaign-details');
            
            const response = await fetch(`${this.API_BASE}/api/klenty/campaigns/${campaignId}`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const campaignData = await response.json();
                this.renderCampaignDetails(campaignData);
                
                // Load campaign analytics
                const analyticsResponse = await fetch(`${this.API_BASE}/api/klenty/campaigns/${campaignId}/analytics`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (analyticsResponse.ok) {
                    const analytics = await analyticsResponse.json();
                    this.renderCampaignAnalytics(analytics);
                }
            }
            
            this.hideLoading('campaign-details');
            
        } catch (error) {
            console.error('Error loading campaign data:', error);
            this.showError('Failed to load campaign data');
            this.hideLoading('campaign-details');
        }
    }
    
    async loadCampaignsData() {
        try {
            const response = await fetch(`${this.API_BASE}/api/klenty/campaigns`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.campaigns = data.campaigns || [];
                this.renderCampaignsTable();
            }
        } catch (error) {
            console.error('Error loading campaigns:', error);
        }
    }
    
    async loadSequencesData() {
        if (!this.currentCampaign) {
            document.getElementById('sequencesContainer').innerHTML = '<p class="text-gray-500">Please select a campaign to view sequences.</p>';
            return;
        }
        
        try {
            const response = await fetch(`${this.API_BASE}/api/klenty/campaigns/${this.currentCampaign}/sequences`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sequences = data.sequences || [];
                this.renderSequencesTable();
            }
        } catch (error) {
            console.error('Error loading sequences:', error);
        }
    }
    
    async loadLeadsData() {
        if (!this.currentCampaign) {
            document.getElementById('leadsContainer').innerHTML = '<p class="text-gray-500">Please select a campaign to view leads.</p>';
            return;
        }
        
        try {
            const response = await fetch(`${this.API_BASE}/api/klenty/campaigns/${this.currentCampaign}/leads`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.leads = data.leads || [];
                this.renderLeadsTable();
            }
        } catch (error) {
            console.error('Error loading leads:', error);
        }
    }
    
    async loadAnalyticsData() {
        if (!this.currentCampaign) {
            document.getElementById('analyticsContainer').innerHTML = '<p class="text-gray-500">Please select a campaign to view analytics.</p>';
            return;
        }
        
        try {
            const response = await fetch(`${this.API_BASE}/api/klenty/campaigns/${this.currentCampaign}/analytics`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.renderDetailedAnalytics(data);
                this.renderPerformanceCharts(data);
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }
    
    async loadIntegrationData() {
        try {
            // Load cross-platform analytics if available
            if (this.currentCampaign) {
                const response = await fetch(`${this.API_BASE}/api/klenty/integration/cross-platform-analytics?campaign_ids=${this.currentCampaign}`, {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.renderIntegrationAnalytics(data);
                }
            }
        } catch (error) {
            console.error('Error loading integration data:', error);
        }
    }
    
    renderOverview(data) {
        if (!data) return;
        
        const overviewContainer = document.getElementById('overviewContainer');
        if (!overviewContainer) return;
        
        overviewContainer.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <div class="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center">
                                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                    </svg>
                                </div>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">Total Campaigns</dt>
                                    <dd class="text-lg font-medium text-gray-900">${data.summary?.total_campaigns || 0}</dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                                    </svg>
                                </div>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">Total Leads</dt>
                                    <dd class="text-lg font-medium text-gray-900">${data.summary?.total_leads || 0}</dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                                    </svg>
                                </div>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">Emails Sent</dt>
                                    <dd class="text-lg font-medium text-gray-900">${data.summary?.total_emails_sent || 0}</dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <div class="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                                    </svg>
                                </div>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">Reply Rate</dt>
                                    <dd class="text-lg font-medium text-gray-900">${data.summary?.reply_rate || 0}%</dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white shadow rounded-lg p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-600">New leads this week</span>
                            <span class="text-sm font-medium text-gray-900">${data.recent_activity?.new_leads_this_week || 0}</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-600">Emails sent this week</span>
                            <span class="text-sm font-medium text-gray-900">${data.recent_activity?.emails_sent_this_week || 0}</span>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white shadow rounded-lg p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Performance Overview</h3>
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-600">Open Rate</span>
                            <span class="text-sm font-medium text-gray-900">${data.summary?.open_rate || 0}%</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-600">Active Campaigns</span>
                            <span class="text-sm font-medium text-gray-900">${data.summary?.active_campaigns || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderCampaignSelect() {
        const select = document.getElementById('klentyCampaignSelect');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select a campaign...</option>' +
            this.campaigns.map(campaign => 
                `<option value="${campaign.campaign_id}">${campaign.name}</option>`
            ).join('');
    }
    
    renderCampaignsTable() {
        const container = document.getElementById('campaignsContainer');
        if (!container) return;
        
        if (this.campaigns.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No campaigns found. Create your first campaign to get started.</p>';
            return;
        }
        
        container.innerHTML = `
            <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                <table class="min-w-full divide-y divide-gray-300">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Campaign</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Leads</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Emails Sent</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Open Rate</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${this.campaigns.map(campaign => `
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div>
                                        <div class="text-sm font-medium text-gray-900">${campaign.name}</div>
                                        <div class="text-sm text-gray-500">${campaign.description || ''}</div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getStatusClass(campaign.status)}">
                                        ${campaign.status}
                                    </span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${campaign.total_prospects || 0}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${campaign.emails_sent || 0}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${this.calculateOpenRate(campaign)}%</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                                    <button onclick="klentyDashboard.selectCampaign('${campaign.campaign_id}')" class="text-indigo-600 hover:text-indigo-900">View</button>
                                    <button onclick="klentyDashboard.editCampaign('${campaign.campaign_id}')" class="text-green-600 hover:text-green-900">Edit</button>
                                    ${campaign.status === 'draft' ? 
                                        `<button onclick="klentyDashboard.startCampaign('${campaign.campaign_id}')" class="text-blue-600 hover:text-blue-900">Start</button>` :
                                        `<button onclick="klentyDashboard.pauseCampaign('${campaign.campaign_id}')" class="text-yellow-600 hover:text-yellow-900">Pause</button>`
                                    }
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    getStatusClass(status) {
        const statusClasses = {
            'draft': 'bg-gray-100 text-gray-800',
            'active': 'bg-green-100 text-green-800',
            'paused': 'bg-yellow-100 text-yellow-800',
            'completed': 'bg-blue-100 text-blue-800',
            'cancelled': 'bg-red-100 text-red-800'
        };
        return statusClasses[status] || 'bg-gray-100 text-gray-800';
    }
    
    calculateOpenRate(campaign) {
        if (!campaign.emails_sent || campaign.emails_sent === 0) return 0;
        return Math.round((campaign.emails_opened || 0) / campaign.emails_sent * 100);
    }
    
    async createCampaign() {
        const form = document.getElementById('createKlentyCampaignForm');
        const formData = new FormData(form);
        
        const campaignData = {
            name: formData.get('name'),
            description: formData.get('description'),
            sender_email: formData.get('sender_email'),
            sender_name: formData.get('sender_name'),
            target_audience: {
                industries: formData.get('industries')?.split(',').map(s => s.trim()).filter(s => s),
                job_titles: formData.get('job_titles')?.split(',').map(s => s.trim()).filter(s => s),
                company_sizes: formData.get('company_sizes')?.split(',').map(s => s.trim()).filter(s => s)
            },
            daily_email_limit: parseInt(formData.get('daily_email_limit')) || 100,
            weekly_email_limit: parseInt(formData.get('weekly_email_limit')) || 500
        };
        
        try {
            const response = await fetch(`${this.API_BASE}/api/klenty/campaigns`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(campaignData)
            });
            
            if (response.ok) {
                this.showSuccess('Campaign created successfully');
                this.hideModal('createKlentyCampaignModal');
                this.loadDashboardData();
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to create campaign');
            }
        } catch (error) {
            console.error('Error creating campaign:', error);
            this.showError('Failed to create campaign');
        }
    }
    
    async sendScheduledEmails() {
        try {
            this.showLoading('send-emails');
            
            const response = await fetch(`${this.API_BASE}/api/klenty/emails/send-scheduled`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ limit: 100 })
            });
            
            if (response.ok) {
                const results = await response.json();
                this.showSuccess(`Sent ${results.results.emails_sent} emails successfully`);
                this.loadDashboardData(); // Refresh data
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to send emails');
            }
            
            this.hideLoading('send-emails');
        } catch (error) {
            console.error('Error sending emails:', error);
            this.showError('Failed to send emails');
            this.hideLoading('send-emails');
        }
    }
    
    selectCampaign(campaignId) {
        this.currentCampaign = campaignId;
        document.getElementById('klentyCampaignSelect').value = campaignId;
        this.loadCampaignData(campaignId);
        this.switchTab('campaigns');
    }
    
    async startCampaign(campaignId) {
        try {
            const response = await fetch(`${this.API_BASE}/api/klenty/campaigns/${campaignId}/start`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                this.showSuccess('Campaign started successfully');
                this.loadCampaignsData();
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to start campaign');
            }
        } catch (error) {
            console.error('Error starting campaign:', error);
            this.showError('Failed to start campaign');
        }
    }
    
    async pauseCampaign(campaignId) {
        try {
            const response = await fetch(`${this.API_BASE}/api/klenty/campaigns/${campaignId}/pause`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                this.showSuccess('Campaign paused successfully');
                this.loadCampaignsData();
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to pause campaign');
            }
        } catch (error) {
            console.error('Error pausing campaign:', error);
            this.showError('Failed to pause campaign');
        }
    }
    
    // Utility methods
    showModal(modalId) {
        document.getElementById(modalId)?.classList.remove('hidden');
    }
    
    hideModal(modalId) {
        document.getElementById(modalId)?.classList.add('hidden');
    }
    
    showCreateCampaignModal() {
        this.showModal('createKlentyCampaignModal');
    }
    
    showCreateSequenceModal() {
        if (!this.currentCampaign) {
            this.showError('Please select a campaign first');
            return;
        }
        this.showModal('createSequenceModal');
    }
    
    showImportLeadsModal() {
        if (!this.currentCampaign) {
            this.showError('Please select a campaign first');
            return;
        }
        this.showModal('importLeadsModal');
    }
    
    showSyncLinkedInModal() {
        this.showModal('syncLinkedInModal');
    }
    
    showLoading(target) {
        const loadingEl = document.getElementById(`${target}-loading`);
        if (loadingEl) loadingEl.classList.remove('hidden');
    }
    
    hideLoading(target) {
        const loadingEl = document.getElementById(`${target}-loading`);
        if (loadingEl) loadingEl.classList.add('hidden');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    startAutoRefresh() {
        // Refresh data every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 300000);
    }
    
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Initialize dashboard when page loads
let klentyDashboard;
document.addEventListener('DOMContentLoaded', () => {
    klentyDashboard = new KlentyDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (klentyDashboard) {
        klentyDashboard.destroy();
    }
});