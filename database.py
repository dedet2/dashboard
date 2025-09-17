from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Float, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()

# ===== LORA DIGITAL CLONE SYSTEM MODELS =====

class DigitalClone(db.Model):
    """Core digital clone profile with training and deployment metadata"""
    __tablename__ = 'digital_clones'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    owner: Mapped[str] = mapped_column(String(100), nullable=False)  # User who owns this clone
    
    # Voice characteristics
    voice_profile: Mapped[dict] = mapped_column(JSON, nullable=True)  # Voice analysis data
    voice_model_path: Mapped[str] = mapped_column(String(500), nullable=True)  # Path to trained voice model
    voice_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Video characteristics
    video_profile: Mapped[dict] = mapped_column(JSON, nullable=True)  # Facial features, expressions
    avatar_model_path: Mapped[str] = mapped_column(String(500), nullable=True)  # Path to avatar model
    video_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Training status
    training_status: Mapped[str] = mapped_column(String(50), default='not_started')  # not_started, training, completed, failed
    training_progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100%
    total_training_time: Mapped[int] = mapped_column(Integer, default=0)  # Minutes of training data
    
    # Deployment settings
    deployment_status: Mapped[str] = mapped_column(String(50), default='inactive')  # inactive, active, maintenance
    deployment_targets: Mapped[list] = mapped_column(JSON, nullable=True)  # Where clone is deployed
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_training: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_used: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner': self.owner,
            'voice_profile': self.voice_profile or {},
            'voice_model_path': self.voice_model_path,
            'voice_quality_score': self.voice_quality_score,
            'video_profile': self.video_profile or {},
            'avatar_model_path': self.avatar_model_path,
            'video_quality_score': self.video_quality_score,
            'training_status': self.training_status,
            'training_progress': self.training_progress,
            'total_training_time': self.total_training_time,
            'deployment_status': self.deployment_status,
            'deployment_targets': self.deployment_targets or [],
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_training': self.last_training.isoformat() if self.last_training else None,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }


class TrainingData(db.Model):
    """Voice and video training data for LoRA models"""
    __tablename__ = 'training_data'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clone_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Reference to DigitalClone
    
    # File information
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # audio, video, image
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Bytes
    duration: Mapped[float] = mapped_column(Float, nullable=True)  # Seconds for audio/video
    
    # Processing status
    processing_status: Mapped[str] = mapped_column(String(50), default='uploaded')  # uploaded, processing, processed, failed
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100 quality assessment
    
    # Extracted features
    transcript: Mapped[str] = mapped_column(Text, nullable=True)  # For audio/video
    voice_features: Mapped[dict] = mapped_column(JSON, nullable=True)  # Voice characteristics
    visual_features: Mapped[dict] = mapped_column(JSON, nullable=True)  # Facial features, expressions
    
    # Descript/CapCut integration
    descript_project_id: Mapped[str] = mapped_column(String(100), nullable=True)
    capcut_project_id: Mapped[str] = mapped_column(String(100), nullable=True)
    processing_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Training metadata
    training_weight: Mapped[float] = mapped_column(Float, default=1.0)  # Importance for training
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'clone_id': self.clone_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'duration': self.duration,
            'processing_status': self.processing_status,
            'quality_score': self.quality_score,
            'transcript': self.transcript,
            'voice_features': self.voice_features or {},
            'visual_features': self.visual_features or {},
            'descript_project_id': self.descript_project_id,
            'capcut_project_id': self.capcut_project_id,
            'processing_metadata': self.processing_metadata or {},
            'training_weight': self.training_weight,
            'is_validated': self.is_validated,
            'validation_notes': self.validation_notes,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }


