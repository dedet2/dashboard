"""
LinkedIn Sales Navigator Automation Models
Database models for LinkedIn lead generation, campaign management, and outreach automation
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Float, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import db
from typing import Dict, List, Optional, Any
from enum import Enum

# ===== LINKEDIN AUTOMATION CORE MODELS =====

class LinkedInCampaignStatus(Enum):
    """LinkedIn campaign status options"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class LinkedInLeadStatus(Enum):
    """LinkedIn lead status options"""
    DISCOVERED = "discovered"
    CONNECTION_SENT = "connection_sent"
    CONNECTION_ACCEPTED = "connection_accepted"
    MESSAGED = "messaged"
    REPLIED = "replied"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    NOT_INTERESTED = "not_interested"
    UNRESPONSIVE = "unresponsive"

class LinkedInMessageStatus(Enum):
    """LinkedIn message status options"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    FAILED = "failed"

class LinkedInCampaign(db.Model):
    """LinkedIn campaign management for automated outreach"""
    __tablename__ = 'linkedin_campaigns'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Campaign configuration
    status: Mapped[str] = mapped_column(String(50), default=LinkedInCampaignStatus.DRAFT.value)
    target_audience: Mapped[dict] = mapped_column(JSON, nullable=False)  # Search criteria and filters
    daily_connection_limit: Mapped[int] = mapped_column(Integer, default=20)  # LinkedIn limits
    daily_message_limit: Mapped[int] = mapped_column(Integer, default=50)
    
    # Campaign goals and metrics
    target_connections: Mapped[int] = mapped_column(Integer, nullable=True)
    target_responses: Mapped[int] = mapped_column(Integer, nullable=True)
    target_conversions: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Automation settings
    auto_connect: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_message: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_follow_up: Mapped[bool] = mapped_column(Boolean, default=True)
    connection_delay_hours: Mapped[int] = mapped_column(Integer, default=24)  # Hours between connections
    message_delay_hours: Mapped[int] = mapped_column(Integer, default=48)  # Hours after connection acceptance
    follow_up_delay_days: Mapped[int] = mapped_column(Integer, default=7)  # Days between follow-ups
    
    # Integration settings
    apollo_integration_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    perplexity_research_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    make_automation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Campaign statistics
    total_prospects: Mapped[int] = mapped_column(Integer, default=0)
    connections_sent: Mapped[int] = mapped_column(Integer, default=0)
    connections_accepted: Mapped[int] = mapped_column(Integer, default=0)
    messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    responses_received: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    leads = relationship("LinkedInLead", back_populates="campaign", cascade="all, delete-orphan")
    message_templates = relationship("LinkedInMessageTemplate", back_populates="campaign", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'target_audience': self.target_audience or {},
            'daily_connection_limit': self.daily_connection_limit,
            'daily_message_limit': self.daily_message_limit,
            'target_connections': self.target_connections,
            'target_responses': self.target_responses,
            'target_conversions': self.target_conversions,
            'auto_connect': self.auto_connect,
            'auto_message': self.auto_message,
            'auto_follow_up': self.auto_follow_up,
            'connection_delay_hours': self.connection_delay_hours,
            'message_delay_hours': self.message_delay_hours,
            'follow_up_delay_days': self.follow_up_delay_days,
            'apollo_integration_enabled': self.apollo_integration_enabled,
            'perplexity_research_enabled': self.perplexity_research_enabled,
            'make_automation_enabled': self.make_automation_enabled,
            'total_prospects': self.total_prospects,
            'connections_sent': self.connections_sent,
            'connections_accepted': self.connections_accepted,
            'messages_sent': self.messages_sent,
            'responses_received': self.responses_received,
            'conversions': self.conversions,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }

class LinkedInLead(db.Model):
    """LinkedIn lead/prospect management with enriched data"""
    __tablename__ = 'linkedin_leads'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(100), ForeignKey('linkedin_campaigns.campaign_id'), nullable=False)
    
    # LinkedIn profile information
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=False)
    linkedin_profile_id: Mapped[str] = mapped_column(String(200), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    headline: Mapped[str] = mapped_column(String(500), nullable=True)
    current_title: Mapped[str] = mapped_column(String(200), nullable=True)
    current_company: Mapped[str] = mapped_column(String(200), nullable=True)
    location: Mapped[str] = mapped_column(String(200), nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    profile_image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Contact information (from Apollo enrichment)
    email: Mapped[str] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    company_domain: Mapped[str] = mapped_column(String(200), nullable=True)
    company_size: Mapped[str] = mapped_column(String(100), nullable=True)
    company_revenue: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Lead status and engagement
    status: Mapped[str] = mapped_column(String(50), default=LinkedInLeadStatus.DISCOVERED.value)
    lead_score: Mapped[float] = mapped_column(Float, default=0.0)  # AI-calculated lead score
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    qualification_status: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Connection and outreach tracking
    connection_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    connection_accepted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    first_message_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_message_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_response_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Enrichment data
    apollo_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Enriched data from Apollo
    perplexity_research: Mapped[dict] = mapped_column(JSON, nullable=True)  # Research insights
    social_signals: Mapped[dict] = mapped_column(JSON, nullable=True)  # LinkedIn activity, posts, etc.
    
    # Personalization data
    personalization_tokens: Mapped[dict] = mapped_column(JSON, nullable=True)  # For message customization
    conversation_context: Mapped[dict] = mapped_column(JSON, nullable=True)  # Conversation history and context
    
    # Executive opportunity integration
    executive_opportunity_id: Mapped[int] = mapped_column(Integer, nullable=True)  # Link to ExecutiveOpportunity
    opportunity_type: Mapped[str] = mapped_column(String(100), nullable=True)  # board_director, speaker, consultant, etc.
    opportunity_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Automation flags
    auto_connect_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_message_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_follow_up_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source: Mapped[str] = mapped_column(String(100), default='linkedin_search')
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationships
    campaign = relationship("LinkedInCampaign", back_populates="leads")
    messages = relationship("LinkedInMessage", back_populates="lead", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'campaign_id': self.campaign_id,
            'linkedin_url': self.linkedin_url,
            'linkedin_profile_id': self.linkedin_profile_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'headline': self.headline,
            'current_title': self.current_title,
            'current_company': self.current_company,
            'location': self.location,
            'industry': self.industry,
            'profile_image_url': self.profile_image_url,
            'email': self.email,
            'phone': self.phone,
            'company_domain': self.company_domain,
            'company_size': self.company_size,
            'company_revenue': self.company_revenue,
            'status': self.status,
            'lead_score': self.lead_score,
            'engagement_score': self.engagement_score,
            'qualification_status': self.qualification_status,
            'connection_sent_at': self.connection_sent_at.isoformat() if self.connection_sent_at else None,
            'connection_accepted_at': self.connection_accepted_at.isoformat() if self.connection_accepted_at else None,
            'first_message_sent_at': self.first_message_sent_at.isoformat() if self.first_message_sent_at else None,
            'last_message_sent_at': self.last_message_sent_at.isoformat() if self.last_message_sent_at else None,
            'last_response_at': self.last_response_at.isoformat() if self.last_response_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'apollo_data': self.apollo_data or {},
            'perplexity_research': self.perplexity_research or {},
            'social_signals': self.social_signals or {},
            'personalization_tokens': self.personalization_tokens or {},
            'conversation_context': self.conversation_context or {},
            'executive_opportunity_id': self.executive_opportunity_id,
            'opportunity_type': self.opportunity_type,
            'opportunity_match_score': self.opportunity_match_score,
            'auto_connect_enabled': self.auto_connect_enabled,
            'auto_message_enabled': self.auto_message_enabled,
            'auto_follow_up_enabled': self.auto_follow_up_enabled,
            'discovered_at': self.discovered_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'source': self.source,
            'notes': self.notes
        }

class LinkedInMessageTemplate(db.Model):
    """Message templates for automated LinkedIn outreach"""
    __tablename__ = 'linkedin_message_templates'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(100), ForeignKey('linkedin_campaigns.campaign_id'), nullable=False)
    
    # Template configuration
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)  # connection_request, first_message, follow_up
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)  # Order in message sequence
    delay_days: Mapped[int] = mapped_column(Integer, default=0)  # Days after previous message
    
    # Message content
    subject: Mapped[str] = mapped_column(String(200), nullable=True)  # For InMail messages
    message_content: Mapped[str] = mapped_column(Text, nullable=False)
    personalization_fields: Mapped[list] = mapped_column(JSON, nullable=True)  # Dynamic fields to personalize
    
    # Conditions for sending
    trigger_conditions: Mapped[dict] = mapped_column(JSON, nullable=True)  # Conditions to trigger this template
    target_audience_criteria: Mapped[dict] = mapped_column(JSON, nullable=True)  # Who should receive this template
    
    # Performance tracking
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    response_count: Mapped[int] = mapped_column(Integer, default=0)
    response_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Settings
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("LinkedInCampaign", back_populates="message_templates")
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'template_type': self.template_type,
            'sequence_order': self.sequence_order,
            'delay_days': self.delay_days,
            'subject': self.subject,
            'message_content': self.message_content,
            'personalization_fields': self.personalization_fields or [],
            'trigger_conditions': self.trigger_conditions or {},
            'target_audience_criteria': self.target_audience_criteria or {},
            'sent_count': self.sent_count,
            'response_count': self.response_count,
            'response_rate': self.response_rate,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class LinkedInMessage(db.Model):
    """Individual LinkedIn messages sent to leads"""
    __tablename__ = 'linkedin_messages'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    lead_id: Mapped[str] = mapped_column(String(100), ForeignKey('linkedin_leads.lead_id'), nullable=False)
    template_id: Mapped[str] = mapped_column(String(100), nullable=True)  # Reference to template used
    
    # Message details
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)  # connection_request, message, inmail
    subject: Mapped[str] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    personalized_content: Mapped[str] = mapped_column(Text, nullable=True)  # Final personalized version
    
    # Status and timing
    status: Mapped[str] = mapped_column(String(50), default=LinkedInMessageStatus.DRAFT.value)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    replied_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Response tracking
    response_received: Mapped[bool] = mapped_column(Boolean, default=False)
    response_content: Mapped[str] = mapped_column(Text, nullable=True)
    response_sentiment: Mapped[str] = mapped_column(String(50), nullable=True)  # positive, neutral, negative
    
    # Automation tracking
    automated: Mapped[bool] = mapped_column(Boolean, default=True)
    sequence_position: Mapped[int] = mapped_column(Integer, nullable=True)  # Position in message sequence
    
    # Error handling
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("LinkedInLead", back_populates="messages")
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'lead_id': self.lead_id,
            'template_id': self.template_id,
            'message_type': self.message_type,
            'subject': self.subject,
            'content': self.content,
            'personalized_content': self.personalized_content,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'replied_at': self.replied_at.isoformat() if self.replied_at else None,
            'response_received': self.response_received,
            'response_content': self.response_content,
            'response_sentiment': self.response_sentiment,
            'automated': self.automated,
            'sequence_position': self.sequence_position,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class LinkedInAutomationRule(db.Model):
    """Business rules for LinkedIn automation logic"""
    __tablename__ = 'linkedin_automation_rules'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Rule configuration
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # connection, messaging, qualification, escalation
    trigger_conditions: Mapped[dict] = mapped_column(JSON, nullable=False)  # When to trigger
    actions: Mapped[dict] = mapped_column(JSON, nullable=False)  # What actions to take
    
    # Targeting
    campaign_filter: Mapped[dict] = mapped_column(JSON, nullable=True)  # Which campaigns this applies to
    lead_criteria: Mapped[dict] = mapped_column(JSON, nullable=True)  # Lead characteristics to match
    
    # Execution settings
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)  # Higher priority rules execute first
    execution_limit: Mapped[int] = mapped_column(Integer, nullable=True)  # Max executions per day/hour
    
    # Performance tracking
    total_executions: Mapped[int] = mapped_column(Integer, default=0)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0)
    last_execution: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'rule_type': self.rule_type,
            'trigger_conditions': self.trigger_conditions or {},
            'actions': self.actions or {},
            'campaign_filter': self.campaign_filter or {},
            'lead_criteria': self.lead_criteria or {},
            'active': self.active,
            'priority': self.priority,
            'execution_limit': self.execution_limit,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class LinkedInAnalytics(db.Model):
    """Analytics and performance tracking for LinkedIn campaigns"""
    __tablename__ = 'linkedin_analytics'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analytics_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(100), nullable=True)  # Null for overall analytics
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # Date of analytics snapshot
    
    # Connection metrics
    connections_sent: Mapped[int] = mapped_column(Integer, default=0)
    connections_accepted: Mapped[int] = mapped_column(Integer, default=0)
    connections_declined: Mapped[int] = mapped_column(Integer, default=0)
    connection_acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Messaging metrics
    messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    messages_read: Mapped[int] = mapped_column(Integer, default=0)
    responses_received: Mapped[int] = mapped_column(Integer, default=0)
    response_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Engagement metrics
    profile_views: Mapped[int] = mapped_column(Integer, default=0)
    content_engagements: Mapped[int] = mapped_column(Integer, default=0)
    follow_ups_sent: Mapped[int] = mapped_column(Integer, default=0)
    
    # Conversion metrics
    qualified_leads: Mapped[int] = mapped_column(Integer, default=0)
    opportunities_created: Mapped[int] = mapped_column(Integer, default=0)
    pipeline_value: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Quality metrics
    average_lead_score: Mapped[float] = mapped_column(Float, default=0.0)
    average_engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    positive_response_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Cost metrics
    estimated_time_spent: Mapped[float] = mapped_column(Float, default=0.0)  # Hours
    automation_efficiency: Mapped[float] = mapped_column(Float, default=0.0)  # Percentage automated
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'analytics_id': self.analytics_id,
            'campaign_id': self.campaign_id,
            'date': self.date.isoformat(),
            'connections_sent': self.connections_sent,
            'connections_accepted': self.connections_accepted,
            'connections_declined': self.connections_declined,
            'connection_acceptance_rate': self.connection_acceptance_rate,
            'messages_sent': self.messages_sent,
            'messages_read': self.messages_read,
            'responses_received': self.responses_received,
            'response_rate': self.response_rate,
            'profile_views': self.profile_views,
            'content_engagements': self.content_engagements,
            'follow_ups_sent': self.follow_ups_sent,
            'qualified_leads': self.qualified_leads,
            'opportunities_created': self.opportunities_created,
            'pipeline_value': self.pipeline_value,
            'average_lead_score': self.average_lead_score,
            'average_engagement_score': self.average_engagement_score,
            'positive_response_rate': self.positive_response_rate,
            'estimated_time_spent': self.estimated_time_spent,
            'automation_efficiency': self.automation_efficiency,
            'created_at': self.created_at.isoformat()
        }