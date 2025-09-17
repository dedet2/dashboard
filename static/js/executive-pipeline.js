// Executive Pipeline Management JavaScript
class ExecutivePipelineManager {
    constructor() {
        this.authToken = localStorage.getItem('authToken');
        this.API_BASE = window.location.origin;
        this.opportunities = [];
        this.speakingOpportunities = [];
        this.currentFilter = 'all';
        this.currentSort = 'ai_match_score';
        this.editingOpportunity = null;
        
        this.init();
    }

    init() {
        if (!this.authToken) {
            window.location.href = '/';
            return;
        }

        this.setupEventListeners();
        this.loadPipelineData();
    }

    setupEventListeners() {
        // Modal controls
        document.getElementById('addOpportunityBtn').addEventListener('click', () => this.openOpportunityModal());
        document.getElementById('closeModal').addEventListener('click', () => this.closeOpportunityModal());
        document.getElementById('cancelForm').addEventListener('click', () => this.closeOpportunityModal());
        document.getElementById('opportunityForm').addEventListener('submit', (e) => this.saveOpportunity(e));
        
        // Hunter controls
        document.getElementById('speakingHunterBtn').addEventListener('click', () => this.openSpeakingHunter());
        document.getElementById('closeHunter').addEventListener('click', () => this.closeSpeakingHunter());
        
        // Analytics controls
        document.getElementById('analyticsBtn').addEventListener('click', () => this.openAnalytics());
        document.getElementById('closeAnalytics').addEventListener('click', () => this.closeAnalytics());
        
        // Detail modal
        document.getElementById('detailModal').addEventListener('click', (e) => {
            if (e.target.id === 'detailModal') {
                this.closeDetailModal();
            }
        });
        
        // Filter controls
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter(e.target.dataset.filter);
            });
        });
        
        // Sort control
        document.getElementById('sortBy').addEventListener('change', (e) => {
            this.currentSort = e.target.value;
            this.renderOpportunities();
        });
        
        // Set initial filter
        this.setFilter('all');
    }

    async loadPipelineData() {
        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };
            
            // Load executive opportunities
            const execResponse = await axios.get(`${this.API_BASE}/api/executive/opportunities`, { headers });
            this.opportunities = execResponse.data;
            
            // Load speaking opportunities
            const speakingResponse = await axios.get(`${this.API_BASE}/api/speaking/opportunities`, { headers });
            this.speakingOpportunities = speakingResponse.data;
            
            // Merge speaking opportunities into main opportunities array
            const speakingAsExec = this.speakingOpportunities.map(opp => ({
                ...opp,
                type: 'speaking',
                ai_match_score: opp.ai_match_score || 0,
                compensation_range: opp.speaking_fee,
                title: opp.title,
                company: opp.organizer
            }));
            
            this.opportunities = [...this.opportunities, ...speakingAsExec];
            
            this.updateSummaryCards();
            this.renderOpportunities();
            
        } catch (error) {
            console.error('Failed to load pipeline data:', error);
            this.showNotification('Failed to load pipeline data', 'error');
        }
    }

    updateSummaryCards() {
        const total = this.opportunities.length;
        const activeInterviews = this.opportunities.filter(opp => opp.status === 'interview_stage').length;
        const pendingOffers = this.opportunities.filter(opp => opp.status === 'offer_received').length;
        const accepted = this.opportunities.filter(opp => opp.status === 'accepted').length;
        const successRate = total > 0 ? Math.round((accepted / total) * 100) : 0;
        
        document.getElementById('totalOpportunities').textContent = total;
        document.getElementById('activeInterviews').textContent = activeInterviews;
        document.getElementById('pendingOffers').textContent = pendingOffers;
        document.getElementById('successRate').textContent = `${successRate}%`;
    }

    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('filter-active', 'bg-gray-200', 'text-gray-700');
            btn.classList.add('bg-gray-200', 'text-gray-700');
        });
        
        document.querySelector(`[data-filter="${filter}"]`).classList.remove('bg-gray-200', 'text-gray-700');
        document.querySelector(`[data-filter="${filter}"]`).classList.add('filter-active');
        
        this.renderOpportunities();
    }

    renderOpportunities() {
        // Filter opportunities
        let filteredOpportunities = this.opportunities;
        if (this.currentFilter !== 'all') {
            filteredOpportunities = this.opportunities.filter(opp => opp.type === this.currentFilter);
        }
        
        // Sort opportunities
        filteredOpportunities.sort((a, b) => {
            if (this.currentSort === 'ai_match_score') {
                return (b.ai_match_score || 0) - (a.ai_match_score || 0);
            } else if (this.currentSort === 'created_at') {
                return new Date(b.created_at || Date.now()) - new Date(a.created_at || Date.now());
            } else if (this.currentSort === 'deadline') {
                if (!a.deadline) return 1;
                if (!b.deadline) return -1;
                return new Date(a.deadline) - new Date(b.deadline);
            } else if (this.currentSort === 'priority_level') {
                const priority = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
                return (priority[b.priority_level] || 0) - (priority[a.priority_level] || 0);
            }
            return 0;
        });
        
        // Group by status
        const statusGroups = {
            prospect: [],
            applied: [],
            interview_stage: [],
            under_consideration: [],
            offer_received: [],
            closed: [] // accepted + rejected
        };
        
        filteredOpportunities.forEach(opp => {
            if (opp.status === 'accepted' || opp.status === 'rejected') {
                statusGroups.closed.push(opp);
            } else if (statusGroups[opp.status]) {
                statusGroups[opp.status].push(opp);
            } else {
                statusGroups.prospect.push(opp);
            }
        });
        
        // Update counts
        Object.keys(statusGroups).forEach(status => {
            const countElement = document.getElementById(`${status}Count`);
            if (countElement) {
                countElement.textContent = statusGroups[status].length;
            }
        });
        
        // Render cards in each column
        Object.keys(statusGroups).forEach(status => {
            const container = document.getElementById(`${status}Opportunities`);
            if (container) {
                container.innerHTML = statusGroups[status]
                    .map(opp => this.createOpportunityCard(opp))
                    .join('');
            }
        });
        
        // Setup drag and drop
        this.setupDragAndDrop();
    }

    createOpportunityCard(opportunity) {
        const typeIcons = {
            board_director: 'fas fa-chess-king board-icon',
            executive_position: 'fas fa-crown executive-icon', 
            advisor: 'fas fa-lightbulb advisor-icon',
            speaking: 'fas fa-microphone speaking-icon'
        };
        
        const priorityClass = `priority-${opportunity.priority_level || 'medium'}`;
        const matchScore = Math.round(opportunity.ai_match_score || 0);
        
        return `
            <div class="opportunity-card ${priorityClass} p-4 cursor-pointer" 
                 data-id="${opportunity.id}" 
                 data-type="${opportunity.type || 'executive'}"
                 onclick="pipelineManager.openOpportunityDetail(${opportunity.id}, '${opportunity.type || 'executive'}')">
                
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center space-x-2">
                        <i class="${typeIcons[opportunity.type] || 'fas fa-briefcase text-gray-500'}"></i>
                        <span class="match-score">${matchScore}%</span>
                    </div>
                    <div class="flex items-center space-x-1">
                        ${opportunity.priority_level === 'critical' ? '<i class="fas fa-exclamation text-red-500"></i>' : ''}
                        ${opportunity.deadline ? '<i class="fas fa-clock text-orange-500"></i>' : ''}
                    </div>
                </div>
                
                <h4 class="font-semibold text-gray-900 mb-2 line-clamp-2">${opportunity.title || 'Untitled'}</h4>
                <p class="text-sm text-gray-600 mb-2">${opportunity.company || 'Unknown Company'}</p>
                
                ${opportunity.compensation_range ? 
                    `<p class="text-sm text-green-600 font-medium mb-2">${opportunity.compensation_range}</p>` : ''}
                
                ${opportunity.location ? 
                    `<p class="text-xs text-gray-500 mb-2"><i class="fas fa-map-marker-alt mr-1"></i>${opportunity.location}</p>` : ''}
                
                ${opportunity.deadline ? 
                    `<p class="text-xs text-red-500 mb-2"><i class="fas fa-calendar mr-1"></i>Due: ${new Date(opportunity.deadline).toLocaleDateString()}</p>` : ''}
                
                ${opportunity.next_step ? 
                    `<p class="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded mt-2">${opportunity.next_step}</p>` : ''}
                
                <div class="flex justify-between items-center mt-3 pt-2 border-t border-gray-100">
                    <span class="text-xs text-gray-400">${this.getTimeAgo(opportunity.created_at || Date.now())}</span>
                    <div class="flex space-x-2">
                        <button onclick="event.stopPropagation(); pipelineManager.editOpportunity(${opportunity.id}, '${opportunity.type || 'executive'}')" 
                                class="text-blue-500 hover:text-blue-700">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="event.stopPropagation(); pipelineManager.deleteOpportunity(${opportunity.id}, '${opportunity.type || 'executive'}')" 
                                class="text-red-500 hover:text-red-700">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    setupDragAndDrop() {
        // Add drag and drop functionality for status updates
        const cards = document.querySelectorAll('.opportunity-card');
        const columns = document.querySelectorAll('.kanban-column');
        
        cards.forEach(card => {
            card.draggable = true;
            
            card.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', card.dataset.id);
                e.dataTransfer.setData('application/json', JSON.stringify({
                    id: card.dataset.id,
                    type: card.dataset.type
                }));
                card.style.opacity = '0.5';
            });
            
            card.addEventListener('dragend', (e) => {
                card.style.opacity = '1';
            });
        });
        
        columns.forEach(column => {
            column.addEventListener('dragover', (e) => {
                e.preventDefault();
                column.classList.add('bg-gray-100');
            });
            
            column.addEventListener('dragleave', (e) => {
                column.classList.remove('bg-gray-100');
            });
            
            column.addEventListener('drop', (e) => {
                e.preventDefault();
                column.classList.remove('bg-gray-100');
                
                const data = JSON.parse(e.dataTransfer.getData('application/json'));
                const newStatus = column.dataset.status;
                
                this.updateOpportunityStatus(data.id, data.type, newStatus);
            });
        });
    }

    async updateOpportunityStatus(id, type, newStatus) {
        try {
            const headers = { 
                'Authorization': `Bearer ${this.authToken}`,
                'Content-Type': 'application/json'
            };
            
            // Map closed status to specific statuses
            let actualStatus = newStatus;
            if (newStatus === 'closed') {
                actualStatus = 'rejected'; // Default to rejected, user can change later
            }
            
            const endpoint = type === 'speaking' ? 
                `/api/speaking/opportunities/${id}` : 
                `/api/executive/opportunities/${id}/status`;
            
            const updateData = { status: actualStatus };
            
            await axios.put(`${this.API_BASE}${endpoint}`, updateData, { headers });
            
            // Update local data
            const oppIndex = this.opportunities.findIndex(opp => 
                opp.id == id && (opp.type || 'executive') === type
            );
            
            if (oppIndex !== -1) {
                this.opportunities[oppIndex].status = actualStatus;
            }
            
            this.renderOpportunities();
            this.showNotification('Status updated successfully', 'success');
            
        } catch (error) {
            console.error('Failed to update status:', error);
            this.showNotification('Failed to update status', 'error');
            this.loadPipelineData(); // Reload data
        }
    }

    openOpportunityModal(opportunity = null) {
        this.editingOpportunity = opportunity;
        
        if (opportunity) {
            document.getElementById('modalTitle').textContent = 'Edit Opportunity';
            this.populateForm(opportunity);
        } else {
            document.getElementById('modalTitle').textContent = 'Add New Opportunity';
            this.clearForm();
        }
        
        document.getElementById('opportunityModal').classList.remove('hidden');
    }

    closeOpportunityModal() {
        document.getElementById('opportunityModal').classList.add('hidden');
        this.editingOpportunity = null;
        this.clearForm();
    }

    populateForm(opportunity) {
        document.getElementById('opportunityType').value = opportunity.type || '';
        document.getElementById('title').value = opportunity.title || '';
        document.getElementById('company').value = opportunity.company || '';
        document.getElementById('location').value = opportunity.location || '';
        document.getElementById('compensationRange').value = opportunity.compensation_range || '';
        document.getElementById('status').value = opportunity.status || 'prospect';
        document.getElementById('priorityLevel').value = opportunity.priority_level || 'medium';
        document.getElementById('applicationDate').value = opportunity.application_date || '';
        document.getElementById('deadline').value = opportunity.deadline || '';
        document.getElementById('source').value = opportunity.source || '';
        document.getElementById('requirements').value = (opportunity.requirements || []).join(', ');
        document.getElementById('notes').value = opportunity.notes || '';
        document.getElementById('nextStep').value = opportunity.next_step || '';
    }

    clearForm() {
        document.getElementById('opportunityForm').reset();
        document.getElementById('priorityLevel').value = 'medium';
        document.getElementById('status').value = 'prospect';
    }

    async saveOpportunity(e) {
        e.preventDefault();
        
        try {
            const formData = {
                type: document.getElementById('opportunityType').value,
                title: document.getElementById('title').value,
                company: document.getElementById('company').value,
                location: document.getElementById('location').value,
                compensation_range: document.getElementById('compensationRange').value,
                status: document.getElementById('status').value,
                priority_level: document.getElementById('priorityLevel').value,
                application_date: document.getElementById('applicationDate').value,
                deadline: document.getElementById('deadline').value,
                source: document.getElementById('source').value,
                requirements: document.getElementById('requirements').value.split(',').map(req => req.trim()).filter(req => req),
                notes: document.getElementById('notes').value,
                next_step: document.getElementById('nextStep').value
            };
            
            const headers = {
                'Authorization': `Bearer ${this.authToken}`,
                'Content-Type': 'application/json'
            };
            
            let response;
            if (this.editingOpportunity) {
                // Update existing opportunity
                const endpoint = this.editingOpportunity.type === 'speaking' ?
                    `/api/speaking/opportunities/${this.editingOpportunity.id}` :
                    `/api/executive/opportunities/${this.editingOpportunity.id}`;
                
                response = await axios.put(`${this.API_BASE}${endpoint}`, formData, { headers });
            } else {
                // Create new opportunity
                const endpoint = formData.type === 'speaking' ?
                    '/api/speaking/opportunities' :
                    '/api/executive/opportunities';
                
                // Score the opportunity with AI
                try {
                    const scoreResponse = await axios.post(`${this.API_BASE}/api/ai-matching/score-opportunity`, {
                        type: formData.type,
                        requirements: formData.requirements,
                        company_info: { industry: 'unknown' },
                        position_details: {}
                    }, { headers });
                    
                    formData.ai_match_score = scoreResponse.data.ai_match_score;
                } catch (scoreError) {
                    console.warn('AI scoring failed, using default score');
                    formData.ai_match_score = 50;
                }
                
                response = await axios.post(`${this.API_BASE}${endpoint}`, formData, { headers });
            }
            
            this.closeOpportunityModal();
            this.showNotification(
                this.editingOpportunity ? 'Opportunity updated successfully' : 'Opportunity created successfully', 
                'success'
            );
            this.loadPipelineData();
            
        } catch (error) {
            console.error('Failed to save opportunity:', error);
            this.showNotification('Failed to save opportunity', 'error');
        }
    }

    async editOpportunity(id, type) {
        const opportunity = this.opportunities.find(opp => 
            opp.id == id && (opp.type || 'executive') === type
        );
        
        if (opportunity) {
            this.openOpportunityModal(opportunity);
        }
    }

    async deleteOpportunity(id, type) {
        if (!confirm('Are you sure you want to delete this opportunity?')) {
            return;
        }
        
        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };
            
            const endpoint = type === 'speaking' ?
                `/api/speaking/opportunities/${id}` :
                `/api/executive/opportunities/${id}`;
            
            await axios.delete(`${this.API_BASE}${endpoint}`, { headers });
            
            this.showNotification('Opportunity deleted successfully', 'success');
            this.loadPipelineData();
            
        } catch (error) {
            console.error('Failed to delete opportunity:', error);
            this.showNotification('Failed to delete opportunity', 'error');
        }
    }

    async openOpportunityDetail(id, type) {
        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };
            
            const endpoint = type === 'speaking' ?
                `/api/speaking/opportunities/${id}` :
                `/api/executive/opportunities/${id}`;
            
            const response = await axios.get(`${this.API_BASE}${endpoint}`, { headers });
            const opportunity = response.data;
            
            // Create detailed view
            const detailHTML = this.createDetailView(opportunity, type);
            document.getElementById('detailContent').innerHTML = detailHTML;
            document.getElementById('detailModal').classList.remove('hidden');
            
        } catch (error) {
            console.error('Failed to load opportunity details:', error);
            this.showNotification('Failed to load opportunity details', 'error');
        }
    }

    createDetailView(opportunity, type) {
        const typeIcons = {
            board_director: 'fas fa-chess-king board-icon',
            executive_position: 'fas fa-crown executive-icon',
            advisor: 'fas fa-lightbulb advisor-icon',
            speaking: 'fas fa-microphone speaking-icon'
        };
        
        return `
            <div class="p-6 border-b border-gray-200">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <i class="${typeIcons[opportunity.type] || 'fas fa-briefcase text-gray-500'} text-2xl"></i>
                        <div>
                            <h2 class="text-2xl font-bold text-gray-900">${opportunity.title || 'Untitled'}</h2>
                            <p class="text-lg text-gray-600">${opportunity.company || 'Unknown Company'}</p>
                        </div>
                    </div>
                    <button onclick="pipelineManager.closeDetailModal()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
            </div>
            
            <div class="p-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="space-y-4">
                        <div>
                            <h3 class="font-semibold text-gray-800 mb-2">Basic Information</h3>
                            <div class="space-y-2">
                                <p><strong>Type:</strong> ${opportunity.type || 'Executive'}</p>
                                <p><strong>Location:</strong> ${opportunity.location || 'Not specified'}</p>
                                <p><strong>Compensation:</strong> ${opportunity.compensation_range || opportunity.speaking_fee || 'Not specified'}</p>
                                <p><strong>Status:</strong> <span class="px-2 py-1 rounded text-sm status-${opportunity.status}">${opportunity.status}</span></p>
                                <p><strong>Priority:</strong> ${opportunity.priority_level || 'Medium'}</p>
                                <p><strong>AI Match Score:</strong> <span class="match-score">${Math.round(opportunity.ai_match_score || 0)}%</span></p>
                            </div>
                        </div>
                        
                        <div>
                            <h3 class="font-semibold text-gray-800 mb-2">Timeline</h3>
                            <div class="space-y-2">
                                <p><strong>Created:</strong> ${new Date(opportunity.created_at || Date.now()).toLocaleDateString()}</p>
                                <p><strong>Application Date:</strong> ${opportunity.application_date ? new Date(opportunity.application_date).toLocaleDateString() : 'Not set'}</p>
                                <p><strong>Deadline:</strong> ${opportunity.deadline ? new Date(opportunity.deadline).toLocaleDateString() : 'Not set'}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="space-y-4">
                        <div>
                            <h3 class="font-semibold text-gray-800 mb-2">Requirements</h3>
                            <div class="flex flex-wrap gap-2">
                                ${(opportunity.requirements || []).map(req => 
                                    `<span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">${req}</span>`
                                ).join('')}
                            </div>
                        </div>
                        
                        <div>
                            <h3 class="font-semibold text-gray-800 mb-2">Notes</h3>
                            <p class="text-gray-700 bg-gray-50 p-3 rounded">${opportunity.notes || 'No notes added'}</p>
                        </div>
                        
                        <div>
                            <h3 class="font-semibold text-gray-800 mb-2">Next Step</h3>
                            <p class="text-blue-600 bg-blue-50 p-3 rounded">${opportunity.next_step || 'No next step defined'}</p>
                        </div>
                    </div>
                </div>
                
                <div class="flex justify-end space-x-4 mt-8 pt-6 border-t border-gray-200">
                    <button onclick="pipelineManager.editOpportunity(${opportunity.id}, '${type}')" 
                            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Edit Opportunity
                    </button>
                </div>
            </div>
        `;
    }

    closeDetailModal() {
        document.getElementById('detailModal').classList.add('hidden');
    }

    async openSpeakingHunter() {
        document.getElementById('hunterModal').classList.remove('hidden');
        
        try {
            const headers = {
                'Authorization': `Bearer ${this.authToken}`,
                'Content-Type': 'application/json'
            };
            
            const response = await axios.post(`${this.API_BASE}/api/speaking-hunter/search`, {
                topics: ['AI governance', 'risk management', 'digital transformation'],
                event_types: ['conference', 'webinar', 'workshop'],
                min_audience: 100
            }, { headers });
            
            const results = response.data.discovered_opportunities;
            
            const hunterHTML = `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-4">🎯 Discovered Speaking Opportunities</h3>
                    <p class="text-gray-600 mb-4">Found ${results.length} speaking opportunities matching your expertise:</p>
                    
                    <div class="space-y-4">
                        ${results.map(opp => `
                            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                                <div class="flex items-start justify-between">
                                    <div class="flex-1">
                                        <h4 class="font-semibold text-gray-900 mb-2">${opp.title}</h4>
                                        <p class="text-sm text-gray-600 mb-2">${opp.event_name} • ${opp.organizer}</p>
                                        <div class="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                                            <span><i class="fas fa-calendar mr-1"></i>${new Date(opp.event_date).toLocaleDateString()}</span>
                                            <span><i class="fas fa-users mr-1"></i>${opp.audience_size} attendees</span>
                                            <span><i class="fas fa-dollar-sign mr-1"></i>${opp.speaking_fee}</span>
                                        </div>
                                        <div class="flex flex-wrap gap-1 mb-2">
                                            ${opp.requirements.map(req => 
                                                `<span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">${req}</span>`
                                            ).join('')}
                                        </div>
                                    </div>
                                    <div class="ml-4 text-center">
                                        <div class="match-score mb-2">${opp.ai_match_score}%</div>
                                        <button onclick="pipelineManager.addSpeakingOpportunity(${JSON.stringify(opp).replace(/\"/g, '&quot;')})" 
                                                class="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600">
                                            Add to Pipeline
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            document.getElementById('hunterResults').innerHTML = hunterHTML;
            
        } catch (error) {
            console.error('Failed to hunt speaking opportunities:', error);
            document.getElementById('hunterResults').innerHTML = '<p class="text-red-600">Failed to discover speaking opportunities. Please try again.</p>';
        }
    }

    closeSpeakingHunter() {
        document.getElementById('hunterModal').classList.add('hidden');
    }

    async addSpeakingOpportunity(opportunity) {
        try {
            const headers = {
                'Authorization': `Bearer ${this.authToken}`,
                'Content-Type': 'application/json'
            };
            
            const speakingData = {
                title: opportunity.title,
                event_name: opportunity.event_name,
                organizer: opportunity.organizer,
                event_type: opportunity.event_type,
                event_date: opportunity.event_date,
                submission_deadline: opportunity.submission_deadline,
                speaking_fee: opportunity.speaking_fee,
                audience_size: opportunity.audience_size,
                location: opportunity.location,
                topic_alignment: opportunity.topic_alignment || [],
                status: 'prospect',
                ai_match_score: opportunity.ai_match_score,
                source: 'automated_hunter',
                requirements: opportunity.requirements || [],
                travel_required: opportunity.travel_required,
                virtual_option: opportunity.virtual_option
            };
            
            await axios.post(`${this.API_BASE}/api/speaking/opportunities`, speakingData, { headers });
            
            this.showNotification('Speaking opportunity added to pipeline', 'success');
            this.closeSpeakingHunter();
            this.loadPipelineData();
            
        } catch (error) {
            console.error('Failed to add speaking opportunity:', error);
            this.showNotification('Failed to add speaking opportunity', 'error');
        }
    }

    async openAnalytics() {
        document.getElementById('analyticsModal').classList.remove('hidden');
        
        try {
            const headers = { 'Authorization': `Bearer ${this.authToken}` };
            const response = await axios.get(`${this.API_BASE}/api/pipeline/analytics`, { headers });
            const analytics = response.data;
            
            const analyticsHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="bg-white p-6 rounded-lg border">
                        <h3 class="text-lg font-semibold mb-4">Executive Opportunities</h3>
                        <div class="space-y-2">
                            <p><strong>Total:</strong> ${analytics.executive_opportunities.total}</p>
                            ${Object.entries(analytics.executive_opportunities.by_status).map(([status, count]) => 
                                `<p><strong>${status.replace('_', ' ')}:</strong> ${count}</p>`
                            ).join('')}
                        </div>
                        <div class="mt-4">
                            <h4 class="font-medium mb-2">By Type:</h4>
                            ${Object.entries(analytics.executive_opportunities.by_type).map(([type, count]) => 
                                `<p>${type.replace('_', ' ')}: ${count}</p>`
                            ).join('')}
                        </div>
                    </div>
                    
                    <div class="bg-white p-6 rounded-lg border">
                        <h3 class="text-lg font-semibold mb-4">Speaking Opportunities</h3>
                        <div class="space-y-2">
                            <p><strong>Total:</strong> ${analytics.speaking_opportunities.total}</p>
                            ${Object.entries(analytics.speaking_opportunities.by_status).map(([status, count]) => 
                                `<p><strong>${status.replace('_', ' ')}:</strong> ${count}</p>`
                            ).join('')}
                        </div>
                    </div>
                    
                    <div class="bg-white p-6 rounded-lg border">
                        <h3 class="text-lg font-semibold mb-4">Conversion Rates</h3>
                        <div class="space-y-2">
                            <p><strong>Application → Interview:</strong> ${analytics.conversion_rates.application_to_interview.toFixed(1)}%</p>
                            <p><strong>Interview → Offer:</strong> ${analytics.conversion_rates.interview_to_offer.toFixed(1)}%</p>
                            <p><strong>Offer → Acceptance:</strong> ${analytics.conversion_rates.offer_to_acceptance.toFixed(1)}%</p>
                            <p><strong>Overall Conversion:</strong> ${analytics.conversion_rates.overall_conversion.toFixed(1)}%</p>
                        </div>
                    </div>
                    
                    <div class="bg-white p-6 rounded-lg border">
                        <h3 class="text-lg font-semibold mb-4">Pipeline Health</h3>
                        <div class="text-center">
                            <div class="text-4xl font-bold text-green-600 mb-2">${analytics.pipeline_health_score}/100</div>
                            <p class="text-gray-600">Overall Health Score</p>
                            <div class="mt-4">
                                <p><strong>Interview Stages:</strong> ${analytics.interview_stages.total}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('analyticsContent').innerHTML = analyticsHTML;
            
        } catch (error) {
            console.error('Failed to load analytics:', error);
            document.getElementById('analyticsContent').innerHTML = '<p class="text-red-600">Failed to load analytics data.</p>';
        }
    }

    closeAnalytics() {
        document.getElementById('analyticsModal').classList.add('hidden');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg transition-all duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-${
                    type === 'success' ? 'check-circle' :
                    type === 'error' ? 'exclamation-circle' :
                    type === 'warning' ? 'exclamation-triangle' :
                    'info-circle'
                }"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
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

// Initialize pipeline manager when DOM is loaded
let pipelineManager;
document.addEventListener('DOMContentLoaded', function() {
    pipelineManager = new ExecutivePipelineManager();
});