"""
Klenty Integration Workflows
Automation workflows that integrate Klenty with LinkedIn Sales Navigator and executive opportunities
for coordinated outreach campaigns across multiple channels
"""

import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from database import db, ExecutiveOpportunity
from klenty_models import (
    KlentyCampaign, KlentySequence, KlentyLead, KlentyTemplate, KlentyEmail,
    KlentyLeadStatus, KlentyEmailStatus
)
from linkedin_models import (
    LinkedInCampaign, LinkedInLead, LinkedInMessage, LinkedInLeadStatus
)
from klenty_automation_service import KlentyAutomationService
from linkedin_automation_service import LinkedInAutomationService
from make_automation_bridges import AutomationBridgeService

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """Types of integrations between platforms"""
    LINKEDIN_TO_KLENTY = "linkedin_to_klenty"
    KLENTY_TO_LINKEDIN = "klenty_to_linkedin"
    BIDIRECTIONAL = "bidirectional"
    EXECUTIVE_OPPORTUNITY = "executive_opportunity"

class SyncDirection(Enum):
    """Direction of data synchronization"""
    PULL = "pull"  # Pull data from source to target
    PUSH = "push"  # Push data from source to target
    SYNC = "sync"  # Bidirectional synchronization

@dataclass
class IntegrationRule:
    """Rule for integrating data between platforms"""
    rule_id: str
    source_platform: str
    target_platform: str
    sync_direction: SyncDirection
    trigger_conditions: Dict[str, Any]
    field_mappings: Dict[str, str]
    transformation_rules: List[Dict[str, Any]]
    active: bool = True
    priority: int = 1

@dataclass
class CampaignCoordinationConfig:
    """Configuration for coordinating campaigns across platforms"""
    linkedin_campaign_id: Optional[str] = None
    klenty_campaign_id: Optional[str] = None
    coordination_strategy: str = "sequential"  # sequential, parallel, conditional
    delay_between_platforms: int = 24  # Hours
    shared_targeting_criteria: Dict[str, Any] = None
    lead_qualification_threshold: float = 70.0
    auto_escalate_to_executive: bool = True

class KlentyIntegrationWorkflows:
    """
    Main class for Klenty integration workflows
    Coordinates outreach campaigns across LinkedIn, Klenty, and executive opportunities
    """
    
    def __init__(self, klenty_service: KlentyAutomationService, 
                 linkedin_service: LinkedInAutomationService,
                 automation_bridge: Optional[AutomationBridgeService] = None):
        self.klenty_service = klenty_service
        self.linkedin_service = linkedin_service
        self.automation_bridge = automation_bridge
        
        # Integration rules storage
        self.integration_rules: Dict[str, IntegrationRule] = {}
        
        # Default field mappings between platforms
        self.default_field_mappings = self._initialize_default_mappings()
        
        # Initialize default integration rules
        self._initialize_default_integration_rules()
    
    def create_coordinated_campaign(self, config: CampaignCoordinationConfig, 
                                   campaign_name: str, target_audience: Dict[str, Any],
                                   created_by: str) -> Dict[str, Any]:
        """
        Create coordinated campaign across LinkedIn and Klenty platforms
        
        Args:
            config: Campaign coordination configuration
            campaign_name: Name for the coordinated campaign
            target_audience: Shared targeting criteria
            created_by: User creating the campaign
            
        Returns:
            Dictionary with created campaign details
        """
        try:
            results = {
                'coordination_id': f"coord_{str(uuid.uuid4())[:8]}_{int(time.time())}",
                'linkedin_campaign': None,
                'klenty_campaign': None,
                'integration_rules': [],
                'errors': []
            }
            
            # Create LinkedIn campaign if specified
            if not config.linkedin_campaign_id:
                linkedin_campaign = self.linkedin_service.create_campaign(
                    name=f"{campaign_name} - LinkedIn",
                    description=f"LinkedIn component of coordinated campaign: {campaign_name}",
                    target_audience=target_audience,
                    created_by=created_by,
                    make_automation_enabled=True
                )
                if linkedin_campaign:
                    results['linkedin_campaign'] = linkedin_campaign.to_dict()
                    config.linkedin_campaign_id = linkedin_campaign.campaign_id
                else:
                    results['errors'].append("Failed to create LinkedIn campaign")
            
            # Create Klenty campaign if specified
            if not config.klenty_campaign_id:
                # Extract sender email from target audience or use default
                sender_email = target_audience.get('sender_email', f"{created_by}")
                sender_name = target_audience.get('sender_name', "Dr. Dede")
                
                klenty_campaign = self.klenty_service.create_campaign(
                    name=f"{campaign_name} - Email",
                    description=f"Email component of coordinated campaign: {campaign_name}",
                    sender_email=sender_email,
                    sender_name=sender_name,
                    target_audience=target_audience,
                    created_by=created_by,
                    make_automation_enabled=True
                )
                if klenty_campaign:
                    results['klenty_campaign'] = klenty_campaign.to_dict()
                    config.klenty_campaign_id = klenty_campaign.campaign_id
                else:
                    results['errors'].append("Failed to create Klenty campaign")
            
            # Create integration rules for campaign coordination
            if config.linkedin_campaign_id and config.klenty_campaign_id:
                integration_rules = self._create_campaign_integration_rules(config)
                results['integration_rules'] = [rule.rule_id for rule in integration_rules]
            
            logger.info(f"Created coordinated campaign {results['coordination_id']}")
            return results
            
        except Exception as e:
            logger.error(f"Error creating coordinated campaign: {e}")
            return {'error': str(e)}
    
    def sync_linkedin_leads_to_klenty(self, linkedin_campaign_id: str, 
                                     klenty_campaign_id: str,
                                     qualification_threshold: float = 70.0) -> Dict[str, Any]:
        """
        Sync qualified LinkedIn leads to Klenty for email follow-up
        
        Args:
            linkedin_campaign_id: Source LinkedIn campaign
            klenty_campaign_id: Target Klenty campaign
            qualification_threshold: Minimum lead score for sync
            
        Returns:
            Dictionary with sync results
        """
        try:
            # Get qualified LinkedIn leads
            linkedin_leads = LinkedInLead.query.filter(
                LinkedInLead.campaign_id == linkedin_campaign_id,
                LinkedInLead.lead_score >= qualification_threshold,
                LinkedInLead.email.isnot(None),  # Must have email for Klenty
                LinkedInLead.status.in_([
                    LinkedInLeadStatus.CONNECTION_ACCEPTED.value,
                    LinkedInLeadStatus.MESSAGED.value,
                    LinkedInLeadStatus.REPLIED.value
                ])
            ).all()
            
            results = {
                'leads_processed': 0,
                'leads_synced': 0,
                'leads_updated': 0,
                'leads_skipped': 0,
                'errors': []
            }
            
            for linkedin_lead in linkedin_leads:
                try:
                    results['leads_processed'] += 1
                    
                    # Check if lead already exists in Klenty
                    existing_klenty_lead = KlentyLead.query.filter_by(
                        email=linkedin_lead.email,
                        campaign_id=klenty_campaign_id
                    ).first()
                    
                    if existing_klenty_lead:
                        # Update existing lead with LinkedIn data
                        self._update_klenty_lead_from_linkedin(existing_klenty_lead, linkedin_lead)
                        results['leads_updated'] += 1
                    else:
                        # Create new Klenty lead
                        klenty_lead_data = self._convert_linkedin_to_klenty_lead(linkedin_lead)
                        klenty_lead_data['campaign_id'] = klenty_campaign_id
                        
                        # Import lead into Klenty
                        import_results = self.klenty_service.import_leads(
                            klenty_campaign_id,
                            [klenty_lead_data],
                            config=self.klenty_service.LeadImportConfig(
                                source='linkedin_sync',
                                auto_enrich=True,
                                auto_score=True,
                                auto_assign_sequence=True
                            )
                        )
                        
                        if import_results.get('imported', 0) > 0:
                            results['leads_synced'] += 1
                        else:
                            results['leads_skipped'] += 1
                            results['errors'].extend(import_results.get('errors', []))
                    
                except Exception as e:
                    error_msg = f"Error syncing LinkedIn lead {linkedin_lead.lead_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['leads_skipped'] += 1
            
            logger.info(f"Synced {results['leads_synced']} LinkedIn leads to Klenty campaign {klenty_campaign_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error syncing LinkedIn leads to Klenty: {e}")
            return {'error': str(e)}
    
    def sync_klenty_engagement_to_linkedin(self, klenty_campaign_id: str,
                                          linkedin_campaign_id: str) -> Dict[str, Any]:
        """
        Sync Klenty email engagement data back to LinkedIn leads
        
        Args:
            klenty_campaign_id: Source Klenty campaign
            linkedin_campaign_id: Target LinkedIn campaign
            
        Returns:
            Dictionary with sync results
        """
        try:
            # Get Klenty leads with email engagement
            klenty_leads = KlentyLead.query.filter(
                KlentyLead.campaign_id == klenty_campaign_id,
                KlentyLead.linkedin_url.isnot(None)  # Must have LinkedIn profile for matching
            ).all()
            
            results = {
                'leads_processed': 0,
                'leads_updated': 0,
                'leads_not_found': 0,
                'errors': []
            }
            
            for klenty_lead in klenty_leads:
                try:
                    results['leads_processed'] += 1
                    
                    # Find matching LinkedIn lead
                    linkedin_lead = LinkedInLead.query.filter(
                        LinkedInLead.campaign_id == linkedin_campaign_id,
                        LinkedInLead.email == klenty_lead.email
                    ).first()
                    
                    if linkedin_lead:
                        # Update LinkedIn lead with Klenty engagement data
                        self._update_linkedin_lead_from_klenty(linkedin_lead, klenty_lead)
                        results['leads_updated'] += 1
                    else:
                        results['leads_not_found'] += 1
                    
                except Exception as e:
                    error_msg = f"Error syncing Klenty lead {klenty_lead.lead_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            db.session.commit()
            
            logger.info(f"Synced engagement data for {results['leads_updated']} leads from Klenty to LinkedIn")
            return results
            
        except Exception as e:
            logger.error(f"Error syncing Klenty engagement to LinkedIn: {e}")
            db.session.rollback()
            return {'error': str(e)}
    
    def escalate_leads_to_executive_opportunities(self, campaign_ids: List[str],
                                                qualification_threshold: float = 85.0) -> Dict[str, Any]:
        """
        Escalate highly qualified leads from campaigns to executive opportunities
        
        Args:
            campaign_ids: List of campaign IDs to process (LinkedIn and/or Klenty)
            qualification_threshold: Minimum score for executive opportunity escalation
            
        Returns:
            Dictionary with escalation results
        """
        try:
            results = {
                'leads_processed': 0,
                'opportunities_created': 0,
                'opportunities_updated': 0,
                'errors': []
            }
            
            # Process LinkedIn leads
            linkedin_leads = LinkedInLead.query.filter(
                LinkedInLead.campaign_id.in_(campaign_ids),
                LinkedInLead.lead_score >= qualification_threshold,
                LinkedInLead.executive_opportunity_id.is_(None),  # Not already escalated
                LinkedInLead.opportunity_type.isnot(None)  # Has opportunity type defined
            ).all()
            
            for lead in linkedin_leads:
                try:
                    results['leads_processed'] += 1
                    opportunity = self._create_executive_opportunity_from_linkedin_lead(lead)
                    if opportunity:
                        lead.executive_opportunity_id = opportunity.id
                        lead.status = LinkedInLeadStatus.CONVERTED.value
                        results['opportunities_created'] += 1
                except Exception as e:
                    results['errors'].append(f"Error escalating LinkedIn lead {lead.lead_id}: {e}")
            
            # Process Klenty leads
            klenty_leads = KlentyLead.query.filter(
                KlentyLead.campaign_id.in_(campaign_ids),
                KlentyLead.lead_score >= qualification_threshold,
                KlentyLead.executive_opportunity_id.is_(None),  # Not already escalated
                KlentyLead.opportunity_type.isnot(None)  # Has opportunity type defined
            ).all()
            
            for lead in klenty_leads:
                try:
                    results['leads_processed'] += 1
                    opportunity = self._create_executive_opportunity_from_klenty_lead(lead)
                    if opportunity:
                        lead.executive_opportunity_id = opportunity.id
                        lead.status = KlentyLeadStatus.CONVERTED.value
                        results['opportunities_created'] += 1
                except Exception as e:
                    results['errors'].append(f"Error escalating Klenty lead {lead.lead_id}: {e}")
            
            db.session.commit()
            
            logger.info(f"Created {results['opportunities_created']} executive opportunities from {results['leads_processed']} qualified leads")
            return results
            
        except Exception as e:
            logger.error(f"Error escalating leads to executive opportunities: {e}")
            db.session.rollback()
            return {'error': str(e)}
    
    def coordinate_sequential_outreach(self, linkedin_campaign_id: str, 
                                     klenty_campaign_id: str,
                                     delay_hours: int = 72) -> Dict[str, Any]:
        """
        Coordinate sequential outreach: LinkedIn first, then email follow-up
        
        Args:
            linkedin_campaign_id: LinkedIn campaign for initial outreach
            klenty_campaign_id: Klenty campaign for email follow-up
            delay_hours: Hours to wait after LinkedIn activity before email
            
        Returns:
            Dictionary with coordination results
        """
        try:
            # Get LinkedIn leads that have had connections accepted but no recent activity
            cutoff_time = datetime.utcnow() - timedelta(hours=delay_hours)
            
            linkedin_leads = LinkedInLead.query.filter(
                LinkedInLead.campaign_id == linkedin_campaign_id,
                LinkedInLead.status == LinkedInLeadStatus.CONNECTION_ACCEPTED.value,
                LinkedInLead.connection_accepted_at <= cutoff_time,
                LinkedInLead.last_activity_at <= cutoff_time,
                LinkedInLead.email.isnot(None)
            ).all()
            
            results = {
                'leads_processed': 0,
                'email_sequences_started': 0,
                'errors': []
            }
            
            for linkedin_lead in linkedin_leads:
                try:
                    results['leads_processed'] += 1
                    
                    # Check if already in Klenty campaign
                    existing_klenty_lead = KlentyLead.query.filter_by(
                        email=linkedin_lead.email,
                        campaign_id=klenty_campaign_id
                    ).first()
                    
                    if not existing_klenty_lead:
                        # Create Klenty lead and start email sequence
                        klenty_lead_data = self._convert_linkedin_to_klenty_lead(linkedin_lead)
                        klenty_lead_data['campaign_id'] = klenty_campaign_id
                        klenty_lead_data['source'] = 'linkedin_sequential_outreach'
                        
                        # Import and assign to sequence
                        import_results = self.klenty_service.import_leads(
                            klenty_campaign_id,
                            [klenty_lead_data],
                            config=self.klenty_service.LeadImportConfig(
                                source='linkedin_sequential',
                                auto_enrich=False,  # Already enriched from LinkedIn
                                auto_score=True,
                                auto_assign_sequence=True
                            )
                        )
                        
                        if import_results.get('imported', 0) > 0:
                            results['email_sequences_started'] += 1
                        
                        # Update LinkedIn lead to track email follow-up
                        linkedin_lead.conversation_context = linkedin_lead.conversation_context or {}
                        linkedin_lead.conversation_context['email_followup_started'] = datetime.utcnow().isoformat()
                        linkedin_lead.conversation_context['klenty_campaign_id'] = klenty_campaign_id
                    
                except Exception as e:
                    error_msg = f"Error coordinating outreach for LinkedIn lead {linkedin_lead.lead_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            db.session.commit()
            
            logger.info(f"Started {results['email_sequences_started']} email sequences for LinkedIn leads")
            return results
            
        except Exception as e:
            logger.error(f"Error coordinating sequential outreach: {e}")
            db.session.rollback()
            return {'error': str(e)}
    
    def process_cross_platform_responses(self) -> Dict[str, Any]:
        """
        Process responses across platforms and coordinate next actions
        
        Returns:
            Dictionary with processing results
        """
        try:
            results = {
                'linkedin_replies_processed': 0,
                'email_replies_processed': 0,
                'sequences_stopped': 0,
                'opportunities_escalated': 0,
                'errors': []
            }
            
            # Process LinkedIn replies that should stop email sequences
            linkedin_replies = LinkedInLead.query.filter(
                LinkedInLead.status == LinkedInLeadStatus.REPLIED.value,
                LinkedInLead.last_response_at >= datetime.utcnow() - timedelta(hours=24)  # Recent replies
            ).all()
            
            for linkedin_lead in linkedin_replies:
                try:
                    results['linkedin_replies_processed'] += 1
                    
                    # Find corresponding Klenty lead
                    klenty_lead = KlentyLead.query.filter_by(email=linkedin_lead.email).first()
                    if klenty_lead and klenty_lead.sequence_status == 'active':
                        # Stop email sequence
                        klenty_lead.sequence_status = 'stopped'
                        klenty_lead.next_email_scheduled_at = None
                        klenty_lead.notes = (klenty_lead.notes or '') + f"\nEmail sequence stopped due to LinkedIn reply on {datetime.utcnow()}"
                        results['sequences_stopped'] += 1
                    
                    # Check for opportunity escalation
                    if linkedin_lead.lead_score >= 80 and not linkedin_lead.executive_opportunity_id:
                        opportunity = self._create_executive_opportunity_from_linkedin_lead(linkedin_lead)
                        if opportunity:
                            linkedin_lead.executive_opportunity_id = opportunity.id
                            results['opportunities_escalated'] += 1
                    
                except Exception as e:
                    results['errors'].append(f"Error processing LinkedIn reply {linkedin_lead.lead_id}: {e}")
            
            # Process email replies that should trigger LinkedIn actions
            klenty_replies = KlentyLead.query.filter(
                KlentyLead.status == KlentyLeadStatus.EMAIL_REPLIED.value,
                KlentyLead.last_reply_at >= datetime.utcnow() - timedelta(hours=24)  # Recent replies
            ).all()
            
            for klenty_lead in klenty_replies:
                try:
                    results['email_replies_processed'] += 1
                    
                    # Find corresponding LinkedIn lead
                    linkedin_lead = LinkedInLead.query.filter_by(email=klenty_lead.email).first()
                    if linkedin_lead:
                        # Update LinkedIn lead with email engagement data
                        linkedin_lead.conversation_context = linkedin_lead.conversation_context or {}
                        linkedin_lead.conversation_context['email_reply_received'] = klenty_lead.last_reply_at.isoformat()
                        linkedin_lead.conversation_context['email_engagement_score'] = klenty_lead.engagement_score
                        
                        # Boost LinkedIn lead score
                        linkedin_lead.lead_score = min(linkedin_lead.lead_score + 20, 100)
                    
                    # Check for opportunity escalation
                    if klenty_lead.lead_score >= 80 and not klenty_lead.executive_opportunity_id:
                        opportunity = self._create_executive_opportunity_from_klenty_lead(klenty_lead)
                        if opportunity:
                            klenty_lead.executive_opportunity_id = opportunity.id
                            results['opportunities_escalated'] += 1
                    
                except Exception as e:
                    results['errors'].append(f"Error processing Klenty reply {klenty_lead.lead_id}: {e}")
            
            db.session.commit()
            
            logger.info(f"Processed cross-platform responses: {results['linkedin_replies_processed']} LinkedIn, {results['email_replies_processed']} email")
            return results
            
        except Exception as e:
            logger.error(f"Error processing cross-platform responses: {e}")
            db.session.rollback()
            return {'error': str(e)}
    
    def analyze_cross_platform_performance(self, campaign_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze performance across LinkedIn and email campaigns
        
        Args:
            campaign_ids: List of campaign IDs to analyze
            
        Returns:
            Dictionary with cross-platform analytics
        """
        try:
            analytics = {
                'summary': {
                    'total_leads': 0,
                    'linkedin_only': 0,
                    'email_only': 0,
                    'cross_platform': 0,
                    'converted_leads': 0,
                    'executive_opportunities': 0
                },
                'platform_performance': {
                    'linkedin': {
                        'connections_sent': 0,
                        'connections_accepted': 0,
                        'messages_sent': 0,
                        'replies_received': 0,
                        'acceptance_rate': 0.0,
                        'response_rate': 0.0
                    },
                    'email': {
                        'emails_sent': 0,
                        'emails_opened': 0,
                        'emails_clicked': 0,
                        'replies_received': 0,
                        'open_rate': 0.0,
                        'click_rate': 0.0,
                        'reply_rate': 0.0
                    }
                },
                'cross_platform_metrics': {
                    'linkedin_to_email_conversion': 0.0,
                    'email_reply_after_linkedin': 0,
                    'linkedin_reply_after_email': 0,
                    'average_touchpoints_to_conversion': 0.0
                },
                'conversion_funnel': {
                    'discovery': 0,
                    'initial_contact': 0,
                    'engagement': 0,
                    'qualified': 0,
                    'converted': 0
                }
            }
            
            # Get all leads from specified campaigns
            all_email_addresses = set()
            
            # LinkedIn leads
            linkedin_leads = LinkedInLead.query.filter(
                LinkedInLead.campaign_id.in_(campaign_ids)
            ).all()
            
            # Klenty leads
            klenty_leads = KlentyLead.query.filter(
                KlentyLead.campaign_id.in_(campaign_ids)
            ).all()
            
            # Build lead mapping
            lead_mapping = {}
            for lead in linkedin_leads:
                if lead.email:
                    all_email_addresses.add(lead.email)
                    if lead.email not in lead_mapping:
                        lead_mapping[lead.email] = {'linkedin': [], 'klenty': []}
                    lead_mapping[lead.email]['linkedin'].append(lead)
            
            for lead in klenty_leads:
                all_email_addresses.add(lead.email)
                if lead.email not in lead_mapping:
                    lead_mapping[lead.email] = {'linkedin': [], 'klenty': []}
                lead_mapping[lead.email]['klenty'].append(lead)
            
            analytics['summary']['total_leads'] = len(all_email_addresses)
            
            # Analyze each lead
            for email, platforms in lead_mapping.items():
                has_linkedin = len(platforms['linkedin']) > 0
                has_klenty = len(platforms['klenty']) > 0
                
                if has_linkedin and has_klenty:
                    analytics['summary']['cross_platform'] += 1
                elif has_linkedin:
                    analytics['summary']['linkedin_only'] += 1
                elif has_klenty:
                    analytics['summary']['email_only'] += 1
                
                # Check for conversions
                converted = False
                for linkedin_lead in platforms['linkedin']:
                    if linkedin_lead.status == LinkedInLeadStatus.CONVERTED.value:
                        converted = True
                        break
                
                if not converted:
                    for klenty_lead in platforms['klenty']:
                        if klenty_lead.status == KlentyLeadStatus.CONVERTED.value:
                            converted = True
                            break
                
                if converted:
                    analytics['summary']['converted_leads'] += 1
                
                # Check for executive opportunities
                has_opportunity = False
                for linkedin_lead in platforms['linkedin']:
                    if linkedin_lead.executive_opportunity_id:
                        has_opportunity = True
                        break
                
                if not has_opportunity:
                    for klenty_lead in platforms['klenty']:
                        if klenty_lead.executive_opportunity_id:
                            has_opportunity = True
                            break
                
                if has_opportunity:
                    analytics['summary']['executive_opportunities'] += 1
            
            # Calculate platform-specific metrics
            self._calculate_platform_metrics(analytics, linkedin_leads, klenty_leads)
            
            # Calculate cross-platform metrics
            self._calculate_cross_platform_metrics(analytics, lead_mapping)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error analyzing cross-platform performance: {e}")
            return {'error': str(e)}
    
    # === PRIVATE HELPER METHODS ===
    
    def _initialize_default_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize default field mappings between platforms"""
        return {
            'linkedin_to_klenty': {
                'first_name': 'first_name',
                'last_name': 'last_name',
                'full_name': 'full_name',
                'email': 'email',
                'current_title': 'title',
                'current_company': 'company',
                'phone': 'phone',
                'location': 'location',
                'industry': 'industry',
                'linkedin_url': 'linkedin_url',
                'company_domain': 'company_domain',
                'company_size': 'company_size',
                'lead_score': 'lead_score',
                'opportunity_type': 'opportunity_type',
                'apollo_data': 'apollo_data',
                'perplexity_research': 'perplexity_research'
            },
            'klenty_to_linkedin': {
                'first_name': 'first_name',
                'last_name': 'last_name',
                'full_name': 'full_name',
                'email': 'email',
                'title': 'current_title',
                'company': 'current_company',
                'phone': 'phone',
                'location': 'location',
                'industry': 'industry',
                'linkedin_url': 'linkedin_url',
                'company_domain': 'company_domain',
                'company_size': 'company_size',
                'lead_score': 'lead_score',
                'engagement_score': 'engagement_score',
                'total_emails_sent': 'email_engagement_count',
                'total_replies': 'email_reply_count'
            }
        }
    
    def _initialize_default_integration_rules(self):
        """Initialize default integration rules"""
        # LinkedIn to Klenty sync rule
        self.integration_rules['linkedin_to_klenty_qualified'] = IntegrationRule(
            rule_id='linkedin_to_klenty_qualified',
            source_platform='linkedin',
            target_platform='klenty',
            sync_direction=SyncDirection.PUSH,
            trigger_conditions={
                'lead_score_min': 70.0,
                'status': ['connection_accepted', 'messaged', 'replied'],
                'has_email': True
            },
            field_mappings=self.default_field_mappings['linkedin_to_klenty'],
            transformation_rules=[
                {'field': 'source', 'value': 'linkedin_sync'},
                {'field': 'personalization_tokens', 'merge_from': 'linkedin_data'}
            ]
        )
        
        # Klenty to LinkedIn engagement sync rule
        self.integration_rules['klenty_to_linkedin_engagement'] = IntegrationRule(
            rule_id='klenty_to_linkedin_engagement',
            source_platform='klenty',
            target_platform='linkedin',
            sync_direction=SyncDirection.PUSH,
            trigger_conditions={
                'has_email_engagement': True,
                'total_emails_sent': {'min': 1}
            },
            field_mappings=self.default_field_mappings['klenty_to_linkedin'],
            transformation_rules=[
                {'field': 'conversation_context.email_engagement', 'merge_from': 'email_stats'}
            ]
        )
    
    def _create_campaign_integration_rules(self, config: CampaignCoordinationConfig) -> List[IntegrationRule]:
        """Create integration rules for campaign coordination"""
        rules = []
        
        # LinkedIn to Klenty lead sync
        if config.linkedin_campaign_id and config.klenty_campaign_id:
            rule = IntegrationRule(
                rule_id=f"sync_{config.linkedin_campaign_id}_to_{config.klenty_campaign_id}",
                source_platform='linkedin',
                target_platform='klenty',
                sync_direction=SyncDirection.PUSH,
                trigger_conditions={
                    'campaign_id': config.linkedin_campaign_id,
                    'lead_score_min': config.lead_qualification_threshold,
                    'has_email': True
                },
                field_mappings=self.default_field_mappings['linkedin_to_klenty'],
                transformation_rules=[
                    {'field': 'campaign_id', 'value': config.klenty_campaign_id},
                    {'field': 'source', 'value': 'coordinated_campaign'}
                ]
            )
            rules.append(rule)
            self.integration_rules[rule.rule_id] = rule
        
        return rules
    
    def _convert_linkedin_to_klenty_lead(self, linkedin_lead: LinkedInLead) -> Dict[str, Any]:
        """Convert LinkedIn lead to Klenty lead data"""
        return {
            'email': linkedin_lead.email,
            'first_name': linkedin_lead.first_name,
            'last_name': linkedin_lead.last_name,
            'title': linkedin_lead.current_title,
            'company': linkedin_lead.current_company,
            'phone': linkedin_lead.phone,
            'location': linkedin_lead.location,
            'industry': linkedin_lead.industry,
            'linkedin_url': linkedin_lead.linkedin_url,
            'company_domain': linkedin_lead.company_domain,
            'company_size': linkedin_lead.company_size,
            'opportunity_type': linkedin_lead.opportunity_type,
            'linkedin_data': linkedin_lead.to_dict(),
            'apollo_data': linkedin_lead.apollo_data,
            'perplexity_research': linkedin_lead.perplexity_research,
            'personalization_tokens': linkedin_lead.personalization_tokens,
            'custom_fields': {
                'linkedin_lead_id': linkedin_lead.lead_id,
                'linkedin_campaign_id': linkedin_lead.campaign_id,
                'linkedin_lead_score': linkedin_lead.lead_score,
                'linkedin_connection_date': linkedin_lead.connection_accepted_at.isoformat() if linkedin_lead.connection_accepted_at else None
            }
        }
    
    def _update_klenty_lead_from_linkedin(self, klenty_lead: KlentyLead, linkedin_lead: LinkedInLead):
        """Update Klenty lead with LinkedIn data"""
        # Update basic fields if they're missing
        if not klenty_lead.title and linkedin_lead.current_title:
            klenty_lead.title = linkedin_lead.current_title
        
        if not klenty_lead.company and linkedin_lead.current_company:
            klenty_lead.company = linkedin_lead.current_company
        
        if not klenty_lead.phone and linkedin_lead.phone:
            klenty_lead.phone = linkedin_lead.phone
        
        if not klenty_lead.linkedin_url and linkedin_lead.linkedin_url:
            klenty_lead.linkedin_url = linkedin_lead.linkedin_url
        
        # Update LinkedIn data
        klenty_lead.linkedin_data = linkedin_lead.to_dict()
        
        # Merge personalization tokens
        if linkedin_lead.personalization_tokens:
            klenty_lead.personalization_tokens = klenty_lead.personalization_tokens or {}
            klenty_lead.personalization_tokens.update(linkedin_lead.personalization_tokens)
        
        # Update custom fields
        klenty_lead.custom_fields = klenty_lead.custom_fields or {}
        klenty_lead.custom_fields.update({
            'linkedin_lead_id': linkedin_lead.lead_id,
            'linkedin_campaign_id': linkedin_lead.campaign_id,
            'linkedin_lead_score': linkedin_lead.lead_score,
            'linkedin_last_activity': linkedin_lead.last_activity_at.isoformat() if linkedin_lead.last_activity_at else None
        })
        
        klenty_lead.last_updated = datetime.utcnow()
    
    def _update_linkedin_lead_from_klenty(self, linkedin_lead: LinkedInLead, klenty_lead: KlentyLead):
        """Update LinkedIn lead with Klenty engagement data"""
        # Update conversation context with email data
        linkedin_lead.conversation_context = linkedin_lead.conversation_context or {}
        linkedin_lead.conversation_context.update({
            'klenty_lead_id': klenty_lead.lead_id,
            'klenty_campaign_id': klenty_lead.campaign_id,
            'email_engagement_score': klenty_lead.engagement_score,
            'total_emails_sent': klenty_lead.total_emails_sent,
            'total_emails_opened': klenty_lead.total_emails_opened,
            'total_emails_clicked': klenty_lead.total_emails_clicked,
            'total_replies': klenty_lead.total_replies,
            'last_email_sent': klenty_lead.last_email_sent_at.isoformat() if klenty_lead.last_email_sent_at else None,
            'last_email_opened': klenty_lead.last_email_opened_at.isoformat() if klenty_lead.last_email_opened_at else None,
            'last_reply': klenty_lead.last_reply_at.isoformat() if klenty_lead.last_reply_at else None
        })
        
        # Boost engagement score based on email performance
        if klenty_lead.engagement_score > 0:
            linkedin_lead.engagement_score = max(linkedin_lead.engagement_score, klenty_lead.engagement_score)
        
        linkedin_lead.last_updated = datetime.utcnow()
    
    def _create_executive_opportunity_from_linkedin_lead(self, linkedin_lead: LinkedInLead) -> Optional[ExecutiveOpportunity]:
        """Create executive opportunity from LinkedIn lead"""
        try:
            opportunity = ExecutiveOpportunity(
                type=linkedin_lead.opportunity_type or 'consulting',
                title=f"{linkedin_lead.opportunity_type or 'Executive'} opportunity at {linkedin_lead.current_company}",
                company=linkedin_lead.current_company,
                status='prospect',
                ai_match_score=linkedin_lead.lead_score,
                source='linkedin_automation',
                notes=f"Escalated from LinkedIn campaign: {linkedin_lead.campaign_id}",
                decision_makers=[{
                    'name': linkedin_lead.full_name,
                    'title': linkedin_lead.current_title,
                    'email': linkedin_lead.email,
                    'phone': linkedin_lead.phone,
                    'linkedin': linkedin_lead.linkedin_url
                }],
                company_research=linkedin_lead.perplexity_research or {},
                networking_connections=linkedin_lead.apollo_data.get('connections', []) if linkedin_lead.apollo_data else []
            )
            
            db.session.add(opportunity)
            db.session.flush()
            return opportunity
            
        except Exception as e:
            logger.error(f"Error creating executive opportunity from LinkedIn lead: {e}")
            return None
    
    def _create_executive_opportunity_from_klenty_lead(self, klenty_lead: KlentyLead) -> Optional[ExecutiveOpportunity]:
        """Create executive opportunity from Klenty lead"""
        try:
            opportunity = ExecutiveOpportunity(
                type=klenty_lead.opportunity_type or 'consulting',
                title=f"{klenty_lead.opportunity_type or 'Executive'} opportunity at {klenty_lead.company}",
                company=klenty_lead.company,
                status='prospect',
                ai_match_score=klenty_lead.lead_score,
                source='klenty_automation',
                notes=f"Escalated from Klenty campaign: {klenty_lead.campaign_id}",
                decision_makers=[{
                    'name': klenty_lead.full_name,
                    'title': klenty_lead.title,
                    'email': klenty_lead.email,
                    'phone': klenty_lead.phone,
                    'linkedin': klenty_lead.linkedin_url
                }],
                company_research=klenty_lead.perplexity_research or {},
                networking_connections=klenty_lead.apollo_data.get('connections', []) if klenty_lead.apollo_data else []
            )
            
            db.session.add(opportunity)
            db.session.flush()
            return opportunity
            
        except Exception as e:
            logger.error(f"Error creating executive opportunity from Klenty lead: {e}")
            return None
    
    def _calculate_platform_metrics(self, analytics: Dict, linkedin_leads: List, klenty_leads: List):
        """Calculate platform-specific metrics"""
        # LinkedIn metrics
        linkedin_connections_sent = len([l for l in linkedin_leads if l.connection_sent_at])
        linkedin_connections_accepted = len([l for l in linkedin_leads if l.status == LinkedInLeadStatus.CONNECTION_ACCEPTED.value])
        linkedin_messages_sent = sum([len(l.messages) for l in linkedin_leads])
        linkedin_replies = len([l for l in linkedin_leads if l.status == LinkedInLeadStatus.REPLIED.value])
        
        analytics['platform_performance']['linkedin'].update({
            'connections_sent': linkedin_connections_sent,
            'connections_accepted': linkedin_connections_accepted,
            'messages_sent': linkedin_messages_sent,
            'replies_received': linkedin_replies,
            'acceptance_rate': (linkedin_connections_accepted / linkedin_connections_sent * 100) if linkedin_connections_sent > 0 else 0,
            'response_rate': (linkedin_replies / linkedin_messages_sent * 100) if linkedin_messages_sent > 0 else 0
        })
        
        # Email metrics
        total_emails_sent = sum([l.total_emails_sent for l in klenty_leads])
        total_emails_opened = sum([l.total_emails_opened for l in klenty_leads])
        total_emails_clicked = sum([l.total_emails_clicked for l in klenty_leads])
        total_email_replies = sum([l.total_replies for l in klenty_leads])
        
        analytics['platform_performance']['email'].update({
            'emails_sent': total_emails_sent,
            'emails_opened': total_emails_opened,
            'emails_clicked': total_emails_clicked,
            'replies_received': total_email_replies,
            'open_rate': (total_emails_opened / total_emails_sent * 100) if total_emails_sent > 0 else 0,
            'click_rate': (total_emails_clicked / total_emails_sent * 100) if total_emails_sent > 0 else 0,
            'reply_rate': (total_email_replies / total_emails_sent * 100) if total_emails_sent > 0 else 0
        })
    
    def _calculate_cross_platform_metrics(self, analytics: Dict, lead_mapping: Dict):
        """Calculate cross-platform metrics"""
        linkedin_to_email_conversions = 0
        email_replies_after_linkedin = 0
        linkedin_replies_after_email = 0
        total_touchpoints = 0
        conversion_count = 0
        
        for email, platforms in lead_mapping.items():
            has_linkedin = len(platforms['linkedin']) > 0
            has_klenty = len(platforms['klenty']) > 0
            
            if has_linkedin and has_klenty:
                linkedin_to_email_conversions += 1
                
                # Check for email replies after LinkedIn activity
                for klenty_lead in platforms['klenty']:
                    if klenty_lead.total_replies > 0:
                        email_replies_after_linkedin += 1
                        break
                
                # Check for LinkedIn replies after email activity
                for linkedin_lead in platforms['linkedin']:
                    if linkedin_lead.status == LinkedInLeadStatus.REPLIED.value:
                        linkedin_replies_after_email += 1
                        break
                
                # Calculate touchpoints to conversion
                touchpoints = 0
                converted = False
                
                for linkedin_lead in platforms['linkedin']:
                    touchpoints += len(linkedin_lead.messages)
                    if linkedin_lead.status == LinkedInLeadStatus.CONVERTED.value:
                        converted = True
                
                for klenty_lead in platforms['klenty']:
                    touchpoints += klenty_lead.total_emails_sent
                    if klenty_lead.status == KlentyLeadStatus.CONVERTED.value:
                        converted = True
                
                if converted and touchpoints > 0:
                    total_touchpoints += touchpoints
                    conversion_count += 1
        
        analytics['cross_platform_metrics'].update({
            'linkedin_to_email_conversion': (linkedin_to_email_conversions / len(lead_mapping) * 100) if lead_mapping else 0,
            'email_reply_after_linkedin': email_replies_after_linkedin,
            'linkedin_reply_after_email': linkedin_replies_after_email,
            'average_touchpoints_to_conversion': (total_touchpoints / conversion_count) if conversion_count > 0 else 0
        })

def create_klenty_integration_workflows(klenty_service, linkedin_service, automation_bridge=None):
    """Factory function to create Klenty integration workflows"""
    return KlentyIntegrationWorkflows(klenty_service, linkedin_service, automation_bridge)