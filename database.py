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
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    compensation: Mapped[str] = mapped_column(String(100), nullable=True)
    location: Mapped[str] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='prospect')
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    requirements: Mapped[list] = mapped_column(JSON, nullable=True)
    application_date: Mapped[str] = mapped_column(String(20), nullable=True)
    next_step: Mapped[str] = mapped_column(String(200), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'company': self.company,
            'compensation': self.compensation,
            'location': self.location,
            'status': self.status,
            'match_score': self.match_score,
            'requirements': self.requirements or [],
            'application_date': self.application_date,
            'next_step': self.next_step,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
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