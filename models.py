from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Float, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# This will be set from main.py
db = None

def init_db(database):
    global db
    db = database
    return db


class RevenueStream(db.Model):
    __tablename__ = 'revenue_streams'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    current_month: Mapped[float] = mapped_column(Float, nullable=False)
    target_month: Mapped[float] = mapped_column(Float, nullable=False)
    target_ytd: Mapped[float] = mapped_column(Float, nullable=False)
    ytd: Mapped[float] = mapped_column(Float, nullable=False)
    growth_rate: Mapped[float] = mapped_column(Float, nullable=False)
    sources: Mapped[list] = mapped_column(JSON, nullable=False)
    projections: Mapped[dict] = mapped_column(JSON, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'current_month': self.current_month,
            'target_month': self.target_month,
            'target_ytd': self.target_ytd,
            'ytd': self.ytd,
            'growth_rate': self.growth_rate,
            'sources': self.sources,
            'projections': self.projections,
            'last_updated': self.last_updated.isoformat()
        }


class AIAgent(db.Model):
    __tablename__ = 'ai_agents'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False)
    function: Mapped[str] = mapped_column(Text, nullable=False)
    tools: Mapped[list] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='active')
    performance: Mapped[dict] = mapped_column(JSON, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    next_scheduled: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    # Additional fields for specific agent types
    revenue_target: Mapped[str] = mapped_column(String(200), nullable=True)
    weekly_goal: Mapped[str] = mapped_column(String(200), nullable=True)
    targets: Mapped[list] = mapped_column(JSON, nullable=True)
    services: Mapped[list] = mapped_column(JSON, nullable=True)
    pricing: Mapped[str] = mapped_column(String(500), nullable=True)
    capabilities: Mapped[list] = mapped_column(JSON, nullable=True)
    coverage: Mapped[str] = mapped_column(String(200), nullable=True)
    output: Mapped[str] = mapped_column(String(500), nullable=True)
    goal: Mapped[str] = mapped_column(String(500), nullable=True)
    strategy: Mapped[str] = mapped_column(String(500), nullable=True)
    target: Mapped[str] = mapped_column(String(500), nullable=True)
    content: Mapped[list] = mapped_column(JSON, nullable=True)
    monetization: Mapped[str] = mapped_column(String(500), nullable=True)
    revenue: Mapped[str] = mapped_column(String(200), nullable=True)
    capability: Mapped[str] = mapped_column(String(500), nullable=True)
    licensing: Mapped[str] = mapped_column(String(200), nullable=True)
    connected_platforms: Mapped[list] = mapped_column(JSON, nullable=True)
    data_flow: Mapped[str] = mapped_column(String(200), nullable=True)
    analytics_focus: Mapped[list] = mapped_column(JSON, nullable=True)
    output_formats: Mapped[list] = mapped_column(JSON, nullable=True)
    crm_functions: Mapped[list] = mapped_column(JSON, nullable=True)
    optimization_areas: Mapped[list] = mapped_column(JSON, nullable=True)
    quality_metrics: Mapped[list] = mapped_column(JSON, nullable=True)
    monitoring_scope: Mapped[list] = mapped_column(JSON, nullable=True)
    coordination_areas: Mapped[list] = mapped_column(JSON, nullable=True)
    intelligence_outputs: Mapped[list] = mapped_column(JSON, nullable=True)
    research_areas: Mapped[list] = mapped_column(JSON, nullable=True)
    target_journals: Mapped[list] = mapped_column(JSON, nullable=True)
    media_types: Mapped[list] = mapped_column(JSON, nullable=True)
    target_outlets: Mapped[list] = mapped_column(JSON, nullable=True)
    conference_types: Mapped[list] = mapped_column(JSON, nullable=True)
    speaking_fees: Mapped[str] = mapped_column(String(200), nullable=True)
    content_types: Mapped[list] = mapped_column(JSON, nullable=True)
    distribution: Mapped[list] = mapped_column(JSON, nullable=True)
    target_roles: Mapped[list] = mapped_column(JSON, nullable=True)
    compensation: Mapped[str] = mapped_column(String(200), nullable=True)
    focus_roles: Mapped[list] = mapped_column(JSON, nullable=True)
    salary_range: Mapped[str] = mapped_column(String(200), nullable=True)
    partnership_types: Mapped[list] = mapped_column(JSON, nullable=True)
    revenue_potential: Mapped[str] = mapped_column(String(200), nullable=True)
    programs: Mapped[list] = mapped_column(JSON, nullable=True)
    subscription_tiers: Mapped[list] = mapped_column(JSON, nullable=True)
    focus_metrics: Mapped[list] = mapped_column(JSON, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'tier': self.tier,
            'function': self.function,
            'tools': self.tools or [],
            'status': self.status,
            'performance': self.performance or {},
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'next_scheduled': self.next_scheduled.isoformat() if self.next_scheduled else None,
            'revenue_target': self.revenue_target,
            'weekly_goal': self.weekly_goal,
            'targets': self.targets or [],
            'services': self.services or [],
            'pricing': self.pricing,
            'capabilities': self.capabilities or [],
            'coverage': self.coverage,
            'output': self.output,
            'goal': self.goal,
            'strategy': self.strategy,
            'target': self.target,
            'content': self.content or [],
            'monetization': self.monetization,
            'revenue': self.revenue,
            'capability': self.capability,
            'licensing': self.licensing,
            'connected_platforms': self.connected_platforms or [],
            'data_flow': self.data_flow,
            'analytics_focus': self.analytics_focus or [],
            'output_formats': self.output_formats or [],
            'crm_functions': self.crm_functions or [],
            'optimization_areas': self.optimization_areas or [],
            'quality_metrics': self.quality_metrics or [],
            'monitoring_scope': self.monitoring_scope or [],
            'coordination_areas': self.coordination_areas or [],
            'intelligence_outputs': self.intelligence_outputs or [],
            'research_areas': self.research_areas or [],
            'target_journals': self.target_journals or [],
            'media_types': self.media_types or [],
            'target_outlets': self.target_outlets or [],
            'conference_types': self.conference_types or [],
            'speaking_fees': self.speaking_fees,
            'content_types': self.content_types or [],
            'distribution': self.distribution or [],
            'target_roles': self.target_roles or [],
            'compensation': self.compensation,
            'focus_roles': self.focus_roles or [],
            'salary_range': self.salary_range,
            'partnership_types': self.partnership_types or [],
            'revenue_potential': self.revenue_potential,
            'programs': self.programs or [],
            'subscription_tiers': self.subscription_tiers or [],
            'focus_metrics': self.focus_metrics or []
        }


class HealthcareProvider(db.Model):
    __tablename__ = 'healthcare_providers'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    insurance_accepted: Mapped[list] = mapped_column(JSON, nullable=True)
    next_available: Mapped[str] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'specialty': self.specialty,
            'phone': self.phone,
            'address': self.address,
            'rating': self.rating,
            'insurance_accepted': self.insurance_accepted or [],
            'next_available': self.next_available,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class HealthcareAppointment(db.Model):
    __tablename__ = 'healthcare_appointments'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(200), nullable=False)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    time: Mapped[str] = mapped_column(String(20), nullable=False)
    purpose: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='scheduled')
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'date': self.date,
            'time': self.time,
            'purpose': self.purpose,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class HealthMetric(db.Model):
    __tablename__ = 'health_metrics'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='normal')
    target: Mapped[str] = mapped_column(String(100), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric': self.metric,
            'value': self.value,
            'unit': self.unit,
            'status': self.status,
            'target': self.target,
            'date': self.date.isoformat()
        }