class LoRAModel(db.Model):
    """Trained LoRA model metadata and versioning"""
    __tablename__ = 'lora_models'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clone_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Reference to DigitalClone
    
    # Model information
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # voice, video, combined
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)
    model_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Bytes
    
    # Training configuration
    training_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    base_model: Mapped[str] = mapped_column(String(200), nullable=False)  # Base model used
    training_epochs: Mapped[int] = mapped_column(Integer, nullable=False)
    learning_rate: Mapped[float] = mapped_column(Float, nullable=False)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Performance metrics
    training_loss: Mapped[float] = mapped_column(Float, nullable=True)
    validation_loss: Mapped[float] = mapped_column(Float, nullable=True)
    quality_metrics: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Status and metadata
    status: Mapped[str] = mapped_column(String(50), default='training')  # training, completed, failed, deployed
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)  # Currently active model
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    training_started: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    training_completed: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'clone_id': self.clone_id,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'model_type': self.model_type,
            'model_path': self.model_path,
            'model_size': self.model_size,
            'training_config': self.training_config,
            'base_model': self.base_model,
            'training_epochs': self.training_epochs,
            'learning_rate': self.learning_rate,
            'batch_size': self.batch_size,
            'training_loss': self.training_loss,
            'validation_loss': self.validation_loss,
            'quality_metrics': self.quality_metrics or {},
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'training_started': self.training_started.isoformat() if self.training_started else None,
            'training_completed': self.training_completed.isoformat() if self.training_completed else None
        }


class CloneSession(db.Model):
    """Training and synthesis sessions for digital clones"""
    __tablename__ = 'clone_sessions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clone_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Reference to DigitalClone
    
    # Session information
    session_type: Mapped[str] = mapped_column(String(50), nullable=False)  # training, synthesis, validation
    session_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Session configuration
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    input_data: Mapped[list] = mapped_column(JSON, nullable=True)  # Input file IDs or synthesis prompts
    
    # Progress tracking
    status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, running, completed, failed
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100%
    current_step: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Results
    output_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Generated files, metrics
    metrics: Mapped[dict] = mapped_column(JSON, nullable=True)  # Performance metrics
    error_log: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)  # Seconds
    
    def to_dict(self):
        return {
            'id': self.id,
            'clone_id': self.clone_id,
            'session_type': self.session_type,
            'session_name': self.session_name,
            'description': self.description,
            'config': self.config,
            'input_data': self.input_data or [],
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'output_data': self.output_data or {},
            'metrics': self.metrics or {},
            'error_log': self.error_log,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration
        }


class SynthesisJob(db.Model):
    """Voice and video synthesis job tracking"""
    __tablename__ = 'synthesis_jobs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clone_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Reference to DigitalClone
    
    # Job information
    job_name: Mapped[str] = mapped_column(String(200), nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)  # voice_synthesis, video_generation, avatar_animation
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10, 1=highest
    
    # Input configuration
    input_text: Mapped[str] = mapped_column(Text, nullable=True)  # Text to synthesize
    input_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Synthesis parameters
    style_settings: Mapped[dict] = mapped_column(JSON, nullable=True)  # Voice style, emotion, etc.
    
    # Processing status
    status: Mapped[str] = mapped_column(String(50), default='queued')  # queued, processing, completed, failed
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100%
    processing_node: Mapped[str] = mapped_column(String(100), nullable=True)  # Which server is processing
    
    # Output results
    output_files: Mapped[list] = mapped_column(JSON, nullable=True)  # Generated file paths
    output_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)  # Duration, quality metrics
    quality_score: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Integration tracking
    descript_job_id: Mapped[str] = mapped_column(String(100), nullable=True)
    capcut_job_id: Mapped[str] = mapped_column(String(100), nullable=True)
    external_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Timing and usage
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    processing_time: Mapped[int] = mapped_column(Integer, nullable=True)  # Seconds
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=True)  # API costs
    
    def to_dict(self):
        return {
            'id': self.id,
            'clone_id': self.clone_id,
            'job_name': self.job_name,
            'job_type': self.job_type,
            'priority': self.priority,
            'input_text': self.input_text,
            'input_config': self.input_config,
            'style_settings': self.style_settings or {},
            'status': self.status,
            'progress': self.progress,
            'processing_node': self.processing_node,
            'output_files': self.output_files or [],
            'output_metadata': self.output_metadata or {},
            'quality_score': self.quality_score,
            'descript_job_id': self.descript_job_id,
            'capcut_job_id': self.capcut_job_id,
            'external_metadata': self.external_metadata or {},
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_time': self.processing_time,
            'estimated_cost': self.estimated_cost
        }


class DeploymentTarget(db.Model):
    """Deployment targets for digital clones (presentations, consultations, etc.)"""
    __tablename__ = 'deployment_targets'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clone_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Reference to DigitalClone
    
    # Target information
    target_name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # presentation, consultation, webinar, content
    platform: Mapped[str] = mapped_column(String(100), nullable=False)  # zoom, teams, youtube, custom
    
    # Configuration
    deployment_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    integration_settings: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Status and scheduling
    status: Mapped[str] = mapped_column(String(50), default='inactive')  # inactive, active, scheduled, running, completed
    scheduled_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    total_duration: Mapped[int] = mapped_column(Integer, default=0)  # Minutes
    audience_size: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Performance metrics
    performance_metrics: Mapped[dict] = mapped_column(JSON, nullable=True)
    feedback_scores: Mapped[list] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'clone_id': self.clone_id,
            'target_name': self.target_name,
            'target_type': self.target_type,
            'platform': self.platform,
            'deployment_config': self.deployment_config,
            'integration_settings': self.integration_settings or {},
            'status': self.status,
            'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None,
            'scheduled_end': self.scheduled_end.isoformat() if self.scheduled_end else None,
            'usage_count': self.usage_count,
            'total_duration': self.total_duration,
            'audience_size': self.audience_size,
            'performance_metrics': self.performance_metrics or {},
            'feedback_scores': self.feedback_scores or [],
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None
        }

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
    
    # Apollo.io integration fields
    apollo_prospect_id: Mapped[str] = mapped_column(String(100), nullable=True)  # Apollo's unique prospect ID
    apollo_organization_id: Mapped[str] = mapped_column(String(100), nullable=True)  # Apollo's organization ID
    apollo_email: Mapped[str] = mapped_column(String(200), nullable=True)  # Email from Apollo
    apollo_email_status: Mapped[str] = mapped_column(String(50), nullable=True)  # verified, unverified, likely_to_engage, unavailable
    apollo_phone_number: Mapped[str] = mapped_column(String(50), nullable=True)  # Phone number from Apollo
    apollo_linkedin_url: Mapped[str] = mapped_column(String(500), nullable=True)  # LinkedIn profile URL
    apollo_seniority: Mapped[str] = mapped_column(String(50), nullable=True)  # Seniority level from Apollo
    apollo_last_enriched: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # When data was last enriched
    apollo_match_criteria: Mapped[dict] = mapped_column(JSON, nullable=True)  # Search criteria that matched this prospect
    apollo_company_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Enriched company information from Apollo
    apollo_raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Full Apollo API response for reference
    
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
            'apollo_prospect_id': self.apollo_prospect_id,
            'apollo_organization_id': self.apollo_organization_id,
            'apollo_email': self.apollo_email,
            'apollo_email_status': self.apollo_email_status,
            'apollo_phone_number': self.apollo_phone_number,
            'apollo_linkedin_url': self.apollo_linkedin_url,
            'apollo_seniority': self.apollo_seniority,
            'apollo_last_enriched': self.apollo_last_enriched.isoformat() if self.apollo_last_enriched else None,
            'apollo_match_criteria': self.apollo_match_criteria or {},
            'apollo_company_data': self.apollo_company_data or {},
            'apollo_raw_data': self.apollo_raw_data or {},
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


# ====================================
# YouTube Video Optimization Models
# ====================================

