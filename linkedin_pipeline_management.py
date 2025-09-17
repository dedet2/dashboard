"""
LinkedIn Pipeline Management System
Comprehensive pipeline management for LinkedIn lead generation, tracking leads from
discovery to conversion with advanced analytics, scoring, and integration orchestration
"""

import logging
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

from database import db, ExecutiveOpportunity
from linkedin_models import (
    LinkedInLead, LinkedInCampaign, LinkedInMessage, LinkedInAnalytics,
    LinkedInLeadStatus, LinkedInCampaignStatus
)
from linkedin_automation_service import LinkedInAutomationService
from linkedin_qualification_engine import LinkedInQualificationEngine, QualificationLevel
from linkedin_outreach_workflows import OutreachWorkflowOrchestrator, WorkflowType
from apollo_integration import ApolloAPIWrapper
from perplexity_service import PerplexityAPI
from make_automation_bridges import AutomationBridgeService

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    """LinkedIn lead pipeline stages"""
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    OUTREACH = "outreach"
    ENGAGEMENT = "engagement"
    NURTURING = "nurturing"
    QUALIFIED = "qualified"
    OPPORTUNITY = "opportunity"
    CONVERTED = "converted"
    CLOSED_LOST = "closed_lost"

class LeadPriority(Enum):
    """Lead priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Alert types for pipeline events"""
    HOT_LEAD = "hot_lead"
    RESPONSE_RECEIVED = "response_received"
    QUALIFICATION_UPDATED = "qualification_updated"
    CONVERSION_READY = "conversion_ready"
    WORKFLOW_STALLED = "workflow_stalled"
    CAMPAIGN_MILESTONE = "campaign_milestone"

@dataclass
class PipelineMetrics:
    """Pipeline performance metrics"""
    total_leads: int
    leads_by_stage: Dict[str, int]
    leads_by_priority: Dict[str, int]
    conversion_rates: Dict[str, float]
    average_cycle_time: float
    pipeline_velocity: float
    qualification_rate: float
    response_rate: float
    opportunity_conversion_rate: float
    revenue_pipeline: float

@dataclass
class LeadInsight:
    """AI-generated insights for a lead"""
    lead_id: str
    insight_type: str
    title: str
    description: str
    confidence_score: float
    recommended_actions: List[str]
    priority_score: float
    created_at: datetime

@dataclass
class PipelineAlert:
    """Pipeline alert for important events"""
    alert_id: str
    alert_type: AlertType
    lead_id: Optional[str]
    campaign_id: Optional[str]
    title: str
    message: str
    priority: LeadPriority
    action_required: bool
    created_at: datetime
    acknowledged: bool = False

class LinkedInPipelineManager:
    """
    Central pipeline management system for LinkedIn automation
    Orchestrates all services and provides comprehensive pipeline analytics
    """
    
    def __init__(self, automation_service: Optional[LinkedInAutomationService] = None,
                 qualification_engine: Optional[LinkedInQualificationEngine] = None,
                 workflow_orchestrator: Optional[OutreachWorkflowOrchestrator] = None,
                 automation_bridge: Optional[AutomationBridgeService] = None):
        
        self.automation_service = automation_service
        self.qualification_engine = qualification_engine
        self.workflow_orchestrator = workflow_orchestrator
        self.automation_bridge = automation_bridge
        
        # Pipeline configuration
        self.stage_thresholds = {
            PipelineStage.QUALIFICATION: {'min_profile_completeness': 60.0},
            PipelineStage.OUTREACH: {'min_lead_score': 40.0},
            PipelineStage.ENGAGEMENT: {'connection_accepted': True},
            PipelineStage.NURTURING: {'first_message_sent': True},
            PipelineStage.QUALIFIED: {'qualification_status': 'qualified'},
            PipelineStage.OPPORTUNITY: {'opportunity_created': True},
            PipelineStage.CONVERTED: {'opportunity_status': 'accepted'}
        }
        
        # Priority scoring weights
        self.priority_weights = {
            'lead_score': 0.30,
            'engagement_score': 0.25,
            'qualification_level': 0.20,
            'response_recency': 0.15,
            'opportunity_potential': 0.10
        }
        
        # Active alerts storage
        self.active_alerts: List[PipelineAlert] = []
        
        # Pipeline analytics cache
        self.analytics_cache = {}
        self.cache_ttl = timedelta(minutes=15)
        self.last_cache_update = datetime.min
    
    def get_pipeline_overview(self, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive pipeline overview
        
        Args:
            campaign_id: Optional campaign filter
            
        Returns:
            Dictionary with pipeline overview data
        """
        try:
            # Get pipeline metrics
            metrics = self.get_pipeline_metrics(campaign_id)
            
            # Get recent activity
            recent_activity = self.get_recent_pipeline_activity(campaign_id, hours=24)
            
            # Get top priority leads
            priority_leads = self.get_priority_leads(campaign_id, limit=10)
            
            # Get active alerts
            alerts = self.get_active_alerts(campaign_id)
            
            # Get conversion funnel data
            funnel_data = self.get_conversion_funnel(campaign_id)
            
            # Get performance trends
            trends = self.get_pipeline_trends(campaign_id, days=30)
            
            return {
                'metrics': metrics,
                'recent_activity': recent_activity,
                'priority_leads': priority_leads,
                'active_alerts': alerts,
                'conversion_funnel': funnel_data,
                'trends': trends,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline overview: {e}")
            return {'error': str(e)}
    
    def get_pipeline_metrics(self, campaign_id: Optional[str] = None) -> PipelineMetrics:
        """
        Calculate comprehensive pipeline metrics
        
        Args:
            campaign_id: Optional campaign filter
            
        Returns:
            PipelineMetrics object with calculated metrics
        """
        try:
            # Check cache
            cache_key = f"metrics_{campaign_id or 'all'}"
            if self._is_cache_valid(cache_key):
                return self.analytics_cache[cache_key]
            
            # Build query
            query = LinkedInLead.query
            if campaign_id:
                query = query.filter_by(campaign_id=campaign_id)
            
            leads = query.all()
            
            if not leads:
                return PipelineMetrics(
                    total_leads=0,
                    leads_by_stage={},
                    leads_by_priority={},
                    conversion_rates={},
                    average_cycle_time=0.0,
                    pipeline_velocity=0.0,
                    qualification_rate=0.0,
                    response_rate=0.0,
                    opportunity_conversion_rate=0.0,
                    revenue_pipeline=0.0
                )
            
            # Calculate metrics
            total_leads = len(leads)
            
            # Leads by stage
            leads_by_stage = {}
            for stage in PipelineStage:
                stage_leads = [l for l in leads if self._get_lead_stage(l) == stage]
                leads_by_stage[stage.value] = len(stage_leads)
            
            # Leads by priority
            leads_by_priority = {}
            for priority in LeadPriority:
                priority_leads = [l for l in leads if self._calculate_lead_priority(l) == priority]
                leads_by_priority[priority.value] = len(priority_leads)
            
            # Conversion rates
            conversion_rates = self._calculate_conversion_rates(leads)
            
            # Cycle time metrics
            average_cycle_time = self._calculate_average_cycle_time(leads)
            pipeline_velocity = self._calculate_pipeline_velocity(leads)
            
            # Qualification and response rates
            qualification_rate = self._calculate_qualification_rate(leads)
            response_rate = self._calculate_response_rate(leads)
            opportunity_conversion_rate = self._calculate_opportunity_conversion_rate(leads)
            
            # Revenue pipeline
            revenue_pipeline = self._calculate_revenue_pipeline(leads)
            
            metrics = PipelineMetrics(
                total_leads=total_leads,
                leads_by_stage=leads_by_stage,
                leads_by_priority=leads_by_priority,
                conversion_rates=conversion_rates,
                average_cycle_time=average_cycle_time,
                pipeline_velocity=pipeline_velocity,
                qualification_rate=qualification_rate,
                response_rate=response_rate,
                opportunity_conversion_rate=opportunity_conversion_rate,
                revenue_pipeline=revenue_pipeline
            )
            
            # Cache results
            self.analytics_cache[cache_key] = metrics
            self.last_cache_update = datetime.utcnow()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating pipeline metrics: {e}")
            return PipelineMetrics(
                total_leads=0,
                leads_by_stage={},
                leads_by_priority={},
                conversion_rates={},
                average_cycle_time=0.0,
                pipeline_velocity=0.0,
                qualification_rate=0.0,
                response_rate=0.0,
                opportunity_conversion_rate=0.0,
                revenue_pipeline=0.0
            )
    
    def advance_lead_through_pipeline(self, lead_id: str) -> Dict[str, Any]:
        """
        Advance a lead through the pipeline based on current status and activities
        
        Args:
            lead_id: LinkedIn lead ID
            
        Returns:
            Dictionary with advancement results
        """
        try:
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                return {'error': f'Lead {lead_id} not found'}
            
            current_stage = self._get_lead_stage(lead)
            logger.info(f"Lead {lead_id} current stage: {current_stage.value}")
            
            # Determine next stage based on current status and activities
            next_stage = self._determine_next_stage(lead, current_stage)
            
            if next_stage != current_stage:
                # Update lead stage
                self._update_lead_stage(lead, next_stage)
                
                # Trigger appropriate workflows based on stage change
                self._trigger_stage_change_workflows(lead, current_stage, next_stage)
                
                # Create stage change alert if significant
                if self._is_significant_stage_change(current_stage, next_stage):
                    self._create_stage_change_alert(lead, current_stage, next_stage)
                
                logger.info(f"Advanced lead {lead_id} from {current_stage.value} to {next_stage.value}")
                
                return {
                    'status': 'advanced',
                    'previous_stage': current_stage.value,
                    'current_stage': next_stage.value,
                    'actions_triggered': True
                }
            
            return {
                'status': 'no_change',
                'current_stage': current_stage.value,
                'reason': 'advancement_criteria_not_met'
            }
            
        except Exception as e:
            logger.error(f"Error advancing lead through pipeline: {e}")
            return {'error': str(e)}
    
    def get_priority_leads(self, campaign_id: Optional[str] = None, 
                          limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get prioritized list of leads requiring attention
        
        Args:
            campaign_id: Optional campaign filter
            limit: Maximum number of leads to return
            
        Returns:
            List of lead dictionaries with priority information
        """
        try:
            # Build query
            query = LinkedInLead.query
            if campaign_id:
                query = query.filter_by(campaign_id=campaign_id)
            
            leads = query.all()
            
            # Calculate priority scores and sort
            prioritized_leads = []
            for lead in leads:
                priority = self._calculate_lead_priority(lead)
                priority_score = self._calculate_priority_score(lead)
                
                lead_data = {
                    'lead': lead.to_dict(),
                    'priority': priority.value,
                    'priority_score': priority_score,
                    'stage': self._get_lead_stage(lead).value,
                    'insights': self._generate_lead_insights(lead),
                    'recommended_actions': self._get_recommended_actions(lead),
                    'next_action_date': self._calculate_next_action_date(lead)
                }
                prioritized_leads.append(lead_data)
            
            # Sort by priority score (highest first)
            prioritized_leads.sort(key=lambda x: x['priority_score'], reverse=True)
            
            return prioritized_leads[:limit]
            
        except Exception as e:
            logger.error(f"Error getting priority leads: {e}")
            return []
    
    def process_pipeline_automation(self) -> Dict[str, Any]:
        """
        Process automated pipeline actions and updates
        
        Returns:
            Dictionary with processing results
        """
        try:
            results = {
                'leads_processed': 0,
                'workflows_triggered': 0,
                'alerts_created': 0,
                'stages_advanced': 0,
                'errors': []
            }
            
            # Get all active leads
            active_leads = LinkedInLead.query.filter(
                LinkedInLead.status.in_([
                    LinkedInLeadStatus.DISCOVERED.value,
                    LinkedInLeadStatus.CONNECTION_SENT.value,
                    LinkedInLeadStatus.CONNECTION_ACCEPTED.value,
                    LinkedInLeadStatus.MESSAGED.value,
                    LinkedInLeadStatus.REPLIED.value
                ])
            ).all()
            
            for lead in active_leads:
                try:
                    # Process lead advancement
                    advancement_result = self.advance_lead_through_pipeline(lead.lead_id)
                    if advancement_result.get('status') == 'advanced':
                        results['stages_advanced'] += 1
                    
                    # Process qualification if needed
                    if self._needs_qualification_update(lead):
                        if self.qualification_engine:
                            self.qualification_engine.qualify_lead(lead.lead_id)
                            results['workflows_triggered'] += 1
                    
                    # Process workflow automation
                    if self.workflow_orchestrator:
                        workflow_result = self._process_lead_workflow_automation(lead)
                        if workflow_result.get('action_taken'):
                            results['workflows_triggered'] += 1
                    
                    # Check for alert conditions
                    alerts = self._check_lead_alert_conditions(lead)
                    results['alerts_created'] += len(alerts)
                    
                    results['leads_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing lead {lead.lead_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Process scheduled workflows
            if self.workflow_orchestrator:
                workflow_results = self.workflow_orchestrator.process_scheduled_workflows()
                results['workflows_triggered'] += workflow_results.get('processed_workflows', 0)
            
            # Update pipeline analytics
            self._update_pipeline_analytics()
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing pipeline automation: {e}")
            return {'error': str(e)}
    
    def create_lead_insight(self, lead_id: str, insight_type: str, 
                           title: str, description: str, 
                           confidence_score: float = 0.8) -> LeadInsight:
        """
        Create an AI-generated insight for a lead
        
        Args:
            lead_id: LinkedIn lead ID
            insight_type: Type of insight (opportunity, risk, engagement, etc.)
            title: Insight title
            description: Detailed description
            confidence_score: Confidence in the insight (0-1)
            
        Returns:
            LeadInsight object
        """
        try:
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Generate recommended actions based on insight type
            recommended_actions = self._generate_insight_actions(insight_type, lead)
            
            # Calculate priority score
            priority_score = self._calculate_insight_priority(insight_type, confidence_score, lead)
            
            insight = LeadInsight(
                lead_id=lead_id,
                insight_type=insight_type,
                title=title,
                description=description,
                confidence_score=confidence_score,
                recommended_actions=recommended_actions,
                priority_score=priority_score,
                created_at=datetime.utcnow()
            )
            
            # Store insight in lead's conversation context
            if not lead.conversation_context:
                lead.conversation_context = {}
            
            if 'insights' not in lead.conversation_context:
                lead.conversation_context['insights'] = []
            
            lead.conversation_context['insights'].append({
                'type': insight_type,
                'title': title,
                'description': description,
                'confidence': confidence_score,
                'actions': recommended_actions,
                'priority': priority_score,
                'created_at': insight.created_at.isoformat()
            })
            
            db.session.commit()
            
            logger.info(f"Created {insight_type} insight for lead {lead_id}")
            return insight
            
        except Exception as e:
            logger.error(f"Error creating lead insight: {e}")
            raise
    
    def get_conversion_funnel(self, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get conversion funnel analysis
        
        Args:
            campaign_id: Optional campaign filter
            
        Returns:
            Dictionary with funnel analysis
        """
        try:
            # Build query
            query = LinkedInLead.query
            if campaign_id:
                query = query.filter_by(campaign_id=campaign_id)
            
            leads = query.all()
            
            if not leads:
                return {'stages': [], 'conversion_rates': [], 'drop_off_points': []}
            
            # Define funnel stages
            funnel_stages = [
                ('Discovered', PipelineStage.DISCOVERY),
                ('Qualified', PipelineStage.QUALIFICATION),
                ('Outreach Started', PipelineStage.OUTREACH),
                ('Engaged', PipelineStage.ENGAGEMENT),
                ('Nurturing', PipelineStage.NURTURING),
                ('Qualified Lead', PipelineStage.QUALIFIED),
                ('Opportunity', PipelineStage.OPPORTUNITY),
                ('Converted', PipelineStage.CONVERTED)
            ]
            
            # Calculate leads at each stage
            stage_counts = []
            for stage_name, stage_enum in funnel_stages:
                count = len([l for l in leads if self._get_lead_stage(l) == stage_enum])
                stage_counts.append({
                    'stage': stage_name,
                    'count': count,
                    'percentage': (count / len(leads)) * 100 if leads else 0
                })
            
            # Calculate conversion rates between stages
            conversion_rates = []
            for i in range(len(stage_counts) - 1):
                current_count = stage_counts[i]['count']
                next_count = stage_counts[i + 1]['count']
                conversion_rate = (next_count / current_count) * 100 if current_count > 0 else 0
                
                conversion_rates.append({
                    'from_stage': stage_counts[i]['stage'],
                    'to_stage': stage_counts[i + 1]['stage'],
                    'conversion_rate': conversion_rate
                })
            
            # Identify drop-off points (stages with low conversion rates)
            drop_off_points = [cr for cr in conversion_rates if cr['conversion_rate'] < 50]
            drop_off_points.sort(key=lambda x: x['conversion_rate'])
            
            return {
                'stages': stage_counts,
                'conversion_rates': conversion_rates,
                'drop_off_points': drop_off_points,
                'total_leads': len(leads),
                'conversion_funnel_efficiency': self._calculate_funnel_efficiency(stage_counts)
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion funnel: {e}")
            return {'error': str(e)}
    
    def get_pipeline_trends(self, campaign_id: Optional[str] = None, 
                           days: int = 30) -> Dict[str, Any]:
        """
        Get pipeline performance trends over time
        
        Args:
            campaign_id: Optional campaign filter
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Build query
            query = LinkedInLead.query.filter(
                LinkedInLead.discovered_at >= start_date
            )
            if campaign_id:
                query = query.filter_by(campaign_id=campaign_id)
            
            leads = query.all()
            
            # Group leads by day
            daily_data = {}
            for lead in leads:
                day_key = lead.discovered_at.date().isoformat()
                if day_key not in daily_data:
                    daily_data[day_key] = {
                        'leads_discovered': 0,
                        'connections_sent': 0,
                        'connections_accepted': 0,
                        'messages_sent': 0,
                        'responses_received': 0,
                        'qualified_leads': 0
                    }
                
                daily_data[day_key]['leads_discovered'] += 1
                
                if lead.connection_sent_at and lead.connection_sent_at.date().isoformat() == day_key:
                    daily_data[day_key]['connections_sent'] += 1
                
                if lead.connection_accepted_at and lead.connection_accepted_at.date().isoformat() == day_key:
                    daily_data[day_key]['connections_accepted'] += 1
                
                if lead.first_message_sent_at and lead.first_message_sent_at.date().isoformat() == day_key:
                    daily_data[day_key]['messages_sent'] += 1
                
                if lead.last_response_at and lead.last_response_at.date().isoformat() == day_key:
                    daily_data[day_key]['responses_received'] += 1
                
                if lead.qualification_status == 'qualified':
                    daily_data[day_key]['qualified_leads'] += 1
            
            # Calculate trends
            trend_data = []
            for i in range(days):
                date = (start_date + timedelta(days=i)).date()
                day_key = date.isoformat()
                data = daily_data.get(day_key, {
                    'leads_discovered': 0,
                    'connections_sent': 0,
                    'connections_accepted': 0,
                    'messages_sent': 0,
                    'responses_received': 0,
                    'qualified_leads': 0
                })
                data['date'] = day_key
                trend_data.append(data)
            
            # Calculate moving averages
            window_size = min(7, len(trend_data))
            moving_averages = self._calculate_moving_averages(trend_data, window_size)
            
            return {
                'daily_data': trend_data,
                'moving_averages': moving_averages,
                'total_period': {
                    'days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'growth_rates': self._calculate_growth_rates(trend_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline trends: {e}")
            return {'error': str(e)}
    
    def get_active_alerts(self, campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get active pipeline alerts
        
        Args:
            campaign_id: Optional campaign filter
            
        Returns:
            List of alert dictionaries
        """
        try:
            # Filter alerts by campaign if specified
            filtered_alerts = self.active_alerts
            if campaign_id:
                filtered_alerts = [
                    alert for alert in self.active_alerts
                    if alert.campaign_id == campaign_id or (
                        alert.lead_id and 
                        self._get_lead_campaign_id(alert.lead_id) == campaign_id
                    )
                ]
            
            # Convert to dictionaries and sort by priority and recency
            alert_dicts = []
            for alert in filtered_alerts:
                if not alert.acknowledged:
                    alert_dict = {
                        'alert_id': alert.alert_id,
                        'alert_type': alert.alert_type.value,
                        'lead_id': alert.lead_id,
                        'campaign_id': alert.campaign_id,
                        'title': alert.title,
                        'message': alert.message,
                        'priority': alert.priority.value,
                        'action_required': alert.action_required,
                        'created_at': alert.created_at.isoformat(),
                        'age_hours': (datetime.utcnow() - alert.created_at).total_seconds() / 3600
                    }
                    alert_dicts.append(alert_dict)
            
            # Sort by priority (critical first) then by recency
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            alert_dicts.sort(key=lambda x: (priority_order.get(x['priority'], 4), x['age_hours']))
            
            return alert_dicts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge a pipeline alert
        
        Args:
            alert_id: Alert ID to acknowledge
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for alert in self.active_alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    logger.info(f"Acknowledged alert {alert_id}")
                    return True
            
            logger.warning(f"Alert {alert_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False
    
    def get_recent_pipeline_activity(self, campaign_id: Optional[str] = None, 
                                   hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent pipeline activity
        
        Args:
            campaign_id: Optional campaign filter
            hours: Number of hours to look back
            
        Returns:
            List of activity events
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Build query
            query = LinkedInLead.query.filter(
                LinkedInLead.last_updated >= cutoff_time
            )
            if campaign_id:
                query = query.filter_by(campaign_id=campaign_id)
            
            leads = query.order_by(LinkedInLead.last_updated.desc()).limit(50).all()
            
            activities = []
            for lead in leads:
                # Determine activity type based on recent changes
                activity_type = self._determine_activity_type(lead)
                
                activity = {
                    'lead_id': lead.lead_id,
                    'lead_name': lead.full_name,
                    'activity_type': activity_type,
                    'timestamp': lead.last_updated.isoformat(),
                    'details': self._get_activity_details(lead, activity_type),
                    'stage': self._get_lead_stage(lead).value,
                    'priority': self._calculate_lead_priority(lead).value
                }
                activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent pipeline activity: {e}")
            return []
    
    # === PRIVATE HELPER METHODS ===
    
    def _get_lead_stage(self, lead: LinkedInLead) -> PipelineStage:
        """Determine current pipeline stage for a lead"""
        try:
            # Check for conversion first
            if lead.status == LinkedInLeadStatus.CONVERTED.value:
                return PipelineStage.CONVERTED
            
            # Check for opportunity
            if lead.executive_opportunity_id:
                return PipelineStage.OPPORTUNITY
            
            # Check for qualification
            if lead.qualification_status == 'qualified':
                return PipelineStage.QUALIFIED
            
            # Check for nurturing (ongoing conversation)
            if lead.last_response_at:
                return PipelineStage.NURTURING
            
            # Check for engagement (connected and messaged)
            if (lead.status in [LinkedInLeadStatus.MESSAGED.value, LinkedInLeadStatus.REPLIED.value] and 
                lead.first_message_sent_at):
                return PipelineStage.ENGAGEMENT
            
            # Check for outreach (connection sent)
            if lead.status == LinkedInLeadStatus.CONNECTION_SENT.value:
                return PipelineStage.OUTREACH
            
            # Check for qualification (basic data available)
            if lead.lead_score > 0 or lead.apollo_data:
                return PipelineStage.QUALIFICATION
            
            # Default to discovery
            return PipelineStage.DISCOVERY
            
        except Exception as e:
            logger.error(f"Error determining lead stage: {e}")
            return PipelineStage.DISCOVERY
    
    def _determine_next_stage(self, lead: LinkedInLead, current_stage: PipelineStage) -> PipelineStage:
        """Determine if lead should advance to next stage"""
        try:
            # Check advancement criteria for each stage
            if current_stage == PipelineStage.DISCOVERY:
                # Can advance to qualification if we have basic data
                if lead.apollo_data or lead.lead_score > 0:
                    return PipelineStage.QUALIFICATION
            
            elif current_stage == PipelineStage.QUALIFICATION:
                # Can advance to outreach if qualified and not yet contacted
                if (lead.lead_score >= 40.0 and 
                    lead.status == LinkedInLeadStatus.DISCOVERED.value):
                    return PipelineStage.OUTREACH
            
            elif current_stage == PipelineStage.OUTREACH:
                # Can advance to engagement if connection accepted
                if lead.status == LinkedInLeadStatus.CONNECTION_ACCEPTED.value:
                    return PipelineStage.ENGAGEMENT
            
            elif current_stage == PipelineStage.ENGAGEMENT:
                # Can advance to nurturing if first message sent
                if lead.first_message_sent_at:
                    return PipelineStage.NURTURING
            
            elif current_stage == PipelineStage.NURTURING:
                # Can advance to qualified if qualification status updated
                if lead.qualification_status == 'qualified':
                    return PipelineStage.QUALIFIED
            
            elif current_stage == PipelineStage.QUALIFIED:
                # Can advance to opportunity if opportunity created
                if lead.executive_opportunity_id:
                    return PipelineStage.OPPORTUNITY
            
            elif current_stage == PipelineStage.OPPORTUNITY:
                # Can advance to converted if opportunity accepted
                opportunity = ExecutiveOpportunity.query.get(lead.executive_opportunity_id)
                if opportunity and opportunity.status == 'accepted':
                    return PipelineStage.CONVERTED
            
            return current_stage
            
        except Exception as e:
            logger.error(f"Error determining next stage: {e}")
            return current_stage
    
    def _calculate_lead_priority(self, lead: LinkedInLead) -> LeadPriority:
        """Calculate lead priority based on multiple factors"""
        try:
            priority_score = self._calculate_priority_score(lead)
            
            if priority_score >= 90:
                return LeadPriority.CRITICAL
            elif priority_score >= 75:
                return LeadPriority.HIGH
            elif priority_score >= 50:
                return LeadPriority.MEDIUM
            else:
                return LeadPriority.LOW
                
        except Exception as e:
            logger.error(f"Error calculating lead priority: {e}")
            return LeadPriority.LOW
    
    def _calculate_priority_score(self, lead: LinkedInLead) -> float:
        """Calculate numerical priority score"""
        try:
            score = 0.0
            
            # Lead score component
            if lead.lead_score:
                score += (lead.lead_score / 100.0) * self.priority_weights['lead_score'] * 100
            
            # Engagement score component
            if lead.engagement_score:
                score += (lead.engagement_score / 100.0) * self.priority_weights['engagement_score'] * 100
            
            # Qualification level component
            qualification_scores = {
                'hot_lead': 100,
                'qualified': 80,
                'potential': 60,
                'developing': 40,
                'unqualified': 20
            }
            qual_score = qualification_scores.get(lead.qualification_status, 20)
            score += (qual_score / 100.0) * self.priority_weights['qualification_level'] * 100
            
            # Response recency component
            if lead.last_response_at:
                days_since_response = (datetime.utcnow() - lead.last_response_at).days
                recency_score = max(0, 100 - (days_since_response * 5))  # Decay 5 points per day
                score += (recency_score / 100.0) * self.priority_weights['response_recency'] * 100
            
            # Opportunity potential component
            if lead.opportunity_match_score:
                score += (lead.opportunity_match_score / 100.0) * self.priority_weights['opportunity_potential'] * 100
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating priority score: {e}")
            return 0.0
    
    def _calculate_conversion_rates(self, leads: List[LinkedInLead]) -> Dict[str, float]:
        """Calculate conversion rates between stages"""
        try:
            if not leads:
                return {}
            
            # Count leads at each stage
            stage_counts = {}
            for stage in PipelineStage:
                stage_counts[stage] = len([l for l in leads if self._get_lead_stage(l) == stage])
            
            # Calculate conversion rates
            conversion_rates = {}
            
            # Discovery to Qualification
            if stage_counts[PipelineStage.DISCOVERY] > 0:
                qualified_count = sum(stage_counts[stage] for stage in PipelineStage if stage != PipelineStage.DISCOVERY)
                conversion_rates['discovery_to_qualification'] = (qualified_count / len(leads)) * 100
            
            # Outreach to Engagement
            outreach_and_beyond = sum(stage_counts[stage] for stage in [
                PipelineStage.OUTREACH, PipelineStage.ENGAGEMENT, PipelineStage.NURTURING,
                PipelineStage.QUALIFIED, PipelineStage.OPPORTUNITY, PipelineStage.CONVERTED
            ])
            if outreach_and_beyond > 0:
                engaged_count = sum(stage_counts[stage] for stage in [
                    PipelineStage.ENGAGEMENT, PipelineStage.NURTURING,
                    PipelineStage.QUALIFIED, PipelineStage.OPPORTUNITY, PipelineStage.CONVERTED
                ])
                conversion_rates['outreach_to_engagement'] = (engaged_count / outreach_and_beyond) * 100
            
            # Qualification to Opportunity
            qualified_count = stage_counts[PipelineStage.QUALIFIED] + stage_counts[PipelineStage.OPPORTUNITY] + stage_counts[PipelineStage.CONVERTED]
            if qualified_count > 0:
                opportunity_count = stage_counts[PipelineStage.OPPORTUNITY] + stage_counts[PipelineStage.CONVERTED]
                conversion_rates['qualified_to_opportunity'] = (opportunity_count / qualified_count) * 100
            
            # Opportunity to Conversion
            if stage_counts[PipelineStage.OPPORTUNITY] + stage_counts[PipelineStage.CONVERTED] > 0:
                conversion_rates['opportunity_to_conversion'] = (
                    stage_counts[PipelineStage.CONVERTED] / 
                    (stage_counts[PipelineStage.OPPORTUNITY] + stage_counts[PipelineStage.CONVERTED])
                ) * 100
            
            return conversion_rates
            
        except Exception as e:
            logger.error(f"Error calculating conversion rates: {e}")
            return {}
    
    def _calculate_average_cycle_time(self, leads: List[LinkedInLead]) -> float:
        """Calculate average time from discovery to conversion"""
        try:
            converted_leads = [l for l in leads if self._get_lead_stage(l) == PipelineStage.CONVERTED]
            
            if not converted_leads:
                return 0.0
            
            cycle_times = []
            for lead in converted_leads:
                # Find conversion date (would need to track stage transitions)
                # For now, use last_updated as proxy
                if lead.discovered_at and lead.last_updated:
                    cycle_time = (lead.last_updated - lead.discovered_at).total_seconds() / 86400  # Days
                    cycle_times.append(cycle_time)
            
            return statistics.mean(cycle_times) if cycle_times else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating average cycle time: {e}")
            return 0.0
    
    def _calculate_pipeline_velocity(self, leads: List[LinkedInLead]) -> float:
        """Calculate pipeline velocity (leads processed per day)"""
        try:
            if not leads:
                return 0.0
            
            # Get date range
            earliest_date = min(lead.discovered_at for lead in leads if lead.discovered_at)
            latest_date = max(lead.last_updated for lead in leads if lead.last_updated)
            
            if earliest_date and latest_date:
                days = (latest_date - earliest_date).days + 1
                return len(leads) / days if days > 0 else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating pipeline velocity: {e}")
            return 0.0
    
    def _calculate_qualification_rate(self, leads: List[LinkedInLead]) -> float:
        """Calculate percentage of leads that get qualified"""
        if not leads:
            return 0.0
        
        qualified_leads = len([l for l in leads if l.qualification_status in ['qualified', 'hot_lead']])
        return (qualified_leads / len(leads)) * 100
    
    def _calculate_response_rate(self, leads: List[LinkedInLead]) -> float:
        """Calculate response rate for outreach"""
        messaged_leads = [l for l in leads if l.first_message_sent_at]
        if not messaged_leads:
            return 0.0
        
        responded_leads = len([l for l in messaged_leads if l.last_response_at])
        return (responded_leads / len(messaged_leads)) * 100
    
    def _calculate_opportunity_conversion_rate(self, leads: List[LinkedInLead]) -> float:
        """Calculate opportunity conversion rate"""
        qualified_leads = [l for l in leads if l.qualification_status in ['qualified', 'hot_lead']]
        if not qualified_leads:
            return 0.0
        
        opportunity_leads = len([l for l in qualified_leads if l.executive_opportunity_id])
        return (opportunity_leads / len(qualified_leads)) * 100
    
    def _calculate_revenue_pipeline(self, leads: List[LinkedInLead]) -> float:
        """Calculate potential revenue in pipeline"""
        # This would integrate with opportunity value data
        # For now, return a simulated value based on qualified leads
        qualified_leads = len([l for l in leads if l.qualification_status in ['qualified', 'hot_lead']])
        average_opportunity_value = 50000  # Placeholder
        return qualified_leads * average_opportunity_value * 0.3  # 30% probability
    
    def _update_lead_stage(self, lead: LinkedInLead, new_stage: PipelineStage):
        """Update lead's pipeline stage"""
        # Store stage in conversation context for tracking
        if not lead.conversation_context:
            lead.conversation_context = {}
        
        if 'pipeline_history' not in lead.conversation_context:
            lead.conversation_context['pipeline_history'] = []
        
        lead.conversation_context['pipeline_history'].append({
            'stage': new_stage.value,
            'timestamp': datetime.utcnow().isoformat(),
            'automated': True
        })
        
        lead.last_updated = datetime.utcnow()
        db.session.commit()
    
    def _trigger_stage_change_workflows(self, lead: LinkedInLead, 
                                      previous_stage: PipelineStage, 
                                      new_stage: PipelineStage):
        """Trigger workflows based on stage changes"""
        try:
            if not self.workflow_orchestrator:
                return
            
            # Trigger appropriate workflows based on stage transitions
            if new_stage == PipelineStage.QUALIFIED:
                # Start VIP sequence for qualified leads
                self.workflow_orchestrator.start_workflow(
                    WorkflowType.VIP_SEQUENCE, 
                    lead.lead_id,
                    trigger_type='stage_change'
                )
            
            elif new_stage == PipelineStage.NURTURING and previous_stage == PipelineStage.ENGAGEMENT:
                # Start response nurture workflow
                self.workflow_orchestrator.start_workflow(
                    WorkflowType.RESPONSE_NURTURE,
                    lead.lead_id,
                    trigger_type='stage_change'
                )
            
        except Exception as e:
            logger.error(f"Error triggering stage change workflows: {e}")
    
    def _is_significant_stage_change(self, previous_stage: PipelineStage, 
                                   new_stage: PipelineStage) -> bool:
        """Check if stage change is significant enough for alert"""
        significant_transitions = [
            (PipelineStage.NURTURING, PipelineStage.QUALIFIED),
            (PipelineStage.QUALIFIED, PipelineStage.OPPORTUNITY),
            (PipelineStage.OPPORTUNITY, PipelineStage.CONVERTED)
        ]
        
        return (previous_stage, new_stage) in significant_transitions
    
    def _create_stage_change_alert(self, lead: LinkedInLead, 
                                 previous_stage: PipelineStage, 
                                 new_stage: PipelineStage):
        """Create alert for significant stage changes"""
        try:
            alert_id = f"stage_change_{lead.lead_id}_{int(datetime.utcnow().timestamp())}"
            
            if new_stage == PipelineStage.QUALIFIED:
                alert_type = AlertType.QUALIFICATION_UPDATED
                title = f"Lead Qualified: {lead.full_name}"
                message = f"{lead.full_name} from {lead.current_company} has been qualified as a hot lead"
                priority = LeadPriority.HIGH
            elif new_stage == PipelineStage.OPPORTUNITY:
                alert_type = AlertType.CONVERSION_READY
                title = f"Opportunity Created: {lead.full_name}"
                message = f"Executive opportunity created for {lead.full_name}"
                priority = LeadPriority.CRITICAL
            else:
                return
            
            alert = PipelineAlert(
                alert_id=alert_id,
                alert_type=alert_type,
                lead_id=lead.lead_id,
                campaign_id=lead.campaign_id,
                title=title,
                message=message,
                priority=priority,
                action_required=True,
                created_at=datetime.utcnow()
            )
            
            self.active_alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error creating stage change alert: {e}")
    
    def _needs_qualification_update(self, lead: LinkedInLead) -> bool:
        """Check if lead needs qualification update"""
        if not lead.qualification_status:
            return True
        
        # Check if last qualification was over a week ago
        if lead.last_updated < datetime.utcnow() - timedelta(days=7):
            return True
        
        # Check if significant new data is available
        if lead.apollo_data and not lead.perplexity_research:
            return True
        
        return False
    
    def _process_lead_workflow_automation(self, lead: LinkedInLead) -> Dict[str, Any]:
        """Process workflow automation for a lead"""
        try:
            # Check if lead needs workflow updates based on qualification
            qualification_result = self.workflow_orchestrator.update_workflow_based_on_qualification(lead.lead_id)
            
            return {
                'action_taken': qualification_result.get('status') != 'no_change_needed',
                'result': qualification_result
            }
            
        except Exception as e:
            logger.error(f"Error processing lead workflow automation: {e}")
            return {'action_taken': False, 'error': str(e)}
    
    def _check_lead_alert_conditions(self, lead: LinkedInLead) -> List[PipelineAlert]:
        """Check if lead meets any alert conditions"""
        alerts = []
        
        try:
            # Hot lead alert
            if (lead.qualification_status == 'hot_lead' and 
                not self._has_recent_alert(lead.lead_id, AlertType.HOT_LEAD)):
                
                alert_id = f"hot_lead_{lead.lead_id}_{int(datetime.utcnow().timestamp())}"
                alert = PipelineAlert(
                    alert_id=alert_id,
                    alert_type=AlertType.HOT_LEAD,
                    lead_id=lead.lead_id,
                    campaign_id=lead.campaign_id,
                    title=f"Hot Lead: {lead.full_name}",
                    message=f"{lead.full_name} from {lead.current_company} is a hot lead with score {lead.lead_score}",
                    priority=LeadPriority.CRITICAL,
                    action_required=True,
                    created_at=datetime.utcnow()
                )
                alerts.append(alert)
                self.active_alerts.append(alert)
            
            # Response received alert
            if (lead.last_response_at and 
                lead.last_response_at > datetime.utcnow() - timedelta(hours=2) and
                not self._has_recent_alert(lead.lead_id, AlertType.RESPONSE_RECEIVED)):
                
                alert_id = f"response_{lead.lead_id}_{int(datetime.utcnow().timestamp())}"
                alert = PipelineAlert(
                    alert_id=alert_id,
                    alert_type=AlertType.RESPONSE_RECEIVED,
                    lead_id=lead.lead_id,
                    campaign_id=lead.campaign_id,
                    title=f"Response Received: {lead.full_name}",
                    message=f"{lead.full_name} has responded to outreach",
                    priority=LeadPriority.HIGH,
                    action_required=True,
                    created_at=datetime.utcnow()
                )
                alerts.append(alert)
                self.active_alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error checking lead alert conditions: {e}")
        
        return alerts
    
    def _has_recent_alert(self, lead_id: str, alert_type: AlertType, hours: int = 24) -> bool:
        """Check if there's a recent alert of the same type for the lead"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for alert in self.active_alerts:
            if (alert.lead_id == lead_id and 
                alert.alert_type == alert_type and 
                alert.created_at > cutoff_time):
                return True
        
        return False
    
    def _update_pipeline_analytics(self):
        """Update pipeline analytics in database"""
        try:
            # Create analytics snapshot
            analytics_id = f"linkedin_analytics_{int(datetime.utcnow().timestamp())}"
            
            # Get overall metrics
            metrics = self.get_pipeline_metrics()
            
            analytics_record = LinkedInAnalytics(
                analytics_id=analytics_id,
                campaign_id=None,  # Overall analytics
                date=datetime.utcnow(),
                connections_sent=sum(metrics.leads_by_stage.get(stage, 0) 
                                   for stage in ['outreach', 'engagement', 'nurturing', 'qualified', 'opportunity', 'converted']),
                connections_accepted=sum(metrics.leads_by_stage.get(stage, 0) 
                                       for stage in ['engagement', 'nurturing', 'qualified', 'opportunity', 'converted']),
                messages_sent=sum(metrics.leads_by_stage.get(stage, 0) 
                                for stage in ['nurturing', 'qualified', 'opportunity', 'converted']),
                responses_received=int(metrics.response_rate * sum(metrics.leads_by_stage.get(stage, 0) 
                                                                  for stage in ['nurturing', 'qualified', 'opportunity', 'converted']) / 100),
                qualified_leads=metrics.leads_by_stage.get('qualified', 0),
                opportunities_created=metrics.leads_by_stage.get('opportunity', 0) + metrics.leads_by_stage.get('converted', 0),
                pipeline_value=metrics.revenue_pipeline,
                average_lead_score=metrics.qualification_rate,  # Placeholder
                automation_efficiency=85.0  # Placeholder
            )
            
            db.session.add(analytics_record)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating pipeline analytics: {e}")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        return (cache_key in self.analytics_cache and 
                datetime.utcnow() - self.last_cache_update < self.cache_ttl)
    
    def _generate_lead_insights(self, lead: LinkedInLead) -> List[Dict[str, Any]]:
        """Generate AI insights for a lead"""
        insights = []
        
        try:
            # High lead score insight
            if lead.lead_score >= 80:
                insights.append({
                    'type': 'opportunity',
                    'title': 'High-Quality Lead',
                    'description': f'Lead has exceptional score of {lead.lead_score}/100',
                    'confidence': 0.9
                })
            
            # Recent engagement insight
            if lead.last_response_at and lead.last_response_at > datetime.utcnow() - timedelta(days=3):
                insights.append({
                    'type': 'engagement',
                    'title': 'Recent Response',
                    'description': 'Lead has responded recently, showing active interest',
                    'confidence': 0.8
                })
            
            # Apollo data insight
            if lead.apollo_data and lead.apollo_data.get('email_status') == 'verified':
                insights.append({
                    'type': 'contact',
                    'title': 'Verified Contact',
                    'description': 'Email address verified through Apollo.io',
                    'confidence': 0.95
                })
            
        except Exception as e:
            logger.error(f"Error generating lead insights: {e}")
        
        return insights
    
    def _get_recommended_actions(self, lead: LinkedInLead) -> List[str]:
        """Get recommended actions for a lead"""
        actions = []
        
        try:
            stage = self._get_lead_stage(lead)
            priority = self._calculate_lead_priority(lead)
            
            if priority == LeadPriority.CRITICAL:
                actions.append("Schedule immediate outreach")
                actions.append("Prepare customized opportunity presentation")
            
            if stage == PipelineStage.QUALIFIED and not lead.executive_opportunity_id:
                actions.append("Create executive opportunity")
            
            if lead.last_response_at and not lead.conversation_context:
                actions.append("Analyze response sentiment")
                actions.append("Prepare personalized follow-up")
            
            if not lead.perplexity_research:
                actions.append("Conduct research for personalization")
            
        except Exception as e:
            logger.error(f"Error getting recommended actions: {e}")
        
        return actions
    
    def _calculate_next_action_date(self, lead: LinkedInLead) -> Optional[str]:
        """Calculate when next action should be taken"""
        try:
            stage = self._get_lead_stage(lead)
            priority = self._calculate_lead_priority(lead)
            
            # Calculate urgency based on priority and stage
            if priority == LeadPriority.CRITICAL:
                next_action = datetime.utcnow() + timedelta(hours=2)
            elif priority == LeadPriority.HIGH:
                next_action = datetime.utcnow() + timedelta(hours=24)
            elif stage == PipelineStage.QUALIFIED:
                next_action = datetime.utcnow() + timedelta(days=3)
            else:
                next_action = datetime.utcnow() + timedelta(days=7)
            
            return next_action.isoformat()
            
        except Exception as e:
            logger.error(f"Error calculating next action date: {e}")
            return None
    
    def _determine_activity_type(self, lead: LinkedInLead) -> str:
        """Determine activity type based on recent changes"""
        # This would analyze what changed recently
        # For now, return based on lead status
        status_activity_map = {
            LinkedInLeadStatus.DISCOVERED.value: 'lead_discovered',
            LinkedInLeadStatus.CONNECTION_SENT.value: 'connection_sent',
            LinkedInLeadStatus.CONNECTION_ACCEPTED.value: 'connection_accepted',
            LinkedInLeadStatus.MESSAGED.value: 'message_sent',
            LinkedInLeadStatus.REPLIED.value: 'response_received',
            LinkedInLeadStatus.QUALIFIED.value: 'lead_qualified',
            LinkedInLeadStatus.CONVERTED.value: 'opportunity_converted'
        }
        
        return status_activity_map.get(lead.status, 'status_updated')
    
    def _get_activity_details(self, lead: LinkedInLead, activity_type: str) -> Dict[str, Any]:
        """Get detailed information about activity"""
        details = {
            'company': lead.current_company,
            'title': lead.current_title,
            'lead_score': lead.lead_score,
            'qualification_status': lead.qualification_status
        }
        
        if activity_type == 'response_received' and lead.last_response_at:
            details['response_time'] = lead.last_response_at.isoformat()
        
        return details
    
    def _get_lead_campaign_id(self, lead_id: str) -> Optional[str]:
        """Get campaign ID for a lead"""
        lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
        return lead.campaign_id if lead else None
    
    def _calculate_funnel_efficiency(self, stage_counts: List[Dict[str, Any]]) -> float:
        """Calculate overall funnel efficiency"""
        if not stage_counts or len(stage_counts) < 2:
            return 0.0
        
        # Calculate efficiency as the ratio of converted leads to discovered leads
        discovered = stage_counts[0]['count'] if stage_counts else 0
        converted = stage_counts[-1]['count'] if stage_counts else 0
        
        return (converted / discovered * 100) if discovered > 0 else 0.0
    
    def _calculate_moving_averages(self, trend_data: List[Dict[str, Any]], 
                                 window_size: int) -> Dict[str, List[float]]:
        """Calculate moving averages for trend data"""
        try:
            metrics = ['leads_discovered', 'connections_sent', 'connections_accepted', 
                      'messages_sent', 'responses_received', 'qualified_leads']
            
            moving_averages = {}
            
            for metric in metrics:
                values = [day.get(metric, 0) for day in trend_data]
                ma_values = []
                
                for i in range(len(values)):
                    if i < window_size - 1:
                        # Not enough data for full window
                        ma_values.append(sum(values[:i+1]) / (i+1))
                    else:
                        # Full window available
                        window_values = values[i-window_size+1:i+1]
                        ma_values.append(sum(window_values) / window_size)
                
                moving_averages[metric] = ma_values
            
            return moving_averages
            
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return {}
    
    def _calculate_growth_rates(self, trend_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate growth rates for metrics"""
        try:
            if len(trend_data) < 2:
                return {}
            
            metrics = ['leads_discovered', 'connections_sent', 'qualified_leads']
            growth_rates = {}
            
            for metric in metrics:
                first_week = sum(day.get(metric, 0) for day in trend_data[:7])
                last_week = sum(day.get(metric, 0) for day in trend_data[-7:])
                
                if first_week > 0:
                    growth_rate = ((last_week - first_week) / first_week) * 100
                    growth_rates[f'{metric}_growth'] = growth_rate
            
            return growth_rates
            
        except Exception as e:
            logger.error(f"Error calculating growth rates: {e}")
            return {}
    
    def _generate_insight_actions(self, insight_type: str, lead: LinkedInLead) -> List[str]:
        """Generate recommended actions for an insight"""
        actions = []
        
        if insight_type == 'opportunity':
            actions.extend([
                "Prioritize immediate outreach",
                "Prepare executive-level conversation",
                "Research specific opportunity alignment"
            ])
        elif insight_type == 'engagement':
            actions.extend([
                "Respond promptly to maintain momentum",
                "Personalize next message based on response",
                "Consider phone call or video meeting"
            ])
        elif insight_type == 'risk':
            actions.extend([
                "Review engagement strategy",
                "Consider alternative approach",
                "Gather additional qualification data"
            ])
        
        return actions
    
    def _calculate_insight_priority(self, insight_type: str, confidence_score: float, 
                                  lead: LinkedInLead) -> float:
        """Calculate priority score for an insight"""
        base_score = confidence_score * 100
        
        # Boost based on insight type
        if insight_type == 'opportunity':
            base_score += 20
        elif insight_type == 'engagement':
            base_score += 15
        elif insight_type == 'risk':
            base_score += 10
        
        # Boost based on lead priority
        lead_priority = self._calculate_lead_priority(lead)
        if lead_priority == LeadPriority.CRITICAL:
            base_score += 25
        elif lead_priority == LeadPriority.HIGH:
            base_score += 15
        
        return min(base_score, 100.0)


# Factory function
def create_linkedin_pipeline_manager(automation_service: Optional[LinkedInAutomationService] = None,
                                   qualification_engine: Optional[LinkedInQualificationEngine] = None,
                                   workflow_orchestrator: Optional[OutreachWorkflowOrchestrator] = None,
                                   automation_bridge: Optional[AutomationBridgeService] = None) -> LinkedInPipelineManager:
    """Factory function to create LinkedIn pipeline manager"""
    return LinkedInPipelineManager(automation_service, qualification_engine, workflow_orchestrator, automation_bridge)