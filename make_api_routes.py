"""
API routes for Make.com integration
Provides REST endpoints for managing Make.com scenarios, webhooks, and automation bridges
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid
import logging
from typing import Dict, Any

from database import db
from make_models import MakeScenario, MakeExecution, MakeEventLog, MakeAutomationBridge, MakeTemplate
from make_integration import (
    create_make_integration_service, 
    create_workflow_template_manager,
    MakeEventType,
    MakeWebhookConfig,
    trigger_opportunity_event,
    trigger_agent_performance_event,
    trigger_revenue_milestone_event,
    trigger_speaking_opportunity_event,
    trigger_research_complete_event
)

logger = logging.getLogger(__name__)

# Create Blueprint
make_bp = Blueprint('make', __name__, url_prefix='/api/make')

# Initialize services
make_service = create_make_integration_service()
template_manager = create_workflow_template_manager()

@make_bp.route('/scenarios', methods=['GET'])
@jwt_required()
def get_scenarios():
    """Get all Make.com scenarios"""
    try:
        scenarios = MakeScenario.query.all()
        return jsonify({
            'success': True,
            'scenarios': [scenario.to_dict() for scenario in scenarios]
        })
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/scenarios', methods=['POST'])
@jwt_required()
def create_scenario():
    """Create a new Make.com scenario"""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['name', 'webhook_url', 'event_types']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Generate scenario ID if not provided
        scenario_id = data.get('scenario_id', f"scenario_{str(uuid.uuid4())[:8]}")
        
        # Create scenario
        scenario = MakeScenario(
            scenario_id=scenario_id,
            name=data['name'],
            description=data.get('description'),
            category=data.get('category', 'custom'),
            webhook_url=data['webhook_url'],
            event_types=data['event_types'],
            authentication_method=data.get('authentication_method', 'none'),
            secret_key=data.get('secret_key'),
            custom_headers=data.get('custom_headers'),
            filter_conditions=data.get('filter_conditions'),
            enabled=data.get('enabled', True),
            priority=data.get('priority', 5),
            template_id=data.get('template_id'),
            expected_data_structure=data.get('expected_data_structure'),
            configuration_steps=data.get('configuration_steps'),
            required_integrations=data.get('required_integrations'),
            created_by=current_user
        )
        
        db.session.add(scenario)
        db.session.commit()
        
        # Register webhook with service
        webhook_config = MakeWebhookConfig(
            scenario_id=scenario_id,
            webhook_url=data['webhook_url'],
            event_types=[MakeEventType(event) for event in data['event_types']],
            authentication_method=data.get('authentication_method', 'none'),
            secret_key=data.get('secret_key'),
            custom_headers=data.get('custom_headers'),
            filter_conditions=data.get('filter_conditions'),
            enabled=data.get('enabled', True)
        )
        
        make_service.register_webhook(webhook_config)
        
        return jsonify({
            'success': True,
            'scenario': scenario.to_dict(),
            'message': 'Scenario created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating scenario: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/scenarios/<scenario_id>', methods=['PUT'])
@jwt_required()
def update_scenario(scenario_id):
    """Update an existing Make.com scenario"""
    try:
        scenario = MakeScenario.query.filter_by(scenario_id=scenario_id).first()
        if not scenario:
            return jsonify({'success': False, 'error': 'Scenario not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            scenario.name = data['name']
        if 'description' in data:
            scenario.description = data['description']
        if 'webhook_url' in data:
            scenario.webhook_url = data['webhook_url']
        if 'event_types' in data:
            scenario.event_types = data['event_types']
        if 'authentication_method' in data:
            scenario.authentication_method = data['authentication_method']
        if 'secret_key' in data:
            scenario.secret_key = data['secret_key']
        if 'custom_headers' in data:
            scenario.custom_headers = data['custom_headers']
        if 'filter_conditions' in data:
            scenario.filter_conditions = data['filter_conditions']
        if 'enabled' in data:
            scenario.enabled = data['enabled']
        if 'priority' in data:
            scenario.priority = data['priority']
        
        scenario.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Update webhook service
        webhook_config = MakeWebhookConfig(
            scenario_id=scenario_id,
            webhook_url=scenario.webhook_url,
            event_types=[MakeEventType(event) for event in scenario.event_types],
            authentication_method=scenario.authentication_method,
            secret_key=scenario.secret_key,
            custom_headers=scenario.custom_headers,
            filter_conditions=scenario.filter_conditions,
            enabled=scenario.enabled
        )
        
        make_service.register_webhook(webhook_config)
        
        return jsonify({
            'success': True,
            'scenario': scenario.to_dict(),
            'message': 'Scenario updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating scenario: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/scenarios/<scenario_id>', methods=['DELETE'])
@jwt_required()
def delete_scenario(scenario_id):
    """Delete a Make.com scenario"""
    try:
        scenario = MakeScenario.query.filter_by(scenario_id=scenario_id).first()
        if not scenario:
            return jsonify({'success': False, 'error': 'Scenario not found'}), 404
        
        db.session.delete(scenario)
        db.session.commit()
        
        # Remove from webhook service
        if scenario_id in make_service.webhook_configs:
            del make_service.webhook_configs[scenario_id]
        
        return jsonify({
            'success': True,
            'message': 'Scenario deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting scenario: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/scenarios/<scenario_id>/trigger', methods=['POST'])
@jwt_required()
def trigger_scenario(scenario_id):
    """Manually trigger a Make.com scenario"""
    try:
        scenario = MakeScenario.query.filter_by(scenario_id=scenario_id).first()
        if not scenario:
            return jsonify({'success': False, 'error': 'Scenario not found'}), 404
        
        payload = request.get_json() or {}
        
        # Add manual trigger metadata
        payload['_manual_trigger'] = {
            'triggered_by': get_jwt_identity(),
            'triggered_at': datetime.utcnow().isoformat()
        }
        
        # Trigger scenario
        success = make_service.trigger_scenario(scenario_id, payload)
        
        if success:
            # Update scenario statistics
            scenario.total_executions += 1
            scenario.last_execution = datetime.utcnow()
            db.session.commit()
            
            # Log execution
            execution = MakeExecution(
                execution_id=f"manual_{str(uuid.uuid4())[:8]}",
                scenario_id=scenario_id,
                event_type="manual_trigger",
                trigger_source=f"user_{get_jwt_identity()}",
                trigger_data=payload,
                status="success",
                request_payload=payload,
                triggered_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.session.add(execution)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Scenario triggered successfully',
                'execution_id': execution.execution_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to trigger scenario'}), 500
            
    except Exception as e:
        logger.error(f"Error triggering scenario: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/scenarios/<scenario_id>/executions', methods=['GET'])
@jwt_required()
def get_scenario_executions(scenario_id):
    """Get execution history for a scenario"""
    try:
        limit = request.args.get('limit', 50, type=int)
        executions = MakeExecution.query.filter_by(scenario_id=scenario_id)\
            .order_by(MakeExecution.triggered_at.desc())\
            .limit(limit).all()
        
        return jsonify({
            'success': True,
            'executions': [execution.to_dict() for execution in executions]
        })
        
    except Exception as e:
        logger.error(f"Error getting executions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """Get all scenario templates"""
    try:
        category = request.args.get('category')
        
        # Get templates from template manager
        templates = template_manager.get_scenario_templates()
        
        if category:
            templates = {k: v for k, v in templates.items() if v.category == category}
        
        return jsonify({
            'success': True,
            'templates': {k: {
                'template_id': v.template_id,
                'name': v.name,
                'description': v.description,
                'category': v.category,
                'trigger_events': [event.value for event in v.trigger_events],
                'expected_data_structure': v.expected_data_structure,
                'sample_payload': v.sample_payload,
                'configuration_steps': v.configuration_steps,
                'required_integrations': v.required_integrations,
                'estimated_operations': v.estimated_operations,
                'complexity_level': v.complexity_level
            } for k, v in templates.items()}
        })
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/bridges', methods=['GET'])
@jwt_required()
def get_automation_bridges():
    """Get all automation bridges"""
    try:
        bridges = MakeAutomationBridge.query.all()
        return jsonify({
            'success': True,
            'bridges': [bridge.to_dict() for bridge in bridges]
        })
    except Exception as e:
        logger.error(f"Error getting bridges: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/bridges', methods=['POST'])
@jwt_required()
def create_automation_bridge():
    """Create a new automation bridge"""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['name', 'internal_trigger_type', 'make_scenario_ids']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Generate bridge ID
        bridge_id = data.get('bridge_id', f"bridge_{str(uuid.uuid4())[:8]}")
        
        # Create bridge
        bridge = MakeAutomationBridge(
            bridge_id=bridge_id,
            name=data['name'],
            description=data.get('description'),
            internal_trigger_type=data['internal_trigger_type'],
            internal_trigger_id=data.get('internal_trigger_id'),
            internal_conditions=data.get('internal_conditions'),
            make_scenario_ids=data['make_scenario_ids'],
            data_mapping=data.get('data_mapping'),
            enabled=data.get('enabled', True),
            bidirectional=data.get('bidirectional', False),
            priority=data.get('priority', 5),
            created_by=current_user
        )
        
        db.session.add(bridge)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'bridge': bridge.to_dict(),
            'message': 'Automation bridge created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating bridge: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/events/trigger', methods=['POST'])
@jwt_required()
def trigger_event():
    """Trigger Make.com scenarios based on event type"""
    try:
        data = request.get_json()
        
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})
        
        if not event_type:
            return jsonify({'success': False, 'error': 'Missing event_type'}), 400
        
        # Map event type to trigger function
        event_triggers = {
            'opportunity_created': trigger_opportunity_event,
            'opportunity_updated': trigger_opportunity_event,
            'opportunity_status_changed': trigger_opportunity_event,
            'agent_performance_alert': trigger_agent_performance_event,
            'revenue_milestone': trigger_revenue_milestone_event,
            'speaking_opportunity_found': trigger_speaking_opportunity_event,
            'perplexity_research_complete': trigger_research_complete_event
        }
        
        if event_type not in event_triggers:
            return jsonify({'success': False, 'error': 'Unsupported event type'}), 400
        
        # Trigger appropriate scenarios
        if event_type in ['opportunity_created', 'opportunity_updated', 'opportunity_status_changed']:
            results = trigger_opportunity_event(make_service, event_data, MakeEventType(event_type))
        elif event_type == 'agent_performance_alert':
            results = trigger_agent_performance_event(make_service, event_data)
        elif event_type == 'revenue_milestone':
            results = trigger_revenue_milestone_event(make_service, event_data)
        elif event_type == 'speaking_opportunity_found':
            results = trigger_speaking_opportunity_event(make_service, event_data)
        elif event_type == 'perplexity_research_complete':
            results = trigger_research_complete_event(make_service, event_data)
        
        # Log the event
        event_log = MakeEventLog(
            event_id=f"event_{str(uuid.uuid4())[:8]}",
            event_type=event_type,
            source_entity=data.get('source_entity', 'manual'),
            source_id=data.get('source_id', 'unknown'),
            event_data=event_data,
            processed=True,
            scenarios_triggered=list(results.keys()),
            processing_results=results,
            processed_at=datetime.utcnow()
        )
        
        db.session.add(event_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'event_id': event_log.event_id,
            'scenarios_triggered': list(results.keys()),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error triggering event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get Make.com integration statistics"""
    try:
        # Get scenario statistics
        total_scenarios = MakeScenario.query.count()
        active_scenarios = MakeScenario.query.filter_by(enabled=True).count()
        
        # Get execution statistics
        total_executions = MakeExecution.query.count()
        successful_executions = MakeExecution.query.filter_by(status='success').count()
        failed_executions = MakeExecution.query.filter_by(status='failure').count()
        
        # Get recent activity
        recent_executions = MakeExecution.query.order_by(MakeExecution.triggered_at.desc()).limit(10).all()
        
        # Calculate success rate
        success_rate = (successful_executions / max(total_executions, 1)) * 100
        
        return jsonify({
            'success': True,
            'stats': {
                'scenarios': {
                    'total': total_scenarios,
                    'active': active_scenarios,
                    'inactive': total_scenarios - active_scenarios
                },
                'executions': {
                    'total': total_executions,
                    'successful': successful_executions,
                    'failed': failed_executions,
                    'success_rate': round(success_rate, 2)
                },
                'recent_activity': [execution.to_dict() for execution in recent_executions]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@make_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Make.com integration"""
    return jsonify({
        'success': True,
        'service': 'Make.com Integration',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

# Event handler utilities
def handle_opportunity_event(opportunity_id: str, event_type: str, opportunity_data: Dict[str, Any]):
    """Handle opportunity-related events and trigger Make.com scenarios"""
    try:
        # Create event log
        event_log = MakeEventLog(
            event_id=f"opp_{opportunity_id}_{str(uuid.uuid4())[:8]}",
            event_type=event_type,
            source_entity='opportunity',
            source_id=str(opportunity_id),
            event_data=opportunity_data
        )
        
        db.session.add(event_log)
        
        # Trigger Make.com scenarios
        results = trigger_opportunity_event(make_service, opportunity_data, MakeEventType(event_type))
        
        # Update event log
        event_log.processed = True
        event_log.scenarios_triggered = list(results.keys())
        event_log.processing_results = results
        event_log.processed_at = datetime.utcnow()
        
        db.session.commit()
        
        return results
        
    except Exception as e:
        logger.error(f"Error handling opportunity event: {e}")
        db.session.rollback()
        return {}

def handle_agent_performance_event(agent_id: str, agent_data: Dict[str, Any]):
    """Handle agent performance events and trigger Make.com scenarios"""
    try:
        # Create event log
        event_log = MakeEventLog(
            event_id=f"agent_{agent_id}_{str(uuid.uuid4())[:8]}",
            event_type='agent_performance_alert',
            source_entity='ai_agent',
            source_id=str(agent_id),
            event_data=agent_data
        )
        
        db.session.add(event_log)
        
        # Trigger Make.com scenarios
        results = trigger_agent_performance_event(make_service, agent_data)
        
        # Update event log
        event_log.processed = True
        event_log.scenarios_triggered = list(results.keys())
        event_log.processing_results = results
        event_log.processed_at = datetime.utcnow()
        
        db.session.commit()
        
        return results
        
    except Exception as e:
        logger.error(f"Error handling agent performance event: {e}")
        db.session.rollback()
        return {}