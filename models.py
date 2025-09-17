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


class ExecutiveOpportunity(db.Model):
    __tablename__ = 'executive_opportunities'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    compensation_range: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='prospect')
    application_date: Mapped[str] = mapped_column(String(20), nullable=True)
    interview_stages: Mapped[list] = mapped_column(JSON, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    ai_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'type': self.type,
            'compensation_range': self.compensation_range,
            'status': self.status,
            'application_date': self.application_date,
            'interview_stages': self.interview_stages or [],
            'notes': self.notes,
            'ai_match_score': self.ai_match_score,
            'created_at': self.created_at.isoformat()
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