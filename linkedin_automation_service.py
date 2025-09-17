"""
LinkedIn Sales Navigator Automation Service
Comprehensive automation system for LinkedIn lead generation, outreach, and pipeline management
"""

import logging
import uuid
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

from database import db, ExecutiveOpportunity
from linkedin_models import (
    LinkedInCampaign, LinkedInLead, LinkedInMessage, LinkedInMessageTemplate,
    LinkedInAutomationRule, LinkedInAnalytics, LinkedInCampaignStatus,
    LinkedInLeadStatus, LinkedInMessageStatus
)

# Import existing services for integration
from apollo_integration import ApolloAPIWrapper, ApolloProspect
from perplexity_service import PerplexityResearchService, PerplexityAPI, PerplexityModel
from make_automation_bridges import AutomationBridgeService

logger = logging.getLogger(__name__)

@dataclass
class LinkedInSearchCriteria:
    """Search criteria for LinkedIn lead discovery"""
    keywords: Optional[str] = None
    titles: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    company_sizes: Optional[List[str]] = None
    connection_degree: Optional[str] = "2nd"  # 1st, 2nd, 3rd+
    premium_account_only: bool = False
    posted_recently: bool = False
    exclude_keywords: Optional[List[str]] = None

@dataclass
class OutreachSequence:
    """Outreach sequence configuration"""
    connection_message: Optional[str] = None
    initial_message: str = ""
    follow_up_messages: List[Dict[str, Any]] = None
    delay_between_messages: int = 3  # Days
    max_follow_ups: int = 2
    personalization_enabled: bool = True

class LinkedInAutomationService:
    """
    Main service class for LinkedIn Sales Navigator automation
    Integrates with Apollo.io, Perplexity AI, and Make.com automation bridges
    """
    
    def __init__(self, apollo_api: Optional[ApolloAPIWrapper] = None, 
                 perplexity_api: Optional[PerplexityAPI] = None,
                 automation_bridge: Optional[AutomationBridgeService] = None):
        self.apollo_api = apollo_api
        self.perplexity_api = perplexity_api
        self.perplexity_research = PerplexityResearchService(perplexity_api) if perplexity_api else None
        self.automation_bridge = automation_bridge
        
        # Default message templates
        self.default_templates = self._initialize_default_templates()
        
        # Lead scoring weights
        self.lead_scoring_weights = {
            'title_match': 0.25,
            'company_size': 0.20,
            'industry_relevance': 0.15,
            'apollo_match_score': 0.20,
            'linkedin_activity': 0.10,
            'mutual_connections': 0.10
        }
    
    def create_campaign(self, name: str, description: str, target_audience: Dict[str, Any],
                       created_by: str, **kwargs) -> Optional[LinkedInCampaign]:
        """
        Create a new LinkedIn automation campaign
        
        Args:
            name: Campaign name
            description: Campaign description
            target_audience: Search criteria and targeting parameters
            created_by: User creating the campaign
            **kwargs: Additional campaign configuration
            
        Returns:
            Created LinkedInCampaign or None if error
        """
        try:
            campaign_id = f"linkedin_campaign_{str(uuid.uuid4())[:8]}_{int(time.time())}"
            
            campaign = LinkedInCampaign(
                campaign_id=campaign_id,
                name=name,
                description=description,
                target_audience=target_audience,
                created_by=created_by,
                daily_connection_limit=kwargs.get('daily_connection_limit', 20),
                daily_message_limit=kwargs.get('daily_message_limit', 50),
                target_connections=kwargs.get('target_connections'),
                target_responses=kwargs.get('target_responses'),
                target_conversions=kwargs.get('target_conversions'),
                auto_connect=kwargs.get('auto_connect', True),
                auto_message=kwargs.get('auto_message', True),
                auto_follow_up=kwargs.get('auto_follow_up', True),
                connection_delay_hours=kwargs.get('connection_delay_hours', 24),
                message_delay_hours=kwargs.get('message_delay_hours', 48),
                follow_up_delay_days=kwargs.get('follow_up_delay_days', 7),
                apollo_integration_enabled=kwargs.get('apollo_integration_enabled', True),
                perplexity_research_enabled=kwargs.get('perplexity_research_enabled', True),
                make_automation_enabled=kwargs.get('make_automation_enabled', True)
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            # Create default message templates
            self._create_default_templates_for_campaign(campaign)
            
            logger.info(f"Created LinkedIn campaign: {campaign_id}")
            return campaign
            
        except Exception as e:
            logger.error(f"Error creating LinkedIn campaign: {e}")
            db.session.rollback()
            return None
    
    def discover_leads(self, campaign_id: str, search_criteria: LinkedInSearchCriteria,
                      limit: int = 100) -> List[LinkedInLead]:
        """
        Discover and import leads for a campaign (simulated LinkedIn search)
        
        Args:
            campaign_id: Campaign to add leads to
            search_criteria: LinkedIn search parameters
            limit: Maximum number of leads to discover
            
        Returns:
            List of discovered LinkedInLead objects
        """
        try:
            campaign = LinkedInCampaign.query.filter_by(campaign_id=campaign_id).first()
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return []
            
            # In a real implementation, this would scrape LinkedIn Sales Navigator
            # For this demo, we'll simulate lead discovery using Apollo.io data
            apollo_leads = self._discover_leads_via_apollo(search_criteria, limit)
            
            discovered_leads = []
            for apollo_lead in apollo_leads:
                # Convert Apollo prospect to LinkedIn lead
                linkedin_lead = self._convert_apollo_to_linkedin_lead(apollo_lead, campaign_id)
                if linkedin_lead:
                    discovered_leads.append(linkedin_lead)
            
            # Update campaign statistics
            campaign.total_prospects = len(discovered_leads)
            campaign.last_activity = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Discovered {len(discovered_leads)} leads for campaign {campaign_id}")
            return discovered_leads
            
        except Exception as e:
            logger.error(f"Error discovering leads: {e}")
            return []
    
    def enrich_lead_with_apollo(self, lead_id: str) -> bool:
        """
        Enrich LinkedIn lead with Apollo.io data
        
        Args:
            lead_id: LinkedIn lead ID to enrich
            
        Returns:
            True if enrichment successful, False otherwise
        """
        try:
            if not self.apollo_api:
                logger.warning("Apollo API not configured for lead enrichment")
                return False
            
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return False
            
            # Enrich using Apollo
            enrichment_data = self.apollo_api.enrich_person(
                first_name=lead.first_name,
                last_name=lead.last_name,
                organization_name=lead.current_company,
                domain=lead.company_domain
            )
            
            if enrichment_data and 'person' in enrichment_data:
                person_data = enrichment_data['person']
                
                # Update lead with enriched data
                lead.email = person_data.get('email')
                lead.phone = person_data.get('phone_numbers', [{}])[0].get('raw_number')
                lead.apollo_data = enrichment_data
                
                # Update company information
                if 'organization' in enrichment_data:
                    org_data = enrichment_data['organization']
                    lead.company_domain = org_data.get('website_url')
                    lead.company_size = org_data.get('employees_count')
                    lead.company_revenue = org_data.get('estimated_num_employees')
                
                # Calculate lead score based on enriched data
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
        Research LinkedIn lead using Perplexity AI for personalization insights
        
        Args:
            lead_id: LinkedIn lead ID to research
            
        Returns:
            True if research successful, False otherwise
        """
        try:
            if not self.perplexity_research:
                logger.warning("Perplexity API not configured for lead research")
                return False
            
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return False
            
            # Research executive for potential opportunities
            research_result = self.perplexity_research.research_executive_opportunity(
                executive_name=lead.full_name,
                company_name=lead.current_company,
                opportunity_type=lead.opportunity_type or "executive_engagement"
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
    
    def send_connection_request(self, lead_id: str, custom_message: Optional[str] = None) -> bool:
        """
        Send LinkedIn connection request to a lead
        
        Args:
            lead_id: LinkedIn lead ID
            custom_message: Optional custom connection message
            
        Returns:
            True if request sent successfully, False otherwise
        """
        try:
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return False
            
            # Check if connection already sent
            if lead.status != LinkedInLeadStatus.DISCOVERED.value:
                logger.warning(f"Connection already sent to lead {lead_id}")
                return False
            
            # Get campaign configuration
            campaign = lead.campaign
            if not campaign or not campaign.auto_connect:
                logger.warning(f"Auto-connect disabled for lead {lead_id}")
                return False
            
            # Check daily limits
            if not self._check_daily_connection_limit(campaign.campaign_id):
                logger.warning(f"Daily connection limit reached for campaign {campaign.campaign_id}")
                return False
            
            # Create connection message
            if not custom_message:
                custom_message = self._generate_connection_message(lead)
            
            # In a real implementation, this would send the connection request via LinkedIn API
            # For this demo, we'll simulate the action
            message = LinkedInMessage(
                message_id=f"conn_{lead_id}_{int(time.time())}",
                lead_id=lead_id,
                message_type="connection_request",
                content=custom_message,
                personalized_content=custom_message,
                status=LinkedInMessageStatus.SENT.value,
                automated=True,
                sent_at=datetime.utcnow()
            )
            
            # Update lead status
            lead.status = LinkedInLeadStatus.CONNECTION_SENT.value
            lead.connection_sent_at = datetime.utcnow()
            lead.last_activity_at = datetime.utcnow()
            
            # Update campaign statistics
            campaign.connections_sent += 1
            campaign.last_activity = datetime.utcnow()
            
            db.session.add(message)
            db.session.commit()
            
            # Trigger Make.com automation
            if campaign.make_automation_enabled and self.automation_bridge:
                self._trigger_linkedin_event("connection_sent", {
                    "lead_id": lead_id,
                    "campaign_id": campaign.campaign_id,
                    "message": custom_message,
                    "lead_data": lead.to_dict()
                })
            
            logger.info(f"Sent connection request to lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending connection request: {e}")
            db.session.rollback()
            return False
    
    def send_message(self, lead_id: str, message_content: str, message_type: str = "message") -> bool:
        """
        Send LinkedIn message to a lead
        
        Args:
            lead_id: LinkedIn lead ID
            message_content: Message content to send
            message_type: Type of message (message, inmail)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return False
            
            # Check if lead is connected
            if lead.status not in [LinkedInLeadStatus.CONNECTION_ACCEPTED.value, 
                                  LinkedInLeadStatus.MESSAGED.value, 
                                  LinkedInLeadStatus.REPLIED.value]:
                logger.warning(f"Cannot send message to unconnected lead {lead_id}")
                return False
            
            # Get campaign configuration
            campaign = lead.campaign
            if not campaign or not campaign.auto_message:
                logger.warning(f"Auto-message disabled for lead {lead_id}")
                return False
            
            # Check daily limits
            if not self._check_daily_message_limit(campaign.campaign_id):
                logger.warning(f"Daily message limit reached for campaign {campaign.campaign_id}")
                return False
            
            # Personalize message content
            personalized_content = self._personalize_message(lead, message_content)
            
            # In a real implementation, this would send the message via LinkedIn API
            # For this demo, we'll simulate the action
            message = LinkedInMessage(
                message_id=f"msg_{lead_id}_{int(time.time())}",
                lead_id=lead_id,
                message_type=message_type,
                content=message_content,
                personalized_content=personalized_content,
                status=LinkedInMessageStatus.SENT.value,
                automated=True,
                sent_at=datetime.utcnow()
            )
            
            # Update lead status and timing
            if lead.status == LinkedInLeadStatus.CONNECTION_ACCEPTED.value:
                lead.status = LinkedInLeadStatus.MESSAGED.value
                lead.first_message_sent_at = datetime.utcnow()
            
            lead.last_message_sent_at = datetime.utcnow()
            lead.last_activity_at = datetime.utcnow()
            
            # Update campaign statistics
            campaign.messages_sent += 1
            campaign.last_activity = datetime.utcnow()
            
            db.session.add(message)
            db.session.commit()
            
            # Trigger Make.com automation
            if campaign.make_automation_enabled and self.automation_bridge:
                self._trigger_linkedin_event("message_sent", {
                    "lead_id": lead_id,
                    "campaign_id": campaign.campaign_id,
                    "message": personalized_content,
                    "message_type": message_type,
                    "lead_data": lead.to_dict()
                })
            
            logger.info(f"Sent message to lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            db.session.rollback()
            return False
    
    def process_automation_rules(self, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process automation rules for LinkedIn campaigns
        
        Args:
            campaign_id: Optional specific campaign to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Get active automation rules
            rules_query = LinkedInAutomationRule.query.filter_by(active=True)
            if campaign_id:
                rules_query = rules_query.filter(
                    LinkedInAutomationRule.campaign_filter.contains({'campaign_id': campaign_id})
                )
            
            rules = rules_query.order_by(LinkedInAutomationRule.priority.desc()).all()
            
            results = {
                'processed_rules': 0,
                'executed_actions': 0,
                'errors': []
            }
            
            for rule in rules:
                try:
                    executed = self._execute_automation_rule(rule)
                    results['processed_rules'] += 1
                    if executed:
                        results['executed_actions'] += 1
                        
                except Exception as e:
                    error_msg = f"Error executing rule {rule.rule_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing automation rules: {e}")
            return {'error': str(e)}
    
    def qualify_lead(self, lead_id: str) -> Dict[str, Any]:
        """
        Qualify a LinkedIn lead using AI scoring and analysis
        
        Args:
            lead_id: LinkedIn lead ID to qualify
            
        Returns:
            Dictionary with qualification results
        """
        try:
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
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
                    lead.status = LinkedInLeadStatus.CONVERTED.value
            
            lead.last_updated = datetime.utcnow()
            db.session.commit()
            
            # Trigger Make.com automation for qualified leads
            if qualification_status == 'qualified' and self.automation_bridge:
                self._trigger_linkedin_event("lead_qualified", {
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
        Get comprehensive analytics for a LinkedIn campaign
        
        Args:
            campaign_id: Campaign ID to analyze
            date_range: Optional tuple of (start_date, end_date)
            
        Returns:
            Dictionary with campaign analytics
        """
        try:
            campaign = LinkedInCampaign.query.filter_by(campaign_id=campaign_id).first()
            if not campaign:
                return {'error': f'Campaign {campaign_id} not found'}
            
            # Build date filter
            date_filter = True
            if date_range:
                start_date, end_date = date_range
                date_filter = LinkedInLead.discovered_at.between(start_date, end_date)
            
            # Get campaign leads with date filter
            leads = LinkedInLead.query.filter_by(campaign_id=campaign_id).filter(date_filter).all()
            
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
                    'discovered': len([l for l in leads if l.status == LinkedInLeadStatus.DISCOVERED.value]),
                    'connection_sent': len([l for l in leads if l.status == LinkedInLeadStatus.CONNECTION_SENT.value]),
                    'connected': len([l for l in leads if l.status == LinkedInLeadStatus.CONNECTION_ACCEPTED.value]),
                    'messaged': len([l for l in leads if l.status == LinkedInLeadStatus.MESSAGED.value]),
                    'replied': len([l for l in leads if l.status == LinkedInLeadStatus.REPLIED.value]),
                    'qualified': len([l for l in leads if l.qualification_status == 'qualified']),
                    'converted': len([l for l in leads if l.status == LinkedInLeadStatus.CONVERTED.value])
                },
                'engagement_metrics': {
                    'connection_acceptance_rate': self._calculate_connection_acceptance_rate(leads),
                    'response_rate': self._calculate_response_rate(leads),
                    'qualification_rate': self._calculate_qualification_rate(leads),
                    'conversion_rate': self._calculate_conversion_rate(leads)
                },
                'performance_metrics': {
                    'average_lead_score': sum([l.lead_score for l in leads]) / len(leads) if leads else 0,
                    'average_engagement_score': sum([l.engagement_score for l in leads]) / len(leads) if leads else 0,
                    'total_messages_sent': sum([len(l.messages) for l in leads]),
                    'automation_efficiency': self._calculate_automation_efficiency(campaign)
                },
                'timeline_data': self._generate_timeline_data(leads, date_range)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting campaign analytics: {e}")
            return {'error': str(e)}
    
    # === PRIVATE HELPER METHODS ===
    
    def _discover_leads_via_apollo(self, search_criteria: LinkedInSearchCriteria, 
                                  limit: int) -> List[ApolloProspect]:
        """Discover leads using Apollo.io integration"""
        if not self.apollo_api:
            logger.warning("Apollo API not configured for lead discovery")
            return []
        
        try:
            # Convert LinkedIn search criteria to Apollo search parameters
            apollo_search_params = {
                'person_titles': search_criteria.titles,
                'organization_locations': search_criteria.locations,
                'keywords': search_criteria.keywords,
                'per_page': min(limit, 100)
            }
            
            # Remove None values
            apollo_search_params = {k: v for k, v in apollo_search_params.items() if v is not None}
            
            # Search for prospects
            search_result = self.apollo_api.search_people(**apollo_search_params)
            
            if search_result and 'people' in search_result:
                apollo_prospects = []
                for person_data in search_result['people']:
                    # Convert to ApolloProspect object
                    prospect = ApolloProspect(
                        id=person_data.get('id', ''),
                        first_name=person_data.get('first_name', ''),
                        last_name=person_data.get('last_name', ''),
                        name=f"{person_data.get('first_name', '')} {person_data.get('last_name', '')}".strip(),
                        email=person_data.get('email'),
                        phone=person_data.get('phone_numbers', [{}])[0].get('raw_number'),
                        title=person_data.get('title', ''),
                        linkedin_url=person_data.get('linkedin_url'),
                        company_name=person_data.get('organization', {}).get('name', ''),
                        company_domain=person_data.get('organization', {}).get('website_url'),
                        company_id=person_data.get('organization', {}).get('id'),
                        location=person_data.get('city', ''),
                        seniority=person_data.get('seniority'),
                        match_score=80.0,  # Default score
                        raw_data=person_data
                    )
                    apollo_prospects.append(prospect)
                
                return apollo_prospects[:limit]
            
            return []
            
        except Exception as e:
            logger.error(f"Error discovering leads via Apollo: {e}")
            return []
    
    def _convert_apollo_to_linkedin_lead(self, apollo_prospect: ApolloProspect, 
                                        campaign_id: str) -> Optional[LinkedInLead]:
        """Convert Apollo prospect to LinkedIn lead"""
        try:
            lead_id = f"linkedin_lead_{str(uuid.uuid4())[:8]}_{int(time.time())}"
            
            lead = LinkedInLead(
                lead_id=lead_id,
                campaign_id=campaign_id,
                linkedin_url=apollo_prospect.linkedin_url or f"https://linkedin.com/in/{apollo_prospect.name.lower().replace(' ', '-')}",
                first_name=apollo_prospect.first_name,
                last_name=apollo_prospect.last_name,
                full_name=apollo_prospect.name,
                headline=f"{apollo_prospect.title} at {apollo_prospect.company_name}",
                current_title=apollo_prospect.title,
                current_company=apollo_prospect.company_name,
                location=apollo_prospect.location,
                email=apollo_prospect.email,
                phone=apollo_prospect.phone,
                company_domain=apollo_prospect.company_domain,
                apollo_data=apollo_prospect.raw_data,
                lead_score=apollo_prospect.match_score,
                status=LinkedInLeadStatus.DISCOVERED.value,
                source='apollo_integration'
            )
            
            db.session.add(lead)
            return lead
            
        except Exception as e:
            logger.error(f"Error converting Apollo prospect to LinkedIn lead: {e}")
            return None
    
    def _calculate_lead_score(self, lead: LinkedInLead) -> float:
        """Calculate AI-powered lead score"""
        try:
            score = 0.0
            
            # Title relevance scoring
            if lead.current_title:
                title_score = self._score_title_relevance(lead.current_title)
                score += title_score * self.lead_scoring_weights['title_match']
            
            # Company size scoring
            if lead.company_size:
                company_score = self._score_company_size(lead.company_size)
                score += company_score * self.lead_scoring_weights['company_size']
            
            # Industry relevance
            if lead.industry:
                industry_score = self._score_industry_relevance(lead.industry)
                score += industry_score * self.lead_scoring_weights['industry_relevance']
            
            # Apollo match score
            if lead.apollo_data and 'match_score' in lead.apollo_data:
                apollo_score = float(lead.apollo_data['match_score']) / 100.0
                score += apollo_score * self.lead_scoring_weights['apollo_match_score']
            
            # LinkedIn activity (simulated)
            activity_score = 0.7  # Would be calculated from actual LinkedIn activity
            score += activity_score * self.lead_scoring_weights['linkedin_activity']
            
            # Mutual connections (simulated)
            connections_score = 0.5  # Would be calculated from actual mutual connections
            score += connections_score * self.lead_scoring_weights['mutual_connections']
            
            return min(score * 100, 100.0)  # Return score out of 100
            
        except Exception as e:
            logger.error(f"Error calculating lead score: {e}")
            return 0.0
    
    def _score_title_relevance(self, title: str) -> float:
        """Score title relevance for executive opportunities"""
        title_lower = title.lower()
        
        # High-value executive titles
        executive_keywords = ['ceo', 'cfo', 'cto', 'chief', 'president', 'vp', 'vice president', 
                             'director', 'head of', 'board', 'partner']
        
        # Risk/governance specific keywords
        grc_keywords = ['risk', 'compliance', 'audit', 'governance', 'regulatory']
        
        score = 0.0
        
        for keyword in executive_keywords:
            if keyword in title_lower:
                score += 0.3
        
        for keyword in grc_keywords:
            if keyword in title_lower:
                score += 0.4
        
        # C-suite gets highest score
        if any(c_title in title_lower for c_title in ['ceo', 'cfo', 'cto', 'chief']):
            score += 0.5
        
        return min(score, 1.0)
    
    def _score_company_size(self, company_size: str) -> float:
        """Score based on company size preference"""
        if not company_size:
            return 0.5
        
        # Convert company size to score (preferring larger companies)
        size_mapping = {
            'enterprise': 1.0,
            'large': 0.9,
            'medium': 0.7,
            'small': 0.5,
            'startup': 0.3
        }
        
        return size_mapping.get(company_size.lower(), 0.5)
    
    def _score_industry_relevance(self, industry: str) -> float:
        """Score industry relevance for target market"""
        if not industry:
            return 0.5
        
        industry_lower = industry.lower()
        
        # High-relevance industries for executive opportunities
        high_relevance = ['financial services', 'banking', 'insurance', 'healthcare', 
                         'technology', 'consulting', 'manufacturing']
        
        # Medium-relevance industries
        medium_relevance = ['retail', 'education', 'energy', 'real estate', 'media']
        
        for high_ind in high_relevance:
            if high_ind in industry_lower:
                return 1.0
        
        for med_ind in medium_relevance:
            if med_ind in industry_lower:
                return 0.7
        
        return 0.5  # Default score for other industries
    
    def _calculate_engagement_score(self, lead: LinkedInLead) -> float:
        """Calculate engagement score based on interactions"""
        try:
            score = 0.0
            
            # Connection acceptance
            if lead.connection_accepted_at:
                score += 30.0
            
            # Response to messages
            if lead.last_response_at:
                score += 40.0
                
                # Recent response gets higher score
                days_since_response = (datetime.utcnow() - lead.last_response_at).days
                if days_since_response <= 7:
                    score += 20.0
                elif days_since_response <= 30:
                    score += 10.0
            
            # Message sentiment analysis (simulated)
            messages = lead.messages
            positive_responses = len([m for m in messages if m.response_sentiment == 'positive'])
            if positive_responses > 0:
                score += min(positive_responses * 10, 30)
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0
    
    def _determine_qualification_status(self, lead_score: float, engagement_score: float) -> str:
        """Determine lead qualification status"""
        combined_score = (lead_score * 0.7) + (engagement_score * 0.3)
        
        if combined_score >= 80:
            return 'qualified'
        elif combined_score >= 60:
            return 'potential'
        elif combined_score >= 40:
            return 'developing'
        else:
            return 'unqualified'
    
    def _convert_to_executive_opportunity(self, lead: LinkedInLead) -> bool:
        """Convert qualified lead to executive opportunity"""
        try:
            # Create executive opportunity
            opportunity = ExecutiveOpportunity(
                title=f"{lead.opportunity_type} - {lead.current_company}",
                company=lead.current_company,
                type=lead.opportunity_type,
                status='lead_qualified',
                compensation_range='TBD',
                location=lead.location,
                source='linkedin_automation',
                linkedin_profile=lead.linkedin_url,
                apollo_email=lead.email,
                apollo_phone=lead.phone,
                ai_match_score=lead.opportunity_match_score,
                research_notes=json.dumps(lead.perplexity_research) if lead.perplexity_research else None
            )
            
            db.session.add(opportunity)
            db.session.commit()
            
            # Link lead to opportunity
            lead.executive_opportunity_id = opportunity.id
            
            logger.info(f"Converted lead {lead.lead_id} to executive opportunity {opportunity.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error converting lead to executive opportunity: {e}")
            db.session.rollback()
            return False
    
    def _generate_connection_message(self, lead: LinkedInLead) -> str:
        """Generate personalized connection message"""
        templates = [
            f"Hi {lead.first_name}, I'd like to connect with you as a fellow professional in {lead.industry}.",
            f"Hello {lead.first_name}, I'm interested in connecting with executives at {lead.current_company}.",
            f"Hi {lead.first_name}, I'd value the opportunity to connect and learn more about your work in {lead.current_title}."
        ]
        
        # Use personalization tokens if available
        if lead.personalization_tokens:
            return self._personalize_message(lead, templates[0])
        
        return templates[0]
    
    def _personalize_message(self, lead: LinkedInLead, message_template: str) -> str:
        """Personalize message using lead data and research"""
        try:
            personalized = message_template
            
            # Basic personalization
            placeholders = {
                '{first_name}': lead.first_name,
                '{last_name}': lead.last_name,
                '{full_name}': lead.full_name,
                '{company}': lead.current_company,
                '{title}': lead.current_title,
                '{industry}': lead.industry or 'your industry',
                '{location}': lead.location or 'your location'
            }
            
            for placeholder, value in placeholders.items():
                if placeholder in personalized and value:
                    personalized = personalized.replace(placeholder, value)
            
            # Advanced personalization using research data
            if lead.personalization_tokens:
                for token, value in lead.personalization_tokens.items():
                    placeholder = f"{{{token}}}"
                    if placeholder in personalized:
                        personalized = personalized.replace(placeholder, str(value))
            
            return personalized
            
        except Exception as e:
            logger.error(f"Error personalizing message: {e}")
            return message_template
    
    def _extract_personalization_tokens(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract personalization tokens from Perplexity research"""
        try:
            tokens = {}
            
            if 'analysis' in research_data:
                analysis = research_data['analysis']
                
                # Extract recent achievements, news, or initiatives
                if 'recent' in analysis.lower():
                    # Simple extraction - would be more sophisticated with NLP
                    sentences = analysis.split('.')
                    recent_info = [s.strip() for s in sentences if 'recent' in s.lower()]
                    if recent_info:
                        tokens['recent_activity'] = recent_info[0]
                
                # Extract company initiatives
                if 'initiative' in analysis.lower() or 'project' in analysis.lower():
                    sentences = analysis.split('.')
                    initiative_info = [s.strip() for s in sentences if any(word in s.lower() for word in ['initiative', 'project', 'program'])]
                    if initiative_info:
                        tokens['company_initiative'] = initiative_info[0]
            
            return tokens
            
        except Exception as e:
            logger.error(f"Error extracting personalization tokens: {e}")
            return {}
    
    def _check_daily_connection_limit(self, campaign_id: str) -> bool:
        """Check if daily connection limit has been reached"""
        try:
            campaign = LinkedInCampaign.query.filter_by(campaign_id=campaign_id).first()
            if not campaign:
                return False
            
            # Count connections sent today
            today = datetime.utcnow().date()
            connections_today = LinkedInLead.query.filter(
                LinkedInLead.campaign_id == campaign_id,
                LinkedInLead.connection_sent_at >= today
            ).count()
            
            return connections_today < campaign.daily_connection_limit
            
        except Exception as e:
            logger.error(f"Error checking daily connection limit: {e}")
            return False
    
    def _check_daily_message_limit(self, campaign_id: str) -> bool:
        """Check if daily message limit has been reached"""
        try:
            campaign = LinkedInCampaign.query.filter_by(campaign_id=campaign_id).first()
            if not campaign:
                return False
            
            # Count messages sent today
            today = datetime.utcnow().date()
            messages_today = LinkedInMessage.query.join(LinkedInLead).filter(
                LinkedInLead.campaign_id == campaign_id,
                LinkedInMessage.sent_at >= today
            ).count()
            
            return messages_today < campaign.daily_message_limit
            
        except Exception as e:
            logger.error(f"Error checking daily message limit: {e}")
            return False
    
    def _trigger_linkedin_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger LinkedIn automation event via Make.com"""
        try:
            if self.automation_bridge:
                self.automation_bridge.handle_internal_event(f"linkedin_{event_type}", event_data)
        except Exception as e:
            logger.error(f"Error triggering LinkedIn event: {e}")
    
    def _execute_automation_rule(self, rule: LinkedInAutomationRule) -> bool:
        """Execute a single automation rule"""
        try:
            # This would contain the rule execution logic
            # For now, return True to indicate successful execution
            rule.total_executions += 1
            rule.successful_executions += 1
            rule.last_execution = datetime.utcnow()
            return True
            
        except Exception as e:
            logger.error(f"Error executing automation rule {rule.rule_id}: {e}")
            rule.total_executions += 1
            return False
    
    def _calculate_connection_acceptance_rate(self, leads: List[LinkedInLead]) -> float:
        """Calculate connection acceptance rate"""
        sent = len([l for l in leads if l.connection_sent_at])
        accepted = len([l for l in leads if l.connection_accepted_at])
        return (accepted / sent * 100) if sent > 0 else 0.0
    
    def _calculate_response_rate(self, leads: List[LinkedInLead]) -> float:
        """Calculate message response rate"""
        messaged = len([l for l in leads if l.first_message_sent_at])
        responded = len([l for l in leads if l.last_response_at])
        return (responded / messaged * 100) if messaged > 0 else 0.0
    
    def _calculate_qualification_rate(self, leads: List[LinkedInLead]) -> float:
        """Calculate lead qualification rate"""
        total = len(leads)
        qualified = len([l for l in leads if l.qualification_status == 'qualified'])
        return (qualified / total * 100) if total > 0 else 0.0
    
    def _calculate_conversion_rate(self, leads: List[LinkedInLead]) -> float:
        """Calculate lead conversion rate"""
        total = len(leads)
        converted = len([l for l in leads if l.status == LinkedInLeadStatus.CONVERTED.value])
        return (converted / total * 100) if total > 0 else 0.0
    
    def _calculate_automation_efficiency(self, campaign: LinkedInCampaign) -> float:
        """Calculate automation efficiency percentage"""
        # This would calculate how much of the process is automated vs manual
        return 85.0  # Placeholder value
    
    def _generate_timeline_data(self, leads: List[LinkedInLead], 
                               date_range: Optional[Tuple[datetime, datetime]]) -> List[Dict[str, Any]]:
        """Generate timeline data for analytics"""
        # This would generate day-by-day activity data
        return []  # Placeholder - would contain actual timeline calculations
    
    def _initialize_default_templates(self) -> Dict[str, str]:
        """Initialize default message templates"""
        return {
            'connection_request': "Hi {first_name}, I'd like to connect with you as a fellow {industry} professional.",
            'first_message': "Hi {first_name}, thanks for connecting! I noticed your role as {title} at {company} and would love to learn more about your work.",
            'follow_up': "Hi {first_name}, I wanted to follow up on my previous message. Would you be interested in a brief conversation about {topic}?"
        }
    
    def _create_default_templates_for_campaign(self, campaign: LinkedInCampaign):
        """Create default message templates for a new campaign"""
        try:
            templates = [
                {
                    'name': 'Connection Request',
                    'template_type': 'connection_request',
                    'sequence_order': 1,
                    'delay_days': 0,
                    'message_content': self.default_templates['connection_request']
                },
                {
                    'name': 'First Message',
                    'template_type': 'first_message',
                    'sequence_order': 2,
                    'delay_days': 1,
                    'message_content': self.default_templates['first_message']
                },
                {
                    'name': 'Follow Up',
                    'template_type': 'follow_up',
                    'sequence_order': 3,
                    'delay_days': 7,
                    'message_content': self.default_templates['follow_up']
                }
            ]
            
            for template_data in templates:
                template = LinkedInMessageTemplate(
                    template_id=f"{campaign.campaign_id}_{template_data['template_type']}",
                    campaign_id=campaign.campaign_id,
                    **template_data
                )
                db.session.add(template)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error creating default templates: {e}")
            db.session.rollback()


# Factory functions
def create_linkedin_automation_service(apollo_api: Optional[ApolloAPIWrapper] = None,
                                     perplexity_api: Optional[PerplexityAPI] = None,
                                     automation_bridge: Optional[AutomationBridgeService] = None) -> LinkedInAutomationService:
    """Factory function to create LinkedIn automation service"""
    return LinkedInAutomationService(apollo_api, perplexity_api, automation_bridge)