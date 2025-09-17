"""
Database models for Make.com integration
Extends the existing database schema with Make.com specific models
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Float, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import db

class MakeScenario(db.Model):
    """Model for Make.com scenarios"""
    __tablename__ = 'make_scenarios'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Configuration
    event_types: Mapped[list] = mapped_column(JSON, nullable=False)  # List of MakeEventType values
    authentication_method: Mapped[str] = mapped_column(String(50), default='none')
    secret_key: Mapped[str] = mapped_column(String(500), nullable=True)
    custom_headers: Mapped[dict] = mapped_column(JSON, nullable=True)
    filter_conditions: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Status and settings
    status: Mapped[str] = mapped_column(String(20), default='active')  # active, inactive, paused, error
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    
    # Template information
    template_id: Mapped[str] = mapped_column(String(200), nullable=True)
    expected_data_structure: Mapped[dict] = mapped_column(JSON, nullable=True)
    configuration_steps: Mapped[list] = mapped_column(JSON, nullable=True)
    required_integrations: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Performance and statistics
    total_executions: Mapped[int] = mapped_column(Integer, default=0)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0)
    failed_executions: Mapped[int] = mapped_column(Integer, default=0)
    last_execution: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_success: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_failure: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    created_by: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'webhook_url': self.webhook_url,
            'event_types': self.event_types,
            'authentication_method': self.authentication_method,
            'custom_headers': self.custom_headers or {},
            'filter_conditions': self.filter_conditions or {},
            'status': self.status,
            'enabled': self.enabled,
            'priority': self.priority,
            'template_id': self.template_id,
            'expected_data_structure': self.expected_data_structure or {},
            'configuration_steps': self.configuration_steps or [],
            'required_integrations': self.required_integrations or [],
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': (self.successful_executions / max(self.total_executions, 1)) * 100,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'last_failure': self.last_failure.isoformat() if self.last_failure else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MakeExecution(db.Model):
    """Model for Make.com execution logs"""
    __tablename__ = 'make_executions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    scenario_id: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Trigger information
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(200), nullable=True)  # Source entity ID
    trigger_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Execution details
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failure, pending, timeout
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    response_status: Mapped[int] = mapped_column(Integer, nullable=True)
    response_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Performance metrics
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'scenario_id': self.scenario_id,
            'event_type': self.event_type,
            'trigger_source': self.trigger_source,
            'trigger_data': self.trigger_data or {},
            'status': self.status,
            'request_payload': self.request_payload or {},
            'response_status': self.response_status,
            'response_data': self.response_data or {},
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms,
            'retry_count': self.retry_count,
            'triggered_at': self.triggered_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class MakeEventLog(db.Model):
    """Model for Make.com event logging"""
    __tablename__ = 'make_event_logs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_entity: Mapped[str] = mapped_column(String(100), nullable=False)  # opportunity, agent, revenue_stream, etc.
    source_id: Mapped[str] = mapped_column(String(200), nullable=False)
    event_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    scenarios_triggered: Mapped[list] = mapped_column(JSON, nullable=True)  # List of scenario IDs
    processing_results: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'event_type': self.event_type,
            'source_entity': self.source_entity,
            'source_id': self.source_id,
            'event_data': self.event_data or {},
            'processed': self.processed,
            'scenarios_triggered': self.scenarios_triggered or [],
            'processing_results': self.processing_results or {},
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class MakeAutomationBridge(db.Model):
    """Model for automation bridges between internal and external workflows"""
    __tablename__ = 'make_automation_bridges'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bridge_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Internal workflow connection
    internal_trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)  # business_rule, workflow_execution, schedule
    internal_trigger_id: Mapped[str] = mapped_column(String(200), nullable=True)  # Reference to internal trigger
    internal_conditions: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # External Make.com connection
    make_scenario_ids: Mapped[list] = mapped_column(JSON, nullable=False)  # List of Make scenarios to trigger
    data_mapping: Mapped[dict] = mapped_column(JSON, nullable=True)  # Map internal data to Make format
    
    # Bridge configuration
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    bidirectional: Mapped[bool] = mapped_column(Boolean, default=False)  # Can Make.com trigger internal workflows
    priority: Mapped[int] = mapped_column(Integer, default=5)
    
    # Performance tracking
    total_executions: Mapped[int] = mapped_column(Integer, default=0)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0)
    last_execution: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    created_by: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'bridge_id': self.bridge_id,
            'name': self.name,
            'description': self.description,
            'internal_trigger_type': self.internal_trigger_type,
            'internal_trigger_id': self.internal_trigger_id,
            'internal_conditions': self.internal_conditions or {},
            'make_scenario_ids': self.make_scenario_ids,
            'data_mapping': self.data_mapping or {},
            'enabled': self.enabled,
            'bidirectional': self.bidirectional,
            'priority': self.priority,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'success_rate': (self.successful_executions / max(self.total_executions, 1)) * 100,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MakeTemplate(db.Model):
    """Model for Make.com scenario templates"""
    __tablename__ = 'make_templates'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Template configuration
    trigger_events: Mapped[list] = mapped_column(JSON, nullable=False)
    expected_data_structure: Mapped[dict] = mapped_column(JSON, nullable=False)
    sample_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    configuration_steps: Mapped[list] = mapped_column(JSON, nullable=False)
    required_integrations: Mapped[list] = mapped_column(JSON, nullable=False)
    
    # Template metadata
    estimated_operations: Mapped[int] = mapped_column(Integer, nullable=False)
    complexity_level: Mapped[str] = mapped_column(String(50), nullable=False)  # beginner, intermediate, advanced
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Documentation
    setup_guide: Mapped[str] = mapped_column(Text, nullable=True)
    troubleshooting_tips: Mapped[dict] = mapped_column(JSON, nullable=True)
    example_use_cases: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    created_by: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'trigger_events': self.trigger_events,
            'expected_data_structure': self.expected_data_structure,
            'sample_payload': self.sample_payload,
            'configuration_steps': self.configuration_steps,
            'required_integrations': self.required_integrations,
            'estimated_operations': self.estimated_operations,
            'complexity_level': self.complexity_level,
            'usage_count': self.usage_count,
            'setup_guide': self.setup_guide,
            'troubleshooting_tips': self.troubleshooting_tips or {},
            'example_use_cases': self.example_use_cases or [],
            'active': self.active,
            'featured': self.featured,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }