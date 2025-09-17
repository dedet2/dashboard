"""
Klenty SDRx Outreach Automation Models
Database models for email sequences, lead nurturing, and sales pipeline automation
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Float, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import db
from typing import Dict, List, Optional, Any
from enum import Enum

# ===== KLENTY AUTOMATION CORE MODELS =====

class KlentyCampaignStatus(Enum):
    """Klenty campaign status options"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class KlentyLeadStatus(Enum):
    """Klenty lead status options"""
    IMPORTED = "imported"
    EMAIL_SENT = "email_sent"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    EMAIL_REPLIED = "email_replied"
    EMAIL_BOUNCED = "email_bounced"
    UNSUBSCRIBED = "unsubscribed"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    NOT_INTERESTED = "not_interested"
    COLD = "cold"

class KlentyEmailStatus(Enum):
    """Klenty email status options"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"

class KlentySequenceStatus(Enum):
    """Klenty sequence status options"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class KlentyCampaign(db.Model):
    """Klenty campaign management for automated email outreach"""
    __tablename__ = 'klenty_campaigns'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Campaign configuration
    status: Mapped[str] = mapped_column(String(50), default=KlentyCampaignStatus.DRAFT.value)
    target_audience: Mapped[dict] = mapped_column(JSON, nullable=False)  # Targeting criteria
    daily_email_limit: Mapped[int] = mapped_column(Integer, default=100)  # Daily sending limits
    weekly_email_limit: Mapped[int] = mapped_column(Integer, default=500)
    
    # Campaign goals and metrics
    target_prospects: Mapped[int] = mapped_column(Integer, nullable=True)
    target_opens: Mapped[int] = mapped_column(Integer, nullable=True)
    target_clicks: Mapped[int] = mapped_column(Integer, nullable=True)
    target_replies: Mapped[int] = mapped_column(Integer, nullable=True)
    target_conversions: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Email sending settings
    sender_email: Mapped[str] = mapped_column(String(200), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(100), nullable=False)
    reply_to_email: Mapped[str] = mapped_column(String(200), nullable=True)
    time_zone: Mapped[str] = mapped_column(String(50), default='UTC')
    
    # Sending schedule
    sending_days: Mapped[list] = mapped_column(JSON, default=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
    sending_hours_start: Mapped[int] = mapped_column(Integer, default=9)  # 9 AM
    sending_hours_end: Mapped[int] = mapped_column(Integer, default=17)   # 5 PM
    
    # Integration settings
    linkedin_integration_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    apollo_enrichment_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    perplexity_research_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    make_automation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Campaign statistics
    total_prospects: Mapped[int] = mapped_column(Integer, default=0)
    emails_sent: Mapped[int] = mapped_column(Integer, default=0)
    emails_delivered: Mapped[int] = mapped_column(Integer, default=0)
    emails_opened: Mapped[int] = mapped_column(Integer, default=0)
    emails_clicked: Mapped[int] = mapped_column(Integer, default=0)
    emails_replied: Mapped[int] = mapped_column(Integer, default=0)
    emails_bounced: Mapped[int] = mapped_column(Integer, default=0)
    unsubscribes: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    
    # A/B testing
    ab_testing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    ab_test_variants: Mapped[dict] = mapped_column(JSON, nullable=True)  # A/B test configuration
    
    # Metadata
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    sequences = relationship("KlentySequence", back_populates="campaign", cascade="all, delete-orphan")
    leads = relationship("KlentyLead", back_populates="campaign", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'target_audience': self.target_audience or {},
            'daily_email_limit': self.daily_email_limit,
            'weekly_email_limit': self.weekly_email_limit,
            'target_prospects': self.target_prospects,
            'target_opens': self.target_opens,
            'target_clicks': self.target_clicks,
            'target_replies': self.target_replies,
            'target_conversions': self.target_conversions,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'reply_to_email': self.reply_to_email,
            'time_zone': self.time_zone,
            'sending_days': self.sending_days or [],
            'sending_hours_start': self.sending_hours_start,
            'sending_hours_end': self.sending_hours_end,
            'linkedin_integration_enabled': self.linkedin_integration_enabled,
            'apollo_enrichment_enabled': self.apollo_enrichment_enabled,
            'perplexity_research_enabled': self.perplexity_research_enabled,
            'make_automation_enabled': self.make_automation_enabled,
            'total_prospects': self.total_prospects,
            'emails_sent': self.emails_sent,
            'emails_delivered': self.emails_delivered,
            'emails_opened': self.emails_opened,
            'emails_clicked': self.emails_clicked,
            'emails_replied': self.emails_replied,
            'emails_bounced': self.emails_bounced,
            'unsubscribes': self.unsubscribes,
            'conversions': self.conversions,
            'ab_testing_enabled': self.ab_testing_enabled,
            'ab_test_variants': self.ab_test_variants or {},
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }

class KlentySequence(db.Model):
    """Email sequences for automated nurturing and follow-up"""
    __tablename__ = 'klenty_sequences'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sequence_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(100), ForeignKey('klenty_campaigns.campaign_id'), nullable=False)
    
    # Sequence configuration
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=KlentySequenceStatus.DRAFT.value)
    
    # Sequence behavior
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_between_emails: Mapped[int] = mapped_column(Integer, default=3)  # Days between emails
    stop_on_reply: Mapped[bool] = mapped_column(Boolean, default=True)
    stop_on_click: Mapped[bool] = mapped_column(Boolean, default=False)
    stop_on_open: Mapped[bool] = mapped_column(Boolean, default=False)
    stop_on_unsubscribe: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Targeting and filtering
    lead_criteria: Mapped[dict] = mapped_column(JSON, nullable=True)  # Which leads should enter this sequence
    priority: Mapped[int] = mapped_column(Integer, default=1)  # Sequence priority for scheduling
    
    # Performance tracking
    leads_entered: Mapped[int] = mapped_column(Integer, default=0)
    leads_completed: Mapped[int] = mapped_column(Integer, default=0)
    leads_stopped: Mapped[int] = mapped_column(Integer, default=0)
    total_emails_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_replies: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("KlentyCampaign", back_populates="sequences")
    templates = relationship("KlentyTemplate", back_populates="sequence", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'sequence_id': self.sequence_id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'total_steps': self.total_steps,
            'delay_between_emails': self.delay_between_emails,
            'stop_on_reply': self.stop_on_reply,
            'stop_on_click': self.stop_on_click,
            'stop_on_open': self.stop_on_open,
            'stop_on_unsubscribe': self.stop_on_unsubscribe,
            'lead_criteria': self.lead_criteria or {},
            'priority': self.priority,
            'leads_entered': self.leads_entered,
            'leads_completed': self.leads_completed,
            'leads_stopped': self.leads_stopped,
            'total_emails_sent': self.total_emails_sent,
            'total_replies': self.total_replies,
            'conversion_rate': self.conversion_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class KlentyLead(db.Model):
    """Klenty lead/prospect management with enriched data and outreach tracking"""
    __tablename__ = 'klenty_leads'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(100), ForeignKey('klenty_campaigns.campaign_id'), nullable=False)
    
    # Lead basic information
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=True)
    company: Mapped[str] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    location: Mapped[str] = mapped_column(String(200), nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Enriched company data
    company_domain: Mapped[str] = mapped_column(String(200), nullable=True)
    company_size: Mapped[str] = mapped_column(String(100), nullable=True)
    company_revenue: Mapped[str] = mapped_column(String(100), nullable=True)
    company_linkedin: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Social profiles
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=True)
    twitter_url: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Lead status and engagement
    status: Mapped[str] = mapped_column(String(50), default=KlentyLeadStatus.IMPORTED.value)
    lead_score: Mapped[float] = mapped_column(Float, default=0.0)  # AI-calculated lead score
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    qualification_status: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Email engagement tracking
    first_email_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_email_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    first_email_opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_email_opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    first_email_clicked_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_email_clicked_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    first_reply_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_reply_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    unsubscribed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Sequence tracking
    current_sequence_id: Mapped[str] = mapped_column(String(100), nullable=True)
    current_sequence_step: Mapped[int] = mapped_column(Integer, default=0)
    sequence_status: Mapped[str] = mapped_column(String(50), default='active')  # active, paused, completed, stopped
    next_email_scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Enrichment data
    apollo_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Enriched data from Apollo
    perplexity_research: Mapped[dict] = mapped_column(JSON, nullable=True)  # Research insights
    linkedin_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Data from LinkedIn integration
    
    # Personalization data
    personalization_tokens: Mapped[dict] = mapped_column(JSON, nullable=True)  # For email customization
    custom_fields: Mapped[dict] = mapped_column(JSON, nullable=True)  # Additional custom data
    
    # Executive opportunity integration
    executive_opportunity_id: Mapped[int] = mapped_column(Integer, nullable=True)  # Link to ExecutiveOpportunity
    opportunity_type: Mapped[str] = mapped_column(String(100), nullable=True)  # board_director, speaker, consultant, etc.
    opportunity_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Email preferences and behavior
    preferred_contact_time: Mapped[str] = mapped_column(String(50), nullable=True)  # morning, afternoon, evening
    response_style: Mapped[str] = mapped_column(String(50), nullable=True)  # formal, casual, technical
    email_frequency_preference: Mapped[str] = mapped_column(String(50), nullable=True)  # daily, weekly, monthly
    
    # Tracking and analytics
    total_emails_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_emails_opened: Mapped[int] = mapped_column(Integer, default=0)
    total_emails_clicked: Mapped[int] = mapped_column(Integer, default=0)
    total_replies: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source: Mapped[str] = mapped_column(String(100), default='manual_import')
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationships
    campaign = relationship("KlentyCampaign", back_populates="leads")
    emails = relationship("KlentyEmail", back_populates="lead", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'campaign_id': self.campaign_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'title': self.title,
            'company': self.company,
            'phone': self.phone,
            'location': self.location,
            'industry': self.industry,
            'company_domain': self.company_domain,
            'company_size': self.company_size,
            'company_revenue': self.company_revenue,
            'company_linkedin': self.company_linkedin,
            'linkedin_url': self.linkedin_url,
            'twitter_url': self.twitter_url,
            'status': self.status,
            'lead_score': self.lead_score,
            'engagement_score': self.engagement_score,
            'qualification_status': self.qualification_status,
            'first_email_sent_at': self.first_email_sent_at.isoformat() if self.first_email_sent_at else None,
            'last_email_sent_at': self.last_email_sent_at.isoformat() if self.last_email_sent_at else None,
            'first_email_opened_at': self.first_email_opened_at.isoformat() if self.first_email_opened_at else None,
            'last_email_opened_at': self.last_email_opened_at.isoformat() if self.last_email_opened_at else None,
            'first_email_clicked_at': self.first_email_clicked_at.isoformat() if self.first_email_clicked_at else None,
            'last_email_clicked_at': self.last_email_clicked_at.isoformat() if self.last_email_clicked_at else None,
            'first_reply_at': self.first_reply_at.isoformat() if self.first_reply_at else None,
            'last_reply_at': self.last_reply_at.isoformat() if self.last_reply_at else None,
            'unsubscribed_at': self.unsubscribed_at.isoformat() if self.unsubscribed_at else None,
            'current_sequence_id': self.current_sequence_id,
            'current_sequence_step': self.current_sequence_step,
            'sequence_status': self.sequence_status,
            'next_email_scheduled_at': self.next_email_scheduled_at.isoformat() if self.next_email_scheduled_at else None,
            'apollo_data': self.apollo_data or {},
            'perplexity_research': self.perplexity_research or {},
            'linkedin_data': self.linkedin_data or {},
            'personalization_tokens': self.personalization_tokens or {},
            'custom_fields': self.custom_fields or {},
            'executive_opportunity_id': self.executive_opportunity_id,
            'opportunity_type': self.opportunity_type,
            'opportunity_match_score': self.opportunity_match_score,
            'preferred_contact_time': self.preferred_contact_time,
            'response_style': self.response_style,
            'email_frequency_preference': self.email_frequency_preference,
            'total_emails_sent': self.total_emails_sent,
            'total_emails_opened': self.total_emails_opened,
            'total_emails_clicked': self.total_emails_clicked,
            'total_replies': self.total_replies,
            'imported_at': self.imported_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'source': self.source,
            'notes': self.notes
        }

class KlentyTemplate(db.Model):
    """Email templates for automated sequences"""
    __tablename__ = 'klenty_templates'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    sequence_id: Mapped[str] = mapped_column(String(100), ForeignKey('klenty_sequences.sequence_id'), nullable=False)
    
    # Template configuration
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Position in sequence
    delay_days: Mapped[int] = mapped_column(Integer, default=0)  # Days after previous email
    
    # Email content
    subject_line: Mapped[str] = mapped_column(String(300), nullable=False)
    email_body: Mapped[str] = mapped_column(Text, nullable=False)
    email_body_html: Mapped[str] = mapped_column(Text, nullable=True)  # HTML version
    
    # Personalization
    personalization_fields: Mapped[list] = mapped_column(JSON, nullable=True)  # Dynamic fields to personalize
    subject_personalization: Mapped[bool] = mapped_column(Boolean, default=True)
    dynamic_content_rules: Mapped[dict] = mapped_column(JSON, nullable=True)  # Conditional content
    
    # A/B testing
    is_ab_test: Mapped[bool] = mapped_column(Boolean, default=False)
    ab_test_variant: Mapped[str] = mapped_column(String(10), nullable=True)  # A, B, C, etc.
    ab_test_percentage: Mapped[float] = mapped_column(Float, default=50.0)  # Percentage for this variant
    
    # Sending conditions
    send_only_if: Mapped[dict] = mapped_column(JSON, nullable=True)  # Conditions to send this email
    skip_if: Mapped[dict] = mapped_column(JSON, nullable=True)  # Conditions to skip this email
    
    # Performance tracking
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    opened_count: Mapped[int] = mapped_column(Integer, default=0)
    clicked_count: Mapped[int] = mapped_column(Integer, default=0)
    replied_count: Mapped[int] = mapped_column(Integer, default=0)
    bounced_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Calculated metrics
    open_rate: Mapped[float] = mapped_column(Float, default=0.0)
    click_rate: Mapped[float] = mapped_column(Float, default=0.0)
    reply_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Settings
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sequence = relationship("KlentySequence", back_populates="templates")
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'sequence_id': self.sequence_id,
            'name': self.name,
            'step_number': self.step_number,
            'delay_days': self.delay_days,
            'subject_line': self.subject_line,
            'email_body': self.email_body,
            'email_body_html': self.email_body_html,
            'personalization_fields': self.personalization_fields or [],
            'subject_personalization': self.subject_personalization,
            'dynamic_content_rules': self.dynamic_content_rules or {},
            'is_ab_test': self.is_ab_test,
            'ab_test_variant': self.ab_test_variant,
            'ab_test_percentage': self.ab_test_percentage,
            'send_only_if': self.send_only_if or {},
            'skip_if': self.skip_if or {},
            'sent_count': self.sent_count,
            'opened_count': self.opened_count,
            'clicked_count': self.clicked_count,
            'replied_count': self.replied_count,
            'bounced_count': self.bounced_count,
            'open_rate': self.open_rate,
            'click_rate': self.click_rate,
            'reply_rate': self.reply_rate,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class KlentyEmail(db.Model):
    """Individual emails sent to leads"""
    __tablename__ = 'klenty_emails'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    lead_id: Mapped[str] = mapped_column(String(100), ForeignKey('klenty_leads.lead_id'), nullable=False)
    template_id: Mapped[str] = mapped_column(String(100), nullable=True)  # Reference to template used
    sequence_id: Mapped[str] = mapped_column(String(100), nullable=True)  # Reference to sequence
    
    # Email details
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=True)
    personalized_subject: Mapped[str] = mapped_column(String(300), nullable=True)  # Final personalized subject
    personalized_content: Mapped[str] = mapped_column(Text, nullable=True)  # Final personalized content
    
    # Sender information
    sender_email: Mapped[str] = mapped_column(String(200), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(100), nullable=False)
    reply_to_email: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Status and timing
    status: Mapped[str] = mapped_column(String(50), default=KlentyEmailStatus.DRAFT.value)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Engagement tracking
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    first_opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    
    clicked_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    first_clicked_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    clicked_links: Mapped[list] = mapped_column(JSON, nullable=True)  # URLs clicked
    
    replied_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    
    bounced_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    bounce_reason: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Response tracking
    response_received: Mapped[bool] = mapped_column(Boolean, default=False)
    response_content: Mapped[str] = mapped_column(Text, nullable=True)
    response_sentiment: Mapped[str] = mapped_column(String(50), nullable=True)  # positive, neutral, negative
    response_classification: Mapped[str] = mapped_column(String(50), nullable=True)  # interested, not_interested, meeting_request, etc.
    
    # Sequence tracking
    sequence_step: Mapped[int] = mapped_column(Integer, nullable=True)  # Position in sequence
    is_followup: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # A/B testing
    ab_test_variant: Mapped[str] = mapped_column(String(10), nullable=True)  # A, B, C, etc.
    
    # Email provider data
    provider_message_id: Mapped[str] = mapped_column(String(200), nullable=True)  # Provider's message ID
    provider_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Provider-specific data
    
    # Error handling
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("KlentyLead", back_populates="emails")
    
    def to_dict(self):
        return {
            'id': self.id,
            'email_id': self.email_id,
            'lead_id': self.lead_id,
            'template_id': self.template_id,
            'sequence_id': self.sequence_id,
            'subject': self.subject,
            'content': self.content,
            'content_html': self.content_html,
            'personalized_subject': self.personalized_subject,
            'personalized_content': self.personalized_content,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'reply_to_email': self.reply_to_email,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'first_opened_at': self.first_opened_at.isoformat() if self.first_opened_at else None,
            'open_count': self.open_count,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'first_clicked_at': self.first_clicked_at.isoformat() if self.first_clicked_at else None,
            'click_count': self.click_count,
            'clicked_links': self.clicked_links or [],
            'replied_at': self.replied_at.isoformat() if self.replied_at else None,
            'reply_count': self.reply_count,
            'bounced_at': self.bounced_at.isoformat() if self.bounced_at else None,
            'bounce_reason': self.bounce_reason,
            'response_received': self.response_received,
            'response_content': self.response_content,
            'response_sentiment': self.response_sentiment,
            'response_classification': self.response_classification,
            'sequence_step': self.sequence_step,
            'is_followup': self.is_followup,
            'ab_test_variant': self.ab_test_variant,
            'provider_message_id': self.provider_message_id,
            'provider_data': self.provider_data or {},
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class KlentyAutomationRule(db.Model):
    """Business rules for Klenty automation logic"""
    __tablename__ = 'klenty_automation_rules'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Rule configuration
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # lead_scoring, sequence_assignment, follow_up, escalation
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

class KlentyAnalytics(db.Model):
    """Analytics and performance tracking for Klenty campaigns"""
    __tablename__ = 'klenty_analytics'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analytics_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(100), nullable=True)  # Null for overall analytics
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # Date of analytics snapshot
    
    # Email metrics
    emails_sent: Mapped[int] = mapped_column(Integer, default=0)
    emails_delivered: Mapped[int] = mapped_column(Integer, default=0)
    emails_bounced: Mapped[int] = mapped_column(Integer, default=0)
    delivery_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Engagement metrics
    emails_opened: Mapped[int] = mapped_column(Integer, default=0)
    unique_opens: Mapped[int] = mapped_column(Integer, default=0)
    open_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    emails_clicked: Mapped[int] = mapped_column(Integer, default=0)
    unique_clicks: Mapped[int] = mapped_column(Integer, default=0)
    click_rate: Mapped[float] = mapped_column(Float, default=0.0)
    click_to_open_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Response metrics
    replies_received: Mapped[int] = mapped_column(Integer, default=0)
    positive_replies: Mapped[int] = mapped_column(Integer, default=0)
    negative_replies: Mapped[int] = mapped_column(Integer, default=0)
    neutral_replies: Mapped[int] = mapped_column(Integer, default=0)
    reply_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Unsubscribe metrics
    unsubscribes: Mapped[int] = mapped_column(Integer, default=0)
    unsubscribe_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Conversion metrics
    meetings_scheduled: Mapped[int] = mapped_column(Integer, default=0)
    opportunities_created: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Revenue metrics
    pipeline_value: Mapped[float] = mapped_column(Float, default=0.0)
    closed_deals: Mapped[int] = mapped_column(Integer, default=0)
    revenue_generated: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Sequence performance
    sequences_completed: Mapped[int] = mapped_column(Integer, default=0)
    sequences_stopped: Mapped[int] = mapped_column(Integer, default=0)
    average_sequence_length: Mapped[float] = mapped_column(Float, default=0.0)
    
    # A/B testing results
    ab_test_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # A/B test performance by variant
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'analytics_id': self.analytics_id,
            'campaign_id': self.campaign_id,
            'date': self.date.isoformat(),
            'emails_sent': self.emails_sent,
            'emails_delivered': self.emails_delivered,
            'emails_bounced': self.emails_bounced,
            'delivery_rate': self.delivery_rate,
            'emails_opened': self.emails_opened,
            'unique_opens': self.unique_opens,
            'open_rate': self.open_rate,
            'emails_clicked': self.emails_clicked,
            'unique_clicks': self.unique_clicks,
            'click_rate': self.click_rate,
            'click_to_open_rate': self.click_to_open_rate,
            'replies_received': self.replies_received,
            'positive_replies': self.positive_replies,
            'negative_replies': self.negative_replies,
            'neutral_replies': self.neutral_replies,
            'reply_rate': self.reply_rate,
            'unsubscribes': self.unsubscribes,
            'unsubscribe_rate': self.unsubscribe_rate,
            'meetings_scheduled': self.meetings_scheduled,
            'opportunities_created': self.opportunities_created,
            'conversions': self.conversions,
            'conversion_rate': self.conversion_rate,
            'pipeline_value': self.pipeline_value,
            'closed_deals': self.closed_deals,
            'revenue_generated': self.revenue_generated,
            'sequences_completed': self.sequences_completed,
            'sequences_stopped': self.sequences_stopped,
            'average_sequence_length': self.average_sequence_length,
            'ab_test_data': self.ab_test_data or {},
            'created_at': self.created_at.isoformat()
        }