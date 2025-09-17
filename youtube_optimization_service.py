"""
YouTube Video Optimization Service
Advanced AI-powered YouTube content optimization using Perplexity AI for thought leadership content
"""

import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import os
import time

# Import existing Perplexity services
from perplexity_service import (
    PerplexityAPI, PerplexityRequest, PerplexityModel, SearchRecency,
    PerplexityContentService, PerplexityResearchService
)

# Import database models
from database import (
    YoutubeVideo, VideoChapter, VideoCaption, VideoOptimization, VideoAnalytics,
    db
)

logger = logging.getLogger(__name__)


class YoutubeVideoOptimizer:
    """
    Comprehensive YouTube video optimization service using Perplexity AI
    Specialized for AI governance and accessibility thought leadership content
    """
    
    def __init__(self, perplexity_api_key: Optional[str] = None):
        """
        Initialize YouTube Video Optimizer
        
        Args:
            perplexity_api_key: Perplexity API key for AI-powered optimization
        """
        self.perplexity_api_key = perplexity_api_key or os.getenv('PERPLEXITY_API_KEY')
        if not self.perplexity_api_key:
            logger.warning("Perplexity API key not configured. Optimization will use fallback methods.")
            
        # Initialize Perplexity services
        self.perplexity_api = None
        self.content_service = None
        self.research_service = None
        
        if self.perplexity_api_key:
            try:
                self.perplexity_api = PerplexityAPI(self.perplexity_api_key)
                self.content_service = PerplexityContentService(self.perplexity_api)
                self.research_service = PerplexityResearchService(self.perplexity_api)
                logger.info("YouTube optimization services initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Perplexity services: {e}")
        
        # YouTube-specific optimization templates
        self.youtube_templates = {
            'video_title_optimization': """
Optimize this YouTube video title for maximum engagement and SEO while maintaining thought leadership authority:

Original Title: {original_title}
Video Topic: {primary_topic}
Target Audience: {target_audience}
Content Category: {category}
Key Points Covered: {key_points}

Create 3 optimized title variations that:
1. Include relevant SEO keywords naturally
2. Create curiosity and urgency
3. Maintain professional authority for executive audience
4. Stay under 70 characters for optimal display
5. Position Dr. Dede as a thought leader in AI governance/accessibility

Focus keywords: AI governance, AI accessibility, compliance, risk management, digital inclusion
Target audience: C-level executives, compliance officers, board directors

Return as JSON:
{
  "titles": [
    {"title": "optimized_title_1", "seo_score": 0.0-1.0, "engagement_potential": 0.0-1.0},
    {"title": "optimized_title_2", "seo_score": 0.0-1.0, "engagement_potential": 0.0-1.0},
    {"title": "optimized_title_3", "seo_score": 0.0-1.0, "engagement_potential": 0.0-1.0}
  ],
  "recommended": 1,
  "seo_improvements": ["improvement1", "improvement2"],
  "keywords_added": ["keyword1", "keyword2"]
}
""",
            'video_description_optimization': """
Create an optimized YouTube video description for thought leadership content:

Video Title: {title}
Primary Topic: {primary_topic}
Secondary Topics: {secondary_topics}
Target Audience: {target_audience}
Content Category: {category}
Key Insights: {key_insights}
Call to Action Goals: {cta_goals}

The description should:
1. Start with a compelling hook (first 2 lines visible in search)
2. Include strategic placement of keywords for SEO
3. Provide valuable content summary
4. Include timestamps for key sections
5. Add strategic sales links at optimal positions
6. Include relevant hashtags
7. Position Dr. Dede as the authority in AI governance and accessibility
8. Drive engagement and consultation requests

Structure:
- Hook (2 lines)
- Content overview and value proposition
- Detailed breakdown with timestamps
- About Dr. Dede (credentials and expertise)
- Strategic calls to action
- Contact information and links
- Hashtags

Target keywords: AI governance, artificial intelligence compliance, AI accessibility, digital inclusion, AI risk management, AI ethics, regulatory compliance

Return optimized description with clear sections marked.
""",
            'chapter_generation': """
Generate timestamped chapters for this YouTube video on AI governance/accessibility:

Video Title: {title}
Video Duration: {duration_seconds} seconds
Primary Topic: {primary_topic}
Content Overview: {content_overview}
Key Points Discussed: {key_points}
Target Audience: {target_audience}

Create 5-8 logical chapters that:
1. Break down complex AI governance concepts into digestible segments
2. Use SEO-friendly chapter titles with relevant keywords
3. Highlight key insights and actionable takeaways
4. Create natural stopping/starting points for viewers
5. Include introduction and conclusion chapters
6. Optimize for YouTube's chapter feature

Each chapter should be 60-300 seconds long for optimal engagement.

Return as JSON:
{
  "chapters": [
    {
      "title": "Chapter Title with Keywords",
      "start_time": 0,
      "estimated_duration": 120,
      "key_topics": ["topic1", "topic2"],
      "seo_keywords": ["keyword1", "keyword2"],
      "description": "Brief chapter description"
    }
  ],
  "total_chapters": 6,
  "seo_optimization_notes": ["note1", "note2"]
}
""",
            'caption_seo_optimization': """
Optimize these video captions for SEO while maintaining natural readability:

Original Caption Text: {original_text}
Video Topic: {video_topic}
Target Keywords: {target_keywords}
Timestamp: {start_time} - {end_time}
Context: {surrounding_context}

Optimization goals:
1. Naturally integrate target keywords without forcing
2. Improve clarity and professional language
3. Ensure accessibility compliance
4. Maintain speaker's authoritative tone
5. Add subtle keyword variations for SEO

Target keywords for AI governance content: AI governance, compliance, risk management, artificial intelligence, digital inclusion, accessibility, ethics, regulation

Return optimized caption that flows naturally while improving SEO value.
""",
            'sales_link_strategy': """
Create a strategic sales link placement strategy for this YouTube video:

Video Topic: {primary_topic}
Target Audience: {target_audience}
Video Duration: {duration_seconds} seconds
Content Type: {content_type}
Key Value Propositions: {value_props}

Revenue Goals:
- Speaking engagement bookings
- Board director opportunities
- Consulting contracts
- Thought leadership positioning

Design strategic placement of:
1. Consultation booking links
2. Speaking engagement inquiry forms
3. Governance assessment tools
4. Free resources/lead magnets
5. Social proof and credentials

Return JSON with optimal placement strategy:
{
  "description_links": [
    {"position": "early/mid/end", "link_type": "consultation", "text": "Click here to...", "placement_reason": "why here"}
  ],
  "call_to_action": "Primary CTA text",
  "lead_magnets": ["Free AI Governance Checklist", "Board Readiness Assessment"],
  "social_proof_elements": ["credential1", "achievement2"],
  "urgency_elements": ["Limited consultation slots", "Regulatory deadline approaching"]
}
"""
        }
        
        # SEO keyword database for AI governance and accessibility
        self.seo_keywords = {
            'primary': [
                'AI governance', 'artificial intelligence governance', 'AI compliance',
                'AI accessibility', 'digital accessibility', 'digital inclusion',
                'AI ethics', 'AI risk management', 'AI regulation', 'AI oversight'
            ],
            'secondary': [
                'machine learning compliance', 'algorithmic accountability', 'AI bias',
                'AI transparency', 'responsible AI', 'ethical AI', 'AI audit',
                'AI policy', 'AI standards', 'AI certification'
            ],
            'audience_specific': {
                'executives': ['board governance', 'C-suite AI strategy', 'executive AI oversight'],
                'compliance': ['regulatory compliance', 'audit requirements', 'compliance framework'],
                'technical': ['AI implementation', 'technical governance', 'AI architecture']
            },
            'trending': [
                'AI Act compliance', 'GDPR AI', 'algorithmic impact assessment',
                'AI safety', 'AI security', 'generative AI governance'
            ]
        }
        
        # Sales link templates
        self.sales_links = {
            'consultation': 'https://risktravel.com/ai-governance-consultation',
            'speaking': 'https://risktravel.com/speaking-requests',
            'board_assessment': 'https://risktravel.com/board-ai-readiness',
            'governance_checklist': 'https://risktravel.com/ai-governance-checklist',
            'risk_assessment': 'https://risktravel.com/ai-risk-assessment',
            'calendar': 'https://calendly.com/dr-dede-risktravel'
        }
    
    def optimize_video_complete(self, video_id: int, optimization_type: str = 'full') -> Dict[str, Any]:
        """
        Run complete video optimization pipeline
        
        Args:
            video_id: Database ID of the video to optimize
            optimization_type: Type of optimization ('full', 'title_only', 'description_only', etc.)
            
        Returns:
            Dictionary with optimization results and metrics
        """
        try:
            # Start optimization tracking
            optimization_start_time = time.time()
            
            # Create optimization record
            optimization = VideoOptimization(
                video_id=video_id,
                optimization_type=optimization_type,
                status='running',
                started_at=datetime.utcnow()
            )
            db.session.add(optimization)
            db.session.commit()
            
            # Get video from database
            video = YoutubeVideo.query.get(video_id)
            if not video:
                raise ValueError(f"Video with ID {video_id} not found")
            
            # Store original content for comparison
            original_content = self._capture_video_snapshot(video)
            optimization.before_optimization = original_content
            
            # Initialize results
            optimization_results = {
                'video_id': video_id,
                'optimization_id': optimization.id,
                'optimization_type': optimization_type,
                'status': 'running',
                'components_optimized': [],
                'seo_improvements': {},
                'performance_scores': {},
                'api_usage': {'calls_made': 0, 'tokens_used': 0, 'estimated_cost': 0.0}
            }
            
            # Run optimization components based on type
            if optimization_type in ['full', 'title_optimization']:
                title_result = self.optimize_video_title(video)
                if title_result['success']:
                    optimization_results['components_optimized'].append('title')
                    optimization_results['seo_improvements']['title'] = title_result
                    optimization.title_optimized = True
                    self._update_api_usage(optimization_results, title_result)
            
            if optimization_type in ['full', 'description_optimization']:
                description_result = self.optimize_video_description(video)
                if description_result['success']:
                    optimization_results['components_optimized'].append('description')
                    optimization_results['seo_improvements']['description'] = description_result
                    optimization.description_optimized = True
                    self._update_api_usage(optimization_results, description_result)
            
            if optimization_type in ['full', 'chapters']:
                chapters_result = self.generate_video_chapters(video)
                if chapters_result['success']:
                    optimization_results['components_optimized'].append('chapters')
                    optimization_results['seo_improvements']['chapters'] = chapters_result
                    optimization.chapters_generated = True
                    self._update_api_usage(optimization_results, chapters_result)
            
            if optimization_type in ['full', 'sales_links']:
                sales_result = self.optimize_sales_links(video)
                if sales_result['success']:
                    optimization_results['components_optimized'].append('sales_links')
                    optimization_results['seo_improvements']['sales_links'] = sales_result
                    optimization.sales_links_added = True
            
            # Calculate overall optimization score
            overall_score = self._calculate_optimization_score(optimization_results)
            optimization_results['optimization_score'] = overall_score
            optimization.optimization_score = overall_score
            
            # Update video optimization status
            video.optimization_status = 'completed'
            video.optimization_score = overall_score
            video.optimized_at = datetime.utcnow()
            video.perplexity_research_used = True
            
            # Complete optimization record
            optimization.status = 'completed'
            optimization.completed_at = datetime.utcnow()
            optimization.processing_time_seconds = time.time() - optimization_start_time
            optimization.after_optimization = self._capture_video_snapshot(video)
            optimization.api_calls_made = optimization_results['api_usage']['calls_made']
            optimization.tokens_used = optimization_results['api_usage']['tokens_used']
            optimization.estimated_cost_usd = optimization_results['api_usage']['estimated_cost']
            
            # Save all changes
            db.session.commit()
            
            optimization_results['status'] = 'completed'
            optimization_results['processing_time_seconds'] = optimization.processing_time_seconds
            
            logger.info(f"Video optimization completed successfully for video {video_id}. Score: {overall_score:.3f}")
            return optimization_results
            
        except Exception as e:
            # Handle optimization failure
            logger.error(f"Video optimization failed for video {video_id}: {e}")
            
            if 'optimization' in locals():
                optimization.status = 'failed'
                optimization.error_message = str(e)
                optimization.completed_at = datetime.utcnow()
                db.session.commit()
            
            return {
                'video_id': video_id,
                'status': 'failed',
                'error': str(e),
                'optimization_type': optimization_type
            }
    
    def optimize_video_title(self, video: YoutubeVideo) -> Dict[str, Any]:
        """
        Optimize video title using AI and SEO best practices
        
        Args:
            video: YoutubeVideo model instance
            
        Returns:
            Dictionary with optimization results
        """
        try:
            if not self.perplexity_api:
                return self._fallback_title_optimization(video)
            
            # Prepare context for title optimization
            prompt_data = {
                'original_title': video.title,
                'primary_topic': video.primary_topic or 'AI Governance',
                'target_audience': video.target_audience or 'executives',
                'category': video.category or 'AI Governance',
                'key_points': ', '.join(video.secondary_topics or ['AI compliance', 'risk management'])
            }
            
            prompt = self.youtube_templates['video_title_optimization'].format(**prompt_data)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a YouTube SEO expert specializing in thought leadership content for AI governance and accessibility. Create titles that balance authority with engagement.",
                model=PerplexityModel.LARGE,
                temperature=0.4,
                max_tokens=800,
                return_related_questions=False
            )
            
            response = self.perplexity_api.chat_completion(request)
            
            if response and response.content:
                # Parse JSON response
                try:
                    result_data = json.loads(response.content)
                    
                    # Select best title
                    recommended_idx = result_data.get('recommended', 0)
                    recommended_title = result_data['titles'][recommended_idx]['title']
                    
                    # Store original title if not already stored
                    if not video.original_title:
                        video.original_title = video.title
                    
                    # Update video title
                    video.title = recommended_title
                    
                    # Update SEO tags based on improvements
                    seo_improvements = result_data.get('seo_improvements', [])
                    keywords_added = result_data.get('keywords_added', [])
                    
                    if keywords_added:
                        current_keywords = video.target_keywords or []
                        video.target_keywords = list(set(current_keywords + keywords_added))
                    
                    return {
                        'success': True,
                        'original_title': video.original_title,
                        'optimized_title': recommended_title,
                        'alternatives': result_data['titles'],
                        'seo_improvements': seo_improvements,
                        'keywords_added': keywords_added,
                        'method': 'perplexity_ai',
                        'api_usage': {
                            'calls_made': 1,
                            'tokens_used': response.usage.get('total_tokens', 0) if response.usage else 0,
                            'model_used': response.model
                        }
                    }
                    
                except json.JSONDecodeError:
                    logger.error("Failed to parse title optimization response")
                    return self._fallback_title_optimization(video)
            
            return self._fallback_title_optimization(video)
            
        except Exception as e:
            logger.error(f"Title optimization error: {e}")
            return self._fallback_title_optimization(video)
    
    def optimize_video_description(self, video: YoutubeVideo) -> Dict[str, Any]:
        """
        Generate optimized video description with SEO and sales integration
        
        Args:
            video: YoutubeVideo model instance
            
        Returns:
            Dictionary with optimization results
        """
        try:
            if not self.perplexity_api:
                return self._fallback_description_optimization(video)
            
            # Prepare context for description optimization
            prompt_data = {
                'title': video.title,
                'primary_topic': video.primary_topic or 'AI Governance',
                'secondary_topics': ', '.join(video.secondary_topics or []),
                'target_audience': video.target_audience or 'executives',
                'category': video.category or 'AI Governance',
                'key_insights': 'Expert insights on AI governance, compliance, and accessibility',
                'cta_goals': 'Drive consultation requests and speaking engagements'
            }
            
            prompt = self.youtube_templates['video_description_optimization'].format(**prompt_data)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are an expert YouTube content strategist for executive thought leadership. Create descriptions that establish authority while driving business results.",
                model=PerplexityModel.LARGE,
                temperature=0.3,
                max_tokens=1500,
                return_related_questions=False
            )
            
            response = self.perplexity_api.chat_completion(request)
            
            if response and response.content:
                # Store original description if not already stored
                if not video.original_description:
                    video.original_description = video.description or ''
                
                # Update video description
                optimized_description = response.content
                
                # Integrate strategic sales links
                optimized_description = self._integrate_sales_links(optimized_description, video)
                
                video.description = optimized_description
                
                # Extract and update SEO tags
                seo_tags = self._extract_seo_tags_from_description(optimized_description)
                video.seo_tags = list(set((video.seo_tags or []) + seo_tags))
                
                return {
                    'success': True,
                    'original_description': video.original_description,
                    'optimized_description': optimized_description,
                    'seo_tags_added': seo_tags,
                    'sales_links_integrated': len(self._find_sales_links_in_text(optimized_description)),
                    'method': 'perplexity_ai',
                    'api_usage': {
                        'calls_made': 1,
                        'tokens_used': response.usage.get('total_tokens', 0) if response.usage else 0,
                        'model_used': response.model
                    }
                }
            
            return self._fallback_description_optimization(video)
            
        except Exception as e:
            logger.error(f"Description optimization error: {e}")
            return self._fallback_description_optimization(video)
    
    def generate_video_chapters(self, video: YoutubeVideo) -> Dict[str, Any]:
        """
        Generate timestamped chapters using AI analysis
        
        Args:
            video: YoutubeVideo model instance
            
        Returns:
            Dictionary with chapter generation results
        """
        try:
            if not self.perplexity_api:
                return self._fallback_chapter_generation(video)
            
            # Prepare context for chapter generation
            prompt_data = {
                'title': video.title,
                'duration_seconds': video.video_duration_seconds or 1800,  # Default 30 minutes
                'primary_topic': video.primary_topic or 'AI Governance',
                'content_overview': video.description or 'Expert discussion on AI governance and compliance',
                'key_points': ', '.join(video.secondary_topics or ['AI compliance', 'risk management', 'best practices']),
                'target_audience': video.target_audience or 'executives'
            }
            
            prompt = self.youtube_templates['chapter_generation'].format(**prompt_data)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a YouTube content strategist creating chapters for executive thought leadership videos. Focus on logical flow and SEO optimization.",
                model=PerplexityModel.LARGE,
                temperature=0.3,
                max_tokens=1200,
                return_related_questions=False
            )
            
            response = self.perplexity_api.chat_completion(request)
            
            if response and response.content:
                try:
                    # Parse JSON response
                    chapters_data = json.loads(response.content)
                    
                    # Create chapter records in database
                    chapters_created = []
                    for idx, chapter_info in enumerate(chapters_data.get('chapters', [])):
                        chapter = VideoChapter(
                            video_id=video.id,
                            chapter_title=chapter_info['title'],
                            start_time_seconds=chapter_info['start_time'],
                            duration_seconds=chapter_info.get('estimated_duration', 180),
                            chapter_order=idx + 1,
                            key_topics=chapter_info.get('key_topics', []),
                            relevant_keywords=chapter_info.get('seo_keywords', []),
                            chapter_description=chapter_info.get('description', ''),
                            ai_generated=True,
                            confidence_score=0.8
                        )
                        
                        # Calculate end time
                        if chapter.duration_seconds:
                            chapter.end_time_seconds = chapter.start_time_seconds + chapter.duration_seconds
                        
                        db.session.add(chapter)
                        chapters_created.append(chapter.to_dict())
                    
                    db.session.commit()
                    
                    return {
                        'success': True,
                        'chapters_created': len(chapters_created),
                        'chapters': chapters_created,
                        'seo_optimization_notes': chapters_data.get('seo_optimization_notes', []),
                        'method': 'perplexity_ai',
                        'api_usage': {
                            'calls_made': 1,
                            'tokens_used': response.usage.get('total_tokens', 0) if response.usage else 0,
                            'model_used': response.model
                        }
                    }
                    
                except json.JSONDecodeError:
                    logger.error("Failed to parse chapter generation response")
                    return self._fallback_chapter_generation(video)
            
            return self._fallback_chapter_generation(video)
            
        except Exception as e:
            logger.error(f"Chapter generation error: {e}")
            return self._fallback_chapter_generation(video)
    
    def optimize_sales_links(self, video: YoutubeVideo) -> Dict[str, Any]:
        """
        Optimize strategic placement of sales and lead generation links
        
        Args:
            video: YoutubeVideo model instance
            
        Returns:
            Dictionary with sales link optimization results
        """
        try:
            if not self.perplexity_api:
                return self._fallback_sales_optimization(video)
            
            # Prepare context for sales link strategy
            prompt_data = {
                'primary_topic': video.primary_topic or 'AI Governance',
                'target_audience': video.target_audience or 'executives',
                'duration_seconds': video.video_duration_seconds or 1800,
                'content_type': video.content_type or 'thought_leadership',
                'value_props': 'AI governance expertise, compliance guidance, risk management'
            }
            
            prompt = self.youtube_templates['sales_link_strategy'].format(**prompt_data)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a conversion optimization expert for professional services. Create strategic link placement that drives high-value business leads.",
                model=PerplexityModel.LARGE,
                temperature=0.2,
                max_tokens=1000,
                return_related_questions=False
            )
            
            response = self.perplexity_api.chat_completion(request)
            
            if response and response.content:
                try:
                    # Parse JSON response
                    strategy_data = json.loads(response.content)
                    
                    # Update video with sales link strategy
                    video.sales_links = {
                        'consultation': self.sales_links['consultation'],
                        'speaking': self.sales_links['speaking'],
                        'board_assessment': self.sales_links['board_assessment'],
                        'governance_checklist': self.sales_links['governance_checklist'],
                        'calendar': self.sales_links['calendar']
                    }
                    
                    video.call_to_action = strategy_data.get('call_to_action', 'Contact Dr. Dede for AI governance consultation')
                    video.lead_magnets = strategy_data.get('lead_magnets', [])
                    
                    # Update monetization strategy
                    video.monetization_strategy = [
                        'speaking_leads', 'consulting_leads', 'board_opportunities', 'thought_leadership'
                    ]
                    
                    return {
                        'success': True,
                        'sales_links_configured': len(video.sales_links),
                        'lead_magnets_added': len(video.lead_magnets),
                        'call_to_action': video.call_to_action,
                        'strategy_data': strategy_data,
                        'method': 'perplexity_ai',
                        'api_usage': {
                            'calls_made': 1,
                            'tokens_used': response.usage.get('total_tokens', 0) if response.usage else 0,
                            'model_used': response.model
                        }
                    }
                    
                except json.JSONDecodeError:
                    logger.error("Failed to parse sales optimization response")
                    return self._fallback_sales_optimization(video)
            
            return self._fallback_sales_optimization(video)
            
        except Exception as e:
            logger.error(f"Sales optimization error: {e}")
            return self._fallback_sales_optimization(video)
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _capture_video_snapshot(self, video: YoutubeVideo) -> Dict[str, Any]:
        """Capture current state of video for before/after comparison"""
        return {
            'title': video.title,
            'description': video.description,
            'seo_tags': video.seo_tags or [],
            'target_keywords': video.target_keywords or [],
            'sales_links': video.sales_links or {},
            'call_to_action': video.call_to_action,
            'lead_magnets': video.lead_magnets or [],
            'optimization_score': video.optimization_score,
            'snapshot_timestamp': datetime.utcnow().isoformat()
        }
    
    def _update_api_usage(self, results: Dict[str, Any], component_result: Dict[str, Any]) -> None:
        """Update API usage tracking in results"""
        if 'api_usage' in component_result:
            usage = component_result['api_usage']
            results['api_usage']['calls_made'] += usage.get('calls_made', 0)
            results['api_usage']['tokens_used'] += usage.get('tokens_used', 0)
            # Estimate cost (approximate Perplexity pricing)
            tokens = usage.get('tokens_used', 0)
            estimated_cost = (tokens / 1000) * 0.002  # Rough estimate
            results['api_usage']['estimated_cost'] += estimated_cost
    
    def _calculate_optimization_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall optimization score based on components"""
        components = results.get('components_optimized', [])
        component_weights = {
            'title': 0.25,
            'description': 0.30,
            'chapters': 0.25,
            'sales_links': 0.20
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for component in components:
            if component in component_weights:
                total_score += component_weights[component]
                total_weight += component_weights[component]
        
        # Base score on components completed
        if total_weight > 0:
            return min(total_score / max(total_weight, 1.0), 1.0)
        
        return 0.0
    
    def _integrate_sales_links(self, description: str, video: YoutubeVideo) -> str:
        """Integrate sales links into video description strategically"""
        # Add consultation link early in description
        consultation_link = f"\n\n🎯 Book a consultation: {self.sales_links['consultation']}\n"
        
        # Add speaking inquiry link
        speaking_link = f"\n🎤 Speaking inquiries: {self.sales_links['speaking']}\n"
        
        # Add free resources
        resources_link = f"\n📋 Free AI Governance Checklist: {self.sales_links['governance_checklist']}\n"
        
        # Insert links at strategic positions
        paragraphs = description.split('\n\n')
        
        if len(paragraphs) >= 3:
            # Insert consultation link after first paragraph
            paragraphs.insert(1, consultation_link.strip())
            # Insert resources link before last paragraph
            paragraphs.insert(-1, resources_link.strip())
            # Add speaking link at end
            paragraphs.append(speaking_link.strip())
        else:
            # Fallback: append all links
            paragraphs.extend([consultation_link.strip(), resources_link.strip(), speaking_link.strip()])
        
        return '\n\n'.join(paragraphs)
    
    def _extract_seo_tags_from_description(self, description: str) -> List[str]:
        """Extract SEO-relevant hashtags and keywords from description"""
        # Look for existing hashtags
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, description.lower())
        
        # Add primary keywords as tags
        seo_tags = []
        for keyword in self.seo_keywords['primary']:
            if keyword.lower() in description.lower():
                # Convert to hashtag format
                tag = keyword.replace(' ', '').replace('-', '').lower()
                seo_tags.append(f"#{tag}")
        
        # Add trending keywords
        for keyword in self.seo_keywords['trending']:
            if keyword.lower() in description.lower():
                tag = keyword.replace(' ', '').replace('-', '').lower()
                seo_tags.append(f"#{tag}")
        
        return list(set(hashtags + [tag.replace('#', '') for tag in seo_tags]))
    
    def _find_sales_links_in_text(self, text: str) -> List[str]:
        """Find sales links in text"""
        links_found = []
        for link_type, url in self.sales_links.items():
            if url in text:
                links_found.append(link_type)
        return links_found
    
    # ========================================
    # Fallback Methods (when Perplexity unavailable)
    # ========================================
    
    def _fallback_title_optimization(self, video: YoutubeVideo) -> Dict[str, Any]:
        """Fallback title optimization using keyword insertion"""
        original_title = video.title
        
        # Simple keyword enhancement
        enhanced_title = original_title
        if 'AI' not in enhanced_title and video.primary_topic:
            enhanced_title = f"AI Governance: {enhanced_title}"
        
        # Store original if not stored
        if not video.original_title:
            video.original_title = original_title
        
        video.title = enhanced_title[:70]  # YouTube limit
        
        return {
            'success': True,
            'original_title': original_title,
            'optimized_title': video.title,
            'method': 'fallback_keyword_insertion',
            'seo_improvements': ['Added primary keyword'],
            'keywords_added': ['AI Governance']
        }
    
    def _fallback_description_optimization(self, video: YoutubeVideo) -> Dict[str, Any]:
        """Fallback description optimization using templates"""
        if not video.original_description:
            video.original_description = video.description or ''
        
        # Use template-based description
        template_description = f"""
{video.title}

In this video, Dr. Dede shares expert insights on {video.primary_topic or 'AI governance'} and its impact on business operations and compliance.

Key topics covered:
• AI governance best practices
• Regulatory compliance strategies  
• Risk management frameworks
• Accessibility considerations

🎯 Book a consultation: {self.sales_links['consultation']}
📋 Free AI Governance Checklist: {self.sales_links['governance_checklist']}
🎤 Speaking inquiries: {self.sales_links['speaking']}

#AIGovernance #Compliance #RiskManagement #DigitalAccessibility
        """.strip()
        
        video.description = template_description
        
        return {
            'success': True,
            'original_description': video.original_description,
            'optimized_description': template_description,
            'method': 'fallback_template',
            'seo_tags_added': ['aigovernance', 'compliance', 'riskmanagement', 'digitalaccessibility']
        }
    
    def _fallback_chapter_generation(self, video: YoutubeVideo) -> Dict[str, Any]:
        """Fallback chapter generation using standard structure"""
        duration = video.video_duration_seconds or 1800
        
        # Create standard chapters
        standard_chapters = [
            {'title': 'Introduction', 'start': 0, 'duration': 120},
            {'title': 'Current State of AI Governance', 'start': 120, 'duration': 300},
            {'title': 'Regulatory Landscape', 'start': 420, 'duration': 360},
            {'title': 'Implementation Strategies', 'start': 780, 'duration': 420},
            {'title': 'Best Practices and Recommendations', 'start': 1200, 'duration': 360},
            {'title': 'Q&A and Conclusions', 'start': 1560, 'duration': 240}
        ]
        
        chapters_created = []
        for idx, chapter_info in enumerate(standard_chapters):
            if chapter_info['start'] < duration:
                chapter = VideoChapter(
                    video_id=video.id,
                    chapter_title=chapter_info['title'],
                    start_time_seconds=chapter_info['start'],
                    duration_seconds=min(chapter_info['duration'], duration - chapter_info['start']),
                    end_time_seconds=min(chapter_info['start'] + chapter_info['duration'], duration),
                    chapter_order=idx + 1,
                    key_topics=['AI governance', 'compliance'],
                    ai_generated=True,
                    confidence_score=0.6
                )
                db.session.add(chapter)
                chapters_created.append(chapter.to_dict())
        
        db.session.commit()
        
        return {
            'success': True,
            'chapters_created': len(chapters_created),
            'chapters': chapters_created,
            'method': 'fallback_standard_structure'
        }
    
    def _fallback_sales_optimization(self, video: YoutubeVideo) -> Dict[str, Any]:
        """Fallback sales optimization using standard configuration"""
        video.sales_links = self.sales_links.copy()
        video.call_to_action = "Contact Dr. Dede for AI governance consultation and speaking opportunities"
        video.lead_magnets = ['Free AI Governance Checklist', 'Risk Assessment Tool']
        video.monetization_strategy = ['speaking_leads', 'consulting_leads', 'board_opportunities']
        
        return {
            'success': True,
            'sales_links_configured': len(video.sales_links),
            'lead_magnets_added': len(video.lead_magnets),
            'method': 'fallback_standard_config'
        }


# Factory functions for service creation
def create_youtube_optimizer(perplexity_api_key: Optional[str] = None) -> YoutubeVideoOptimizer:
    """
    Create YouTube video optimizer service
    
    Args:
        perplexity_api_key: Optional Perplexity API key
        
    Returns:
        YoutubeVideoOptimizer instance
    """
    return YoutubeVideoOptimizer(perplexity_api_key)


def create_youtube_service() -> YoutubeVideoOptimizer:
    """
    Create YouTube service with auto-configured API key
    
    Returns:
        YoutubeVideoOptimizer instance with environment API key
    """
    return YoutubeVideoOptimizer()