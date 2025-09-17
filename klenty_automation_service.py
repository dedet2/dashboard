"""
Klenty SDRx Outreach Automation Service
Comprehensive automation system for email sequences, lead nurturing, and sales pipeline automation
"""

import logging
import uuid
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from database import db, ExecutiveOpportunity
from klenty_models import (
    KlentyCampaign, KlentySequence, KlentyLead, KlentyTemplate, KlentyEmail, 
    KlentyAutomationRule, KlentyAnalytics, KlentyCampaignStatus, KlentyLeadStatus, 
    KlentyEmailStatus, KlentySequenceStatus
)

# Import existing services for integration
from apollo_integration import ApolloAPIWrapper, ApolloProspect
from perplexity_service import PerplexityResearchService, PerplexityAPI, PerplexityModel
from make_automation_bridges import AutomationBridgeService

logger = logging.getLogger(__name__)

@dataclass
class EmailSequenceConfig:
    """Email sequence configuration"""
    sequence_name: str
    total_steps: int
    delay_between_emails: int = 3  # Days
    stop_on_reply: bool = True
    stop_on_click: bool = False
    stop_on_open: bool = False
    stop_on_unsubscribe: bool = True
    personalization_enabled: bool = True

@dataclass
class EmailTemplate:
    """Email template configuration"""
    subject_line: str
    email_body: str
    step_number: int
    delay_days: int = 0
    personalization_fields: List[str] = None
    html_body: Optional[str] = None

@dataclass
class LeadImportConfig:
    """Lead import configuration"""
    source: str = "manual_import"
    auto_enrich: bool = True
    auto_score: bool = True
    auto_assign_sequence: bool = True
    default_sequence_id: Optional[str] = None