class YoutubeVideo(db.Model):
    __tablename__ = 'youtube_videos'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Video metadata
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    original_title: Mapped[str] = mapped_column(String(300), nullable=True)  # Before optimization
    description: Mapped[str] = mapped_column(Text, nullable=True)
    original_description: Mapped[str] = mapped_column(Text, nullable=True)  # Before optimization
    
    # Video file information
    video_file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    video_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    video_format: Mapped[str] = mapped_column(String(50), nullable=True)
    video_size_mb: Mapped[float] = mapped_column(Float, nullable=True)
    
    # YouTube specific
    youtube_video_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    youtube_url: Mapped[str] = mapped_column(String(500), nullable=True)
    youtube_status: Mapped[str] = mapped_column(String(50), default='draft')  # draft, uploaded, published, unlisted
    
    # SEO and categorization
    primary_topic: Mapped[str] = mapped_column(String(200), nullable=True)
    secondary_topics: Mapped[list] = mapped_column(JSON, nullable=True)
    target_keywords: Mapped[list] = mapped_column(JSON, nullable=True)
    seo_tags: Mapped[list] = mapped_column(JSON, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True)  # AI Governance, Accessibility, etc.
    
    # Content type and strategy
    content_type: Mapped[str] = mapped_column(String(100), nullable=True)  # thought_leadership, tutorial, interview, etc.
    target_audience: Mapped[str] = mapped_column(String(100), nullable=True)  # executives, compliance_officers, etc.
    monetization_strategy: Mapped[list] = mapped_column(JSON, nullable=True)  # speaking_leads, consulting_leads, etc.
    
    # Optimization tracking
    optimization_status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, optimizing, completed, failed
    optimization_score: Mapped[float] = mapped_column(Float, nullable=True)  # 0.0 to 1.0
    perplexity_research_used: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Sales and lead generation
    sales_links: Mapped[dict] = mapped_column(JSON, nullable=True)  # Strategic placement of sales links
    call_to_action: Mapped[str] = mapped_column(Text, nullable=True)
    lead_magnets: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    optimized_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'original_title': self.original_title,
            'description': self.description,
            'original_description': self.original_description,
            'video_file_path': self.video_file_path,
            'video_duration_seconds': self.video_duration_seconds,
            'video_format': self.video_format,
            'video_size_mb': self.video_size_mb,
            'youtube_video_id': self.youtube_video_id,
            'youtube_url': self.youtube_url,
            'youtube_status': self.youtube_status,
            'primary_topic': self.primary_topic,
            'secondary_topics': self.secondary_topics or [],
            'target_keywords': self.target_keywords or [],
            'seo_tags': self.seo_tags or [],
            'category': self.category,
            'content_type': self.content_type,
            'target_audience': self.target_audience,
            'monetization_strategy': self.monetization_strategy or [],
            'optimization_status': self.optimization_status,
            'optimization_score': self.optimization_score,
            'perplexity_research_used': self.perplexity_research_used,
            'sales_links': self.sales_links or {},
            'call_to_action': self.call_to_action,
            'lead_magnets': self.lead_magnets or [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'optimized_at': self.optimized_at.isoformat() if self.optimized_at else None
        }