class RetreatEvent(db.Model):
    __tablename__ = 'retreat_events'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    end_date: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    registered: Mapped[int] = mapped_column(Integer, default=0)
    price_per_person: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='planning')
    description: Mapped[str] = mapped_column(Text, nullable=True)
    amenities: Mapped[list] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'capacity': self.capacity,
            'registered': self.registered,
            'price_per_person': self.price_per_person,
            'status': self.status,
            'description': self.description,
            'amenities': self.amenities or [],
            'created_at': self.created_at.isoformat()
        }


class WellnessMetric(db.Model):
    __tablename__ = 'wellness_metrics'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    target: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    trend: Mapped[str] = mapped_column(String(20), default='stable')
    date_recorded: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'metric_name': self.metric_name,
            'value': self.value,
            'target': self.target,
            'unit': self.unit,
            'trend': self.trend,
            'date_recorded': self.date_recorded.isoformat(),
            'notes': self.notes
        }


class KPIMetric(db.Model):
    __tablename__ = 'kpi_metrics'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    target: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    trend: Mapped[str] = mapped_column(String(20), default='stable')
    change_percent: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    empire_focus: Mapped[str] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'target': self.target,
            'unit': self.unit,
            'trend': self.trend,
            'change_percent': self.change_percent,
            'category': self.category,
            'empire_focus': self.empire_focus,
            'last_updated': self.last_updated.isoformat()
        }


class Milestone(db.Model):
    __tablename__ = 'milestones'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_date: Mapped[str] = mapped_column(String(20), nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default='pending')
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'target_date': self.target_date,
            'progress': self.progress,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }


class EnergyTracking(db.Model):
    __tablename__ = 'energy_tracking'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    energy_level: Mapped[int] = mapped_column(Integer, nullable=False)
    focus_level: Mapped[int] = mapped_column(Integer, nullable=False)
    stress_level: Mapped[int] = mapped_column(Integer, nullable=False)
    sleep_hours: Mapped[float] = mapped_column(Float, nullable=False)
    recovery_time: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'energy_level': self.energy_level,
            'focus_level': self.focus_level,
            'stress_level': self.stress_level,
            'sleep_hours': self.sleep_hours,
            'recovery_time': self.recovery_time,
            'notes': self.notes
        }


class WellnessGoal(db.Model):
    __tablename__ = 'wellness_goals'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal: Mapped[str] = mapped_column(String(200), nullable=False)
    current: Mapped[float] = mapped_column(Float, nullable=False)
    target: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'goal': self.goal,
            'current': self.current,
            'target': self.target,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class WellnessAlert(db.Model):
    __tablename__ = 'wellness_alerts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'active': self.active,
            'created_at': self.created_at.isoformat()
        }


# ========================================
# Perplexity AI Integration Database Models
# ========================================

class PerplexityResearchResult(db.Model):
    __tablename__ = 'perplexity_research_results'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_type: Mapped[str] = mapped_column(String(100), nullable=False)  # market, company, industry, executive, competitive
    query: Mapped[str] = mapped_column(Text, nullable=False)  # The research query/prompt
    subject: Mapped[str] = mapped_column(String(300), nullable=False)  # Company name, industry, person name, etc.
    model_used: Mapped[str] = mapped_column(String(50), nullable=False)  # small, large, huge
    
    # Research results
    analysis: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    key_findings: Mapped[list] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list] = mapped_column(JSON, nullable=True)
    risk_factors: Mapped[list] = mapped_column(JSON, nullable=True)
    opportunities: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Metadata
    recency_used: Mapped[str] = mapped_column(String(20), nullable=True)  # hour, day, week, month, year
    sources_count: Mapped[int] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Raw data storage
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Status and timestamps
    status: Mapped[str] = mapped_column(String(50), default='completed')  # pending, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # For cache management
    
    def to_dict(self):
        return {
            'id': self.id,
            'research_type': self.research_type,
            'query': self.query,
            'subject': self.subject,
            'model_used': self.model_used,
            'analysis': self.analysis,
            'summary': self.summary,
            'key_findings': self.key_findings,
            'recommendations': self.recommendations,
            'risk_factors': self.risk_factors,
            'opportunities': self.opportunities,
            'recency_used': self.recency_used,
            'sources_count': self.sources_count,
            'confidence_score': self.confidence_score,
            'execution_time_ms': self.execution_time_ms,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class PerplexityInsight(db.Model):
    __tablename__ = 'perplexity_insights'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)  # governance, market_trend, risk_signal, opportunity
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # industry, company, executive, market
    
    # Core insight data
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact_level: Mapped[str] = mapped_column(String(20), nullable=False)  # low, medium, high, critical
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Context and associations
    related_subject: Mapped[str] = mapped_column(String(300), nullable=True)  # Company/person name
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Supporting data
    evidence: Mapped[list] = mapped_column(JSON, nullable=True)
    related_research_ids: Mapped[list] = mapped_column(JSON, nullable=True)  # References to research results
    
    # AI metadata
    generated_by_model: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Status and timestamps
    status: Mapped[str] = mapped_column(String(50), default='active')  # active, archived, outdated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_validated: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'insight_type': self.insight_type,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'impact_level': self.impact_level,
            'relevance_score': self.relevance_score,
            'related_subject': self.related_subject,
            'industry': self.industry,
            'tags': self.tags,
            'evidence': self.evidence,
            'related_research_ids': self.related_research_ids,
            'generated_by_model': self.generated_by_model,
            'confidence_level': self.confidence_level,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'last_validated': self.last_validated.isoformat() if self.last_validated else None
        }


