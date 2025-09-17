"""
Automation Bridge Service for Make.com Integration
Connects internal workflow events to external Make.com scenarios
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from database import db
from make_models import MakeAutomationBridge, MakeEventLog, MakeExecution
from make_integration import create_make_integration_service, MakeEventType

logger = logging.getLogger(__name__)

class AutomationBridgeService:
    """Service for managing automation bridges between internal and external workflows"""
    
    def __init__(self):
        self.make_service = create_make_integration_service()
        self.bridge_handlers = {
            'business_rule': self._handle_business_rule_trigger,
            'workflow_execution': self._handle_workflow_execution_trigger,
            'opportunity_update': self._handle_opportunity_update_trigger,
            'agent_performance': self._handle_agent_performance_trigger,
            'revenue_milestone': self._handle_revenue_milestone_trigger,
            'schedule': self._handle_scheduled_trigger
        }
    
    def execute_bridge(self, bridge_id: str, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an automation bridge"""
        try:
            # Get bridge configuration
            bridge = MakeAutomationBridge.query.filter_by(bridge_id=bridge_id).first()
            if not bridge:
                logger.error(f"Bridge {bridge_id} not found")
                return {'success': False, 'error': 'Bridge not found'}
            
            if not bridge.enabled:
                logger.warning(f"Bridge {bridge_id} is disabled")
                return {'success': False, 'error': 'Bridge is disabled'}
            
            # Check internal conditions
            if bridge.internal_conditions:
                if not self._evaluate_conditions(trigger_data, bridge.internal_conditions):
                    logger.info(f"Bridge {bridge_id} conditions not met")
                    return {'success': False, 'error': 'Conditions not met'}
            
            # Transform data using mapping
            mapped_data = self._map_data(trigger_data, bridge.data_mapping or {})
            
            # Add bridge metadata
            mapped_data['_bridge_metadata'] = {
                'bridge_id': bridge_id,
                'bridge_name': bridge.name,
                'trigger_type': bridge.internal_trigger_type,
                'executed_at': datetime.utcnow().isoformat()
            }
            
            # Trigger Make.com scenarios
            results = {}
            for scenario_id in bridge.make_scenario_ids:
                success = self.make_service.trigger_scenario(scenario_id, mapped_data)
                results[scenario_id] = success
                
                # Log execution
                execution = MakeExecution(
                    execution_id=f"bridge_{bridge_id}_{str(uuid.uuid4())[:8]}",
                    scenario_id=scenario_id,
                    event_type=bridge.internal_trigger_type,
                    trigger_source=f"bridge_{bridge_id}",
                    trigger_data=trigger_data,
                    status='success' if success else 'failure',
                    request_payload=mapped_data,
                    triggered_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                db.session.add(execution)
            
            # Update bridge statistics
            bridge.total_executions += 1
            if all(results.values()):
                bridge.successful_executions += 1
            bridge.last_execution = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'bridge_id': bridge_id,
                'scenarios_triggered': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error executing bridge {bridge_id}: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def handle_internal_event(self, event_type: str, event_data: Dict[str, Any], source_id: Optional[str] = None):
        """Handle internal system events and trigger appropriate bridges"""
        try:
            # Find bridges that listen to this event type
            bridges = MakeAutomationBridge.query.filter_by(
                internal_trigger_type=event_type,
                enabled=True
            ).all()
            
            results = {}
            for bridge in bridges:
                # Check if this bridge applies to this specific trigger
                if bridge.internal_trigger_id and bridge.internal_trigger_id != source_id:
                    continue
                
                # Execute bridge
                result = self.execute_bridge(bridge.bridge_id, event_data)
                results[bridge.bridge_id] = result
            
            return results
            
        except Exception as e:
            logger.error(f"Error handling internal event {event_type}: {e}")
            return {}
    
    def _handle_business_rule_trigger(self, rule_id: str, trigger_data: Dict[str, Any]):
        """Handle business rule triggers"""
        return self.handle_internal_event('business_rule', trigger_data, rule_id)
    
    def _handle_workflow_execution_trigger(self, execution_id: str, trigger_data: Dict[str, Any]):
        """Handle workflow execution triggers"""
        return self.handle_internal_event('workflow_execution', trigger_data, execution_id)
    
    def _handle_opportunity_update_trigger(self, opportunity_id: str, trigger_data: Dict[str, Any]):
        """Handle opportunity update triggers"""
        return self.handle_internal_event('opportunity_update', trigger_data, opportunity_id)
    
    def _handle_agent_performance_trigger(self, agent_id: str, trigger_data: Dict[str, Any]):
        """Handle agent performance triggers"""
        return self.handle_internal_event('agent_performance', trigger_data, agent_id)
    
    def _handle_revenue_milestone_trigger(self, milestone_data: Dict[str, Any]):
        """Handle revenue milestone triggers"""
        return self.handle_internal_event('revenue_milestone', milestone_data)
    
    def _handle_scheduled_trigger(self, schedule_data: Dict[str, Any]):
        """Handle scheduled triggers"""
        return self.handle_internal_event('schedule', schedule_data)
    
    def _evaluate_conditions(self, data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """Evaluate whether conditions are met for bridge execution"""
        try:
            # Simple condition evaluation - can be extended for complex logic
            for field, expected_value in conditions.items():
                if field not in data:
                    return False
                
                actual_value = data[field]
                
                # Handle different condition types
                if isinstance(expected_value, dict):
                    operator = expected_value.get('operator', 'equals')
                    value = expected_value.get('value')
                    
                    if operator == 'equals':
                        if actual_value != value:
                            return False
                    elif operator == 'not_equals':
                        if actual_value == value:
                            return False
                    elif operator == 'greater_than':
                        if not (isinstance(actual_value, (int, float)) and actual_value > value):
                            return False
                    elif operator == 'less_than':
                        if not (isinstance(actual_value, (int, float)) and actual_value < value):
                            return False
                    elif operator == 'contains':
                        if isinstance(actual_value, str) and value not in actual_value:
                            return False
                    elif operator == 'in':
                        if actual_value not in value:
                            return False
                else:
                    # Simple equality check
                    if actual_value != expected_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating conditions: {e}")
            return False
    
    def _map_data(self, source_data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Map data from internal format to Make.com format"""
        try:
            if not mapping:
                return source_data
            
            mapped_data = {}
            
            for target_field, source_field in mapping.items():
                if isinstance(source_field, str):
                    # Direct field mapping
                    if source_field in source_data:
                        mapped_data[target_field] = source_data[source_field]
                elif isinstance(source_field, dict):
                    # Complex mapping with transformations
                    source_path = source_field.get('source_path')
                    transform = source_field.get('transform')
                    default_value = source_field.get('default')
                    
                    # Get source value
                    value = self._get_nested_value(source_data, source_path) if source_path else default_value
                    
                    # Apply transformation
                    if transform and value is not None:
                        value = self._apply_transform(value, transform)
                    
                    mapped_data[target_field] = value
            
            # Include unmapped fields if specified
            if mapping.get('_include_unmapped', False):
                for key, value in source_data.items():
                    if key not in mapped_data:
                        mapped_data[key] = value
            
            return mapped_data
            
        except Exception as e:
            logger.error(f"Error mapping data: {e}")
            return source_data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from data using dot notation"""
        try:
            keys = path.split('.')
            value = data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            
            return value
            
        except Exception:
            return None
    
    def _apply_transform(self, value: Any, transform: Dict[str, Any]) -> Any:
        """Apply data transformation"""
        try:
            transform_type = transform.get('type')
            
            if transform_type == 'format_string':
                template = transform.get('template', '{}')
                return template.format(value)
            elif transform_type == 'multiply':
                factor = transform.get('factor', 1)
                return value * factor if isinstance(value, (int, float)) else value
            elif transform_type == 'map_values':
                mapping = transform.get('mapping', {})
                return mapping.get(str(value), value)
            elif transform_type == 'date_format':
                date_format = transform.get('format', '%Y-%m-%d')
                if isinstance(value, datetime):
                    return value.strftime(date_format)
                elif isinstance(value, str):
                    try:
                        parsed_date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        return parsed_date.strftime(date_format)
                    except:
                        return value
            elif transform_type == 'boolean':
                return bool(value)
            elif transform_type == 'string':
                return str(value)
            elif transform_type == 'number':
                try:
                    return float(value) if '.' in str(value) else int(value)
                except:
                    return 0
            
            return value
            
        except Exception as e:
            logger.error(f"Error applying transform: {e}")
            return value
    
    def create_default_bridges(self):
        """Create default automation bridges for common scenarios"""
        try:
            default_bridges = [
                {
                    'bridge_id': 'opportunity_to_crm',
                    'name': 'Opportunity to CRM Sync',
                    'description': 'Sync new opportunities to CRM system via Make.com',
                    'internal_trigger_type': 'opportunity_update',
                    'make_scenario_ids': ['crm_sync_scenario'],
                    'data_mapping': {
                        'contact_email': 'apollo_email',
                        'company_name': 'company',
                        'opportunity_title': 'title',
                        'opportunity_status': 'status',
                        'estimated_value': 'compensation_range',
                        'opportunity_type': 'type',
                        'source': 'source'
                    },
                    'internal_conditions': {
                        'status': {'operator': 'in', 'value': ['applied', 'interview_stage']}
                    }
                },
                {
                    'bridge_id': 'agent_alerts_to_slack',
                    'name': 'Agent Performance Alerts to Slack',
                    'description': 'Send agent performance alerts to Slack via Make.com',
                    'internal_trigger_type': 'agent_performance',
                    'make_scenario_ids': ['slack_alert_scenario'],
                    'data_mapping': {
                        'agent_name': 'name',
                        'performance_score': 'performance.success_rate',
                        'alert_level': {'source_path': 'performance.success_rate', 'transform': {'type': 'map_values', 'mapping': {'90': 'good', '70': 'warning', '50': 'critical'}}},
                        'recommendations': 'recommended_actions'
                    },
                    'internal_conditions': {
                        'performance.success_rate': {'operator': 'less_than', 'value': 80}
                    }
                },
                {
                    'bridge_id': 'revenue_milestone_celebration',
                    'name': 'Revenue Milestone Celebration',
                    'description': 'Trigger celebration workflows when revenue milestones are reached',
                    'internal_trigger_type': 'revenue_milestone',
                    'make_scenario_ids': ['celebration_scenario', 'reporting_scenario'],
                    'data_mapping': {
                        'milestone_amount': 'milestone_value',
                        'actual_amount': 'current_value',
                        'achievement_percentage': 'percentage_complete',
                        'revenue_stream': 'revenue_stream',
                        'achievement_date': {'source_path': 'achievement_date', 'transform': {'type': 'date_format', 'format': '%B %d, %Y'}}
                    },
                    'internal_conditions': {
                        'percentage_complete': {'operator': 'greater_than', 'value': 100}
                    }
                },
                {
                    'bridge_id': 'speaking_opportunity_application',
                    'name': 'Automated Speaking Opportunity Application',
                    'description': 'Automatically apply to high-scoring speaking opportunities',
                    'internal_trigger_type': 'opportunity_update',
                    'make_scenario_ids': ['speaking_application_scenario'],
                    'data_mapping': {
                        'event_name': 'event_name',
                        'organizer_contact': 'organizer',
                        'event_topic': 'topic_alignment',
                        'speaking_fee': 'speaking_fee',
                        'event_date': 'event_date',
                        'match_score': 'ai_match_score'
                    },
                    'internal_conditions': {
                        'type': 'speaking',
                        'ai_match_score': {'operator': 'greater_than', 'value': 85},
                        'status': 'ready_to_apply'
                    }
                },
                {
                    'bridge_id': 'research_to_content',
                    'name': 'Research to Content Pipeline',
                    'description': 'Convert completed research into content formats',
                    'internal_trigger_type': 'research_complete',
                    'make_scenario_ids': ['content_generation_scenario', 'social_media_scenario'],
                    'data_mapping': {
                        'research_topic': 'subject',
                        'key_insights': 'key_findings',
                        'confidence_level': 'confidence_score',
                        'research_summary': 'analysis',
                        'content_suggestions': 'recommendations'
                    },
                    'internal_conditions': {
                        'confidence_score': {'operator': 'greater_than', 'value': 0.8}
                    }
                }
            ]
            
            for bridge_data in default_bridges:
                # Check if bridge already exists
                existing = MakeAutomationBridge.query.filter_by(bridge_id=bridge_data['bridge_id']).first()
                if existing:
                    continue
                
                bridge = MakeAutomationBridge(
                    bridge_id=bridge_data['bridge_id'],
                    name=bridge_data['name'],
                    description=bridge_data['description'],
                    internal_trigger_type=bridge_data['internal_trigger_type'],
                    make_scenario_ids=bridge_data['make_scenario_ids'],
                    data_mapping=bridge_data['data_mapping'],
                    internal_conditions=bridge_data.get('internal_conditions'),
                    enabled=True,
                    created_by='system'
                )
                
                db.session.add(bridge)
            
            db.session.commit()
            logger.info("Created default automation bridges")
            
        except Exception as e:
            logger.error(f"Error creating default bridges: {e}")
            db.session.rollback()

# Event handlers for integration with existing system
def handle_opportunity_created(opportunity_data: Dict[str, Any]):
    """Handle opportunity creation events"""
    bridge_service = AutomationBridgeService()
    return bridge_service.handle_internal_event('opportunity_update', opportunity_data, str(opportunity_data.get('id')))

def handle_agent_performance_alert(agent_data: Dict[str, Any]):
    """Handle agent performance alerts"""
    bridge_service = AutomationBridgeService()
    return bridge_service.handle_internal_event('agent_performance', agent_data, str(agent_data.get('id')))

def handle_revenue_milestone(revenue_data: Dict[str, Any]):
    """Handle revenue milestone events"""
    bridge_service = AutomationBridgeService()
    return bridge_service.handle_internal_event('revenue_milestone', revenue_data)

def handle_research_complete(research_data: Dict[str, Any]):
    """Handle research completion events"""
    bridge_service = AutomationBridgeService()
    return bridge_service.handle_internal_event('research_complete', research_data)

# Factory function
def create_automation_bridge_service():
    """Factory function to create automation bridge service"""
    return AutomationBridgeService()