class VideoChapter(db.Model):
    __tablename__ = 'video_chapters'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationship to video
    video_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to YoutubeVideo
    
    # Chapter information
    chapter_title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    end_time_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Chapter content and SEO
    chapter_description: Mapped[str] = mapped_column(Text, nullable=True)
    key_topics: Mapped[list] = mapped_column(JSON, nullable=True)
    relevant_keywords: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Chapter ordering and importance
    chapter_order: Mapped[int] = mapped_column(Integer, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0
    
    # AI generation metadata
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    perplexity_prompt_used: Mapped[str] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'chapter_title': self.chapter_title,
            'start_time_seconds': self.start_time_seconds,
            'end_time_seconds': self.end_time_seconds,
            'duration_seconds': self.duration_seconds,
            'chapter_description': self.chapter_description,
            'key_topics': self.key_topics or [],
            'relevant_keywords': self.relevant_keywords or [],
            'chapter_order': self.chapter_order,
            'importance_score': self.importance_score,
            'ai_generated': self.ai_generated,
            'perplexity_prompt_used': self.perplexity_prompt_used,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class VideoCaption(db.Model):
    __tablename__ = 'video_captions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationship to video
    video_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to YoutubeVideo
    
    # Caption timing
    start_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Caption content
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    optimized_text: Mapped[str] = mapped_column(Text, nullable=True)  # SEO optimized version
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    
    # SEO optimization
    contains_keywords: Mapped[list] = mapped_column(JSON, nullable=True)
    seo_enhanced: Mapped[bool] = mapped_column(Boolean, default=False)
    optimization_changes: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Caption formatting and style
    caption_style: Mapped[str] = mapped_column(String(50), default='standard')  # standard, highlight, emphasis
    font_size: Mapped[str] = mapped_column(String(20), nullable=True)
    position: Mapped[str] = mapped_column(String(50), nullable=True)  # bottom, top, center
    
    # AI processing metadata
    ai_transcribed: Mapped[bool] = mapped_column(Boolean, default=False)
    transcription_source: Mapped[str] = mapped_column(String(100), nullable=True)  # whisper, human, auto
    reviewed_by_human: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'start_time_seconds': self.start_time_seconds,
            'end_time_seconds': self.end_time_seconds,
            'duration_seconds': self.duration_seconds,
            'original_text': self.original_text,
            'optimized_text': self.optimized_text,
            'confidence_score': self.confidence_score,
            'contains_keywords': self.contains_keywords or [],
            'seo_enhanced': self.seo_enhanced,
            'optimization_changes': self.optimization_changes or {},
            'caption_style': self.caption_style,
            'font_size': self.font_size,
            'position': self.position,
            'ai_transcribed': self.ai_transcribed,
            'transcription_source': self.transcription_source,
            'reviewed_by_human': self.reviewed_by_human,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class VideoOptimization(db.Model):
    __tablename__ = 'video_optimizations'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationship to video
    video_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to YoutubeVideo
    
    # Optimization run metadata
    optimization_type: Mapped[str] = mapped_column(String(100), nullable=False)  # full, title_only, description_only, etc.
    optimization_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, running, completed, failed
    
    # AI model and prompt information
    perplexity_model_used: Mapped[str] = mapped_column(String(100), nullable=True)
    optimization_prompts: Mapped[dict] = mapped_column(JSON, nullable=True)
    research_data_used: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Optimization results
    before_optimization: Mapped[dict] = mapped_column(JSON, nullable=True)  # Original content snapshot
    after_optimization: Mapped[dict] = mapped_column(JSON, nullable=True)  # Optimized content
    optimization_score: Mapped[float] = mapped_column(Float, nullable=True)  # Overall quality score
    seo_improvements: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Specific optimizations applied
    title_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    description_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    tags_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    chapters_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    captions_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    sales_links_added: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Performance metrics
    processing_time_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    api_calls_made: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Quality assessment
    content_quality_score: Mapped[float] = mapped_column(Float, nullable=True)  # 0.0 to 1.0
    seo_readiness_score: Mapped[float] = mapped_column(Float, nullable=True)  # 0.0 to 1.0
    engagement_potential_score: Mapped[float] = mapped_column(Float, nullable=True)  # 0.0 to 1.0
    monetization_alignment_score: Mapped[float] = mapped_column(Float, nullable=True)  # 0.0 to 1.0
    
    # Error handling
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'optimization_type': self.optimization_type,
            'optimization_version': self.optimization_version,
            'status': self.status,
            'perplexity_model_used': self.perplexity_model_used,
            'optimization_prompts': self.optimization_prompts or {},
            'research_data_used': self.research_data_used or {},
            'before_optimization': self.before_optimization or {},
            'after_optimization': self.after_optimization or {},
            'optimization_score': self.optimization_score,
            'seo_improvements': self.seo_improvements or {},
            'title_optimized': self.title_optimized,
            'description_optimized': self.description_optimized,
            'tags_optimized': self.tags_optimized,
            'chapters_generated': self.chapters_generated,
            'captions_optimized': self.captions_optimized,
            'sales_links_added': self.sales_links_added,
            'processing_time_seconds': self.processing_time_seconds,
            'api_calls_made': self.api_calls_made,
            'tokens_used': self.tokens_used,
            'estimated_cost_usd': self.estimated_cost_usd,
            'content_quality_score': self.content_quality_score,
            'seo_readiness_score': self.seo_readiness_score,
            'engagement_potential_score': self.engagement_potential_score,
            'monetization_alignment_score': self.monetization_alignment_score,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat()
        }


