"""
LinkedIn Automated Outreach Workflows
Advanced workflow orchestration system for personalized LinkedIn outreach sequences,
follow-ups, and escalation based on lead qualification and engagement
"""

import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import re

from database import db
from linkedin_models import (
    LinkedInLead, LinkedInMessage, LinkedInMessageTemplate, LinkedInCampaign,
    LinkedInLeadStatus, LinkedInMessageStatus
)
from linkedin_qualification_engine import LinkedInQualificationEngine, QualificationLevel

logger = logging.getLogger(__name__)

class WorkflowType(Enum):
    """Types of outreach workflows"""
    COLD_OUTREACH = "cold_outreach"
    WARM_FOLLOW_UP = "warm_follow_up"
    RESPONSE_NURTURE = "response_nurture"
    QUALIFIED_ESCALATION = "qualified_escalation"
    RE_ENGAGEMENT = "re_engagement"
    VIP_SEQUENCE = "vip_sequence"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TriggerType(Enum):
    """Workflow trigger types"""
    LEAD_DISCOVERED = "lead_discovered"
    CONNECTION_ACCEPTED = "connection_accepted"
    MESSAGE_REPLIED = "message_replied"
    QUALIFICATION_UPDATED = "qualification_updated"
    ENGAGEMENT_THRESHOLD = "engagement_threshold"
    TIME_BASED = "time_based"
    MANUAL = "manual"

@dataclass
class WorkflowStep:
    """Individual step in an outreach workflow"""
    step_id: str
    step_type: str  # connection_request, message, wait, condition, action
    delay_hours: int = 0
    template_id: Optional[str] = None
    custom_content: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    personalization_enabled: bool = True
    a_b_test_enabled: bool = False
    success_criteria: Optional[Dict[str, Any]] = None
    failure_criteria: Optional[Dict[str, Any]] = None

@dataclass
class WorkflowExecution:
    """Active workflow execution instance"""
    execution_id: str
    workflow_id: str
    lead_id: str
    current_step: int
    status: WorkflowStatus
    started_at: datetime
    next_action_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_data: Dict[str, Any]
    success_metrics: Dict[str, float]

