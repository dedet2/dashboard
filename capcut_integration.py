"""
CapCut Integration Service for LoRA Digital Clone Development System
Handles video processing, avatar generation, and automated video creation using CapCutAPI
"""

import os
import requests
import json
import asyncio
import aiohttp
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import uuid
import time

# Configure logging
logger = logging.getLogger(__name__)

class CapCutAPIError(Exception):
    """Custom exception for CapCut API errors"""
    pass

class CapCutIntegration:
    """
    Comprehensive CapCut integration using the open-source CapCutAPI for video processing and avatar generation
    """
    
    def __init__(self, api_base_url: str = "http://localhost:9001", capcut_executable_path: Optional[str] = None):
        self.api_base_url = api_base_url
        self.capcut_executable = capcut_executable_path or self._find_capcut_executable()
        self.session = requests.Session()
        
        # Default avatar styles and configurations
        self.avatar_styles = {
            'professional': {
                'style': 'business',
                'clothing': 'suit',
                'background': 'office',
                'expressions': ['confident', 'friendly', 'focused']
            },
            'casual': {
                'style': 'relaxed',
                'clothing': 'casual',
                'background': 'neutral',
                'expressions': ['friendly', 'approachable', 'warm']
            },
            'presenter': {
                'style': 'polished',
                'clothing': 'presentation',
                'background': 'clean',
                'expressions': ['engaging', 'authoritative', 'welcoming']
            },
            'expert': {
                'style': 'authoritative',
                'clothing': 'professional',
                'background': 'library',
                'expressions': ['knowledgeable', 'thoughtful', 'confident']
            }
        }
        
        # Voice configurations for avatar integration
        self.voice_configs = {
            'en-US-female': {'gender': 'female', 'accent': 'american', 'tone': 'professional'},
            'en-US-male': {'gender': 'male', 'accent': 'american', 'tone': 'confident'},
            'en-UK-female': {'gender': 'female', 'accent': 'british', 'tone': 'elegant'},
            'en-UK-male': {'gender': 'male', 'accent': 'british', 'tone': 'authoritative'}
        }
        
        logger.info("CapCut Integration initialized")
    
    def _find_capcut_executable(self) -> Optional[str]:
        """Find CapCut executable on the system"""
        possible_paths = [
            "C:\\Program Files\\CapCut\\CapCut.exe",  # Windows
            "/Applications/CapCut.app/Contents/MacOS/CapCut",  # macOS
            "/usr/bin/capcut",  # Linux
            "/opt/CapCut/capcut"  # Linux alternative
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found CapCut executable at {path}")
                return path
        
        # Try to find in PATH
        capcut_path = shutil.which("capcut")
        if capcut_path:
            logger.info(f"Found CapCut in PATH: {capcut_path}")
            return capcut_path
        
        logger.warning("CapCut executable not found")
        return None
    
    def check_api_status(self) -> Dict:
        """Check if CapCutAPI server is running and responsive"""
        try:
            response = self.session.get(f"{self.api_base_url}/status", timeout=5)
            if response.status_code == 200:
                return {'status': 'running', 'api_version': response.json().get('version', 'unknown')}
            else:
                return {'status': 'error', 'message': f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {'status': 'offline', 'error': str(e)}
    
    def create_draft(self, draft_name: Optional[str] = None) -> Dict:
        """
        Create a new CapCut project draft
        
        Args:
            draft_name: Name for the draft (auto-generated if not provided)
            
        Returns:
            Dict with draft information
        """
        try:
            if not draft_name:
                draft_name = f"lora_clone_{uuid.uuid4().hex[:8]}_{int(time.time())}"
            
            payload = {'draft_name': draft_name}
            
            response = self.session.post(
                f"{self.api_base_url}/create_draft",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Created CapCut draft: {draft_name}")
                return {
                    'draft_id': result.get('draft_id'),
                    'draft_name': draft_name,
                    'created_at': datetime.utcnow().isoformat(),
                    'status': 'created'
                }
            else:
                raise CapCutAPIError(f"Failed to create draft: {response.text}")
                
        except Exception as e:
            logger.error(f"Error creating draft: {str(e)}")
            raise CapCutAPIError(f"Draft creation failed: {str(e)}")
    
    def add_avatar(self, draft_id: str, avatar_config: Dict) -> Dict:
        """
        Add AI avatar to CapCut project
        
        Args:
            draft_id: Draft identifier
            avatar_config: Avatar configuration with style, script, voice, etc.
            
        Returns:
            Dict with avatar addition results
        """
        try:
            # Extract configuration
            script = avatar_config.get('script', '')
            avatar_style = avatar_config.get('style', 'professional')
            voice = avatar_config.get('voice', 'en-US-female')
            duration = avatar_config.get('duration', 0)
            
            # Get style configuration
            style_config = self.avatar_styles.get(avatar_style, self.avatar_styles['professional'])
            
            payload = {
                'draft_id': draft_id,
                'avatar_type': avatar_style,
                'script': script,
                'voice': voice,
                'duration': duration,
                'style_settings': style_config,
                'animation_settings': {
                    'gesture_frequency': avatar_config.get('gesture_frequency', 'medium'),
                    'eye_contact': avatar_config.get('eye_contact', True),
                    'head_movement': avatar_config.get('head_movement', 'natural'),
                    'facial_expressions': avatar_config.get('expressions', style_config['expressions'])
                }
            }
            
            response = self.session.post(
                f"{self.api_base_url}/add_avatar",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Added avatar to draft {draft_id}")
                return {
                    'avatar_id': result.get('avatar_id'),
                    'draft_id': draft_id,
                    'style': avatar_style,
                    'script_length': len(script),
                    'estimated_duration': result.get('duration', duration),
                    'status': 'added'
                }
            else:
                raise CapCutAPIError(f"Failed to add avatar: {response.text}")
                
        except Exception as e:
            logger.error(f"Error adding avatar: {str(e)}")
            raise CapCutAPIError(f"Avatar addition failed: {str(e)}")
    
    def add_video_background(self, draft_id: str, video_url: str, settings: Dict = None) -> Dict:
        """
        Add video background to CapCut project
        
        Args:
            draft_id: Draft identifier
            video_url: URL or path to background video
            settings: Video settings (start, end, volume, etc.)
            
        Returns:
            Dict with video addition results
        """
        try:
            settings = settings or {}
            
            payload = {
                'draft_id': draft_id,
                'video_url': video_url,
                'start': settings.get('start', 0),
                'end': settings.get('end', 10),
                'volume': settings.get('volume', 0.3),  # Lower volume for background
                'transition': settings.get('transition', 'fade_in'),
                'effects': settings.get('effects', []),
                'position': settings.get('position', 'background')
            }
            
            response = self.session.post(
                f"{self.api_base_url}/add_video",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Added video background to draft {draft_id}")
                return {
                    'video_id': result.get('video_id'),
                    'draft_id': draft_id,
                    'duration': payload['end'] - payload['start'],
                    'status': 'added'
                }
            else:
                raise CapCutAPIError(f"Failed to add video background: {response.text}")
                
        except Exception as e:
            logger.error(f"Error adding video background: {str(e)}")
            raise CapCutAPIError(f"Video background addition failed: {str(e)}")
    
    def add_text_overlay(self, draft_id: str, text_config: Dict) -> Dict:
        """
        Add text overlay to CapCut project
        
        Args:
            draft_id: Draft identifier
            text_config: Text configuration with content, styling, timing
            
        Returns:
            Dict with text addition results
        """
        try:
            payload = {
                'draft_id': draft_id,
                'text': text_config.get('text', ''),
                'start': text_config.get('start', 0),
                'end': text_config.get('end', 5),
                'font': text_config.get('font', 'Source Han Sans'),
                'font_color': text_config.get('color', '#FFFFFF'),
                'font_size': text_config.get('size', 48),
                'position': text_config.get('position', 'bottom'),
                'animation': text_config.get('animation', 'fade_in'),
                'shadow_enabled': text_config.get('shadow', True),
                'background_enabled': text_config.get('background', False),
                'background_color': text_config.get('background_color', '#00000080')
            }
            
            response = self.session.post(
                f"{self.api_base_url}/add_text",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Added text overlay to draft {draft_id}")
                return {
                    'text_id': result.get('text_id'),
                    'draft_id': draft_id,
                    'text_content': payload['text'],
                    'duration': payload['end'] - payload['start'],
                    'status': 'added'
                }
            else:
                raise CapCutAPIError(f"Failed to add text overlay: {response.text}")
                
        except Exception as e:
            logger.error(f"Error adding text overlay: {str(e)}")
            raise CapCutAPIError(f"Text overlay addition failed: {str(e)}")
    
    def apply_template(self, draft_id: str, template_config: Dict) -> Dict:
        """
        Apply pre-configured template to CapCut project
        
        Args:
            draft_id: Draft identifier
            template_config: Template configuration
            
        Returns:
            Dict with template application results
        """
        try:
            payload = {
                'draft_id': draft_id,
                'template_name': template_config.get('name', 'corporate'),
                'brand_colors': template_config.get('brand_colors', ['#1E40AF', '#FFFFFF']),
                'logo_url': template_config.get('logo_url'),
                'transition_style': template_config.get('transitions', 'professional'),
                'effects': template_config.get('effects', ['color_correction', 'audio_enhancement'])
            }
            
            response = self.session.post(
                f"{self.api_base_url}/apply_template",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Applied template to draft {draft_id}")
                return {
                    'template_id': result.get('template_id'),
                    'draft_id': draft_id,
                    'template_name': payload['template_name'],
                    'status': 'applied'
                }
            else:
                raise CapCutAPIError(f"Failed to apply template: {response.text}")
                
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            raise CapCutAPIError(f"Template application failed: {str(e)}")
    
    def export_video(self, draft_id: str, export_config: Dict = None) -> Dict:
        """
        Export CapCut project to video file
        
        Args:
            draft_id: Draft identifier
            export_config: Export configuration (quality, format, etc.)
            
        Returns:
            Dict with export results and file path
        """
        try:
            export_config = export_config or {}
            
            payload = {
                'draft_id': draft_id,
                'quality': export_config.get('quality', 'high'),  # low, medium, high, ultra
                'format': export_config.get('format', 'mp4'),
                'resolution': export_config.get('resolution', '1920x1080'),
                'frame_rate': export_config.get('frame_rate', 30),
                'bitrate': export_config.get('bitrate', 'auto'),
                'output_path': export_config.get('output_path', f"/tmp/lora_clone_{draft_id}_{int(time.time())}.mp4"),
                'include_watermark': export_config.get('watermark', False)
            }
            
            response = self.session.post(
                f"{self.api_base_url}/export_video",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Exported video for draft {draft_id}")
                
                # Wait for export completion (simplified polling)
                export_status = self._wait_for_export_completion(result.get('job_id'), draft_id)
                
                return {
                    'export_id': result.get('job_id'),
                    'draft_id': draft_id,
                    'output_path': payload['output_path'],
                    'quality': payload['quality'],
                    'resolution': payload['resolution'],
                    'status': export_status,
                    'exported_at': datetime.utcnow().isoformat()
                }
            else:
                raise CapCutAPIError(f"Failed to export video: {response.text}")
                
        except Exception as e:
            logger.error(f"Error exporting video: {str(e)}")
            raise CapCutAPIError(f"Video export failed: {str(e)}")
    
    def _wait_for_export_completion(self, job_id: str, draft_id: str, timeout: int = 300) -> str:
        """Wait for video export to complete with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.api_base_url}/export_status/{job_id}")
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get('status', 'processing')
                    
                    if status == 'completed':
                        logger.info(f"Export completed for draft {draft_id}")
                        return 'completed'
                    elif status == 'failed':
                        logger.error(f"Export failed for draft {draft_id}")
                        return 'failed'
                    
                    # Still processing, wait before checking again
                    time.sleep(10)
                else:
                    logger.warning(f"Unable to check export status: {response.status_code}")
                    time.sleep(10)
                    
            except Exception as e:
                logger.warning(f"Error checking export status: {str(e)}")
                time.sleep(10)
        
        logger.warning(f"Export timeout for draft {draft_id}")
        return 'timeout'

class CapCutAvatarPipeline:
    """
    Complete pipeline for avatar video generation using CapCut
    """
    
    def __init__(self, capcut_integration: CapCutIntegration):
        self.capcut = capcut_integration
        self.templates = {
            'corporate': {
                'name': 'corporate',
                'brand_colors': ['#1E40AF', '#FFFFFF', '#F8FAFC'],
                'transitions': 'professional',
                'effects': ['color_correction', 'audio_enhancement']
            },
            'educational': {
                'name': 'educational',
                'brand_colors': ['#059669', '#FFFFFF', '#F0FDF4'],
                'transitions': 'smooth',
                'effects': ['clarity_boost', 'subtitle_enhancement']
            },
            'marketing': {
                'name': 'marketing',
                'brand_colors': ['#DC2626', '#FFFFFF', '#FEF2F2'],
                'transitions': 'dynamic',
                'effects': ['energy_boost', 'attention_grabber']
            }
        }
    
    async def generate_avatar_video(self, script: str, avatar_style: str = "professional", template: str = "corporate") -> Dict:
        """
        Generate complete avatar video from script
        
        Args:
            script: Text script for avatar to speak
            avatar_style: Style of avatar (professional, casual, presenter, expert)
            template: Video template to apply
            
        Returns:
            Dict with generation results and video file path
        """
        try:
            logger.info(f"Starting avatar video generation with {avatar_style} style")
            
            # Step 1: Create draft
            draft = self.capcut.create_draft()
            draft_id = draft['draft_id']
            
            # Step 2: Calculate estimated duration from script
            estimated_duration = self._calculate_script_duration(script)
            
            # Step 3: Add avatar with script
            avatar_config = {
                'script': script,
                'style': avatar_style,
                'voice': 'en-US-female',  # Can be customized
                'duration': estimated_duration,
                'gesture_frequency': 'medium',
                'eye_contact': True,
                'head_movement': 'natural'
            }
            
            avatar_result = self.capcut.add_avatar(draft_id, avatar_config)
            
            # Step 4: Apply template styling
            template_config = self.templates.get(template, self.templates['corporate'])
            template_result = self.capcut.apply_template(draft_id, template_config)
            
            # Step 5: Add title text if script is long enough
            if len(script) > 100:
                title = self._extract_title_from_script(script)
                text_config = {
                    'text': title,
                    'start': 0,
                    'end': 3,
                    'position': 'top',
                    'size': 52,
                    'color': template_config['brand_colors'][0]
                }
                text_result = self.capcut.add_text_overlay(draft_id, text_config)
            
            # Step 6: Export video
            export_config = {
                'quality': 'high',
                'resolution': '1920x1080',
                'format': 'mp4',
                'output_path': f"/tmp/avatar_video_{draft_id}_{int(time.time())}.mp4"
            }
            
            export_result = self.capcut.export_video(draft_id, export_config)
            
            # Step 7: Compile results
            result = {
                'draft_id': draft_id,
                'avatar_style': avatar_style,
                'template': template,
                'script_length': len(script),
                'estimated_duration': estimated_duration,
                'output_video': export_result['output_path'],
                'export_status': export_result['status'],
                'generated_at': datetime.utcnow().isoformat(),
                'components': {
                    'avatar': avatar_result,
                    'template': template_result,
                    'export': export_result
                }
            }
            
            logger.info(f"Avatar video generation completed: {export_result['output_path']}")
            return result
            
        except Exception as e:
            logger.error(f"Avatar video generation failed: {str(e)}")
            raise CapCutAPIError(f"Generation failed: {str(e)}")
    
    def _calculate_script_duration(self, script: str) -> float:
        """Calculate estimated duration for script based on word count"""
        words = len(script.split())
        # Average speaking rate: 150-160 words per minute
        duration_minutes = words / 155
        return round(duration_minutes * 60, 1)  # Convert to seconds
    
    def _extract_title_from_script(self, script: str) -> str:
        """Extract title from script (first sentence or phrase)"""
        sentences = script.split('.')
        if sentences:
            title = sentences[0].strip()
            # Limit title length
            if len(title) > 50:
                title = title[:47] + "..."
            return title
        return "Presentation"
    
    async def batch_generate_videos(self, scripts: List[Dict], template: str = "corporate") -> List[Dict]:
        """
        Generate multiple avatar videos in batch
        
        Args:
            scripts: List of script dicts with 'text' and optional 'style'
            template: Template to apply to all videos
            
        Returns:
            List of generation results
        """
        results = []
        
        for i, script_config in enumerate(scripts):
            try:
                logger.info(f"Processing batch video {i+1}/{len(scripts)}")
                
                script = script_config['text']
                style = script_config.get('style', 'professional')
                
                result = await self.generate_avatar_video(script, style, template)
                result['batch_index'] = i
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch video {i+1} failed: {str(e)}")
                results.append({
                    'batch_index': i,
                    'error': str(e),
                    'status': 'failed'
                })
        
        logger.info(f"Batch generation completed: {len(results)} videos processed")
        return results

# Factory functions for easy integration
def create_capcut_integration(api_base_url: str = "http://localhost:9001") -> CapCutIntegration:
    """Create CapCut integration instance"""
    return CapCutIntegration(api_base_url)

def create_capcut_avatar_pipeline(capcut_integration: CapCutIntegration) -> CapCutAvatarPipeline:
    """Create CapCut avatar pipeline"""
    return CapCutAvatarPipeline(capcut_integration)

# Usage example
if __name__ == "__main__":
    async def main():
        # Initialize CapCut integration
        capcut = create_capcut_integration()
        avatar_pipeline = create_capcut_avatar_pipeline(capcut)
        
        # Check API status
        status = capcut.check_api_status()
        print(f"CapCut API Status: {status}")
        
        if status['status'] == 'running':
            try:
                # Generate avatar video
                script = "Welcome to our digital clone demonstration. This avatar is powered by advanced LoRA technology."
                result = await avatar_pipeline.generate_avatar_video(script, "professional", "corporate")
                print(f"Video generated: {result['output_video']}")
                
            except CapCutAPIError as e:
                print(f"Error: {e}")
        else:
            print("CapCut API not available")
    
    # Run example
    asyncio.run(main())