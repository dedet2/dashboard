"""
Make.com Workflow Automation Integration Service
Comprehensive webhook system for triggering Make.com scenarios and managing workflow automation
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import uuid
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class MakeEventType(Enum):
    """Make.com trigger event types"""
    OPPORTUNITY_CREATED = "opportunity_created"
    OPPORTUNITY_UPDATED = "opportunity_updated" 
    OPPORTUNITY_STATUS_CHANGED = "opportunity_status_changed"
    LEAD_QUALIFIED = "lead_qualified"
    REVENUE_MILESTONE = "revenue_milestone"
    AGENT_PERFORMANCE_ALERT = "agent_performance_alert"
    SPEAKING_OPPORTUNITY_FOUND = "speaking_opportunity_found"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    FOLLOW_UP_REQUIRED = "follow_up_required"
    CONTENT_PUBLISHED = "content_published"
    APOLLO_LEAD_ENRICHED = "apollo_lead_enriched"
    PERPLEXITY_RESEARCH_COMPLETE = "perplexity_research_complete"
    WORKFLOW_EXECUTION_COMPLETE = "workflow_execution_complete"
    BUSINESS_RULE_TRIGGERED = "business_rule_triggered"

class MakeScenarioStatus(Enum):
    """Make.com scenario status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class MakeWebhookConfig:
    """Configuration for Make.com webhook"""
    scenario_id: str
    webhook_url: str
    event_types: List[MakeEventType]
    authentication_method: str = "none"  # none, basic, bearer, custom
    secret_key: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None
    filter_conditions: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None
    enabled: bool = True

@dataclass
class MakeScenarioTemplate:
    """Template for Make.com scenario"""
    template_id: str
    name: str
    description: str
    category: str
    trigger_events: List[MakeEventType]
    expected_data_structure: Dict[str, Any]
    sample_payload: Dict[str, Any]
    configuration_steps: List[str]
    required_integrations: List[str]
    estimated_operations: int
    complexity_level: str  # beginner, intermediate, advanced

class MakeIntegrationService:
    """Main service class for Make.com integration"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv('MAKE_BASE_URL', 'https://hook.integromat.com')
        self.api_key = api_key or os.getenv('MAKE_API_KEY')
        self.webhook_configs: Dict[str, MakeWebhookConfig] = {}
        self.scenario_templates: Dict[str, MakeScenarioTemplate] = {}
        self.session = requests.Session()
        
        # Configure session headers
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def register_webhook(self, config: MakeWebhookConfig) -> bool:
        """Register a new Make.com webhook"""
        try:
            self.webhook_configs[config.scenario_id] = config
            logger.info(f"Registered Make.com webhook for scenario {config.scenario_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register webhook: {e}")
            return False
    
    def trigger_scenario(self, scenario_id: str, payload: Dict[str, Any]) -> bool:
        """Trigger a Make.com scenario with payload"""
        if scenario_id not in self.webhook_configs:
            logger.error(f"Webhook config not found for scenario {scenario_id}")
            return False
        
        config = self.webhook_configs[scenario_id]
        
        if not config.enabled:
            logger.warning(f"Webhook {scenario_id} is disabled")
            return False
        
        try:
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AI-Empire-Platform/1.0'
            }
            
            # Add authentication headers
            if config.authentication_method == "bearer" and config.secret_key:
                headers['Authorization'] = f'Bearer {config.secret_key}'
            elif config.authentication_method == "custom" and config.custom_headers:
                headers.update(config.custom_headers)
            
            # Add custom headers if specified
            if config.custom_headers:
                headers.update(config.custom_headers)
            
            # Add webhook signature for security
            if config.secret_key:
                payload_str = json.dumps(payload, sort_keys=True)
                signature = hmac.new(
                    config.secret_key.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers['X-Make-Signature'] = f'sha256={signature}'
            
            # Add metadata to payload
            enhanced_payload = {
                **payload,
                '_make_metadata': {
                    'scenario_id': scenario_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'ai_empire_platform',
                    'webhook_id': str(uuid.uuid4())
                }
            }
            
            # Send webhook request
            response = self.session.post(
                config.webhook_url,
                json=enhanced_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Successfully triggered Make.com scenario {scenario_id}")
                return True
            else:
                logger.error(f"Make.com webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to trigger Make.com scenario {scenario_id}: {e}")
            return False
    
    def batch_trigger_scenarios(self, triggers: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Trigger multiple Make.com scenarios in batch"""
        results = {}
        
        for trigger in triggers:
            scenario_id = trigger.get('scenario_id')
            payload = trigger.get('payload', {})
            
            if scenario_id:
                results[scenario_id] = self.trigger_scenario(scenario_id, payload)
            else:
                logger.error("Missing scenario_id in batch trigger")
                results['invalid'] = False
        
        return results
    
    def get_scenario_templates(self) -> Dict[str, MakeScenarioTemplate]:
        """Get all available scenario templates"""
        return self.scenario_templates
    
    def get_template_by_category(self, category: str) -> List[MakeScenarioTemplate]:
        """Get scenario templates by category"""
        return [template for template in self.scenario_templates.values() 
                if template.category == category]
    
    def validate_webhook_payload(self, scenario_id: str, payload: Dict[str, Any]) -> bool:
        """Validate payload against scenario template"""
        if scenario_id not in self.scenario_templates:
            return True  # Allow if no template defined
        
        template = self.scenario_templates[scenario_id]
        expected_structure = template.expected_data_structure
        
        # Basic validation - ensure required fields are present
        for key, field_type in expected_structure.items():
            if key not in payload:
                logger.warning(f"Missing required field {key} in payload for scenario {scenario_id}")
                return False
            
            # Type validation could be added here
        
        return True
    
    def get_webhook_status(self, scenario_id: str) -> Dict[str, Any]:
        """Get webhook status and statistics"""
        if scenario_id not in self.webhook_configs:
            return {"error": "Webhook not found"}
        
        config = self.webhook_configs[scenario_id]
        
        return {
            "scenario_id": scenario_id,
            "status": "active" if config.enabled else "inactive",
            "webhook_url": config.webhook_url,
            "event_types": [event.value for event in config.event_types],
            "authentication": config.authentication_method,
            "last_triggered": None,  # Would be tracked in database
            "success_rate": None,    # Would be calculated from execution logs
            "total_executions": None  # Would be tracked in database
        }

class MakeWorkflowTemplateManager:
    """Manager for Make.com workflow templates"""
    
    def __init__(self):
        self.templates = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default scenario templates"""
        
        # Lead Nurturing Template
        self.templates["lead_nurturing"] = MakeScenarioTemplate(
            template_id="lead_nurturing",
            name="AI Lead Nurturing Automation",
            description="Automatically nurture leads with personalized communication based on engagement and profile",
            category="lead_management",
            trigger_events=[MakeEventType.LEAD_QUALIFIED, MakeEventType.APOLLO_LEAD_ENRICHED],
            expected_data_structure={
                "lead_id": "string",
                "lead_email": "string",
                "lead_name": "string",
                "company": "string",
                "title": "string",
                "engagement_score": "number",
                "lead_source": "string",
                "industry": "string",
                "company_size": "string"
            },
            sample_payload={
                "lead_id": "12345",
                "lead_email": "john.doe@example.com",
                "lead_name": "John Doe",
                "company": "TechCorp Inc",
                "title": "Chief Technology Officer",
                "engagement_score": 85,
                "lead_source": "linkedin",
                "industry": "technology",
                "company_size": "enterprise"
            },
            configuration_steps=[
                "Set up email integration (Gmail, Outlook, or SMTP)",
                "Configure lead scoring logic",
                "Create email templates for different engagement levels",
                "Set up delay timers between communications",
                "Configure CRM integration for lead updates"
            ],
            required_integrations=["Email", "CRM", "Calendar"],
            estimated_operations=15,
            complexity_level="intermediate"
        )
        
        # Opportunity Management Template
        self.templates["opportunity_management"] = MakeScenarioTemplate(
            template_id="opportunity_management",
            name="Executive Opportunity Pipeline Automation",
            description="Automate opportunity tracking, follow-ups, and pipeline management for executive positions",
            category="opportunity_management",
            trigger_events=[MakeEventType.OPPORTUNITY_CREATED, MakeEventType.OPPORTUNITY_UPDATED, MakeEventType.INTERVIEW_SCHEDULED],
            expected_data_structure={
                "opportunity_id": "string",
                "title": "string",
                "company": "string",
                "type": "string",
                "status": "string",
                "compensation_range": "string",
                "application_date": "string",
                "next_step": "string",
                "interview_stages": "array",
                "priority_level": "string"
            },
            sample_payload={
                "opportunity_id": "opp_67890",
                "title": "Chief Risk Officer",
                "company": "Global Financial Services",
                "type": "executive_position",
                "status": "interview_stage",
                "compensation_range": "$500K-$750K",
                "application_date": "2024-03-15",
                "next_step": "Second round interview",
                "interview_stages": [{"stage": "Initial screening", "status": "completed"}],
                "priority_level": "high"
            },
            configuration_steps=[
                "Connect calendar integration for interview scheduling",
                "Set up CRM updates for opportunity tracking",
                "Configure email templates for follow-ups",
                "Create Slack/Teams notifications for status changes",
                "Set up document generation for interview prep"
            ],
            required_integrations=["Calendar", "CRM", "Email", "Slack/Teams", "Document Generator"],
            estimated_operations=20,
            complexity_level="advanced"
        )
        
        # Agent Coordination Template
        self.templates["agent_coordination"] = MakeScenarioTemplate(
            template_id="agent_coordination",
            name="AI Agent Performance & Coordination",
            description="Coordinate AI agents, monitor performance, and trigger actions based on agent metrics",
            category="agent_management",
            trigger_events=[MakeEventType.AGENT_PERFORMANCE_ALERT, MakeEventType.WORKFLOW_EXECUTION_COMPLETE],
            expected_data_structure={
                "agent_id": "string",
                "agent_name": "string",
                "tier": "string",
                "performance_metrics": "object",
                "status": "string",
                "alert_type": "string",
                "threshold_breached": "boolean",
                "recommended_actions": "array"
            },
            sample_payload={
                "agent_id": "agent_001",
                "agent_name": "Speaking Opportunity Hunter Agent",
                "tier": "revenue_generation",
                "performance_metrics": {
                    "opportunities_found": 23,
                    "success_rate": 87.2,
                    "pipeline_value": 175000
                },
                "status": "underperforming",
                "alert_type": "performance_degradation",
                "threshold_breached": True,
                "recommended_actions": ["retrain_model", "adjust_parameters", "increase_search_scope"]
            },
            configuration_steps=[
                "Configure performance monitoring thresholds",
                "Set up agent retraining workflows",
                "Create performance dashboards",
                "Set up alert notifications to admin team",
                "Configure automatic parameter adjustments"
            ],
            required_integrations=["Monitoring Dashboard", "Alert System", "Database", "Analytics Platform"],
            estimated_operations=12,
            complexity_level="intermediate"
        )
        
        # Speaking Opportunity Automation Template
        self.templates["speaking_automation"] = MakeScenarioTemplate(
            template_id="speaking_automation",
            name="Speaking Opportunity Application Automation",
            description="Automatically apply to speaking opportunities and manage the application pipeline",
            category="business_development",
            trigger_events=[MakeEventType.SPEAKING_OPPORTUNITY_FOUND, MakeEventType.FOLLOW_UP_REQUIRED],
            expected_data_structure={
                "opportunity_id": "string",
                "event_name": "string",
                "organizer": "string",
                "event_date": "string",
                "submission_deadline": "string",
                "topic_alignment": "array",
                "ai_match_score": "number",
                "speaking_fee": "string",
                "application_status": "string"
            },
            sample_payload={
                "opportunity_id": "speak_456",
                "event_name": "AI Governance Summit 2024",
                "organizer": "Tech Conference Group",
                "event_date": "2024-09-15",
                "submission_deadline": "2024-06-01",
                "topic_alignment": ["AI governance", "risk management", "compliance"],
                "ai_match_score": 92,
                "speaking_fee": "$25,000",
                "application_status": "ready_to_apply"
            },
            configuration_steps=[
                "Set up application form auto-fill",
                "Configure speaker bio and presentation templates",
                "Set up calendar integration for event scheduling",
                "Create follow-up email sequences",
                "Configure contract management workflow"
            ],
            required_integrations=["Form Filler", "Document Generator", "Calendar", "Email", "CRM"],
            estimated_operations=18,
            complexity_level="intermediate"
        )
        
        # Revenue Milestone Tracking Template
        self.templates["revenue_tracking"] = MakeScenarioTemplate(
            template_id="revenue_tracking",
            name="Revenue Milestone & Alert Automation",
            description="Track revenue milestones and trigger celebrations, reports, and strategic actions",
            category="financial_management",
            trigger_events=[MakeEventType.REVENUE_MILESTONE],
            expected_data_structure={
                "milestone_type": "string",
                "milestone_value": "number",
                "current_value": "number",
                "percentage_complete": "number",
                "revenue_stream": "string",
                "achievement_date": "string",
                "next_milestone": "object"
            },
            sample_payload={
                "milestone_type": "monthly_target",
                "milestone_value": 100000,
                "current_value": 105000,
                "percentage_complete": 105,
                "revenue_stream": "speaking_engagements",
                "achievement_date": "2024-03-31",
                "next_milestone": {"type": "quarterly", "value": 300000, "due_date": "2024-06-30"}
            },
            configuration_steps=[
                "Set up financial data integration",
                "Configure milestone tracking logic",
                "Create celebration workflows (team notifications)",
                "Set up executive reporting automation",
                "Configure strategic planning triggers"
            ],
            required_integrations=["Financial System", "Reporting Tool", "Team Communication", "Analytics"],
            estimated_operations=10,
            complexity_level="beginner"
        )
        
        # Research & Content Automation Template
        self.templates["research_content"] = MakeScenarioTemplate(
            template_id="research_content",
            name="AI Research to Content Pipeline",
            description="Convert Perplexity research results into various content formats and distribute",
            category="content_management",
            trigger_events=[MakeEventType.PERPLEXITY_RESEARCH_COMPLETE, MakeEventType.CONTENT_PUBLISHED],
            expected_data_structure={
                "research_id": "string",
                "research_type": "string",
                "subject": "string",
                "analysis": "string",
                "key_findings": "array",
                "recommendations": "array",
                "confidence_score": "number",
                "target_content_types": "array"
            },
            sample_payload={
                "research_id": "research_789",
                "research_type": "industry",
                "subject": "AI Governance Trends 2024",
                "analysis": "Comprehensive analysis of current AI governance landscape...",
                "key_findings": ["Regulatory compliance increasing", "Board oversight expanding"],
                "recommendations": ["Develop governance framework", "Create compliance checklist"],
                "confidence_score": 0.95,
                "target_content_types": ["blog_post", "linkedin_article", "speaking_topics"]
            },
            configuration_steps=[
                "Connect content management system",
                "Set up AI content generation tools",
                "Configure social media publishing",
                "Set up SEO optimization workflow",
                "Create content approval process"
            ],
            required_integrations=["CMS", "AI Writing Tool", "Social Media", "SEO Tool", "Approval System"],
            estimated_operations=25,
            complexity_level="advanced"
        )

def create_make_integration_service():
    """Factory function to create Make.com integration service"""
    return MakeIntegrationService()

def create_workflow_template_manager():
    """Factory function to create workflow template manager"""
    return MakeWorkflowTemplateManager()

# Event trigger utility functions
def trigger_opportunity_event(make_service: MakeIntegrationService, opportunity_data: Dict[str, Any], event_type: MakeEventType):
    """Trigger Make.com scenarios for opportunity events"""
    # Find scenarios that listen to this event type
    matching_scenarios = []
    for scenario_id, config in make_service.webhook_configs.items():
        if event_type in config.event_types:
            matching_scenarios.append(scenario_id)
    
    # Trigger all matching scenarios
    results = {}
    for scenario_id in matching_scenarios:
        results[scenario_id] = make_service.trigger_scenario(scenario_id, opportunity_data)
    
    return results

def trigger_agent_performance_event(make_service: MakeIntegrationService, agent_data: Dict[str, Any]):
    """Trigger Make.com scenarios for agent performance events"""
    return trigger_opportunity_event(make_service, agent_data, MakeEventType.AGENT_PERFORMANCE_ALERT)

def trigger_revenue_milestone_event(make_service: MakeIntegrationService, revenue_data: Dict[str, Any]):
    """Trigger Make.com scenarios for revenue milestone events"""
    return trigger_opportunity_event(make_service, revenue_data, MakeEventType.REVENUE_MILESTONE)

def trigger_speaking_opportunity_event(make_service: MakeIntegrationService, speaking_data: Dict[str, Any]):
    """Trigger Make.com scenarios for speaking opportunity events"""
    return trigger_opportunity_event(make_service, speaking_data, MakeEventType.SPEAKING_OPPORTUNITY_FOUND)

def trigger_research_complete_event(make_service: MakeIntegrationService, research_data: Dict[str, Any]):
    """Trigger Make.com scenarios for completed research events"""
    return trigger_opportunity_event(make_service, research_data, MakeEventType.PERPLEXITY_RESEARCH_COMPLETE)