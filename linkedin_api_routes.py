"""
LinkedIn Sales Navigator Automation API Routes
Comprehensive REST API endpoints for LinkedIn campaign management, lead pipeline, 
workflow automation, and performance analytics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional, Any

from database import db
from linkedin_models import (
    LinkedInCampaign, LinkedInLead, LinkedInMessage, LinkedInMessageTemplate,
    LinkedInAutomationRule, LinkedInAnalytics, LinkedInCampaignStatus, LinkedInLeadStatus
)
from linkedin_automation_service import LinkedInAutomationService, LinkedInSearchCriteria
from linkedin_qualification_engine import LinkedInQualificationEngine, QualificationCriteria
from linkedin_outreach_workflows import OutreachWorkflowOrchestrator, WorkflowType
from linkedin_pipeline_management import LinkedInPipelineManager
from apollo_integration import ApolloAPIWrapper, create_apollo_wrapper
from perplexity_service import PerplexityAPI, create_perplexity_api
from make_automation_bridges import AutomationBridgeService

logger = logging.getLogger(__name__)

# Create Blueprint
linkedin_bp = Blueprint('linkedin_api', __name__, url_prefix='/api/linkedin')

# Initialize services (these would be properly initialized with credentials in production)
apollo_api = create_apollo_wrapper()
perplexity_api = create_perplexity_api()
automation_service = LinkedInAutomationService(apollo_api, perplexity_api)
qualification_engine = LinkedInQualificationEngine(apollo_api, perplexity_api)
workflow_orchestrator = OutreachWorkflowOrchestrator(qualification_engine)
pipeline_manager = LinkedInPipelineManager(
    automation_service, qualification_engine, workflow_orchestrator
)

# ===== CAMPAIGN MANAGEMENT ENDPOINTS =====

@linkedin_bp.route('/campaigns', methods=['GET'])
@jwt_required()
def get_campaigns():
    """Get all LinkedIn campaigns for the current user"""
    try:
        current_user = get_jwt_identity()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        # Build query
        query = LinkedInCampaign.query.filter_by(created_by=current_user)
        
        if status:
            query = query.filter_by(status=status)
        
        # Paginate results
        campaigns = query.order_by(LinkedInCampaign.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'campaigns': [campaign.to_dict() for campaign in campaigns.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': campaigns.total,
                'pages': campaigns.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting campaigns: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/campaigns', methods=['POST'])
@jwt_required()
def create_campaign():
    """Create a new LinkedIn campaign"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'target_audience']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Create campaign using automation service
        campaign = automation_service.create_campaign(
            name=data['name'],
            description=data.get('description', ''),
            target_audience=data['target_audience'],
            created_by=current_user,
            **data
        )
        
        if campaign:
            return jsonify({
                'success': True,
                'campaign': campaign.to_dict(),
                'message': 'Campaign created successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create campaign'}), 500
            
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/campaigns/<campaign_id>', methods=['GET'])
@jwt_required()
def get_campaign(campaign_id):
    """Get specific campaign details"""
    try:
        campaign = LinkedInCampaign.query.filter_by(campaign_id=campaign_id).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        # Get campaign analytics
        analytics = automation_service.get_campaign_analytics(campaign_id)
        
        campaign_data = campaign.to_dict()
        campaign_data['analytics'] = analytics
        
        return jsonify({
            'success': True,
            'campaign': campaign_data
        })
        
    except Exception as e:
        logger.error(f"Error getting campaign: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/campaigns/<campaign_id>/start', methods=['POST'])
@jwt_required()
def start_campaign(campaign_id):
    """Start a LinkedIn campaign"""
    try:
        campaign = LinkedInCampaign.query.filter_by(campaign_id=campaign_id).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        # Update campaign status
        campaign.status = LinkedInCampaignStatus.ACTIVE.value
        campaign.started_at = datetime.utcnow()
        campaign.last_activity = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Campaign started successfully',
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error starting campaign: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== LEAD MANAGEMENT ENDPOINTS =====

@linkedin_bp.route('/campaigns/<campaign_id>/leads', methods=['GET'])
@jwt_required()
def get_campaign_leads(campaign_id):
    """Get leads for a specific campaign"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        qualification = request.args.get('qualification')
        priority = request.args.get('priority')
        
        # Build query
        query = LinkedInLead.query.filter_by(campaign_id=campaign_id)
        
        if status:
            query = query.filter_by(status=status)
        if qualification:
            query = query.filter_by(qualification_status=qualification)
        
        # Paginate results
        leads = query.order_by(LinkedInLead.lead_score.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Add pipeline stage and priority to each lead
        leads_data = []
        for lead in leads.items:
            lead_data = lead.to_dict()
            lead_data['pipeline_stage'] = pipeline_manager._get_lead_stage(lead).value
            lead_data['priority'] = pipeline_manager._calculate_lead_priority(lead).value
            leads_data.append(lead_data)
        
        return jsonify({
            'success': True,
            'leads': leads_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': leads.total,
                'pages': leads.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting campaign leads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/campaigns/<campaign_id>/discover-leads', methods=['POST'])
@jwt_required()
def discover_leads(campaign_id):
    """Discover new leads for a campaign"""
    try:
        data = request.get_json()
        
        # Create search criteria
        search_criteria = LinkedInSearchCriteria(
            keywords=data.get('keywords'),
            titles=data.get('titles'),
            companies=data.get('companies'),
            industries=data.get('industries'),
            locations=data.get('locations'),
            experience_levels=data.get('experience_levels'),
            company_sizes=data.get('company_sizes'),
            connection_degree=data.get('connection_degree', '2nd')
        )
        
        limit = data.get('limit', 50)
        
        # Discover leads using automation service
        discovered_leads = automation_service.discover_leads(campaign_id, search_criteria, limit)
        
        return jsonify({
            'success': True,
            'leads_discovered': len(discovered_leads),
            'leads': [lead.to_dict() for lead in discovered_leads],
            'message': f'Discovered {len(discovered_leads)} new leads'
        })
        
    except Exception as e:
        logger.error(f"Error discovering leads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/leads/<lead_id>/qualify', methods=['POST'])
@jwt_required()
def qualify_lead(lead_id):
    """Qualify a specific lead"""
    try:
        # Enrich and qualify lead
        result = qualification_engine.enrich_and_qualify(lead_id)
        
        return jsonify({
            'success': True,
            'qualification_result': {
                'lead_id': result.lead_id,
                'qualification_level': result.qualification_level.value,
                'overall_score': result.overall_score,
                'component_scores': result.component_scores,
                'opportunity_matches': result.opportunity_matches,
                'recommended_actions': result.recommended_actions,
                'confidence_score': result.confidence_score
            },
            'message': 'Lead qualified successfully'
        })
        
    except Exception as e:
        logger.error(f"Error qualifying lead: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/leads/<lead_id>/connect', methods=['POST'])
@jwt_required()
def send_connection_request(lead_id):
    """Send connection request to a lead"""
    try:
        data = request.get_json()
        custom_message = data.get('message')
        
        # Send connection request
        success = automation_service.send_connection_request(lead_id, custom_message)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Connection request sent successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to send connection request'}), 500
            
    except Exception as e:
        logger.error(f"Error sending connection request: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/leads/<lead_id>/message', methods=['POST'])
@jwt_required()
def send_message(lead_id):
    """Send message to a lead"""
    try:
        data = request.get_json()
        
        if 'content' not in data:
            return jsonify({'success': False, 'error': 'Message content is required'}), 400
        
        # Send message
        success = automation_service.send_message(
            lead_id, 
            data['content'], 
            data.get('message_type', 'message')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Message sent successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to send message'}), 500
            
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== WORKFLOW MANAGEMENT ENDPOINTS =====

@linkedin_bp.route('/workflows/start', methods=['POST'])
@jwt_required()
def start_workflow():
    """Start an outreach workflow for a lead"""
    try:
        data = request.get_json()
        
        required_fields = ['workflow_type', 'lead_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Map workflow type string to enum
        workflow_type_map = {
            'cold_outreach': WorkflowType.COLD_OUTREACH,
            'warm_follow_up': WorkflowType.WARM_FOLLOW_UP,
            'response_nurture': WorkflowType.RESPONSE_NURTURE,
            'qualified_escalation': WorkflowType.QUALIFIED_ESCALATION,
            'vip_sequence': WorkflowType.VIP_SEQUENCE
        }
        
        workflow_type = workflow_type_map.get(data['workflow_type'])
        if not workflow_type:
            return jsonify({'success': False, 'error': 'Invalid workflow type'}), 400
        
        # Start workflow
        execution = workflow_orchestrator.start_workflow(
            workflow_type, 
            data['lead_id'],
            custom_params=data.get('custom_params')
        )
        
        if execution:
            return jsonify({
                'success': True,
                'execution_id': execution.execution_id,
                'workflow_type': execution.execution_data['workflow_type'],
                'message': 'Workflow started successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to start workflow'}), 500
            
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/workflows/process', methods=['POST'])
@jwt_required()
def process_workflows():
    """Process scheduled workflow actions"""
    try:
        # Process scheduled workflows
        results = workflow_orchestrator.process_scheduled_workflows()
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f"Processed {results.get('processed_workflows', 0)} workflows"
        })
        
    except Exception as e:
        logger.error(f"Error processing workflows: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/workflows/analytics', methods=['GET'])
@jwt_required()
def get_workflow_analytics():
    """Get workflow performance analytics"""
    try:
        campaign_id = request.args.get('campaign_id')
        
        # Get workflow analytics
        analytics = workflow_orchestrator.get_workflow_analytics(campaign_id)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting workflow analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== PIPELINE MANAGEMENT ENDPOINTS =====

@linkedin_bp.route('/pipeline/overview', methods=['GET'])
@jwt_required()
def get_pipeline_overview():
    """Get comprehensive pipeline overview"""
    try:
        campaign_id = request.args.get('campaign_id')
        
        # Get pipeline overview
        overview = pipeline_manager.get_pipeline_overview(campaign_id)
        
        return jsonify({
            'success': True,
            'overview': overview
        })
        
    except Exception as e:
        logger.error(f"Error getting pipeline overview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/pipeline/metrics', methods=['GET'])
@jwt_required()
def get_pipeline_metrics():
    """Get pipeline performance metrics"""
    try:
        campaign_id = request.args.get('campaign_id')
        
        # Get pipeline metrics
        metrics = pipeline_manager.get_pipeline_metrics(campaign_id)
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_leads': metrics.total_leads,
                'leads_by_stage': metrics.leads_by_stage,
                'leads_by_priority': metrics.leads_by_priority,
                'conversion_rates': metrics.conversion_rates,
                'average_cycle_time': metrics.average_cycle_time,
                'pipeline_velocity': metrics.pipeline_velocity,
                'qualification_rate': metrics.qualification_rate,
                'response_rate': metrics.response_rate,
                'opportunity_conversion_rate': metrics.opportunity_conversion_rate,
                'revenue_pipeline': metrics.revenue_pipeline
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting pipeline metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/pipeline/priority-leads', methods=['GET'])
@jwt_required()
def get_priority_leads():
    """Get prioritized leads requiring attention"""
    try:
        campaign_id = request.args.get('campaign_id')
        limit = request.args.get('limit', 20, type=int)
        
        # Get priority leads
        priority_leads = pipeline_manager.get_priority_leads(campaign_id, limit)
        
        return jsonify({
            'success': True,
            'priority_leads': priority_leads
        })
        
    except Exception as e:
        logger.error(f"Error getting priority leads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/pipeline/alerts', methods=['GET'])
@jwt_required()
def get_pipeline_alerts():
    """Get active pipeline alerts"""
    try:
        campaign_id = request.args.get('campaign_id')
        
        # Get active alerts
        alerts = pipeline_manager.get_active_alerts(campaign_id)
        
        return jsonify({
            'success': True,
            'alerts': alerts
        })
        
    except Exception as e:
        logger.error(f"Error getting pipeline alerts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/pipeline/alerts/<alert_id>/acknowledge', methods=['POST'])
@jwt_required()
def acknowledge_alert(alert_id):
    """Acknowledge a pipeline alert"""
    try:
        # Acknowledge alert
        success = pipeline_manager.acknowledge_alert(alert_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Alert acknowledged successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
            
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/pipeline/funnel', methods=['GET'])
@jwt_required()
def get_conversion_funnel():
    """Get conversion funnel analysis"""
    try:
        campaign_id = request.args.get('campaign_id')
        
        # Get conversion funnel
        funnel = pipeline_manager.get_conversion_funnel(campaign_id)
        
        return jsonify({
            'success': True,
            'funnel': funnel
        })
        
    except Exception as e:
        logger.error(f"Error getting conversion funnel: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/pipeline/trends', methods=['GET'])
@jwt_required()
def get_pipeline_trends():
    """Get pipeline performance trends"""
    try:
        campaign_id = request.args.get('campaign_id')
        days = request.args.get('days', 30, type=int)
        
        # Get pipeline trends
        trends = pipeline_manager.get_pipeline_trends(campaign_id, days)
        
        return jsonify({
            'success': True,
            'trends': trends
        })
        
    except Exception as e:
        logger.error(f"Error getting pipeline trends: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/pipeline/process', methods=['POST'])
@jwt_required()
def process_pipeline_automation():
    """Process pipeline automation tasks"""
    try:
        # Process pipeline automation
        results = pipeline_manager.process_pipeline_automation()
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f"Processed {results.get('leads_processed', 0)} leads"
        })
        
    except Exception as e:
        logger.error(f"Error processing pipeline automation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== MESSAGE TEMPLATE ENDPOINTS =====

@linkedin_bp.route('/campaigns/<campaign_id>/templates', methods=['GET'])
@jwt_required()
def get_message_templates(campaign_id):
    """Get message templates for a campaign"""
    try:
        templates = LinkedInMessageTemplate.query.filter_by(campaign_id=campaign_id).all()
        
        return jsonify({
            'success': True,
            'templates': [template.to_dict() for template in templates]
        })
        
    except Exception as e:
        logger.error(f"Error getting message templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/campaigns/<campaign_id>/templates', methods=['POST'])
@jwt_required()
def create_message_template(campaign_id):
    """Create a new message template"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'template_type', 'message_content']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        template_id = f"{campaign_id}_{data['template_type']}_{int(datetime.utcnow().timestamp())}"
        
        template = LinkedInMessageTemplate(
            template_id=template_id,
            campaign_id=campaign_id,
            name=data['name'],
            template_type=data['template_type'],
            sequence_order=data.get('sequence_order', 1),
            delay_days=data.get('delay_days', 0),
            message_content=data['message_content'],
            personalization_fields=data.get('personalization_fields', []),
            trigger_conditions=data.get('trigger_conditions'),
            target_audience_criteria=data.get('target_audience_criteria')
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'template': template.to_dict(),
            'message': 'Template created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating message template: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== ANALYTICS ENDPOINTS =====

@linkedin_bp.route('/analytics/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    try:
        current_user = get_jwt_identity()
        
        # Get user's campaigns
        campaigns = LinkedInCampaign.query.filter_by(created_by=current_user).all()
        
        # Aggregate analytics across all campaigns
        total_campaigns = len(campaigns)
        active_campaigns = len([c for c in campaigns if c.status == LinkedInCampaignStatus.ACTIVE.value])
        
        # Get overall pipeline metrics
        overall_metrics = pipeline_manager.get_pipeline_metrics()
        
        # Get recent activity
        recent_activity = pipeline_manager.get_recent_pipeline_activity(hours=24)
        
        # Get active alerts
        active_alerts = pipeline_manager.get_active_alerts()
        
        analytics = {
            'summary': {
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'total_leads': overall_metrics.total_leads,
                'qualified_leads': overall_metrics.leads_by_stage.get('qualified', 0),
                'opportunities': overall_metrics.leads_by_stage.get('opportunity', 0),
                'conversions': overall_metrics.leads_by_stage.get('converted', 0),
                'response_rate': overall_metrics.response_rate,
                'qualification_rate': overall_metrics.qualification_rate,
                'revenue_pipeline': overall_metrics.revenue_pipeline
            },
            'pipeline_breakdown': overall_metrics.leads_by_stage,
            'priority_breakdown': overall_metrics.leads_by_priority,
            'recent_activity': recent_activity[:10],  # Last 10 activities
            'active_alerts': len(active_alerts),
            'conversion_rates': overall_metrics.conversion_rates
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/analytics/performance', methods=['GET'])
@jwt_required()
def get_performance_analytics():
    """Get detailed performance analytics"""
    try:
        campaign_id = request.args.get('campaign_id')
        days = request.args.get('days', 30, type=int)
        
        # Get performance trends
        trends = pipeline_manager.get_pipeline_trends(campaign_id, days)
        
        # Get workflow analytics
        workflow_analytics = workflow_orchestrator.get_workflow_analytics(campaign_id)
        
        return jsonify({
            'success': True,
            'performance': {
                'trends': trends,
                'workflow_analytics': workflow_analytics
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== AUTOMATION RULE ENDPOINTS =====

@linkedin_bp.route('/automation-rules', methods=['GET'])
@jwt_required()
def get_automation_rules():
    """Get automation rules"""
    try:
        current_user = get_jwt_identity()
        rules = LinkedInAutomationRule.query.filter_by(created_by=current_user).all()
        
        return jsonify({
            'success': True,
            'rules': [rule.to_dict() for rule in rules]
        })
        
    except Exception as e:
        logger.error(f"Error getting automation rules: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@linkedin_bp.route('/automation-rules/process', methods=['POST'])
@jwt_required()
def process_automation_rules():
    """Process automation rules"""
    try:
        campaign_id = request.args.get('campaign_id')
        
        # Process automation rules
        results = automation_service.process_automation_rules(campaign_id)
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f"Processed {results.get('processed_rules', 0)} automation rules"
        })
        
    except Exception as e:
        logger.error(f"Error processing automation rules: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== HEALTH CHECK ENDPOINT =====

@linkedin_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for LinkedIn automation"""
    return jsonify({
        'success': True,
        'service': 'LinkedIn Sales Navigator Automation',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {
            'automation_service': bool(automation_service),
            'qualification_engine': bool(qualification_engine),
            'workflow_orchestrator': bool(workflow_orchestrator),
            'pipeline_manager': bool(pipeline_manager)
        }
    })