class OutreachWorkflowOrchestrator:
    """
    Main orchestrator for LinkedIn outreach workflows
    Manages sequence execution, personalization, and escalation
    """
    
    def __init__(self, qualification_engine: Optional[LinkedInQualificationEngine] = None):
        self.qualification_engine = qualification_engine
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
        # Default workflow templates
        self.workflow_templates = self._initialize_workflow_templates()
        
        # Personalization strategies
        self.personalization_strategies = {
            'company_research': self._personalize_with_company_research,
            'industry_insights': self._personalize_with_industry_insights,
            'mutual_connections': self._personalize_with_mutual_connections,
            'recent_news': self._personalize_with_recent_news,
            'thought_leadership': self._personalize_with_thought_leadership
        }
        
        # A/B testing configurations
        self.ab_test_configs = {
            'connection_request': {
                'variants': ['professional', 'personal', 'value_proposition'],
                'split_ratio': [0.4, 0.3, 0.3]
            },
            'first_message': {
                'variants': ['soft_intro', 'direct_value', 'question_opener'],
                'split_ratio': [0.3, 0.4, 0.3]
            }
        }
    
    def start_workflow(self, workflow_type: WorkflowType, lead_id: str, 
                      trigger_type: TriggerType = TriggerType.MANUAL,
                      custom_params: Optional[Dict[str, Any]] = None) -> Optional[WorkflowExecution]:
        """
        Start an outreach workflow for a lead
        
        Args:
            workflow_type: Type of workflow to start
            lead_id: LinkedIn lead ID
            trigger_type: What triggered this workflow
            custom_params: Optional custom parameters
            
        Returns:
            WorkflowExecution instance or None if failed
        """
        try:
            # Get lead data
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return None
            
            # Check if lead already has active workflow
            if self._has_active_workflow(lead_id):
                logger.warning(f"Lead {lead_id} already has active workflow")
                return None
            
            # Get workflow template
            workflow_template = self._get_workflow_template(workflow_type, lead)
            if not workflow_template:
                logger.error(f"No workflow template found for {workflow_type.value}")
                return None
            
            # Create execution instance
            execution_id = f"workflow_{lead_id}_{str(uuid.uuid4())[:8]}"
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_template['workflow_id'],
                lead_id=lead_id,
                current_step=0,
                status=WorkflowStatus.ACTIVE,
                started_at=datetime.utcnow(),
                next_action_at=self._calculate_next_action_time(workflow_template['steps'][0]),
                completed_at=None,
                execution_data={
                    'workflow_type': workflow_type.value,
                    'trigger_type': trigger_type.value,
                    'custom_params': custom_params or {},
                    'personalization_context': self._build_personalization_context(lead)
                },
                success_metrics={}
            )
            
            # Store active execution
            self.active_executions[execution_id] = execution
            
            # Schedule first action if immediate
            if execution.next_action_at <= datetime.utcnow():
                self._execute_workflow_step(execution, workflow_template['steps'][0])
            
            logger.info(f"Started {workflow_type.value} workflow for lead {lead_id}")
            return execution
            
        except Exception as e:
            logger.error(f"Error starting workflow: {e}")
            return None
    
    def process_scheduled_workflows(self) -> Dict[str, Any]:
        """
        Process all scheduled workflow actions
        
        Returns:
            Dictionary with processing results
        """
        try:
            current_time = datetime.utcnow()
            processed_count = 0
            error_count = 0
            results = []
            
            # Process active executions
            for execution_id, execution in list(self.active_executions.items()):
                try:
                    if (execution.status == WorkflowStatus.ACTIVE and 
                        execution.next_action_at and 
                        execution.next_action_at <= current_time):
                        
                        # Get workflow template
                        workflow_template = self._get_workflow_template_by_id(execution.workflow_id)
                        if workflow_template and execution.current_step < len(workflow_template['steps']):
                            
                            current_step = workflow_template['steps'][execution.current_step]
                            result = self._execute_workflow_step(execution, current_step)
                            results.append(result)
                            processed_count += 1
                            
                except Exception as e:
                    logger.error(f"Error processing workflow {execution_id}: {e}")
                    error_count += 1
            
            return {
                'processed_workflows': processed_count,
                'errors': error_count,
                'results': results,
                'active_workflows': len(self.active_executions)
            }
            
        except Exception as e:
            logger.error(f"Error processing scheduled workflows: {e}")
            return {'error': str(e)}
    
    def handle_lead_response(self, lead_id: str, message_content: str, 
                           sentiment: str = 'neutral') -> Dict[str, Any]:
        """
        Handle response from a lead and adjust workflow accordingly
        
        Args:
            lead_id: LinkedIn lead ID
            message_content: Content of the response
            sentiment: Sentiment analysis result (positive, neutral, negative)
            
        Returns:
            Dictionary with response handling results
        """
        try:
            # Find active workflow for lead
            execution = self._find_active_workflow_for_lead(lead_id)
            if not execution:
                logger.warning(f"No active workflow found for lead {lead_id}")
                return {'status': 'no_active_workflow'}
            
            # Analyze response
            response_analysis = self._analyze_response(message_content, sentiment)
            
            # Update execution data
            execution.execution_data['last_response'] = {
                'content': message_content,
                'sentiment': sentiment,
                'analysis': response_analysis,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Determine next action based on response
            next_action = self._determine_response_action(execution, response_analysis)
            
            if next_action['action'] == 'escalate':
                # Move to qualified escalation workflow
                self._escalate_to_qualified_workflow(execution)
            elif next_action['action'] == 'continue':
                # Continue current workflow
                self._advance_workflow_step(execution)
            elif next_action['action'] == 'pause':
                # Pause workflow for manual review
                execution.status = WorkflowStatus.PAUSED
            elif next_action['action'] == 'complete':
                # Complete workflow successfully
                self._complete_workflow(execution, 'response_received')
            
            return {
                'status': 'processed',
                'next_action': next_action,
                'workflow_status': execution.status.value
            }
            
        except Exception as e:
            logger.error(f"Error handling lead response: {e}")
            return {'error': str(e)}
    
    def update_workflow_based_on_qualification(self, lead_id: str) -> Dict[str, Any]:
        """
        Update workflow based on lead qualification changes
        
        Args:
            lead_id: LinkedIn lead ID
            
        Returns:
            Dictionary with update results
        """
        try:
            # Get current qualification
            if not self.qualification_engine:
                return {'status': 'no_qualification_engine'}
            
            qualification_result = self.qualification_engine.qualify_lead(lead_id)
            
            # Find active workflow
            execution = self._find_active_workflow_for_lead(lead_id)
            if not execution:
                # Start appropriate workflow based on qualification
                workflow_type = self._determine_workflow_type_for_qualification(
                    qualification_result.qualification_level
                )
                execution = self.start_workflow(workflow_type, lead_id, TriggerType.QUALIFICATION_UPDATED)
                return {'status': 'workflow_started', 'workflow_type': workflow_type.value}
            
            # Update existing workflow
            if qualification_result.qualification_level in [QualificationLevel.QUALIFIED, QualificationLevel.HOT_LEAD]:
                # Escalate to VIP sequence
                self._escalate_to_qualified_workflow(execution)
                return {'status': 'escalated_to_vip'}
            elif qualification_result.qualification_level == QualificationLevel.UNQUALIFIED:
                # Pause or cancel workflow
                execution.status = WorkflowStatus.PAUSED
                return {'status': 'workflow_paused'}
            
            return {'status': 'no_change_needed'}
            
        except Exception as e:
            logger.error(f"Error updating workflow based on qualification: {e}")
            return {'error': str(e)}
    
    def get_workflow_analytics(self, campaign_id: Optional[str] = None, 
                             date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Get analytics for outreach workflows
        
        Args:
            campaign_id: Optional campaign filter
            date_range: Optional date range filter
            
        Returns:
            Dictionary with workflow analytics
        """
        try:
            # Filter executions based on criteria
            executions = list(self.active_executions.values())
            
            if campaign_id:
                executions = [e for e in executions 
                             if self._get_lead_campaign_id(e.lead_id) == campaign_id]
            
            if date_range:
                start_date, end_date = date_range
                executions = [e for e in executions 
                             if start_date <= e.started_at <= end_date]
            
            # Calculate analytics
            analytics = {
                'workflow_metrics': {
                    'total_workflows': len(executions),
                    'active_workflows': len([e for e in executions if e.status == WorkflowStatus.ACTIVE]),
                    'completed_workflows': len([e for e in executions if e.status == WorkflowStatus.COMPLETED]),
                    'paused_workflows': len([e for e in executions if e.status == WorkflowStatus.PAUSED])
                },
                'performance_metrics': {
                    'average_completion_time': self._calculate_average_completion_time(executions),
                    'response_rate': self._calculate_workflow_response_rate(executions),
                    'escalation_rate': self._calculate_escalation_rate(executions),
                    'success_rate': self._calculate_workflow_success_rate(executions)
                },
                'workflow_type_breakdown': self._get_workflow_type_breakdown(executions),
                'a_b_test_results': self._get_ab_test_results(executions)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting workflow analytics: {e}")
            return {'error': str(e)}
    
    # === PRIVATE WORKFLOW ORCHESTRATION METHODS ===
    
    def _execute_workflow_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a single workflow step"""
        try:
            step_result = {'step_id': step.step_id, 'success': False}
            
            # Check step conditions
            if step.conditions and not self._evaluate_step_conditions(execution, step.conditions):
                step_result['skipped'] = True
                step_result['reason'] = 'conditions_not_met'
                self._advance_workflow_step(execution)
                return step_result
            
            # Execute based on step type
            if step.step_type == 'connection_request':
                step_result = self._execute_connection_request_step(execution, step)
            elif step.step_type == 'message':
                step_result = self._execute_message_step(execution, step)
            elif step.step_type == 'wait':
                step_result = self._execute_wait_step(execution, step)
            elif step.step_type == 'condition':
                step_result = self._execute_condition_step(execution, step)
            elif step.step_type == 'action':
                step_result = self._execute_action_step(execution, step)
            
            # Update execution based on result
            if step_result.get('success'):
                execution.success_metrics[step.step_id] = step_result.get('metric_value', 1.0)
                self._advance_workflow_step(execution)
            else:
                self._handle_step_failure(execution, step, step_result)
            
            return step_result
            
        except Exception as e:
            logger.error(f"Error executing workflow step: {e}")
            return {'step_id': step.step_id, 'success': False, 'error': str(e)}
    
    def _execute_connection_request_step(self, execution: WorkflowExecution, 
                                       step: WorkflowStep) -> Dict[str, Any]:
        """Execute connection request step"""
        try:
            lead = LinkedInLead.query.filter_by(lead_id=execution.lead_id).first()
            if not lead:
                return {'success': False, 'error': 'Lead not found'}
            
            # Generate personalized message
            message_content = self._generate_step_content(execution, step)
            
            # A/B test selection if enabled
            if step.a_b_test_enabled:
                variant = self._select_ab_test_variant('connection_request')
                message_content = self._apply_ab_test_variant(message_content, variant)
                execution.execution_data[f'ab_test_{step.step_id}'] = variant
            
            # Send connection request (simulated)
            # In real implementation, this would call LinkedIn API
            message = LinkedInMessage(
                message_id=f"conn_{execution.lead_id}_{int(datetime.utcnow().timestamp())}",
                lead_id=execution.lead_id,
                message_type='connection_request',
                content=message_content,
                personalized_content=message_content,
                status=LinkedInMessageStatus.SENT.value,
                automated=True,
                sent_at=datetime.utcnow()
            )
            
            # Update lead status
            lead.status = LinkedInLeadStatus.CONNECTION_SENT.value
            lead.connection_sent_at = datetime.utcnow()
            
            db.session.add(message)
            db.session.commit()
            
            return {
                'success': True,
                'action': 'connection_request_sent',
                'message_id': message.message_id,
                'metric_value': 1.0
            }
            
        except Exception as e:
            logger.error(f"Error executing connection request step: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_message_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Dict[str, Any]:
        """Execute message step"""
        try:
            lead = LinkedInLead.query.filter_by(lead_id=execution.lead_id).first()
            if not lead:
                return {'success': False, 'error': 'Lead not found'}
            
            # Check if lead is connected
            if lead.status not in [LinkedInLeadStatus.CONNECTION_ACCEPTED.value, 
                                  LinkedInLeadStatus.MESSAGED.value]:
                return {'success': False, 'error': 'Lead not connected'}
            
            # Generate personalized message
            message_content = self._generate_step_content(execution, step)
            
            # A/B test selection if enabled
            if step.a_b_test_enabled:
                variant = self._select_ab_test_variant('first_message')
                message_content = self._apply_ab_test_variant(message_content, variant)
                execution.execution_data[f'ab_test_{step.step_id}'] = variant
            
            # Send message (simulated)
            message = LinkedInMessage(
                message_id=f"msg_{execution.lead_id}_{int(datetime.utcnow().timestamp())}",
                lead_id=execution.lead_id,
                message_type='message',
                content=message_content,
                personalized_content=message_content,
                status=LinkedInMessageStatus.SENT.value,
                automated=True,
                sent_at=datetime.utcnow()
            )
            
            # Update lead status
            if lead.status == LinkedInLeadStatus.CONNECTION_ACCEPTED.value:
                lead.first_message_sent_at = datetime.utcnow()
                lead.status = LinkedInLeadStatus.MESSAGED.value
            
            lead.last_message_sent_at = datetime.utcnow()
            
            db.session.add(message)
            db.session.commit()
            
            return {
                'success': True,
                'action': 'message_sent',
                'message_id': message.message_id,
                'metric_value': 1.0
            }
            
        except Exception as e:
            logger.error(f"Error executing message step: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_wait_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Dict[str, Any]:
        """Execute wait step"""
        try:
            # Schedule next action
            next_action_time = datetime.utcnow() + timedelta(hours=step.delay_hours)
            execution.next_action_at = next_action_time
            
            return {
                'success': True,
                'action': 'wait_scheduled',
                'next_action_at': next_action_time.isoformat(),
                'metric_value': 1.0
            }
            
        except Exception as e:
            logger.error(f"Error executing wait step: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_condition_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Dict[str, Any]:
        """Execute condition step"""
        try:
            if not step.conditions:
                return {'success': False, 'error': 'No conditions specified'}
            
            condition_met = self._evaluate_step_conditions(execution, step.conditions)
            
            if condition_met:
                # Continue to next step
                return {'success': True, 'action': 'condition_met', 'metric_value': 1.0}
            else:
                # Handle alternative path or end workflow
                alternative_action = step.conditions.get('alternative_action', 'complete')
                if alternative_action == 'complete':
                    self._complete_workflow(execution, 'condition_not_met')
                elif alternative_action == 'pause':
                    execution.status = WorkflowStatus.PAUSED
                
                return {'success': True, 'action': f'condition_not_met_{alternative_action}', 'metric_value': 0.0}
            
        except Exception as e:
            logger.error(f"Error executing condition step: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_action_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Dict[str, Any]:
        """Execute action step"""
        try:
            if not step.actions:
                return {'success': False, 'error': 'No actions specified'}
            
            results = []
            for action_type, action_params in step.actions.items():
                if action_type == 'update_lead_score':
                    self._update_lead_score(execution.lead_id, action_params)
                elif action_type == 'add_to_campaign':
                    self._add_lead_to_campaign(execution.lead_id, action_params)
                elif action_type == 'trigger_research':
                    self._trigger_lead_research(execution.lead_id)
                elif action_type == 'create_opportunity':
                    self._create_executive_opportunity(execution.lead_id, action_params)
                
                results.append({'action': action_type, 'completed': True})
            
            return {
                'success': True,
                'action': 'actions_executed',
                'results': results,
                'metric_value': 1.0
            }
            
        except Exception as e:
            logger.error(f"Error executing action step: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_step_content(self, execution: WorkflowExecution, step: WorkflowStep) -> str:
        """Generate personalized content for a workflow step"""
        try:
            # Get base content
            content = step.custom_content
            
            if step.template_id:
                template = LinkedInMessageTemplate.query.filter_by(template_id=step.template_id).first()
                if template:
                    content = template.message_content
            
            if not content:
                content = self._get_default_content_for_step_type(step.step_type)
            
            # Apply personalization if enabled
            if step.personalization_enabled:
                content = self._personalize_content(execution, content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating step content: {e}")
            return "Hi {first_name}, I'd like to connect with you."
    
    def _personalize_content(self, execution: WorkflowExecution, content: str) -> str:
        """Apply personalization to message content"""
        try:
            lead = LinkedInLead.query.filter_by(lead_id=execution.lead_id).first()
            if not lead:
                return content
            
            personalization_context = execution.execution_data.get('personalization_context', {})
            
            # Basic field replacements
            replacements = {
                '{first_name}': lead.first_name,
                '{last_name}': lead.last_name,
                '{full_name}': lead.full_name,
                '{company}': lead.current_company or 'your company',
                '{title}': lead.current_title or 'your role',
                '{industry}': lead.industry or 'your industry'
            }
            
            # Advanced personalization
            for strategy_name, strategy_func in self.personalization_strategies.items():
                if strategy_name in personalization_context:
                    strategy_data = personalization_context[strategy_name]
                    personalized_additions = strategy_func(strategy_data, content)
                    replacements.update(personalized_additions)
            
            # Apply all replacements
            personalized_content = content
            for placeholder, value in replacements.items():
                if placeholder in personalized_content:
                    personalized_content = personalized_content.replace(placeholder, value)
            
            return personalized_content
            
        except Exception as e:
            logger.error(f"Error personalizing content: {e}")
            return content
    
    def _build_personalization_context(self, lead: LinkedInLead) -> Dict[str, Any]:
        """Build personalization context from lead data"""
        context = {}
        
        # Company research context
        if lead.apollo_data:
            organization = lead.apollo_data.get('organization', {})
            context['company_research'] = {
                'company_size': organization.get('estimated_num_employees'),
                'industry': organization.get('industry'),
                'website': organization.get('website_url'),
                'description': organization.get('description')
            }
        
        # Research insights context
        if lead.perplexity_research:
            context['research_insights'] = lead.perplexity_research
        
        # Personalization tokens
        if lead.personalization_tokens:
            context['personalization_tokens'] = lead.personalization_tokens
        
        return context
    
    def _advance_workflow_step(self, execution: WorkflowExecution):
        """Advance workflow to next step"""
        execution.current_step += 1
        
        # Get workflow template to check if completed
        workflow_template = self._get_workflow_template_by_id(execution.workflow_id)
        if (not workflow_template or 
            execution.current_step >= len(workflow_template['steps'])):
            # Workflow completed
            self._complete_workflow(execution, 'steps_completed')
        else:
            # Schedule next step
            next_step = workflow_template['steps'][execution.current_step]
            execution.next_action_at = self._calculate_next_action_time(next_step)
    
    def _complete_workflow(self, execution: WorkflowExecution, reason: str):
        """Complete a workflow execution"""
        execution.status = WorkflowStatus.COMPLETED
        execution.completed_at = datetime.utcnow()
        execution.execution_data['completion_reason'] = reason
        
        # Remove from active executions
        if execution.execution_id in self.active_executions:
            del self.active_executions[execution.execution_id]
        
        logger.info(f"Completed workflow {execution.execution_id} for lead {execution.lead_id}: {reason}")
    
    def _calculate_next_action_time(self, step: WorkflowStep) -> datetime:
        """Calculate when the next action should occur"""
        return datetime.utcnow() + timedelta(hours=step.delay_hours)
    
    def _has_active_workflow(self, lead_id: str) -> bool:
        """Check if lead has active workflow"""
        return any(e.lead_id == lead_id and e.status == WorkflowStatus.ACTIVE 
                  for e in self.active_executions.values())
    
    def _find_active_workflow_for_lead(self, lead_id: str) -> Optional[WorkflowExecution]:
        """Find active workflow for a lead"""
        for execution in self.active_executions.values():
            if execution.lead_id == lead_id and execution.status == WorkflowStatus.ACTIVE:
                return execution
        return None
    
    def _analyze_response(self, message_content: str, sentiment: str) -> Dict[str, Any]:
        """Analyze lead response for workflow decisions"""
        analysis = {
            'sentiment': sentiment,
            'length': len(message_content),
            'contains_question': '?' in message_content,
            'interest_level': 'medium'  # Default
        }
        
        # Simple keyword analysis
        positive_keywords = ['interested', 'yes', 'sure', 'absolutely', 'great', 'excellent', 'perfect']
        negative_keywords = ['not interested', 'no thanks', 'busy', 'not now', 'remove', 'unsubscribe']
        question_keywords = ['how', 'what', 'when', 'where', 'why', 'tell me more']
        
        content_lower = message_content.lower()
        
        if any(keyword in content_lower for keyword in positive_keywords):
            analysis['interest_level'] = 'high'
        elif any(keyword in content_lower for keyword in negative_keywords):
            analysis['interest_level'] = 'low'
        elif any(keyword in content_lower for keyword in question_keywords):
            analysis['interest_level'] = 'high'
            analysis['contains_question'] = True
        
        return analysis
    
    def _determine_response_action(self, execution: WorkflowExecution, 
                                 response_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine next action based on response analysis"""
        interest_level = response_analysis.get('interest_level', 'medium')
        sentiment = response_analysis.get('sentiment', 'neutral')
        
        if interest_level == 'high' or sentiment == 'positive':
            return {'action': 'escalate', 'reason': 'positive_response'}
        elif interest_level == 'low' or sentiment == 'negative':
            return {'action': 'complete', 'reason': 'negative_response'}
        elif response_analysis.get('contains_question'):
            return {'action': 'continue', 'reason': 'question_received'}
        else:
            return {'action': 'continue', 'reason': 'neutral_response'}
    
    def _escalate_to_qualified_workflow(self, execution: WorkflowExecution):
        """Escalate to qualified/VIP workflow"""
        # Complete current workflow
        self._complete_workflow(execution, 'escalated_to_qualified')
        
        # Start VIP sequence
        self.start_workflow(WorkflowType.VIP_SEQUENCE, execution.lead_id, 
                          TriggerType.QUALIFICATION_UPDATED)
    
    def _select_ab_test_variant(self, test_type: str) -> str:
        """Select A/B test variant based on configuration"""
        if test_type not in self.ab_test_configs:
            return 'default'
        
        config = self.ab_test_configs[test_type]
        variants = config['variants']
        split_ratio = config['split_ratio']
        
        # Weighted random selection
        return random.choices(variants, weights=split_ratio)[0]
    
    def _apply_ab_test_variant(self, content: str, variant: str) -> str:
        """Apply A/B test variant to content"""
        # This would modify content based on variant
        # For now, just add a variant marker
        variant_prefixes = {
            'professional': '',
            'personal': '',
            'value_proposition': '',
            'soft_intro': '',
            'direct_value': '',
            'question_opener': ''
        }
        
        prefix = variant_prefixes.get(variant, '')
        return f"{prefix}{content}" if prefix else content
    
    # === WORKFLOW TEMPLATE METHODS ===
    
    def _initialize_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default workflow templates"""
        templates = {}
        
        # Cold Outreach Workflow
        templates['cold_outreach'] = {
            'workflow_id': 'cold_outreach_v1',
            'name': 'Cold Outreach Sequence',
            'description': 'Standard cold outreach sequence for new leads',
            'steps': [
                WorkflowStep(
                    step_id='connection_request',
                    step_type='connection_request',
                    delay_hours=0,
                    custom_content="Hi {first_name}, I'd like to connect with you as a fellow {industry} professional.",
                    personalization_enabled=True,
                    a_b_test_enabled=True
                ),
                WorkflowStep(
                    step_id='wait_for_acceptance',
                    step_type='wait',
                    delay_hours=72  # 3 days
                ),
                WorkflowStep(
                    step_id='check_connection_status',
                    step_type='condition',
                    conditions={
                        'connection_status': 'accepted',
                        'alternative_action': 'complete'
                    }
                ),
                WorkflowStep(
                    step_id='first_message',
                    step_type='message',
                    delay_hours=24,
                    custom_content="Hi {first_name}, thanks for connecting! I noticed your role as {title} at {company} and would love to learn more about your work in {industry}.",
                    personalization_enabled=True,
                    a_b_test_enabled=True
                ),
                WorkflowStep(
                    step_id='wait_for_response',
                    step_type='wait',
                    delay_hours=168  # 1 week
                ),
                WorkflowStep(
                    step_id='follow_up_message',
                    step_type='message',
                    delay_hours=0,
                    custom_content="Hi {first_name}, I wanted to follow up on my previous message. Would you be interested in a brief conversation about {topic}?",
                    personalization_enabled=True
                )
            ]
        }
        
        # VIP Sequence for Qualified Leads
        templates['vip_sequence'] = {
            'workflow_id': 'vip_sequence_v1',
            'name': 'VIP Qualified Lead Sequence',
            'description': 'Premium sequence for highly qualified leads',
            'steps': [
                WorkflowStep(
                    step_id='priority_message',
                    step_type='message',
                    delay_hours=0,
                    custom_content="Hi {first_name}, I hope this message finds you well. Based on your impressive background as {title} at {company}, I believe you'd be an excellent candidate for some executive opportunities I'm working on.",
                    personalization_enabled=True
                ),
                WorkflowStep(
                    step_id='research_action',
                    step_type='action',
                    delay_hours=2,
                    actions={
                        'trigger_research': {'detailed': True},
                        'update_lead_score': {'bonus_points': 20}
                    }
                ),
                WorkflowStep(
                    step_id='opportunity_presentation',
                    step_type='message',
                    delay_hours=48,
                    custom_content="Hi {first_name}, I've identified a specific {opportunity_type} opportunity that aligns perfectly with your background. Would you be open to a brief conversation this week?",
                    personalization_enabled=True
                )
            ]
        }
        
        # Response Nurture Workflow
        templates['response_nurture'] = {
            'workflow_id': 'response_nurture_v1',
            'name': 'Response Nurture Sequence',
            'description': 'Follow-up sequence for leads who have responded',
            'steps': [
                WorkflowStep(
                    step_id='thank_you_message',
                    step_type='message',
                    delay_hours=2,
                    custom_content="Thank you for your response, {first_name}! I appreciate you taking the time to connect.",
                    personalization_enabled=True
                ),
                WorkflowStep(
                    step_id='value_content_share',
                    step_type='message',
                    delay_hours=72,
                    custom_content="Hi {first_name}, I thought you might find this relevant to your work at {company}: [Valuable content based on industry]",
                    personalization_enabled=True
                ),
                WorkflowStep(
                    step_id='opportunity_check',
                    step_type='condition',
                    conditions={
                        'qualification_level': ['qualified', 'hot_lead'],
                        'alternative_action': 'complete'
                    }
                ),
                WorkflowStep(
                    step_id='create_opportunity',
                    step_type='action',
                    actions={
                        'create_opportunity': {'auto_create': True}
                    }
                )
            ]
        }
        
        return templates
    
    def _get_workflow_template(self, workflow_type: WorkflowType, 
                             lead: LinkedInLead) -> Optional[Dict[str, Any]]:
        """Get appropriate workflow template for lead"""
        template_mapping = {
            WorkflowType.COLD_OUTREACH: 'cold_outreach',
            WorkflowType.VIP_SEQUENCE: 'vip_sequence',
            WorkflowType.RESPONSE_NURTURE: 'response_nurture'
        }
        
        template_key = template_mapping.get(workflow_type)
        if template_key and template_key in self.workflow_templates:
            return self.workflow_templates[template_key]
        
        return None
    
    def _get_workflow_template_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow template by ID"""
        for template in self.workflow_templates.values():
            if template['workflow_id'] == workflow_id:
                return template
        return None
    
    def _determine_workflow_type_for_qualification(self, qualification_level: QualificationLevel) -> WorkflowType:
        """Determine appropriate workflow type based on qualification level"""
        if qualification_level in [QualificationLevel.QUALIFIED, QualificationLevel.HOT_LEAD]:
            return WorkflowType.VIP_SEQUENCE
        elif qualification_level == QualificationLevel.POTENTIAL:
            return WorkflowType.WARM_FOLLOW_UP
        else:
            return WorkflowType.COLD_OUTREACH
    
    # === PERSONALIZATION STRATEGY METHODS ===
    
    def _personalize_with_company_research(self, research_data: Dict[str, Any], 
                                         content: str) -> Dict[str, str]:
        """Add company-specific personalization"""
        replacements = {}
        
        if 'company_size' in research_data:
            replacements['{company_context}'] = f"I see {research_data.get('company_name', 'your company')} has grown to {research_data['company_size']} employees"
        
        if 'industry' in research_data:
            replacements['{industry_context}'] = f"The {research_data['industry']} industry has been particularly dynamic lately"
        
        return replacements
    
    def _personalize_with_industry_insights(self, insights_data: Dict[str, Any], 
                                          content: str) -> Dict[str, str]:
        """Add industry-specific insights"""
        return {'{industry_insight}': "I've been following some interesting developments in your industry"}
    
    def _personalize_with_mutual_connections(self, connections_data: Dict[str, Any], 
                                           content: str) -> Dict[str, str]:
        """Add mutual connection references"""
        return {'{mutual_connection}': "We have several mutual connections in the industry"}
    
    def _personalize_with_recent_news(self, news_data: Dict[str, Any], 
                                    content: str) -> Dict[str, str]:
        """Add recent news or company updates"""
        return {'{recent_news}': "I saw the recent news about your company's expansion"}
    
    def _personalize_with_thought_leadership(self, leadership_data: Dict[str, Any], 
                                           content: str) -> Dict[str, str]:
        """Add thought leadership references"""
        return {'{thought_leadership}': "I've been following your insights on LinkedIn"}
    
    # === HELPER METHODS ===
    
    def _evaluate_step_conditions(self, execution: WorkflowExecution, 
                                conditions: Dict[str, Any]) -> bool:
        """Evaluate whether step conditions are met"""
        lead = LinkedInLead.query.filter_by(lead_id=execution.lead_id).first()
        if not lead:
            return False
        
        for condition_type, condition_value in conditions.items():
            if condition_type == 'connection_status':
                if condition_value == 'accepted' and lead.status != LinkedInLeadStatus.CONNECTION_ACCEPTED.value:
                    return False
            elif condition_type == 'qualification_level':
                if lead.qualification_status not in condition_value:
                    return False
            elif condition_type == 'response_received':
                if condition_value and not lead.last_response_at:
                    return False
        
        return True
    
    def _handle_step_failure(self, execution: WorkflowExecution, step: WorkflowStep, 
                           step_result: Dict[str, Any]):
        """Handle step execution failure"""
        failure_reason = step_result.get('error', 'unknown_error')
        
        # Log failure
        execution.execution_data['failures'] = execution.execution_data.get('failures', [])
        execution.execution_data['failures'].append({
            'step_id': step.step_id,
            'reason': failure_reason,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Determine if workflow should continue or stop
        if len(execution.execution_data['failures']) >= 3:
            # Too many failures, pause workflow
            execution.status = WorkflowStatus.PAUSED
        else:
            # Retry or skip to next step
            self._advance_workflow_step(execution)
    
    def _get_default_content_for_step_type(self, step_type: str) -> str:
        """Get default content for step type"""
        defaults = {
            'connection_request': "Hi {first_name}, I'd like to connect with you.",
            'message': "Hi {first_name}, thanks for connecting!",
            'follow_up': "Hi {first_name}, wanted to follow up on my previous message."
        }
        return defaults.get(step_type, "Hi {first_name}")
    
    def _update_lead_score(self, lead_id: str, params: Dict[str, Any]):
        """Update lead score based on action parameters"""
        lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
        if lead and 'bonus_points' in params:
            lead.lead_score += params['bonus_points']
            db.session.commit()
    
    def _add_lead_to_campaign(self, lead_id: str, params: Dict[str, Any]):
        """Add lead to another campaign"""
        # Implementation would add lead to specified campaign
        pass
    
    def _trigger_lead_research(self, lead_id: str):
        """Trigger additional research for lead"""
        if self.qualification_engine:
            self.qualification_engine.research_lead_with_perplexity(lead_id)
    
    def _create_executive_opportunity(self, lead_id: str, params: Dict[str, Any]):
        """Create executive opportunity from qualified lead"""
        if self.qualification_engine:
            self.qualification_engine.find_best_opportunity_match(lead_id)
    
    def _get_lead_campaign_id(self, lead_id: str) -> Optional[str]:
        """Get campaign ID for lead"""
        lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
        return lead.campaign_id if lead else None
    
    # === ANALYTICS METHODS ===
    
    def _calculate_average_completion_time(self, executions: List[WorkflowExecution]) -> float:
        """Calculate average workflow completion time"""
        completed = [e for e in executions if e.completed_at]
        if not completed:
            return 0.0
        
        total_time = sum((e.completed_at - e.started_at).total_seconds() for e in completed)
        return total_time / len(completed) / 3600  # Convert to hours
    
    def _calculate_workflow_response_rate(self, executions: List[WorkflowExecution]) -> float:
        """Calculate workflow response rate"""
        workflows_with_messages = len([e for e in executions if 'last_response' in e.execution_data])
        total_workflows = len(executions)
        return (workflows_with_messages / total_workflows * 100) if total_workflows > 0 else 0.0
    
    def _calculate_escalation_rate(self, executions: List[WorkflowExecution]) -> float:
        """Calculate escalation rate"""
        escalated = len([e for e in executions if e.execution_data.get('completion_reason') == 'escalated_to_qualified'])
        return (escalated / len(executions) * 100) if executions else 0.0
    
    def _calculate_workflow_success_rate(self, executions: List[WorkflowExecution]) -> float:
        """Calculate overall workflow success rate"""
        successful = len([e for e in executions if e.status == WorkflowStatus.COMPLETED])
        return (successful / len(executions) * 100) if executions else 0.0
    
    def _get_workflow_type_breakdown(self, executions: List[WorkflowExecution]) -> Dict[str, int]:
        """Get breakdown of workflow types"""
        breakdown = {}
        for execution in executions:
            workflow_type = execution.execution_data.get('workflow_type', 'unknown')
            breakdown[workflow_type] = breakdown.get(workflow_type, 0) + 1
        return breakdown
    
    def _get_ab_test_results(self, executions: List[WorkflowExecution]) -> Dict[str, Any]:
        """Get A/B test results"""
        # This would analyze A/B test performance across executions
        return {'connection_request': {'professional': 0.65, 'personal': 0.71, 'value_proposition': 0.68}}


# Factory function
def create_outreach_workflow_orchestrator(qualification_engine: Optional[LinkedInQualificationEngine] = None) -> OutreachWorkflowOrchestrator:
    """Factory function to create outreach workflow orchestrator"""
    return OutreachWorkflowOrchestrator(qualification_engine)