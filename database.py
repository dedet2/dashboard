from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Float, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()

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
    # Store additional fields as JSON for flexibility
    additional_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    def to_dict(self):
        result = {
            'id': self.id,
            'name': self.name,
            'tier': self.tier,
            'function': self.function,
            'tools': self.tools or [],
            'status': self.status,
            'performance': self.performance or {},
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'next_scheduled': self.next_scheduled.isoformat() if self.next_scheduled else None,
        }
        # Add additional data fields
        if self.additional_data:
            result.update(self.additional_data)
        return result


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
    value: Mapped[str] = mapped_column(String(100), nullable=False)  # Changed to String to handle "125/80" format
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
    type: Mapped[str] = mapped_column(String(100), nullable=False)  # board_director, executive_position, advisor, speaking
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    compensation_range: Mapped[str] = mapped_column(String(200), nullable=True)
    location: Mapped[str] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='prospect')  # prospect, applied, interview_stage, offer_received, accepted, rejected
    ai_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    requirements: Mapped[list] = mapped_column(JSON, nullable=True)
    application_date: Mapped[str] = mapped_column(String(20), nullable=True)
    next_step: Mapped[str] = mapped_column(String(200), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Enhanced pipeline management fields
    interview_stages: Mapped[list] = mapped_column(JSON, nullable=True)  # [{stage, date, status, feedback}]
    decision_makers: Mapped[list] = mapped_column(JSON, nullable=True)  # Contact information
    company_research: Mapped[dict] = mapped_column(JSON, nullable=True)  # Company insights
    networking_connections: Mapped[list] = mapped_column(JSON, nullable=True)  # Internal connections
    follow_up_dates: Mapped[list] = mapped_column(JSON, nullable=True)  # Scheduled follow-ups
    
    # Board director specific fields
    board_size: Mapped[int] = mapped_column(Integer, nullable=True)
    board_tenure_expectation: Mapped[str] = mapped_column(String(100), nullable=True)
    committee_assignments: Mapped[list] = mapped_column(JSON, nullable=True)
    governance_focus: Mapped[list] = mapped_column(JSON, nullable=True)  # Risk, Audit, Compensation, etc.
    
    # Speaking opportunity fields
    event_type: Mapped[str] = mapped_column(String(100), nullable=True)  # conference, webinar, podcast
    speaking_fee: Mapped[str] = mapped_column(String(100), nullable=True)
    audience_size: Mapped[int] = mapped_column(Integer, nullable=True)
    topic_alignment: Mapped[list] = mapped_column(JSON, nullable=True)  # AI governance, risk management, etc.
    event_date: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Priority and urgency
    priority_level: Mapped[str] = mapped_column(String(20), default='medium')  # low, medium, high, critical
    deadline: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Tracking and analytics
    source: Mapped[str] = mapped_column(String(100), nullable=True)  # LinkedIn, referral, search, etc.
    conversion_probability: Mapped[float] = mapped_column(Float, default=0.5)
    estimated_close_date: Mapped[str] = mapped_column(String(20), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'company': self.company,
            'compensation_range': self.compensation_range,
            'location': self.location,
            'status': self.status,
            'ai_match_score': self.ai_match_score,
            'requirements': self.requirements or [],
            'application_date': self.application_date,
            'next_step': self.next_step,
            'notes': self.notes,
            'interview_stages': self.interview_stages or [],
            'decision_makers': self.decision_makers or [],
            'company_research': self.company_research or {},
            'networking_connections': self.networking_connections or [],
            'follow_up_dates': self.follow_up_dates or [],
            'board_size': self.board_size,
            'board_tenure_expectation': self.board_tenure_expectation,
            'committee_assignments': self.committee_assignments or [],
            'governance_focus': self.governance_focus or [],
            'event_type': self.event_type,
            'speaking_fee': self.speaking_fee,
            'audience_size': self.audience_size,
            'topic_alignment': self.topic_alignment or [],
            'event_date': self.event_date,
            'priority_level': self.priority_level,
            'deadline': self.deadline,
            'source': self.source,
            'conversion_probability': self.conversion_probability,
            'estimated_close_date': self.estimated_close_date,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class SpeakingOpportunity(db.Model):
    __tablename__ = 'speaking_opportunities'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    event_name: Mapped[str] = mapped_column(String(200), nullable=False)
    organizer: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # conference, webinar, podcast, workshop
    event_date: Mapped[str] = mapped_column(String(20), nullable=True)
    submission_deadline: Mapped[str] = mapped_column(String(20), nullable=True)
    speaking_fee: Mapped[str] = mapped_column(String(100), nullable=True)
    audience_size: Mapped[int] = mapped_column(Integer, nullable=True)
    location: Mapped[str] = mapped_column(String(200), nullable=True)
    topic_alignment: Mapped[list] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='prospect')  # prospect, applied, accepted, rejected, completed
    application_date: Mapped[str] = mapped_column(String(20), nullable=True)
    ai_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    requirements: Mapped[list] = mapped_column(JSON, nullable=True)
    travel_required: Mapped[bool] = mapped_column(Boolean, default=False)
    virtual_option: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'event_name': self.event_name,
            'organizer': self.organizer,
            'event_type': self.event_type,
            'event_date': self.event_date,
            'submission_deadline': self.submission_deadline,
            'speaking_fee': self.speaking_fee,
            'audience_size': self.audience_size,
            'location': self.location,
            'topic_alignment': self.topic_alignment or [],
            'status': self.status,
            'application_date': self.application_date,
            'ai_match_score': self.ai_match_score,
            'notes': self.notes,
            'source': self.source,
            'requirements': self.requirements or [],
            'travel_required': self.travel_required,
            'virtual_option': self.virtual_option,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class InterviewStage(db.Model):
    __tablename__ = 'interview_stages'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    opportunity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # executive or speaking
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage_date: Mapped[str] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='scheduled')  # scheduled, completed, cancelled
    interviewer_name: Mapped[str] = mapped_column(String(200), nullable=True)
    interviewer_role: Mapped[str] = mapped_column(String(100), nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(String(50), nullable=True)  # positive, negative, neutral
    next_step: Mapped[str] = mapped_column(String(200), nullable=True)
    preparation_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'opportunity_id': self.opportunity_id,
            'opportunity_type': self.opportunity_type,
            'stage_name': self.stage_name,
            'stage_date': self.stage_date,
            'status': self.status,
            'interviewer_name': self.interviewer_name,
            'interviewer_role': self.interviewer_role,
            'feedback': self.feedback,
            'outcome': self.outcome,
            'next_step': self.next_step,
            'preparation_notes': self.preparation_notes,
            'created_at': self.created_at.isoformat()
        }