class VideoAnalytics(db.Model):
    __tablename__ = 'video_analytics'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationship to video
    video_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Foreign key to YoutubeVideo
    
    # Analytics snapshot metadata
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    analytics_source: Mapped[str] = mapped_column(String(100), default='youtube_api')  # youtube_api, manual, estimated
    
    # YouTube performance metrics
    views_total: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    dislikes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    subscribers_gained: Mapped[int] = mapped_column(Integer, default=0)
    
    # Engagement metrics
    average_watch_time_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    watch_time_percentage: Mapped[float] = mapped_column(Float, nullable=True)  # % of video watched on average
    engagement_rate: Mapped[float] = mapped_column(Float, nullable=True)  # likes+comments+shares/views
    click_through_rate: Mapped[float] = mapped_column(Float, nullable=True)  # CTR from impressions
    
    # Discovery and reach
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    impression_click_through_rate: Mapped[float] = mapped_column(Float, nullable=True)
    traffic_sources: Mapped[dict] = mapped_column(JSON, nullable=True)  # youtube_search, suggested, external, etc.
    top_keywords: Mapped[list] = mapped_column(JSON, nullable=True)  # Keywords driving traffic
    
    # Revenue and lead generation (estimated)
    estimated_leads_generated: Mapped[int] = mapped_column(Integer, default=0)
    website_clicks: Mapped[int] = mapped_column(Integer, default=0)
    consultation_requests: Mapped[int] = mapped_column(Integer, default=0)
    estimated_revenue_impact: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Content performance indicators
    retention_curve: Mapped[dict] = mapped_column(JSON, nullable=True)  # Watch time at different timestamps
    most_replayed_segments: Mapped[list] = mapped_column(JSON, nullable=True)
    drop_off_points: Mapped[list] = mapped_column(JSON, nullable=True)
    chapter_performance: Mapped[dict] = mapped_column(JSON, nullable=True)  # Performance by chapter
    
    # Optimization impact assessment
    pre_optimization_baseline: Mapped[dict] = mapped_column(JSON, nullable=True)
    optimization_impact_score: Mapped[float] = mapped_column(Float, nullable=True)  # Performance improvement
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'snapshot_date': self.snapshot_date.isoformat(),
            'analytics_source': self.analytics_source,
            'views_total': self.views_total,
            'likes': self.likes,
            'dislikes': self.dislikes,
            'comments': self.comments,
            'shares': self.shares,
            'subscribers_gained': self.subscribers_gained,
            'average_watch_time_seconds': self.average_watch_time_seconds,
            'watch_time_percentage': self.watch_time_percentage,
            'engagement_rate': self.engagement_rate,
            'click_through_rate': self.click_through_rate,
            'impressions': self.impressions,
            'impression_click_through_rate': self.impression_click_through_rate,
            'traffic_sources': self.traffic_sources or {},
            'top_keywords': self.top_keywords or [],
            'estimated_leads_generated': self.estimated_leads_generated,
            'website_clicks': self.website_clicks,
            'consultation_requests': self.consultation_requests,
            'estimated_revenue_impact': self.estimated_revenue_impact,
            'retention_curve': self.retention_curve or {},
            'most_replayed_segments': self.most_replayed_segments or [],
            'drop_off_points': self.drop_off_points or [],
            'chapter_performance': self.chapter_performance or {},
            'pre_optimization_baseline': self.pre_optimization_baseline or {},
            'optimization_impact_score': self.optimization_impact_score,
            'created_at': self.created_at.isoformat()
        }