class KlentyAutomationService:
    """
    Main service class for Klenty SDRx outreach automation
    Integrates with Apollo.io, Perplexity AI, LinkedIn, and Make.com automation bridges
    """
    
    def __init__(self, apollo_api: Optional[ApolloAPIWrapper] = None, 
                 perplexity_api: Optional[PerplexityAPI] = None,
                 automation_bridge: Optional[AutomationBridgeService] = None,
                 smtp_config: Optional[Dict[str, Any]] = None):
        self.apollo_api = apollo_api
        self.perplexity_api = perplexity_api
        self.perplexity_research = PerplexityResearchService(perplexity_api) if perplexity_api else None
        self.automation_bridge = automation_bridge
        self.smtp_config = smtp_config or {}
        
        # Default email templates
        self.default_templates = self._initialize_default_templates()
        
        # Lead scoring weights
        self.lead_scoring_weights = {
            'title_match': 0.25,
            'company_size': 0.20,
            'industry_relevance': 0.15,
            'apollo_match_score': 0.20,
            'email_deliverability': 0.10,
            'linkedin_profile_completeness': 0.10
        }
        
        # Email personalization patterns
        self.personalization_patterns = {
            'first_name': r'\{\{first_name\}\}',
            'last_name': r'\{\{last_name\}\}',
            'full_name': r'\{\{full_name\}\}',
            'company': r'\{\{company\}\}',
            'title': r'\{\{title\}\}',
            'industry': r'\{\{industry\}\}',
            'location': r'\{\{location\}\}',
            'custom_field': r'\{\{([^}]+)\}\}'
        }
    
    def create_campaign(self, name: str, description: str, sender_email: str, sender_name: str,
                       target_audience: Dict[str, Any], created_by: str, **kwargs) -> Optional[KlentyCampaign]:
        """
        Create a new Klenty email campaign
        
        Args:
            name: Campaign name
            description: Campaign description
            sender_email: Email address to send from
            sender_name: Name to send from
            target_audience: Targeting criteria and filters
            created_by: User creating the campaign
            **kwargs: Additional campaign configuration
            
        Returns:
            Created KlentyCampaign or None if error
        """
        try:
            campaign_id = f"klenty_campaign_{str(uuid.uuid4())[:8]}_{int(time.time())}"
            
            campaign = KlentyCampaign(
                campaign_id=campaign_id,
                name=name,
                description=description,
                target_audience=target_audience,
                sender_email=sender_email,
                sender_name=sender_name,
                created_by=created_by,
                reply_to_email=kwargs.get('reply_to_email', sender_email),
                daily_email_limit=kwargs.get('daily_email_limit', 100),
                weekly_email_limit=kwargs.get('weekly_email_limit', 500),
                target_prospects=kwargs.get('target_prospects'),
                target_opens=kwargs.get('target_opens'),
                target_clicks=kwargs.get('target_clicks'),
                target_replies=kwargs.get('target_replies'),
                target_conversions=kwargs.get('target_conversions'),
                time_zone=kwargs.get('time_zone', 'UTC'),
                sending_days=kwargs.get('sending_days', ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']),
                sending_hours_start=kwargs.get('sending_hours_start', 9),
                sending_hours_end=kwargs.get('sending_hours_end', 17),
                linkedin_integration_enabled=kwargs.get('linkedin_integration_enabled', True),
                apollo_enrichment_enabled=kwargs.get('apollo_enrichment_enabled', True),
                perplexity_research_enabled=kwargs.get('perplexity_research_enabled', True),
                make_automation_enabled=kwargs.get('make_automation_enabled', True),
                ab_testing_enabled=kwargs.get('ab_testing_enabled', False)
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            logger.info(f"Created Klenty campaign: {campaign_id}")
            return campaign
            
        except Exception as e:
            logger.error(f"Error creating Klenty campaign: {e}")
            db.session.rollback()
            return None
    
    def create_sequence(self, campaign_id: str, config: EmailSequenceConfig, 
                       templates: List[EmailTemplate]) -> Optional[KlentySequence]:
        """
        Create an email sequence with templates
        
        Args:
            campaign_id: Parent campaign ID
            config: Sequence configuration
            templates: List of email templates for the sequence
            
        Returns:
            Created KlentySequence or None if error
        """
        try:
            campaign = KlentyCampaign.query.filter_by(campaign_id=campaign_id).first()
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return None
            
            sequence_id = f"klenty_seq_{str(uuid.uuid4())[:8]}_{int(time.time())}"
            
            sequence = KlentySequence(
                sequence_id=sequence_id,
                campaign_id=campaign_id,
                name=config.sequence_name,
                total_steps=config.total_steps,
                delay_between_emails=config.delay_between_emails,
                stop_on_reply=config.stop_on_reply,
                stop_on_click=config.stop_on_click,
                stop_on_open=config.stop_on_open,
                stop_on_unsubscribe=config.stop_on_unsubscribe
            )
            
            db.session.add(sequence)
            db.session.flush()  # Get sequence ID for templates
            
            # Create templates for the sequence
            for template in templates:
                self._create_template_for_sequence(sequence, template)
            
            db.session.commit()
            
            logger.info(f"Created email sequence: {sequence_id} with {len(templates)} templates")
            return sequence
            
        except Exception as e:
            logger.error(f"Error creating email sequence: {e}")
            db.session.rollback()
            return None
    
    def import_leads(self, campaign_id: str, leads_data: List[Dict[str, Any]], 
                    config: LeadImportConfig) -> Dict[str, Any]:
        """
        Import leads into a campaign
        
        Args:
            campaign_id: Campaign to import leads into
            leads_data: List of lead data dictionaries
            config: Import configuration
            
        Returns:
            Dictionary with import results
        """
        try:
            campaign = KlentyCampaign.query.filter_by(campaign_id=campaign_id).first()
            if not campaign:
                return {'error': f'Campaign {campaign_id} not found'}
            
            results = {
                'imported': 0,
                'enriched': 0,
                'scored': 0,
                'assigned_to_sequence': 0,
                'errors': []
            }
            
            for lead_data in leads_data:
                try:
                    # Create lead
                    lead = self._create_lead_from_data(campaign_id, lead_data, config.source)
                    if lead:
                        results['imported'] += 1
                        
                        # Auto-enrich with Apollo
                        if config.auto_enrich and self.apollo_api:
                            if self.enrich_lead_with_apollo(lead.lead_id):
                                results['enriched'] += 1
                        
                        # Auto-score lead
                        if config.auto_score:
                            lead.lead_score = self._calculate_lead_score(lead)
                            results['scored'] += 1
                        
                        # Auto-assign to sequence
                        if config.auto_assign_sequence and config.default_sequence_id:
                            if self.assign_lead_to_sequence(lead.lead_id, config.default_sequence_id):
                                results['assigned_to_sequence'] += 1
                        
                        db.session.commit()
                
                except Exception as e:
                    error_msg = f"Error importing lead {lead_data.get('email', 'unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    db.session.rollback()
            
            # Update campaign statistics
            campaign.total_prospects = KlentyLead.query.filter_by(campaign_id=campaign_id).count()
            campaign.last_activity = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Imported {results['imported']} leads into campaign {campaign_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error importing leads: {e}")
            return {'error': str(e)}
    
    def enrich_lead_with_apollo(self, lead_id: str) -> bool:
        """
        Enrich Klenty lead with Apollo.io data
        
        Args:
            lead_id: Klenty lead ID to enrich
            
        Returns:
            True if enrichment successful, False otherwise
        """
        try:
            if not self.apollo_api:
                logger.warning("Apollo API not configured for lead enrichment")
                return False
            
            lead = KlentyLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return False
            
            # Enrich using Apollo
            enrichment_data = self.apollo_api.enrich_person(
                first_name=lead.first_name,
                last_name=lead.last_name,
                organization_name=lead.company,
                domain=lead.company_domain,
                email=lead.email
            )
            
            if enrichment_data and 'person' in enrichment_data:
                person_data = enrichment_data['person']
                
                # Update lead with enriched data
                if not lead.phone and person_data.get('phone_numbers'):
                    lead.phone = person_data['phone_numbers'][0].get('raw_number')
                
                if not lead.linkedin_url and person_data.get('linkedin_url'):
                    lead.linkedin_url = person_data['linkedin_url']
                
                if not lead.title and person_data.get('title'):
                    lead.title = person_data['title']
                
                lead.apollo_data = enrichment_data
                
                # Update company information
                if 'organization' in enrichment_data:
                    org_data = enrichment_data['organization']
                    if not lead.company_domain and org_data.get('website_url'):
                        lead.company_domain = org_data['website_url']
                    if not lead.company_size and org_data.get('employees_count'):
                        lead.company_size = str(org_data['employees_count'])
                    if not lead.industry and org_data.get('industry'):
                        lead.industry = org_data['industry']
                
                # Recalculate lead score with enriched data
                lead.lead_score = self._calculate_lead_score(lead)
                
                lead.last_updated = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Successfully enriched lead {lead_id} with Apollo data")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enriching lead with Apollo: {e}")
            return False
    
    def research_lead_with_perplexity(self, lead_id: str) -> bool:
        """
        Research Klenty lead using Perplexity AI for personalization insights
        
        Args:
            lead_id: Klenty lead ID to research
            
        Returns:
            True if research successful, False otherwise
        """
        try:
            if not self.perplexity_research:
                logger.warning("Perplexity API not configured for lead research")
                return False
            
            lead = KlentyLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return False
            
            # Research lead for personalization insights
            research_result = self.perplexity_research.research_executive_opportunity(
                executive_name=lead.full_name,
                company_name=lead.company,
                opportunity_type=lead.opportunity_type or "business_engagement"
            )
            
            if research_result:
                # Extract personalization tokens from research
                personalization_tokens = self._extract_personalization_tokens(research_result)
                
                lead.perplexity_research = research_result
                lead.personalization_tokens = personalization_tokens
                lead.last_updated = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Successfully researched lead {lead_id} with Perplexity")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error researching lead with Perplexity: {e}")
            return False
    
    def assign_lead_to_sequence(self, lead_id: str, sequence_id: str) -> bool:
        """
        Assign a lead to an email sequence
        
        Args:
            lead_id: Lead to assign
            sequence_id: Sequence to assign lead to
            
        Returns:
            True if assignment successful, False otherwise
        """
        try:
            lead = KlentyLead.query.filter_by(lead_id=lead_id).first()
            sequence = KlentySequence.query.filter_by(sequence_id=sequence_id).first()
            
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return False
            
            if not sequence:
                logger.error(f"Sequence {sequence_id} not found")
                return False
            
            # Check if lead is already in a sequence
            if lead.current_sequence_id and lead.sequence_status == 'active':
                logger.warning(f"Lead {lead_id} is already in active sequence {lead.current_sequence_id}")
                return False
            
            # Assign lead to sequence
            lead.current_sequence_id = sequence_id
            lead.current_sequence_step = 0
            lead.sequence_status = 'active'
            
            # Schedule first email
            first_template = KlentyTemplate.query.filter_by(
                sequence_id=sequence_id, 
                step_number=1, 
                active=True
            ).first()
            
            if first_template:
                lead.next_email_scheduled_at = self._calculate_next_send_time(
                    first_template.delay_days, 
                    lead.campaign.sending_days,
                    lead.campaign.sending_hours_start,
                    lead.campaign.sending_hours_end,
                    lead.campaign.time_zone
                )
            
            # Update sequence statistics
            sequence.leads_entered += 1
            
            lead.last_updated = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Assigned lead {lead_id} to sequence {sequence_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning lead to sequence: {e}")
            db.session.rollback()
            return False
    
    def send_scheduled_emails(self, limit: int = 100) -> Dict[str, Any]:
        """
        Send all scheduled emails that are due
        
        Args:
            limit: Maximum number of emails to send in this batch
            
        Returns:
            Dictionary with sending results
        """
        try:
            # Get leads with scheduled emails
            now = datetime.utcnow()
            leads_to_send = KlentyLead.query.filter(
                KlentyLead.next_email_scheduled_at <= now,
                KlentyLead.sequence_status == 'active',
                KlentyLead.current_sequence_id.isnot(None)
            ).limit(limit).all()
            
            results = {
                'emails_sent': 0,
                'emails_failed': 0,
                'sequences_completed': 0,
                'errors': []
            }
            
            for lead in leads_to_send:
                try:
                    # Check daily limits
                    if not self._check_daily_email_limits(lead.campaign):
                        logger.warning(f"Daily email limit reached for campaign {lead.campaign_id}")
                        continue
                    
                    # Get next template in sequence
                    next_step = lead.current_sequence_step + 1
                    template = KlentyTemplate.query.filter_by(
                        sequence_id=lead.current_sequence_id,
                        step_number=next_step,
                        active=True
                    ).first()
                    
                    if template:
                        # Send email
                        if self.send_email_from_template(lead.lead_id, template.template_id):
                            results['emails_sent'] += 1
                            
                            # Update lead sequence progress
                            lead.current_sequence_step = next_step
                            
                            # Check if sequence is complete
                            sequence = KlentySequence.query.filter_by(
                                sequence_id=lead.current_sequence_id
                            ).first()
                            
                            if next_step >= sequence.total_steps:
                                # Sequence completed
                                lead.sequence_status = 'completed'
                                lead.current_sequence_id = None
                                lead.next_email_scheduled_at = None
                                sequence.leads_completed += 1
                                results['sequences_completed'] += 1
                            else:
                                # Schedule next email
                                next_template = KlentyTemplate.query.filter_by(
                                    sequence_id=lead.current_sequence_id,
                                    step_number=next_step + 1,
                                    active=True
                                ).first()
                                
                                if next_template:
                                    lead.next_email_scheduled_at = self._calculate_next_send_time(
                                        next_template.delay_days,
                                        lead.campaign.sending_days,
                                        lead.campaign.sending_hours_start,
                                        lead.campaign.sending_hours_end,
                                        lead.campaign.time_zone
                                    )
                        else:
                            results['emails_failed'] += 1
                    else:
                        # No more templates, complete sequence
                        lead.sequence_status = 'completed'
                        lead.current_sequence_id = None
                        lead.next_email_scheduled_at = None
                        results['sequences_completed'] += 1
                    
                    db.session.commit()
                    
                except Exception as e:
                    error_msg = f"Error sending email to lead {lead.lead_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    db.session.rollback()
            
            logger.info(f"Sent {results['emails_sent']} scheduled emails")
            return results
            
        except Exception as e:
            logger.error(f"Error sending scheduled emails: {e}")
            return {'error': str(e)}
    
    def send_email_from_template(self, lead_id: str, template_id: str) -> bool:
        """
        Send personalized email to a lead using a template
        
        Args:
            lead_id: Lead to send email to
            template_id: Template to use for email
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            lead = KlentyLead.query.filter_by(lead_id=lead_id).first()
            template = KlentyTemplate.query.filter_by(template_id=template_id).first()
            
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return False
            
            if not template:
                logger.error(f"Template {template_id} not found")
                return False
            
            # Check if lead is unsubscribed or bounced
            if lead.status in [KlentyLeadStatus.UNSUBSCRIBED.value, KlentyLeadStatus.EMAIL_BOUNCED.value]:
                logger.warning(f"Cannot send email to lead {lead_id} - status: {lead.status}")
                return False
            
            # Personalize email content
            personalized_subject = self._personalize_content(lead, template.subject_line)
            personalized_body = self._personalize_content(lead, template.email_body)
            personalized_html = None
            if template.email_body_html:
                personalized_html = self._personalize_content(lead, template.email_body_html)
            
            # Create email record
            email_id = f"klenty_email_{str(uuid.uuid4())[:8]}_{int(time.time())}"
            email = KlentyEmail(
                email_id=email_id,
                lead_id=lead_id,
                template_id=template_id,
                sequence_id=template.sequence_id,
                subject=template.subject_line,
                content=template.email_body,
                content_html=template.email_body_html,
                personalized_subject=personalized_subject,
                personalized_content=personalized_body,
                sender_email=lead.campaign.sender_email,
                sender_name=lead.campaign.sender_name,
                reply_to_email=lead.campaign.reply_to_email,
                sequence_step=template.step_number,
                is_followup=template.step_number > 1,
                scheduled_at=datetime.utcnow()
            )
            
            # Send email
            if self._send_email_via_smtp(email, personalized_html):
                email.status = KlentyEmailStatus.SENT.value
                email.sent_at = datetime.utcnow()
                
                # Update lead status and statistics
                if lead.first_email_sent_at is None:
                    lead.first_email_sent_at = datetime.utcnow()
                    lead.status = KlentyLeadStatus.EMAIL_SENT.value
                
                lead.last_email_sent_at = datetime.utcnow()
                lead.total_emails_sent += 1
                
                # Update template statistics
                template.sent_count += 1
                
                # Update campaign statistics
                lead.campaign.emails_sent += 1
                lead.campaign.last_activity = datetime.utcnow()
                
                db.session.add(email)
                db.session.commit()
                
                # Trigger Make.com automation
                if lead.campaign.make_automation_enabled and self.automation_bridge:
                    self._trigger_klenty_event("email_sent", {
                        "lead_id": lead_id,
                        "email_id": email_id,
                        "campaign_id": lead.campaign_id,
                        "sequence_id": template.sequence_id,
                        "template_id": template_id,
                        "subject": personalized_subject,
                        "lead_data": lead.to_dict()
                    })
                
                logger.info(f"Sent email {email_id} to lead {lead_id}")
                return True
            else:
                email.status = KlentyEmailStatus.FAILED.value
                email.error_message = "Failed to send via SMTP"
                db.session.add(email)
                db.session.commit()
                return False
                
        except Exception as e:
            logger.error(f"Error sending email from template: {e}")
            return False
    
    def process_email_webhooks(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Process email engagement webhooks (opens, clicks, replies, bounces)
        
        Args:
            webhook_data: Webhook payload from email provider
            
        Returns:
            True if processed successfully, False otherwise
        """
        try:
            event_type = webhook_data.get('event')
            email_id = webhook_data.get('email_id')
            timestamp = webhook_data.get('timestamp', datetime.utcnow().isoformat())
            
            if not email_id:
                logger.error("No email_id in webhook data")
                return False
            
            email = KlentyEmail.query.filter_by(email_id=email_id).first()
            if not email:
                logger.error(f"Email {email_id} not found")
                return False
            
            lead = email.lead
            campaign = lead.campaign
            
            # Process different event types
            if event_type == 'opened':
                self._process_email_open(email, lead, webhook_data, timestamp)
            elif event_type == 'clicked':
                self._process_email_click(email, lead, webhook_data, timestamp)
            elif event_type == 'replied':
                self._process_email_reply(email, lead, webhook_data, timestamp)
            elif event_type == 'bounced':
                self._process_email_bounce(email, lead, webhook_data, timestamp)
            elif event_type == 'delivered':
                self._process_email_delivery(email, lead, webhook_data, timestamp)
            elif event_type == 'unsubscribed':
                self._process_email_unsubscribe(email, lead, webhook_data, timestamp)
            
            db.session.commit()
            
            # Trigger Make.com automation for significant events
            if event_type in ['replied', 'clicked'] and campaign.make_automation_enabled and self.automation_bridge:
                self._trigger_klenty_event(f"email_{event_type}", {
                    "lead_id": lead.lead_id,
                    "email_id": email_id,
                    "campaign_id": campaign.campaign_id,
                    "event_type": event_type,
                    "webhook_data": webhook_data,
                    "lead_data": lead.to_dict()
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing email webhook: {e}")
            db.session.rollback()
            return False
    
    def qualify_lead(self, lead_id: str) -> Dict[str, Any]:
        """
        Qualify a Klenty lead using AI scoring and analysis
        
        Args:
            lead_id: Klenty lead ID to qualify
            
        Returns:
            Dictionary with qualification results
        """
        try:
            lead = KlentyLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                return {'error': f'Lead {lead_id} not found'}
            
            # Calculate comprehensive lead score
            lead_score = self._calculate_lead_score(lead)
            engagement_score = self._calculate_engagement_score(lead)
            
            # Determine qualification status
            qualification_status = self._determine_qualification_status(lead_score, engagement_score)
            
            # Update lead with qualification results
            lead.lead_score = lead_score
            lead.engagement_score = engagement_score
            lead.qualification_status = qualification_status
            
            # Check if lead should be converted to executive opportunity
            if qualification_status == 'qualified' and lead.opportunity_type:
                opportunity_created = self._convert_to_executive_opportunity(lead)
                if opportunity_created:
                    lead.status = KlentyLeadStatus.CONVERTED.value
            
            lead.last_updated = datetime.utcnow()
            db.session.commit()
            
            # Trigger Make.com automation for qualified leads
            if qualification_status == 'qualified' and self.automation_bridge:
                self._trigger_klenty_event("lead_qualified", {
                    "lead_id": lead_id,
                    "lead_score": lead_score,
                    "engagement_score": engagement_score,
                    "qualification_status": qualification_status,
                    "lead_data": lead.to_dict()
                })
            
            return {
                'lead_id': lead_id,
                'lead_score': lead_score,
                'engagement_score': engagement_score,
                'qualification_status': qualification_status,
                'qualified': qualification_status == 'qualified'
            }
            
        except Exception as e:
            logger.error(f"Error qualifying lead: {e}")
            return {'error': str(e)}
    
    def get_campaign_analytics(self, campaign_id: str, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a Klenty campaign
        
        Args:
            campaign_id: Campaign ID to analyze
            date_range: Optional tuple of (start_date, end_date)
            
        Returns:
            Dictionary with campaign analytics
        """
        try:
            campaign = KlentyCampaign.query.filter_by(campaign_id=campaign_id).first()
            if not campaign:
                return {'error': f'Campaign {campaign_id} not found'}
            
            # Build date filter
            date_filter = True
            if date_range:
                start_date, end_date = date_range
                date_filter = KlentyLead.imported_at.between(start_date, end_date)
            
            # Get campaign leads with date filter
            leads = KlentyLead.query.filter_by(campaign_id=campaign_id).filter(date_filter).all()
            emails = KlentyEmail.query.join(KlentyLead).filter(
                KlentyLead.campaign_id == campaign_id
            ).filter(date_filter).all()
            
            # Calculate analytics
            analytics = {
                'campaign_info': {
                    'id': campaign_id,
                    'name': campaign.name,
                    'status': campaign.status,
                    'created_at': campaign.created_at.isoformat(),
                    'last_activity': campaign.last_activity.isoformat() if campaign.last_activity else None
                },
                'lead_metrics': {
                    'total_leads': len(leads),
                    'imported': len([l for l in leads if l.status == KlentyLeadStatus.IMPORTED.value]),
                    'email_sent': len([l for l in leads if l.status == KlentyLeadStatus.EMAIL_SENT.value]),
                    'email_opened': len([l for l in leads if l.status == KlentyLeadStatus.EMAIL_OPENED.value]),
                    'email_clicked': len([l for l in leads if l.status == KlentyLeadStatus.EMAIL_CLICKED.value]),
                    'email_replied': len([l for l in leads if l.status == KlentyLeadStatus.EMAIL_REPLIED.value]),
                    'qualified': len([l for l in leads if l.qualification_status == 'qualified']),
                    'converted': len([l for l in leads if l.status == KlentyLeadStatus.CONVERTED.value]),
                    'unsubscribed': len([l for l in leads if l.status == KlentyLeadStatus.UNSUBSCRIBED.value]),
                    'bounced': len([l for l in leads if l.status == KlentyLeadStatus.EMAIL_BOUNCED.value])
                },
                'email_metrics': {
                    'total_emails_sent': len([e for e in emails if e.status == KlentyEmailStatus.SENT.value]),
                    'emails_delivered': len([e for e in emails if e.status in [KlentyEmailStatus.DELIVERED.value, KlentyEmailStatus.OPENED.value, KlentyEmailStatus.CLICKED.value]]),
                    'emails_opened': len([e for e in emails if e.status in [KlentyEmailStatus.OPENED.value, KlentyEmailStatus.CLICKED.value]]),
                    'emails_clicked': len([e for e in emails if e.status == KlentyEmailStatus.CLICKED.value]),
                    'emails_replied': len([e for e in emails if e.status == KlentyEmailStatus.REPLIED.value]),
                    'emails_bounced': len([e for e in emails if e.status == KlentyEmailStatus.BOUNCED.value])
                },
                'engagement_metrics': {
                    'open_rate': self._calculate_open_rate(emails),
                    'click_rate': self._calculate_click_rate(emails),
                    'reply_rate': self._calculate_reply_rate(emails),
                    'bounce_rate': self._calculate_bounce_rate(emails),
                    'unsubscribe_rate': self._calculate_unsubscribe_rate(leads)
                },
                'performance_metrics': {
                    'average_lead_score': sum([l.lead_score for l in leads]) / len(leads) if leads else 0,
                    'average_engagement_score': sum([l.engagement_score for l in leads]) / len(leads) if leads else 0,
                    'conversion_rate': self._calculate_conversion_rate(leads),
                    'qualified_lead_rate': self._calculate_qualified_rate(leads)
                },
                'timeline_data': self._generate_email_timeline_data(emails, date_range)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting campaign analytics: {e}")
            return {'error': str(e)}
    
    # === PRIVATE HELPER METHODS ===
    
    def _initialize_default_templates(self) -> Dict[str, EmailTemplate]:
        """Initialize default email templates"""
        templates = {}
        
        # Cold outreach template
        templates['cold_outreach'] = EmailTemplate(
            subject_line="Quick question about {{company}}'s {{industry}} strategy",
            email_body="""Hi {{first_name}},

I hope this email finds you well. I noticed {{company}} has been making interesting moves in the {{industry}} space.

I'm Dr. Dede, and I specialize in AI governance and risk management for executive teams. Given your role as {{title}}, I thought you might be interested in how other {{industry}} leaders are approaching AI implementation while managing regulatory compliance.

Would you be open to a brief 15-minute conversation about this? I'd be happy to share some insights that might be relevant to {{company}}'s strategic initiatives.

Best regards,
Dr. Dede""",
            step_number=1,
            delay_days=0,
            personalization_fields=['first_name', 'company', 'industry', 'title']
        )
        
        # Follow-up template
        templates['follow_up'] = EmailTemplate(
            subject_line="Re: {{company}}'s AI governance approach",
            email_body="""Hi {{first_name}},

I wanted to follow up on my previous email about AI governance strategies for {{company}}.

I recently helped a similar {{industry}} company implement a comprehensive AI governance framework that resulted in 40% faster regulatory approvals and significantly reduced compliance risks.

I understand you're likely busy, but I believe this could be valuable for {{company}}. Would you have 10 minutes for a quick call this week?

Best regards,
Dr. Dede""",
            step_number=2,
            delay_days=3,
            personalization_fields=['first_name', 'company', 'industry']
        )
        
        return templates
    
    def _create_lead_from_data(self, campaign_id: str, lead_data: Dict[str, Any], source: str) -> Optional[KlentyLead]:
        """Create a lead from import data"""
        try:
            lead_id = f"klenty_lead_{str(uuid.uuid4())[:8]}_{int(time.time())}"
            
            lead = KlentyLead(
                lead_id=lead_id,
                campaign_id=campaign_id,
                email=lead_data['email'],
                first_name=lead_data['first_name'],
                last_name=lead_data['last_name'],
                full_name=f"{lead_data['first_name']} {lead_data['last_name']}",
                title=lead_data.get('title'),
                company=lead_data.get('company'),
                phone=lead_data.get('phone'),
                location=lead_data.get('location'),
                industry=lead_data.get('industry'),
                company_domain=lead_data.get('company_domain'),
                company_size=lead_data.get('company_size'),
                linkedin_url=lead_data.get('linkedin_url'),
                twitter_url=lead_data.get('twitter_url'),
                opportunity_type=lead_data.get('opportunity_type'),
                custom_fields=lead_data.get('custom_fields', {}),
                source=source
            )
            
            db.session.add(lead)
            return lead
            
        except Exception as e:
            logger.error(f"Error creating lead from data: {e}")
            return None
    
    def _create_template_for_sequence(self, sequence: KlentySequence, template: EmailTemplate):
        """Create a template for a sequence"""
        template_id = f"klenty_template_{str(uuid.uuid4())[:8]}_{int(time.time())}"
        
        klenty_template = KlentyTemplate(
            template_id=template_id,
            sequence_id=sequence.sequence_id,
            name=f"{sequence.name} - Step {template.step_number}",
            step_number=template.step_number,
            delay_days=template.delay_days,
            subject_line=template.subject_line,
            email_body=template.email_body,
            email_body_html=template.html_body,
            personalization_fields=template.personalization_fields or []
        )
        
        db.session.add(klenty_template)
    
    def _calculate_lead_score(self, lead: KlentyLead) -> float:
        """Calculate AI-driven lead score"""
        score = 0.0
        
        # Title relevance
        if lead.title:
            executive_titles = ['CEO', 'CTO', 'CRO', 'Chief', 'President', 'VP', 'Director', 'Head of']
            if any(title.lower() in lead.title.lower() for title in executive_titles):
                score += self.lead_scoring_weights['title_match'] * 100
        
        # Company size
        if lead.company_size:
            try:
                size = int(lead.company_size.replace(',', '').replace('+', ''))
                if size >= 1000:
                    score += self.lead_scoring_weights['company_size'] * 100
                elif size >= 100:
                    score += self.lead_scoring_weights['company_size'] * 70
                else:
                    score += self.lead_scoring_weights['company_size'] * 40
            except:
                score += self.lead_scoring_weights['company_size'] * 50
        
        # Industry relevance
        if lead.industry:
            high_value_industries = ['Technology', 'Financial Services', 'Healthcare', 'Manufacturing']
            if any(industry.lower() in lead.industry.lower() for industry in high_value_industries):
                score += self.lead_scoring_weights['industry_relevance'] * 100
        
        # Apollo match score
        if lead.apollo_data and 'match_score' in lead.apollo_data:
            score += self.lead_scoring_weights['apollo_match_score'] * lead.apollo_data['match_score']
        
        # Email deliverability
        if lead.email and '@' in lead.email:
            domain = lead.email.split('@')[1]
            if not domain.endswith('.gmail.com') and not domain.endswith('.yahoo.com'):
                score += self.lead_scoring_weights['email_deliverability'] * 80
            else:
                score += self.lead_scoring_weights['email_deliverability'] * 50
        
        # LinkedIn profile completeness
        if lead.linkedin_url:
            score += self.lead_scoring_weights['linkedin_profile_completeness'] * 100
        
        return min(score, 100.0)  # Cap at 100
    
    def _calculate_engagement_score(self, lead: KlentyLead) -> float:
        """Calculate engagement score based on email interactions"""
        score = 0.0
        
        if lead.total_emails_sent > 0:
            # Open rate contribution
            if lead.total_emails_opened > 0:
                open_rate = lead.total_emails_opened / lead.total_emails_sent
                score += open_rate * 30
            
            # Click rate contribution
            if lead.total_emails_clicked > 0:
                click_rate = lead.total_emails_clicked / lead.total_emails_sent
                score += click_rate * 40
            
            # Reply rate contribution (most important)
            if lead.total_replies > 0:
                reply_rate = lead.total_replies / lead.total_emails_sent
                score += reply_rate * 30
        
        return min(score, 100.0)  # Cap at 100
    
    def _determine_qualification_status(self, lead_score: float, engagement_score: float) -> str:
        """Determine lead qualification status"""
        combined_score = (lead_score * 0.6) + (engagement_score * 0.4)
        
        if combined_score >= 80:
            return 'qualified'
        elif combined_score >= 60:
            return 'nurture'
        elif combined_score >= 40:
            return 'monitor'
        else:
            return 'cold'
    
    def _convert_to_executive_opportunity(self, lead: KlentyLead) -> bool:
        """Convert qualified lead to executive opportunity"""
        try:
            # Create executive opportunity
            opportunity = ExecutiveOpportunity(
                type=lead.opportunity_type or 'consulting',
                title=f"{lead.opportunity_type} opportunity at {lead.company}",
                company=lead.company,
                status='prospect',
                ai_match_score=lead.lead_score,
                source='klenty_automation',
                notes=f"Qualified lead from Klenty campaign: {lead.campaign_id}",
                decision_makers=[{
                    'name': lead.full_name,
                    'title': lead.title,
                    'email': lead.email,
                    'phone': lead.phone,
                    'linkedin': lead.linkedin_url
                }]
            )
            
            db.session.add(opportunity)
            db.session.flush()
            
            # Link opportunity to lead
            lead.executive_opportunity_id = opportunity.id
            
            return True
            
        except Exception as e:
            logger.error(f"Error converting lead to executive opportunity: {e}")
            return False
    
    def _personalize_content(self, lead: KlentyLead, content: str) -> str:
        """Personalize email content with lead data"""
        personalized = content
        
        # Basic personalization
        personalizations = {
            'first_name': lead.first_name or '',
            'last_name': lead.last_name or '',
            'full_name': lead.full_name or '',
            'company': lead.company or '',
            'title': lead.title or '',
            'industry': lead.industry or '',
            'location': lead.location or ''
        }
        
        for field, value in personalizations.items():
            pattern = self.personalization_patterns.get(field)
            if pattern:
                personalized = re.sub(pattern, value, personalized, flags=re.IGNORECASE)
        
        # Custom field personalization
        if lead.custom_fields:
            for field, value in lead.custom_fields.items():
                pattern = f"{{{{ {field} }}}}"
                personalized = personalized.replace(pattern, str(value))
        
        # Advanced personalization tokens from research
        if lead.personalization_tokens:
            for token, value in lead.personalization_tokens.items():
                pattern = f"{{{{ {token} }}}}"
                personalized = personalized.replace(pattern, str(value))
        
        return personalized
    
    def _send_email_via_smtp(self, email: KlentyEmail, html_content: Optional[str] = None) -> bool:
        """Send email via SMTP"""
        try:
            # For demo purposes, we'll simulate email sending
            # In production, this would use actual SMTP configuration
            logger.info(f"Sending email {email.email_id} to {email.lead.email}")
            logger.debug(f"Subject: {email.personalized_subject}")
            logger.debug(f"Content: {email.personalized_content[:100]}...")
            
            # Simulate successful sending
            return True
            
        except Exception as e:
            logger.error(f"Error sending email via SMTP: {e}")
            return False
    
    def _check_daily_email_limits(self, campaign: KlentyCampaign) -> bool:
        """Check if daily email limits are reached"""
        today = datetime.utcnow().date()
        
        # Count emails sent today for this campaign
        emails_sent_today = KlentyEmail.query.join(KlentyLead).filter(
            KlentyLead.campaign_id == campaign.campaign_id,
            KlentyEmail.sent_at >= today,
            KlentyEmail.status == KlentyEmailStatus.SENT.value
        ).count()
        
        return emails_sent_today < campaign.daily_email_limit
    
    def _calculate_next_send_time(self, delay_days: int, sending_days: List[str], 
                                 start_hour: int, end_hour: int, timezone: str) -> datetime:
        """Calculate next email send time based on campaign settings"""
        next_send = datetime.utcnow() + timedelta(days=delay_days)
        
        # Adjust for sending days and hours
        # This is a simplified implementation
        # In production, you would use proper timezone handling
        
        return next_send
    
    def _extract_personalization_tokens(self, research_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract personalization tokens from research data"""
        tokens = {}
        
        if 'key_insights' in research_data:
            tokens['research_insight'] = research_data['key_insights'][0] if research_data['key_insights'] else ''
        
        if 'company_news' in research_data:
            tokens['recent_news'] = research_data['company_news'][0] if research_data['company_news'] else ''
        
        if 'industry_trends' in research_data:
            tokens['industry_trend'] = research_data['industry_trends'][0] if research_data['industry_trends'] else ''
        
        return tokens
    
    def _process_email_open(self, email: KlentyEmail, lead: KlentyLead, webhook_data: Dict, timestamp: str):
        """Process email open event"""
        if not email.first_opened_at:
            email.first_opened_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            email.status = KlentyEmailStatus.OPENED.value
            lead.first_email_opened_at = email.first_opened_at
            lead.status = KlentyLeadStatus.EMAIL_OPENED.value
        
        email.opened_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        email.open_count += 1
        lead.last_email_opened_at = email.opened_at
        lead.total_emails_opened += 1
    
    def _process_email_click(self, email: KlentyEmail, lead: KlentyLead, webhook_data: Dict, timestamp: str):
        """Process email click event"""
        if not email.first_clicked_at:
            email.first_clicked_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            email.status = KlentyEmailStatus.CLICKED.value
            lead.first_email_clicked_at = email.first_clicked_at
            lead.status = KlentyLeadStatus.EMAIL_CLICKED.value
        
        email.clicked_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        email.click_count += 1
        lead.last_email_clicked_at = email.clicked_at
        lead.total_emails_clicked += 1
        
        # Track clicked URLs
        if webhook_data.get('url'):
            if not email.clicked_links:
                email.clicked_links = []
            email.clicked_links.append(webhook_data['url'])
    
    def _process_email_reply(self, email: KlentyEmail, lead: KlentyLead, webhook_data: Dict, timestamp: str):
        """Process email reply event"""
        email.replied_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        email.reply_count += 1
        email.response_received = True
        email.response_content = webhook_data.get('reply_content', '')
        email.status = KlentyEmailStatus.REPLIED.value
        
        if not lead.first_reply_at:
            lead.first_reply_at = email.replied_at
        
        lead.last_reply_at = email.replied_at
        lead.total_replies += 1
        lead.status = KlentyLeadStatus.EMAIL_REPLIED.value
        
        # Stop sequence if configured to stop on reply
        sequence = KlentySequence.query.filter_by(sequence_id=lead.current_sequence_id).first()
        if sequence and sequence.stop_on_reply:
            lead.sequence_status = 'stopped'
            lead.next_email_scheduled_at = None
    
    def _process_email_bounce(self, email: KlentyEmail, lead: KlentyLead, webhook_data: Dict, timestamp: str):
        """Process email bounce event"""
        email.bounced_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        email.bounce_reason = webhook_data.get('bounce_reason', 'Unknown')
        email.status = KlentyEmailStatus.BOUNCED.value
        
        lead.status = KlentyLeadStatus.EMAIL_BOUNCED.value
        lead.sequence_status = 'stopped'
        lead.next_email_scheduled_at = None
    
    def _process_email_delivery(self, email: KlentyEmail, lead: KlentyLead, webhook_data: Dict, timestamp: str):
        """Process email delivery event"""
        email.delivered_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        if email.status == KlentyEmailStatus.SENT.value:
            email.status = KlentyEmailStatus.DELIVERED.value
    
    def _process_email_unsubscribe(self, email: KlentyEmail, lead: KlentyLead, webhook_data: Dict, timestamp: str):
        """Process email unsubscribe event"""
        lead.unsubscribed_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        lead.status = KlentyLeadStatus.UNSUBSCRIBED.value
        lead.sequence_status = 'stopped'
        lead.next_email_scheduled_at = None
    
    def _trigger_klenty_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger Make.com automation for Klenty events"""
        try:
            if self.automation_bridge:
                self.automation_bridge.trigger_event(f"klenty_{event_type}", event_data)
        except Exception as e:
            logger.error(f"Error triggering Klenty event {event_type}: {e}")
    
    def _calculate_open_rate(self, emails: List[KlentyEmail]) -> float:
        """Calculate email open rate"""
        sent_emails = [e for e in emails if e.status in [
            KlentyEmailStatus.SENT.value, 
            KlentyEmailStatus.DELIVERED.value,
            KlentyEmailStatus.OPENED.value,
            KlentyEmailStatus.CLICKED.value,
            KlentyEmailStatus.REPLIED.value
        ]]
        
        if not sent_emails:
            return 0.0
        
        opened_emails = [e for e in sent_emails if e.first_opened_at is not None]
        return (len(opened_emails) / len(sent_emails)) * 100
    
    def _calculate_click_rate(self, emails: List[KlentyEmail]) -> float:
        """Calculate email click rate"""
        sent_emails = [e for e in emails if e.status in [
            KlentyEmailStatus.SENT.value, 
            KlentyEmailStatus.DELIVERED.value,
            KlentyEmailStatus.OPENED.value,
            KlentyEmailStatus.CLICKED.value,
            KlentyEmailStatus.REPLIED.value
        ]]
        
        if not sent_emails:
            return 0.0
        
        clicked_emails = [e for e in sent_emails if e.first_clicked_at is not None]
        return (len(clicked_emails) / len(sent_emails)) * 100
    
    def _calculate_reply_rate(self, emails: List[KlentyEmail]) -> float:
        """Calculate email reply rate"""
        sent_emails = [e for e in emails if e.status in [
            KlentyEmailStatus.SENT.value, 
            KlentyEmailStatus.DELIVERED.value,
            KlentyEmailStatus.OPENED.value,
            KlentyEmailStatus.CLICKED.value,
            KlentyEmailStatus.REPLIED.value
        ]]
        
        if not sent_emails:
            return 0.0
        
        replied_emails = [e for e in sent_emails if e.replied_at is not None]
        return (len(replied_emails) / len(sent_emails)) * 100
    
    def _calculate_bounce_rate(self, emails: List[KlentyEmail]) -> float:
        """Calculate email bounce rate"""
        total_emails = len(emails)
        if not total_emails:
            return 0.0
        
        bounced_emails = [e for e in emails if e.status == KlentyEmailStatus.BOUNCED.value]
        return (len(bounced_emails) / total_emails) * 100
    
    def _calculate_unsubscribe_rate(self, leads: List[KlentyLead]) -> float:
        """Calculate unsubscribe rate"""
        total_leads = len(leads)
        if not total_leads:
            return 0.0
        
        unsubscribed_leads = [l for l in leads if l.status == KlentyLeadStatus.UNSUBSCRIBED.value]
        return (len(unsubscribed_leads) / total_leads) * 100
    
    def _calculate_conversion_rate(self, leads: List[KlentyLead]) -> float:
        """Calculate conversion rate"""
        total_leads = len(leads)
        if not total_leads:
            return 0.0
        
        converted_leads = [l for l in leads if l.status == KlentyLeadStatus.CONVERTED.value]
        return (len(converted_leads) / total_leads) * 100
    
    def _calculate_qualified_rate(self, leads: List[KlentyLead]) -> float:
        """Calculate qualified lead rate"""
        total_leads = len(leads)
        if not total_leads:
            return 0.0
        
        qualified_leads = [l for l in leads if l.qualification_status == 'qualified']
        return (len(qualified_leads) / total_leads) * 100
    
    def _generate_email_timeline_data(self, emails: List[KlentyEmail], 
                                     date_range: Optional[Tuple[datetime, datetime]]) -> List[Dict[str, Any]]:
        """Generate timeline data for email metrics"""
        timeline = []
        
        # Group emails by date
        from collections import defaultdict
        daily_stats = defaultdict(lambda: {
            'sent': 0, 'delivered': 0, 'opened': 0, 'clicked': 0, 'replied': 0, 'bounced': 0
        })
        
        for email in emails:
            if email.sent_at:
                date_key = email.sent_at.date().isoformat()
                daily_stats[date_key]['sent'] += 1
                
                if email.delivered_at:
                    daily_stats[date_key]['delivered'] += 1
                if email.first_opened_at:
                    daily_stats[date_key]['opened'] += 1
                if email.first_clicked_at:
                    daily_stats[date_key]['clicked'] += 1
                if email.replied_at:
                    daily_stats[date_key]['replied'] += 1
                if email.status == KlentyEmailStatus.BOUNCED.value:
                    daily_stats[date_key]['bounced'] += 1
        
        # Convert to timeline format
        for date, stats in sorted(daily_stats.items()):
            timeline.append({
                'date': date,
                **stats
            })
        
        return timeline

def create_klenty_automation_service(apollo_api=None, perplexity_api=None, automation_bridge=None, smtp_config=None):
    """Factory function to create Klenty automation service"""
    return KlentyAutomationService(apollo_api, perplexity_api, automation_bridge, smtp_config)