class CompensationBenchmark(db.Model):
    __tablename__ = 'compensation_benchmarks'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_type: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    company_size: Mapped[str] = mapped_column(String(50), nullable=False)  # startup, midsize, enterprise
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    base_salary_min: Mapped[float] = mapped_column(Float, nullable=True)
    base_salary_max: Mapped[float] = mapped_column(Float, nullable=True)
    equity_percentage: Mapped[float] = mapped_column(Float, nullable=True)
    cash_bonus_percentage: Mapped[float] = mapped_column(Float, nullable=True)
    board_fees: Mapped[float] = mapped_column(Float, nullable=True)  # Annual board fees
    meeting_fees: Mapped[float] = mapped_column(Float, nullable=True)  # Per meeting fees
    speaking_fee_min: Mapped[float] = mapped_column(Float, nullable=True)
    speaking_fee_max: Mapped[float] = mapped_column(Float, nullable=True)
    data_source: Mapped[str] = mapped_column(String(200), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'position_type': self.position_type,
            'industry': self.industry,
            'company_size': self.company_size,
            'location': self.location,
            'base_salary_min': self.base_salary_min,
            'base_salary_max': self.base_salary_max,
            'equity_percentage': self.equity_percentage,
            'cash_bonus_percentage': self.cash_bonus_percentage,
            'board_fees': self.board_fees,
            'meeting_fees': self.meeting_fees,
            'speaking_fee_min': self.speaking_fee_min,
            'speaking_fee_max': self.speaking_fee_max,
            'data_source': self.data_source,
            'last_updated': self.last_updated.isoformat()
        }


class RetreatEvent(db.Model):
    __tablename__ = 'retreat_events'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=True)
    dates: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    registered: Mapped[int] = mapped_column(Integer, default=0)
    pricing: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='planning')
    focus: Mapped[list] = mapped_column(JSON, nullable=True)
    amenities: Mapped[list] = mapped_column(JSON, nullable=True)
    speakers: Mapped[list] = mapped_column(JSON, nullable=True)
    revenue_projected: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'dates': self.dates,
            'location': self.location,
            'capacity': self.capacity,
            'registered': self.registered,
            'pricing': self.pricing,
            'status': self.status,
            'focus': self.focus or [],
            'amenities': self.amenities or [],
            'speakers': self.speakers or [],
            'revenue_projected': self.revenue_projected,
            'created_at': self.created_at.isoformat()
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


# Workflow Automation Models

class WorkflowTrigger(db.Model):
    __tablename__ = 'workflow_triggers'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)  # event, schedule, manual, webhook
    event_type: Mapped[str] = mapped_column(String(100), nullable=True)  # revenue_milestone, agent_performance, opportunity_status, etc.
    conditions: Mapped[dict] = mapped_column(JSON, nullable=True)  # Trigger conditions
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10, higher priority executes first
    created_by: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'trigger_type': self.trigger_type,
            'event_type': self.event_type,
            'conditions': self.conditions or {},
            'enabled': self.enabled,
            'priority': self.priority,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }


class BusinessRule(db.Model):
    __tablename__ = 'business_rules'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    rule_category: Mapped[str] = mapped_column(String(100), nullable=False)  # revenue, agents, opportunities, health, etc.
    conditions: Mapped[list] = mapped_column(JSON, nullable=False)  # List of condition objects
    actions: Mapped[list] = mapped_column(JSON, nullable=False)  # List of action objects
    logical_operator: Mapped[str] = mapped_column(String(10), default='AND')  # AND, OR
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    last_execution: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rule_category': self.rule_category,
            'conditions': self.conditions or [],
            'actions': self.actions or [],
            'logical_operator': self.logical_operator,
            'enabled': self.enabled,
            'priority': self.priority,
            'execution_count': self.execution_count,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class WorkflowAction(db.Model):
    __tablename__ = 'workflow_actions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # notification, api_call, agent_task, email, webhook
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)  # Action-specific parameters
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    retry_attempts: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay: Mapped[int] = mapped_column(Integer, default=60)  # seconds
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'action_type': self.action_type,
            'parameters': self.parameters or {},
            'timeout_seconds': self.timeout_seconds,
            'retry_attempts': self.retry_attempts,
            'retry_delay': self.retry_delay,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat()
        }


class WorkflowSchedule(db.Model):
    __tablename__ = 'workflow_schedules'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # cron, interval, one_time
    schedule_expression: Mapped[str] = mapped_column(String(200), nullable=False)  # Cron expression or interval
    workflow_rules: Mapped[list] = mapped_column(JSON, nullable=False)  # List of rule IDs to execute
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(50), default='UTC')
    next_run: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_run: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'schedule_type': self.schedule_type,
            'schedule_expression': self.schedule_expression,
            'workflow_rules': self.workflow_rules or [],
            'enabled': self.enabled,
            'timezone': self.timezone,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'run_count': self.run_count,
            'created_at': self.created_at.isoformat()
        }


class WorkflowExecution(db.Model):
    __tablename__ = 'workflow_executions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    trigger_id: Mapped[int] = mapped_column(Integer, nullable=True)
    rule_id: Mapped[int] = mapped_column(Integer, nullable=True)
    schedule_id: Mapped[int] = mapped_column(Integer, nullable=True)
    execution_type: Mapped[str] = mapped_column(String(50), nullable=False)  # trigger, schedule, manual
    status: Mapped[str] = mapped_column(String(50), default='running')  # running, completed, failed, cancelled
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    actions_executed: Mapped[int] = mapped_column(Integer, default=0)
    actions_successful: Mapped[int] = mapped_column(Integer, default=0)
    actions_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    execution_context: Mapped[dict] = mapped_column(JSON, nullable=True)  # Context data for execution
    result_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Results from actions
    
    def to_dict(self):
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'trigger_id': self.trigger_id,
            'rule_id': self.rule_id,
            'schedule_id': self.schedule_id,
            'execution_type': self.execution_type,
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'actions_executed': self.actions_executed,
            'actions_successful': self.actions_successful,
            'actions_failed': self.actions_failed,
            'error_message': self.error_message,
            'execution_context': self.execution_context or {},
            'result_data': self.result_data or {}
        }


class NotificationChannel(db.Model):
    __tablename__ = 'notification_channels'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)  # email, slack, webhook, sms, internal
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False)  # Channel-specific config
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    rate_limit: Mapped[int] = mapped_column(Integer, nullable=True)  # Max notifications per hour
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'channel_type': self.channel_type,
            'configuration': self.configuration or {},
            'enabled': self.enabled,
            'priority': self.priority,
            'rate_limit': self.rate_limit,
            'created_at': self.created_at.isoformat()
        }


class WorkflowWebhook(db.Model):
    __tablename__ = 'workflow_webhooks'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret_key: Mapped[str] = mapped_column(String(200), nullable=True)
    event_types: Mapped[list] = mapped_column(JSON, nullable=False)  # Events to send to this webhook
    headers: Mapped[dict] = mapped_column(JSON, nullable=True)  # Custom headers
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    retry_attempts: Mapped[int] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_triggered: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'webhook_url': self.webhook_url,
            'secret_key': self.secret_key,
            'event_types': self.event_types or [],
            'headers': self.headers or {},
            'enabled': self.enabled,
            'retry_attempts': self.retry_attempts,
            'timeout_seconds': self.timeout_seconds,
            'created_at': self.created_at.isoformat(),
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }


class BusinessEvent(db.Model):
    __tablename__ = 'business_events'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # revenue_stream, ai_agent, opportunity, etc.
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Event-specific data
    source: Mapped[str] = mapped_column(String(100), nullable=True)  # Source that generated the event
    priority: Mapped[str] = mapped_column(String(20), default='medium')  # low, medium, high, critical
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'event_type': self.event_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'event_data': self.event_data or {},
            'source': self.source,
            'priority': self.priority,
            'processed': self.processed,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }