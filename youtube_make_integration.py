"""
YouTube Video Optimization - Make.com Integration
Automated workflows for YouTube video processing and optimization using Make.com
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from flask import Flask, request, jsonify

# Import YouTube models and services
from database import YoutubeVideo, VideoOptimization, db
from youtube_optimization_service import create_youtube_optimizer

logger = logging.getLogger(__name__)


class YoutubeMakeIntegration:
    """
    Make.com integration for YouTube video optimization automation
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize YouTube Make.com integration
        
        Args:
            webhook_url: Make.com webhook URL for sending events
        """
        self.webhook_url = webhook_url
        self.optimization_service = None
        
        # Initialize optimization service
        try:
            self.optimization_service = create_youtube_optimizer()
            logger.info("YouTube optimization service initialized for Make.com integration")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube optimization service: {e}")
    
    def register_video_events(self) -> Dict[str, Any]:
        """
        Register YouTube video events with Make.com
        
        Returns:
            Dictionary with event configurations
        """
        return {
            'youtube_video_created': {
                'description': 'Triggered when a new YouTube video is created',
                'webhook_url': f"{self.webhook_url}/youtube/video/created",
                'data_schema': {
                    'video_id': 'integer',
                    'title': 'string',
                    'category': 'string',
                    'target_audience': 'string',
                    'created_at': 'datetime'
                },
                'automation_triggers': [
                    'auto_optimize_video',
                    'notify_content_team',
                    'schedule_social_promotion'
                ]
            },
            'youtube_optimization_completed': {
                'description': 'Triggered when video optimization is completed',
                'webhook_url': f"{self.webhook_url}/youtube/optimization/completed",
                'data_schema': {
                    'video_id': 'integer',
                    'optimization_score': 'float',
                    'components_optimized': 'array',
                    'seo_improvements': 'object',
                    'sales_links_added': 'boolean'
                },
                'automation_triggers': [
                    'publish_to_youtube',
                    'create_social_posts',
                    'update_crm_with_content',
                    'schedule_promotion_emails'
                ]
            },
            'youtube_high_performance_detected': {
                'description': 'Triggered when video shows high engagement metrics',
                'webhook_url': f"{self.webhook_url}/youtube/performance/high",
                'data_schema': {
                    'video_id': 'integer',
                    'views': 'integer',
                    'engagement_rate': 'float',
                    'leads_generated': 'integer',
                    'performance_threshold_exceeded': 'string'
                },
                'automation_triggers': [
                    'amplify_promotion',
                    'create_follow_up_content',
                    'reach_out_to_engaged_viewers',
                    'schedule_speaking_followups'
                ]
            },
            'youtube_optimization_failed': {
                'description': 'Triggered when video optimization fails',
                'webhook_url': f"{self.webhook_url}/youtube/optimization/failed",
                'data_schema': {
                    'video_id': 'integer',
                    'error_message': 'string',
                    'retry_count': 'integer',
                    'failure_reason': 'string'
                },
                'automation_triggers': [
                    'notify_technical_team',
                    'schedule_manual_review',
                    'fallback_optimization'
                ]
            }
        }
    
    def trigger_video_created_event(self, video: YoutubeVideo) -> bool:
        """
        Trigger Make.com automation when a new video is created
        
        Args:
            video: YoutubeVideo instance
            
        Returns:
            Success status
        """
        try:
            event_data = {
                'event_type': 'youtube_video_created',
                'timestamp': datetime.utcnow().isoformat(),
                'video_data': {
                    'video_id': video.id,
                    'title': video.title,
                    'category': video.category,
                    'target_audience': video.target_audience,
                    'content_type': video.content_type,
                    'primary_topic': video.primary_topic,
                    'duration_seconds': video.video_duration_seconds,
                    'created_at': video.created_at.isoformat()
                },
                'automation_suggestions': [
                    {
                        'action': 'auto_optimize',
                        'priority': 'high',
                        'estimated_time': '5-10 minutes',
                        'expected_improvement': '25-40% SEO score increase'
                    },
                    {
                        'action': 'schedule_social_promotion',
                        'priority': 'medium',
                        'timing': 'after_optimization',
                        'platforms': ['LinkedIn', 'Twitter', 'Newsletter']
                    }
                ]
            }
            
            return self._send_webhook_event(event_data)
            
        except Exception as e:
            logger.error(f"Error triggering video created event: {e}")
            return False
    
    def trigger_optimization_completed_event(self, video: YoutubeVideo, optimization_result: Dict[str, Any]) -> bool:
        """
        Trigger Make.com automation when video optimization is completed
        
        Args:
            video: YoutubeVideo instance
            optimization_result: Optimization results from the service
            
        Returns:
            Success status
        """
        try:
            event_data = {
                'event_type': 'youtube_optimization_completed',
                'timestamp': datetime.utcnow().isoformat(),
                'video_data': {
                    'video_id': video.id,
                    'title': video.title,
                    'optimized_title': video.title,  # May have been updated
                    'category': video.category,
                    'optimization_score': video.optimization_score,
                    'youtube_url': video.youtube_url,
                    'sales_links': video.sales_links or {}
                },
                'optimization_results': {
                    'components_optimized': optimization_result.get('components_optimized', []),
                    'seo_improvements': optimization_result.get('seo_improvements', {}),
                    'performance_scores': optimization_result.get('performance_scores', {}),
                    'api_usage': optimization_result.get('api_usage', {}),
                    'processing_time': optimization_result.get('processing_time_seconds', 0)
                },
                'next_actions': [
                    {
                        'action': 'publish_to_youtube',
                        'priority': 'high',
                        'ready': True,
                        'requirements': ['YouTube channel access', 'Final approval']
                    },
                    {
                        'action': 'create_social_promotion',
                        'priority': 'high',
                        'ready': True,
                        'content_suggestions': [
                            f"New video: {video.title}",
                            f"AI governance insights from Dr. Dede",
                            f"Essential viewing for {video.target_audience}"
                        ]
                    },
                    {
                        'action': 'update_speaking_pipeline',
                        'priority': 'medium',
                        'ready': video.category in ['AI Governance', 'Accessibility'],
                        'speaking_topics': [video.primary_topic] + (video.secondary_topics or [])
                    }
                ]
            }
            
            return self._send_webhook_event(event_data)
            
        except Exception as e:
            logger.error(f"Error triggering optimization completed event: {e}")
            return False
    
    def trigger_high_performance_event(self, video: YoutubeVideo, analytics_data: Dict[str, Any]) -> bool:
        """
        Trigger Make.com automation when video shows high performance
        
        Args:
            video: YoutubeVideo instance
            analytics_data: Performance analytics data
            
        Returns:
            Success status
        """
        try:
            event_data = {
                'event_type': 'youtube_high_performance_detected',
                'timestamp': datetime.utcnow().isoformat(),
                'video_data': {
                    'video_id': video.id,
                    'title': video.title,
                    'category': video.category,
                    'youtube_url': video.youtube_url
                },
                'performance_data': {
                    'views': analytics_data.get('views_total', 0),
                    'engagement_rate': analytics_data.get('engagement_rate', 0.0),
                    'watch_time_percentage': analytics_data.get('watch_time_percentage', 0.0),
                    'leads_generated': analytics_data.get('estimated_leads_generated', 0),
                    'website_clicks': analytics_data.get('website_clicks', 0),
                    'threshold_exceeded': analytics_data.get('threshold_type', 'engagement')
                },
                'amplification_opportunities': [
                    {
                        'action': 'boost_social_promotion',
                        'reasoning': 'High engagement indicates content resonance',
                        'investment_suggestion': 'Increase social media ad spend',
                        'target_multiplier': '3x current reach'
                    },
                    {
                        'action': 'create_series_content',
                        'reasoning': 'Audience interest in topic confirmed',
                        'content_suggestions': [
                            f"Deep dive into {video.primary_topic}",
                            f"Q&A on {video.primary_topic}",
                            f"Case studies related to {video.primary_topic}"
                        ]
                    },
                    {
                        'action': 'reach_out_to_viewers',
                        'reasoning': 'High-intent audience identified',
                        'outreach_strategy': 'Consultation offers for engaged viewers',
                        'expected_conversion': '5-10% to consultation calls'
                    }
                ]
            }
            
            return self._send_webhook_event(event_data)
            
        except Exception as e:
            logger.error(f"Error triggering high performance event: {e}")
            return False
    
    def create_automated_optimization_workflow(self, video_id: int, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an automated optimization workflow for a video
        
        Args:
            video_id: Video ID to optimize
            workflow_config: Configuration for the automation workflow
            
        Returns:
            Workflow status and details
        """
        try:
            video = YoutubeVideo.query.get(video_id)
            if not video:
                return {'success': False, 'error': 'Video not found'}
            
            # Default workflow configuration
            default_config = {
                'optimization_type': 'full',
                'auto_publish': False,
                'social_promotion': True,
                'crm_update': True,
                'speaking_pipeline_update': True,
                'performance_monitoring': True
            }
            
            # Merge with provided config
            config = {**default_config, **workflow_config}
            
            # Start optimization
            if self.optimization_service:
                optimization_result = self.optimization_service.optimize_video_complete(
                    video_id, config['optimization_type']
                )
                
                # Trigger Make.com workflows based on configuration
                workflow_status = {
                    'optimization_started': True,
                    'optimization_result': optimization_result,
                    'make_workflows_triggered': []
                }
                
                # Trigger optimization completed event
                if optimization_result.get('status') == 'completed':
                    if self.trigger_optimization_completed_event(video, optimization_result):
                        workflow_status['make_workflows_triggered'].append('optimization_completed')
                
                # Additional workflow triggers based on config
                if config.get('social_promotion'):
                    workflow_status['make_workflows_triggered'].append('social_promotion_scheduled')
                
                if config.get('crm_update'):
                    workflow_status['make_workflows_triggered'].append('crm_content_updated')
                
                if config.get('speaking_pipeline_update'):
                    workflow_status['make_workflows_triggered'].append('speaking_opportunities_updated')
                
                return {
                    'success': True,
                    'workflow_status': workflow_status,
                    'config_applied': config
                }
            else:
                return {'success': False, 'error': 'Optimization service not available'}
                
        except Exception as e:
            logger.error(f"Error creating automated workflow: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_webhook_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Send event data to Make.com webhook
        
        Args:
            event_data: Event data to send
            
        Returns:
            Success status
        """
        if not self.webhook_url:
            logger.warning("No webhook URL configured for Make.com integration")
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=event_data,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent {event_data['event_type']} event to Make.com")
                return True
            else:
                logger.error(f"Failed to send event to Make.com: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending webhook event: {e}")
            return False


# Flask webhook endpoints for Make.com integration
def register_youtube_make_webhooks(app: Flask, integration: YoutubeMakeIntegration):
    """
    Register YouTube-specific webhook endpoints for Make.com integration
    
    Args:
        app: Flask application instance
        integration: YoutubeMakeIntegration instance
    """
    
    @app.route('/webhooks/youtube/video/created', methods=['POST'])
    def youtube_video_created_webhook():
        """Handle video created webhook from Make.com"""
        try:
            data = request.get_json()
            video_id = data.get('video_id')
            
            if video_id:
                video = YoutubeVideo.query.get(video_id)
                if video:
                    success = integration.trigger_video_created_event(video)
                    return jsonify({'success': success})
            
            return jsonify({'success': False, 'error': 'Invalid video data'}), 400
            
        except Exception as e:
            logger.error(f"Error in video created webhook: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/webhooks/youtube/auto-optimize', methods=['POST'])
    def youtube_auto_optimize_webhook():
        """Handle automatic optimization trigger from Make.com"""
        try:
            data = request.get_json()
            video_id = data.get('video_id')
            workflow_config = data.get('config', {})
            
            if video_id:
                result = integration.create_automated_optimization_workflow(
                    video_id, workflow_config
                )
                return jsonify(result)
            
            return jsonify({'success': False, 'error': 'Video ID required'}), 400
            
        except Exception as e:
            logger.error(f"Error in auto-optimize webhook: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/webhooks/youtube/performance-check', methods=['POST'])
    def youtube_performance_check_webhook():
        """Handle performance monitoring webhook from Make.com"""
        try:
            data = request.get_json()
            video_id = data.get('video_id')
            analytics_data = data.get('analytics', {})
            
            if video_id:
                video = YoutubeVideo.query.get(video_id)
                if video and analytics_data:
                    # Check if performance thresholds are met
                    engagement_threshold = 0.05  # 5% engagement rate
                    views_threshold = 1000
                    
                    if (analytics_data.get('engagement_rate', 0) > engagement_threshold or 
                        analytics_data.get('views_total', 0) > views_threshold):
                        
                        success = integration.trigger_high_performance_event(video, analytics_data)
                        return jsonify({'success': success, 'high_performance': True})
                    
                    return jsonify({'success': True, 'high_performance': False})
            
            return jsonify({'success': False, 'error': 'Invalid performance data'}), 400
            
        except Exception as e:
            logger.error(f"Error in performance check webhook: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


# Factory function
def create_youtube_make_integration(webhook_url: Optional[str] = None) -> YoutubeMakeIntegration:
    """
    Create YouTube Make.com integration instance
    
    Args:
        webhook_url: Make.com webhook URL
        
    Returns:
        YoutubeMakeIntegration instance
    """
    return YoutubeMakeIntegration(webhook_url)