class ProspectScoringResult(db.Model):
    __tablename__ = 'prospect_scoring_results'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Prospect information
    prospect_id: Mapped[str] = mapped_column(String(200), nullable=False)  # Apollo prospect ID or similar
    prospect_name: Mapped[str] = mapped_column(String(300), nullable=False)
    company_name: Mapped[str] = mapped_column(String(300), nullable=False)
    company_domain: Mapped[str] = mapped_column(String(200), nullable=True)
    prospect_title: Mapped[str] = mapped_column(String(300), nullable=True)
    opportunity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Scoring results
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    component_scores: Mapped[dict] = mapped_column(JSON, nullable=False)  # Individual component scores
    
    # Enhanced analysis results
    research_insights: Mapped[dict] = mapped_column(JSON, nullable=True)  # Company, role, market, opportunity insights
    content_briefs: Mapped[dict] = mapped_column(JSON, nullable=True)  # Generated content briefs
    analysis_summary: Mapped[str] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list] = mapped_column(JSON, nullable=True)
    risk_factors: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # AI metadata
    enhanced_analysis: Mapped[bool] = mapped_column(Boolean, default=False)  # Whether Perplexity enhancement was used
    models_used: Mapped[list] = mapped_column(JSON, nullable=True)  # List of AI models used
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Related research references
    related_research_ids: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Status and timestamps
    status: Mapped[str] = mapped_column(String(50), default='completed')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'prospect_id': self.prospect_id,
            'prospect_name': self.prospect_name,
            'company_name': self.company_name,
            'company_domain': self.company_domain,
            'prospect_title': self.prospect_title,
            'opportunity_type': self.opportunity_type,
            'final_score': self.final_score,
            'component_scores': self.component_scores,
            'research_insights': self.research_insights,
            'content_briefs': self.content_briefs,
            'analysis_summary': self.analysis_summary,
            'recommendations': self.recommendations,
            'risk_factors': self.risk_factors,
            'enhanced_analysis': self.enhanced_analysis,
            'models_used': self.models_used,
            'execution_time_ms': self.execution_time_ms,
            'related_research_ids': self.related_research_ids,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }


class ContentBrief(db.Model):
    __tablename__ = 'content_briefs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Content metadata
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)  # executive_summary, market_report, opportunity_brief, industry_insight
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    target_audience: Mapped[str] = mapped_column(String(300), nullable=True)
    
    # Content data
    executive_summary: Mapped[str] = mapped_column(Text, nullable=True)
    key_points: Mapped[list] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list] = mapped_column(JSON, nullable=True)
    call_to_action: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Full content
    full_content: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Context and associations
    related_subject: Mapped[str] = mapped_column(String(300), nullable=True)  # Company/prospect name
    opportunity_context: Mapped[str] = mapped_column(String(200), nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Source references
    source_research_ids: Mapped[list] = mapped_column(JSON, nullable=True)  # Related research results
    prospect_scoring_id: Mapped[int] = mapped_column(Integer, nullable=True)  # Related scoring result
    
    # AI generation metadata
    generated_by_model: Mapped[str] = mapped_column(String(50), nullable=False)
    generation_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Usage and engagement
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    last_viewed: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Status and timestamps
    status: Mapped[str] = mapped_column(String(50), default='draft')  # draft, ready, published, archived
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content_type': self.content_type,
            'title': self.title,
            'target_audience': self.target_audience,
            'executive_summary': self.executive_summary,
            'key_points': self.key_points,
            'recommendations': self.recommendations,
            'call_to_action': self.call_to_action,
            'full_content': self.full_content,
            'related_subject': self.related_subject,
            'opportunity_context': self.opportunity_context,
            'industry': self.industry,
            'source_research_ids': self.source_research_ids,
            'prospect_scoring_id': self.prospect_scoring_id,
            'generated_by_model': self.generated_by_model,
            'generation_prompt': self.generation_prompt,
            'quality_score': self.quality_score,
            'view_count': self.view_count,
            'last_viewed': self.last_viewed.isoformat() if self.last_viewed else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class OpportunityAnalysis(db.Model):
    __tablename__ = 'opportunity_analyses'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Opportunity context
    analysis_type: Mapped[str] = mapped_column(String(100), nullable=False)  # governance, speaking, market_entry
    subject_company: Mapped[str] = mapped_column(String(300), nullable=False)
    subject_domain: Mapped[str] = mapped_column(String(200), nullable=True)
    target_context: Mapped[str] = mapped_column(Text, nullable=True)  # Event context, market segment, etc.
    
    # Analysis results
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    strategic_fit: Mapped[float] = mapped_column(Float, nullable=True)
    value_potential: Mapped[float] = mapped_column(Float, nullable=True)
    execution_feasibility: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Detailed analysis
    governance_assessment: Mapped[dict] = mapped_column(JSON, nullable=True)
    market_conditions: Mapped[dict] = mapped_column(JSON, nullable=True)
    competitive_landscape: Mapped[dict] = mapped_column(JSON, nullable=True)
    entry_barriers: Mapped[list] = mapped_column(JSON, nullable=True)
    success_factors: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Recommendations and insights
    recommended_approach: Mapped[str] = mapped_column(Text, nullable=True)
    key_stakeholders: Mapped[list] = mapped_column(JSON, nullable=True)
    timeline_estimate: Mapped[str] = mapped_column(String(100), nullable=True)
    resource_requirements: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Risk assessment
    risk_factors: Mapped[list] = mapped_column(JSON, nullable=True)
    mitigation_strategies: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Source references
    source_research_ids: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # AI metadata
    analyzed_by_model: Mapped[str] = mapped_column(String(50), nullable=False)
    analysis_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Status and timestamps
    status: Mapped[str] = mapped_column(String(50), default='completed')  # pending, completed, reviewed, archived
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # Analysis validity period
    
    def to_dict(self):
        return {
            'id': self.id,
            'analysis_type': self.analysis_type,
            'subject_company': self.subject_company,
            'subject_domain': self.subject_domain,
            'target_context': self.target_context,
            'opportunity_score': self.opportunity_score,
            'strategic_fit': self.strategic_fit,
            'value_potential': self.value_potential,
            'execution_feasibility': self.execution_feasibility,
            'governance_assessment': self.governance_assessment,
            'market_conditions': self.market_conditions,
            'competitive_landscape': self.competitive_landscape,
            'entry_barriers': self.entry_barriers,
            'success_factors': self.success_factors,
            'recommended_approach': self.recommended_approach,
            'key_stakeholders': self.key_stakeholders,
            'timeline_estimate': self.timeline_estimate,
            'resource_requirements': self.resource_requirements,
            'risk_factors': self.risk_factors,
            'mitigation_strategies': self.mitigation_strategies,
            'source_research_ids': self.source_research_ids,
            'analyzed_by_model': self.analyzed_by_model,
            'analysis_prompt': self.analysis_prompt,
            'confidence_level': self.confidence_level,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class PerplexityAPIUsage(db.Model):
    __tablename__ = 'perplexity_api_usage'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Request metadata
    endpoint_used: Mapped[str] = mapped_column(String(200), nullable=False)
    model_used: Mapped[str] = mapped_column(String(50), nullable=False)
    request_type: Mapped[str] = mapped_column(String(100), nullable=False)  # research, content_generation, scoring
    
    # Usage metrics
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Cost tracking
    estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Request context
    user_context: Mapped[str] = mapped_column(String(300), nullable=True)  # User session or context
    related_prospect_id: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'endpoint_used': self.endpoint_used,
            'model_used': self.model_used,
            'request_type': self.request_type,
            'tokens_used': self.tokens_used,
            'response_time_ms': self.response_time_ms,
            'success': self.success,
            'error_message': self.error_message,
            'estimated_cost_usd': self.estimated_cost_usd,
            'user_context': self.user_context,
            'related_prospect_id': self.related_prospect_id,
            'created_at': self.created_at.isoformat()
        }