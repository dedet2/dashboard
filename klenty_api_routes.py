"""
Klenty SDRx Outreach Automation API Routes
Flask Blueprint for Klenty campaign management, lead nurturing, and analytics
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from typing import Dict, List, Optional, Any

from database import db
from klenty_models import (
    KlentyCampaign, KlentySequence, KlentyLead, KlentyTemplate, KlentyEmail,
    KlentyAutomationRule, KlentyAnalytics, KlentyCampaignStatus, KlentyLeadStatus
)
from klenty_automation_service import (
    KlentyAutomationService, EmailSequenceConfig, EmailTemplate, LeadImportConfig
)
from klenty_integration_workflows import KlentyIntegrationWorkflows, CampaignCoordinationConfig

# Import existing services for integration
try:
    from apollo_integration import ApolloAPIWrapper
    from perplexity_service import PerplexityAPI
    from linkedin_automation_service import LinkedInAutomationService
    from make_automation_bridges import AutomationBridgeService
except ImportError as e:
    logging.warning(f"Some integration services not available: {e}")

logger = logging.getLogger(__name__)

# Create Blueprint
klenty_bp = Blueprint('klenty', __name__, url_prefix='/api/klenty')
CORS(klenty_bp)

# Initialize services (will be properly configured in main.py)
klenty_service = None
integration_workflows = None

def initialize_klenty_services(apollo_api=None, perplexity_api=None, linkedin_service=None, automation_bridge=None):
    """Initialize Klenty services with proper dependencies"""
    global klenty_service, integration_workflows
    
    klenty_service = KlentyAutomationService(
        apollo_api=apollo_api,
        perplexity_api=perplexity_api,
        automation_bridge=automation_bridge
    )
    
    if linkedin_service:
        integration_workflows = KlentyIntegrationWorkflows(
            klenty_service=klenty_service,
            linkedin_service=linkedin_service,
            automation_bridge=automation_bridge
        )

# ===== CAMPAIGN MANAGEMENT ROUTES =====

@klenty_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """Get all Klenty campaigns with filtering options"""
    try:
        # Get query parameters
        user = request.args.get('user', 'dede@risktravel.com')
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = KlentyCampaign.query.filter_by(created_by=user)
        
        if status:
            query = query.filter_by(status=status)
        
        # Get campaigns with pagination
        campaigns = query.order_by(KlentyCampaign.created_at.desc()).offset(offset).limit(limit).all()
        
        # Get total count
        total_count = query.count()
        
        campaigns_data = [campaign.to_dict() for campaign in campaigns]
        
        return jsonify({
            'campaigns': campaigns_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error getting campaigns: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    """Create a new Klenty campaign"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'sender_email', 'sender_name', 'target_audience']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create campaign
        campaign = klenty_service.create_campaign(
            name=data['name'],
            description=data.get('description', ''),
            sender_email=data['sender_email'],
            sender_name=data['sender_name'],
            target_audience=data['target_audience'],
            created_by=data.get('created_by', 'dede@risktravel.com'),
            **data.get('additional_config', {})
        )
        
        if campaign:
            return jsonify({
                'success': True,
                'campaign': campaign.to_dict()
            }), 201
        else:
            return jsonify({'error': 'Failed to create campaign'}), 500
            
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/campaigns/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get specific campaign details"""
    try:
        campaign = KlentyCampaign.query.filter_by(campaign_id=campaign_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Get related data
        sequences = KlentySequence.query.filter_by(campaign_id=campaign_id).all()
        leads_count = KlentyLead.query.filter_by(campaign_id=campaign_id).count()
        
        campaign_data = campaign.to_dict()
        campaign_data['sequences'] = [seq.to_dict() for seq in sequences]
        campaign_data['leads_count'] = leads_count
        
        return jsonify(campaign_data)
        
    except Exception as e:
        logger.error(f"Error getting campaign {campaign_id}: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/campaigns/<campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    """Update campaign settings"""
    try:
        campaign = KlentyCampaign.query.filter_by(campaign_id=campaign_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = [
            'name', 'description', 'status', 'daily_email_limit', 'weekly_email_limit',
            'target_prospects', 'target_opens', 'target_clicks', 'target_replies',
            'sending_days', 'sending_hours_start', 'sending_hours_end',
            'linkedin_integration_enabled', 'apollo_enrichment_enabled',
            'perplexity_research_enabled', 'make_automation_enabled'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(campaign, field, data[field])
        
        campaign.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating campaign {campaign_id}: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/campaigns/<campaign_id>/start', methods=['POST'])
def start_campaign(campaign_id):
    """Start a campaign"""
    try:
        campaign = KlentyCampaign.query.filter_by(campaign_id=campaign_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        if campaign.status != KlentyCampaignStatus.DRAFT.value:
            return jsonify({'error': 'Campaign is not in draft status'}), 400
        
        campaign.status = KlentyCampaignStatus.ACTIVE.value
        campaign.started_at = datetime.utcnow()
        campaign.last_activity = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Campaign started successfully',
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error starting campaign {campaign_id}: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/campaigns/<campaign_id>/pause', methods=['POST'])
def pause_campaign(campaign_id):
    """Pause a campaign"""
    try:
        campaign = KlentyCampaign.query.filter_by(campaign_id=campaign_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        campaign.status = KlentyCampaignStatus.PAUSED.value
        campaign.last_activity = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Campaign paused successfully',
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error pausing campaign {campaign_id}: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===== SEQUENCE MANAGEMENT ROUTES =====

@klenty_bp.route('/campaigns/<campaign_id>/sequences', methods=['GET'])
def get_campaign_sequences(campaign_id):
    """Get all sequences for a campaign"""
    try:
        sequences = KlentySequence.query.filter_by(campaign_id=campaign_id).all()
        
        sequences_data = []
        for sequence in sequences:
            seq_data = sequence.to_dict()
            # Get templates for this sequence
            templates = KlentyTemplate.query.filter_by(sequence_id=sequence.sequence_id).order_by(KlentyTemplate.step_number).all()
            seq_data['templates'] = [template.to_dict() for template in templates]
            sequences_data.append(seq_data)
        
        return jsonify({
            'sequences': sequences_data
        })
        
    except Exception as e:
        logger.error(f"Error getting sequences for campaign {campaign_id}: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/campaigns/<campaign_id>/sequences', methods=['POST'])
def create_sequence(campaign_id):
    """Create a new email sequence"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'templates']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create sequence configuration
        config = EmailSequenceConfig(
            sequence_name=data['name'],
            total_steps=len(data['templates']),
            delay_between_emails=data.get('delay_between_emails', 3),
            stop_on_reply=data.get('stop_on_reply', True),
            stop_on_click=data.get('stop_on_click', False),
            stop_on_open=data.get('stop_on_open', False),
            stop_on_unsubscribe=data.get('stop_on_unsubscribe', True)
        )
        
        # Create email templates
        templates = []
        for i, template_data in enumerate(data['templates'], 1):
            template = EmailTemplate(
                subject_line=template_data['subject_line'],
                email_body=template_data['email_body'],
                step_number=i,
                delay_days=template_data.get('delay_days', 0),
                personalization_fields=template_data.get('personalization_fields', []),
                html_body=template_data.get('html_body')
            )
            templates.append(template)
        
        # Create sequence
        sequence = klenty_service.create_sequence(campaign_id, config, templates)
        
        if sequence:
            return jsonify({
                'success': True,
                'sequence': sequence.to_dict()
            }), 201
        else:
            return jsonify({'error': 'Failed to create sequence'}), 500
            
    except Exception as e:
        logger.error(f"Error creating sequence: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/sequences/<sequence_id>', methods=['GET'])
def get_sequence(sequence_id):
    """Get specific sequence details"""
    try:
        sequence = KlentySequence.query.filter_by(sequence_id=sequence_id).first()
        
        if not sequence:
            return jsonify({'error': 'Sequence not found'}), 404
        
        # Get templates
        templates = KlentyTemplate.query.filter_by(sequence_id=sequence_id).order_by(KlentyTemplate.step_number).all()
        
        sequence_data = sequence.to_dict()
        sequence_data['templates'] = [template.to_dict() for template in templates]
        
        return jsonify(sequence_data)
        
    except Exception as e:
        logger.error(f"Error getting sequence {sequence_id}: {e}")
        return jsonify({'error': str(e)}), 500

# ===== LEAD MANAGEMENT ROUTES =====

@klenty_bp.route('/campaigns/<campaign_id>/leads', methods=['GET'])
def get_campaign_leads(campaign_id):
    """Get leads for a campaign with filtering"""
    try:
        # Get query parameters
        status = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = KlentyLead.query.filter_by(campaign_id=campaign_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if search:
            search_filter = (
                KlentyLead.full_name.ilike(f'%{search}%') |
                KlentyLead.email.ilike(f'%{search}%') |
                KlentyLead.company.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Get leads with pagination
        leads = query.order_by(KlentyLead.imported_at.desc()).offset(offset).limit(limit).all()
        
        # Get total count
        total_count = query.count()
        
        leads_data = [lead.to_dict() for lead in leads]
        
        return jsonify({
            'leads': leads_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error getting leads for campaign {campaign_id}: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/campaigns/<campaign_id>/leads', methods=['POST'])
def import_leads(campaign_id):
    """Import leads into a campaign"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('leads'):
            return jsonify({'error': 'Missing leads data'}), 400
        
        # Create import configuration
        config = LeadImportConfig(
            source=data.get('source', 'manual_import'),
            auto_enrich=data.get('auto_enrich', True),
            auto_score=data.get('auto_score', True),
            auto_assign_sequence=data.get('auto_assign_sequence', False),
            default_sequence_id=data.get('default_sequence_id')
        )
        
        # Import leads
        results = klenty_service.import_leads(campaign_id, data['leads'], config)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error importing leads: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/leads/<lead_id>', methods=['GET'])
def get_lead(lead_id):
    """Get specific lead details"""
    try:
        lead = KlentyLead.query.filter_by(lead_id=lead_id).first()
        
        if not lead:
            return jsonify({'error': 'Lead not found'}), 404
        
        # Get lead emails
        emails = KlentyEmail.query.filter_by(lead_id=lead_id).order_by(KlentyEmail.sent_at.desc()).all()
        
        lead_data = lead.to_dict()
        lead_data['emails'] = [email.to_dict() for email in emails]
        
        return jsonify(lead_data)
        
    except Exception as e:
        logger.error(f"Error getting lead {lead_id}: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/leads/<lead_id>/assign-sequence', methods=['POST'])
def assign_lead_to_sequence(lead_id):
    """Assign a lead to an email sequence"""
    try:
        data = request.get_json()
        
        if not data.get('sequence_id'):
            return jsonify({'error': 'Missing sequence_id'}), 400
        
        success = klenty_service.assign_lead_to_sequence(lead_id, data['sequence_id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Lead assigned to sequence successfully'
            })
        else:
            return jsonify({'error': 'Failed to assign lead to sequence'}), 500
            
    except Exception as e:
        logger.error(f"Error assigning lead to sequence: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/leads/<lead_id>/enrich', methods=['POST'])
def enrich_lead(lead_id):
    """Enrich lead with Apollo.io data"""
    try:
        success = klenty_service.enrich_lead_with_apollo(lead_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Lead enriched successfully'
            })
        else:
            return jsonify({'error': 'Failed to enrich lead'}), 500
            
    except Exception as e:
        logger.error(f"Error enriching lead {lead_id}: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/leads/<lead_id>/research', methods=['POST'])
def research_lead(lead_id):
    """Research lead with Perplexity AI"""
    try:
        success = klenty_service.research_lead_with_perplexity(lead_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Lead researched successfully'
            })
        else:
            return jsonify({'error': 'Failed to research lead'}), 500
            
    except Exception as e:
        logger.error(f"Error researching lead {lead_id}: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/leads/<lead_id>/qualify', methods=['POST'])
def qualify_lead(lead_id):
    """Qualify a lead using AI scoring"""
    try:
        results = klenty_service.qualify_lead(lead_id)
        
        if 'error' in results:
            return jsonify(results), 500
        
        return jsonify({
            'success': True,
            'qualification': results
        })
        
    except Exception as e:
        logger.error(f"Error qualifying lead {lead_id}: {e}")
        return jsonify({'error': str(e)}), 500

# ===== EMAIL MANAGEMENT ROUTES =====

@klenty_bp.route('/emails/send-scheduled', methods=['POST'])
def send_scheduled_emails():
    """Send all scheduled emails that are due"""
    try:
        data = request.get_json()
        limit = data.get('limit', 100) if data else 100
        
        results = klenty_service.send_scheduled_emails(limit)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error sending scheduled emails: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/emails/webhooks', methods=['POST'])
def process_email_webhook():
    """Process email engagement webhooks"""
    try:
        webhook_data = request.get_json()
        
        success = klenty_service.process_email_webhooks(webhook_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Webhook processed successfully'
            })
        else:
            return jsonify({'error': 'Failed to process webhook'}), 500
            
    except Exception as e:
        logger.error(f"Error processing email webhook: {e}")
        return jsonify({'error': str(e)}), 500

# ===== ANALYTICS ROUTES =====

@klenty_bp.route('/campaigns/<campaign_id>/analytics', methods=['GET'])
def get_campaign_analytics(campaign_id):
    """Get comprehensive analytics for a campaign"""
    try:
        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        date_range = None
        if start_date and end_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                date_range = (start_dt, end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        analytics = klenty_service.get_campaign_analytics(campaign_id, date_range)
        
        if 'error' in analytics:
            return jsonify(analytics), 500
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting campaign analytics: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get dashboard analytics for all campaigns"""
    try:
        user = request.args.get('user', 'dede@risktravel.com')
        
        # Get user's campaigns
        campaigns = KlentyCampaign.query.filter_by(created_by=user).all()
        
        # Aggregate analytics
        total_campaigns = len(campaigns)
        active_campaigns = len([c for c in campaigns if c.status == KlentyCampaignStatus.ACTIVE.value])
        
        # Get aggregate metrics
        total_leads = KlentyLead.query.join(KlentyCampaign).filter(KlentyCampaign.created_by == user).count()
        total_emails_sent = sum([c.emails_sent for c in campaigns])
        total_emails_opened = sum([c.emails_opened for c in campaigns])
        total_replies = sum([c.emails_replied for c in campaigns])
        
        # Calculate rates
        open_rate = (total_emails_opened / total_emails_sent * 100) if total_emails_sent > 0 else 0
        reply_rate = (total_replies / total_emails_sent * 100) if total_emails_sent > 0 else 0
        
        # Get recent activity
        recent_leads = KlentyLead.query.join(KlentyCampaign).filter(
            KlentyCampaign.created_by == user,
            KlentyLead.imported_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        recent_emails = KlentyEmail.query.join(KlentyLead).join(KlentyCampaign).filter(
            KlentyCampaign.created_by == user,
            KlentyEmail.sent_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        return jsonify({
            'summary': {
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'total_leads': total_leads,
                'total_emails_sent': total_emails_sent,
                'total_emails_opened': total_emails_opened,
                'total_replies': total_replies,
                'open_rate': round(open_rate, 2),
                'reply_rate': round(reply_rate, 2)
            },
            'recent_activity': {
                'new_leads_this_week': recent_leads,
                'emails_sent_this_week': recent_emails
            },
            'campaigns': [campaign.to_dict() for campaign in campaigns[:10]]  # Recent campaigns
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        return jsonify({'error': str(e)}), 500

# ===== INTEGRATION ROUTES =====

@klenty_bp.route('/integration/coordinated-campaigns', methods=['POST'])
def create_coordinated_campaign():
    """Create coordinated campaign across LinkedIn and Klenty"""
    try:
        if not integration_workflows:
            return jsonify({'error': 'Integration workflows not available'}), 503
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['campaign_name', 'target_audience']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create coordination configuration
        config = CampaignCoordinationConfig(
            linkedin_campaign_id=data.get('linkedin_campaign_id'),
            klenty_campaign_id=data.get('klenty_campaign_id'),
            coordination_strategy=data.get('coordination_strategy', 'sequential'),
            delay_between_platforms=data.get('delay_between_platforms', 24),
            shared_targeting_criteria=data['target_audience'],
            lead_qualification_threshold=data.get('lead_qualification_threshold', 70.0),
            auto_escalate_to_executive=data.get('auto_escalate_to_executive', True)
        )
        
        results = integration_workflows.create_coordinated_campaign(
            config=config,
            campaign_name=data['campaign_name'],
            target_audience=data['target_audience'],
            created_by=data.get('created_by', 'dede@risktravel.com')
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error creating coordinated campaign: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/integration/sync-linkedin-leads', methods=['POST'])
def sync_linkedin_leads():
    """Sync qualified LinkedIn leads to Klenty"""
    try:
        if not integration_workflows:
            return jsonify({'error': 'Integration workflows not available'}), 503
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['linkedin_campaign_id', 'klenty_campaign_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        results = integration_workflows.sync_linkedin_leads_to_klenty(
            linkedin_campaign_id=data['linkedin_campaign_id'],
            klenty_campaign_id=data['klenty_campaign_id'],
            qualification_threshold=data.get('qualification_threshold', 70.0)
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error syncing LinkedIn leads: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/integration/sync-engagement', methods=['POST'])
def sync_email_engagement():
    """Sync Klenty email engagement back to LinkedIn"""
    try:
        if not integration_workflows:
            return jsonify({'error': 'Integration workflows not available'}), 503
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['klenty_campaign_id', 'linkedin_campaign_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        results = integration_workflows.sync_klenty_engagement_to_linkedin(
            klenty_campaign_id=data['klenty_campaign_id'],
            linkedin_campaign_id=data['linkedin_campaign_id']
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error syncing email engagement: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/integration/escalate-opportunities', methods=['POST'])
def escalate_to_opportunities():
    """Escalate qualified leads to executive opportunities"""
    try:
        if not integration_workflows:
            return jsonify({'error': 'Integration workflows not available'}), 503
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('campaign_ids'):
            return jsonify({'error': 'Missing campaign_ids'}), 400
        
        results = integration_workflows.escalate_leads_to_executive_opportunities(
            campaign_ids=data['campaign_ids'],
            qualification_threshold=data.get('qualification_threshold', 85.0)
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error escalating opportunities: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/integration/sequential-outreach', methods=['POST'])
def coordinate_sequential_outreach():
    """Coordinate sequential outreach: LinkedIn first, then email"""
    try:
        if not integration_workflows:
            return jsonify({'error': 'Integration workflows not available'}), 503
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['linkedin_campaign_id', 'klenty_campaign_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        results = integration_workflows.coordinate_sequential_outreach(
            linkedin_campaign_id=data['linkedin_campaign_id'],
            klenty_campaign_id=data['klenty_campaign_id'],
            delay_hours=data.get('delay_hours', 72)
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error coordinating sequential outreach: {e}")
        return jsonify({'error': str(e)}), 500

@klenty_bp.route('/integration/cross-platform-analytics', methods=['GET'])
def get_cross_platform_analytics():
    """Get cross-platform analytics for campaigns"""
    try:
        if not integration_workflows:
            return jsonify({'error': 'Integration workflows not available'}), 503
        
        campaign_ids = request.args.getlist('campaign_ids')
        
        if not campaign_ids:
            return jsonify({'error': 'Missing campaign_ids parameter'}), 400
        
        analytics = integration_workflows.analyze_cross_platform_performance(campaign_ids)
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting cross-platform analytics: {e}")
        return jsonify({'error': str(e)}), 500

# ===== AUTOMATION ROUTES =====

@klenty_bp.route('/automation/process-responses', methods=['POST'])
def process_cross_platform_responses():
    """Process responses across platforms and coordinate actions"""
    try:
        if not integration_workflows:
            return jsonify({'error': 'Integration workflows not available'}), 503
        
        results = integration_workflows.process_cross_platform_responses()
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error processing cross-platform responses: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@klenty_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@klenty_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500