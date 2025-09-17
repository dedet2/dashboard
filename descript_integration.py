"""
Descript Integration Service for LoRA Digital Clone Development System
Handles voice/audio processing, transcription, and Descript partner workflows
"""

import os
import requests
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class DescriptAPIError(Exception):
    """Custom exception for Descript API errors"""
    pass

class DescriptIntegration:
    """
    Comprehensive Descript integration for voice processing and transcription.
    Combines Descript partner API with OpenAI Whisper for full functionality.
    """
    
    def __init__(self, descript_token: Optional[str] = None, openai_api_key: Optional[str] = None):
        self.descript_token = descript_token or os.getenv('DESCRIPT_API_KEY')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = "https://descriptapi.com/v1"
        
        # Headers for Descript API
        self.headers = {
            'Authorization': f'Bearer {self.descript_token}' if self.descript_token else '',
            'Content-Type': 'application/json'
        }
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info("Descript Integration initialized")
    
    async def transcribe_audio(self, audio_file_path: str, language: str = "en") -> Dict:
        """
        Transcribe audio using OpenAI Whisper API (more reliable than Descript's limited API)
        
        Args:
            audio_file_path: Path to audio file
            language: Language code for transcription
            
        Returns:
            Dict with transcription data including text, timing, and confidence scores
        """
        try:
            if not self.openai_api_key:
                raise DescriptAPIError("OpenAI API key required for transcription")
            
            logger.info(f"Starting transcription for {audio_file_path}")
            
            # Prepare file for OpenAI Whisper
            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'file': audio_file,
                    'model': (None, 'whisper-1'),
                    'language': (None, language),
                    'response_format': (None, 'verbose_json'),
                    'timestamp_granularities[]': (None, 'word'),
                    'timestamp_granularities[]': (None, 'segment')
                }
                
                headers = {'Authorization': f'Bearer {self.openai_api_key}'}
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        'https://api.openai.com/v1/audio/transcriptions',
                        headers=headers,
                        data=files
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Transcription completed successfully")
                            return self._process_whisper_response(result, audio_file_path)
                        else:
                            error_text = await response.text()
                            raise DescriptAPIError(f"Transcription failed: {error_text}")
                            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise DescriptAPIError(f"Transcription failed: {str(e)}")
    
    def _process_whisper_response(self, whisper_result: Dict, audio_file_path: str) -> Dict:
        """Process OpenAI Whisper response into standardized format"""
        
        return {
            'text': whisper_result.get('text', ''),
            'language': whisper_result.get('language', 'en'),
            'duration': whisper_result.get('duration', 0),
            'segments': whisper_result.get('segments', []),
            'words': whisper_result.get('words', []),
            'confidence': self._calculate_average_confidence(whisper_result.get('segments', [])),
            'metadata': {
                'source_file': audio_file_path,
                'processing_time': datetime.utcnow().isoformat(),
                'processor': 'whisper-1',
                'language_detected': whisper_result.get('language', 'en')
            }
        }
    
    def _calculate_average_confidence(self, segments: List[Dict]) -> float:
        """Calculate average confidence score from segments"""
        if not segments:
            return 0.0
        
        total_confidence = sum(segment.get('no_speech_prob', 0) for segment in segments)
        # Convert no_speech_prob to confidence (inverse)
        avg_no_speech = total_confidence / len(segments)
        return max(0.0, min(1.0, 1.0 - avg_no_speech))
    
    def create_descript_import_url(self, audio_files: List[Dict], partner_drive_id: str, source_id: str) -> Dict:
        """
        Create Descript import URL for partner workflow (for users who want to edit in Descript)
        
        Args:
            audio_files: List of audio file dicts with url, type, name
            partner_drive_id: Partner drive identifier
            source_id: Source identifier for tracking
            
        Returns:
            Dict with import URL and metadata
        """
        try:
            if not self.descript_token:
                raise DescriptAPIError("Descript API token required for partner workflow")
            
            payload = {
                "partner_drive_id": partner_drive_id,
                "source_id": source_id,
                "files": audio_files
            }
            
            response = self.session.post(
                f"{self.base_url}/edit_in_descript/schema",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Descript import URL created for source {source_id}")
                return {
                    'import_url': result.get('import_url'),
                    'expires_at': (datetime.utcnow() + timedelta(hours=3)).isoformat(),
                    'partner_drive_id': partner_drive_id,
                    'source_id': source_id,
                    'files_count': len(audio_files),
                    'created_at': datetime.utcnow().isoformat()
                }
            else:
                error_msg = f"Descript API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise DescriptAPIError(error_msg)
                
        except Exception as e:
            logger.error(f"Error creating Descript import URL: {str(e)}")
            raise DescriptAPIError(f"Failed to create import URL: {str(e)}")
    
    async def analyze_voice_characteristics(self, audio_file_path: str) -> Dict:
        """
        Analyze voice characteristics for LoRA training
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Dict with voice analysis data
        """
        try:
            logger.info(f"Analyzing voice characteristics for {audio_file_path}")
            
            # Get transcription with timing data
            transcription = await self.transcribe_audio(audio_file_path)
            
            # Analyze voice characteristics from transcription segments
            voice_analysis = {
                'pitch_analysis': self._analyze_pitch_from_segments(transcription.get('segments', [])),
                'speech_rate': self._calculate_speech_rate(transcription),
                'voice_quality': self._assess_voice_quality(transcription),
                'emotional_tone': self._detect_emotional_tone(transcription.get('text', '')),
                'speaking_patterns': self._analyze_speaking_patterns(transcription.get('words', [])),
                'audio_quality': {
                    'clarity_score': transcription.get('confidence', 0),
                    'background_noise': self._assess_background_noise(transcription),
                    'recommended_for_training': transcription.get('confidence', 0) > 0.7
                },
                'metadata': {
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'source_file': audio_file_path,
                    'duration': transcription.get('duration', 0)
                }
            }
            
            logger.info(f"Voice analysis completed for {audio_file_path}")
            return voice_analysis
            
        except Exception as e:
            logger.error(f"Voice analysis error: {str(e)}")
            raise DescriptAPIError(f"Voice analysis failed: {str(e)}")
    
    def _analyze_pitch_from_segments(self, segments: List[Dict]) -> Dict:
        """Analyze pitch characteristics from transcription segments"""
        # Simplified pitch analysis based on segment timing and no_speech_prob
        if not segments:
            return {'average_pitch': 'unknown', 'pitch_variation': 'unknown'}
        
        # Basic pitch estimation from segment characteristics
        avg_segment_length = sum(seg.get('end', 0) - seg.get('start', 0) for seg in segments) / len(segments)
        pitch_variation = len([seg for seg in segments if seg.get('no_speech_prob', 0) < 0.1]) / len(segments)
        
        return {
            'average_pitch': 'medium',  # Would need audio analysis library for actual pitch
            'pitch_variation': 'high' if pitch_variation > 0.8 else 'medium' if pitch_variation > 0.5 else 'low',
            'segment_analysis': {
                'average_segment_length': avg_segment_length,
                'speech_density': pitch_variation
            }
        }
    
    def _calculate_speech_rate(self, transcription: Dict) -> Dict:
        """Calculate speech rate from transcription"""
        text = transcription.get('text', '')
        duration = transcription.get('duration', 1)
        
        word_count = len(text.split()) if text else 0
        words_per_minute = (word_count / duration) * 60 if duration > 0 else 0
        
        return {
            'words_per_minute': round(words_per_minute, 2),
            'total_words': word_count,
            'duration_seconds': duration,
            'speech_pace': 'fast' if words_per_minute > 160 else 'normal' if words_per_minute > 120 else 'slow'
        }
    
    def _assess_voice_quality(self, transcription: Dict) -> Dict:
        """Assess voice quality from transcription confidence and metadata"""
        confidence = transcription.get('confidence', 0)
        segments = transcription.get('segments', [])
        
        # Assess consistency across segments
        if segments:
            confidence_values = [1 - seg.get('no_speech_prob', 0) for seg in segments]
            consistency = 1 - (max(confidence_values) - min(confidence_values)) if confidence_values else 0
        else:
            consistency = 0
        
        return {
            'overall_quality': 'excellent' if confidence > 0.9 else 'good' if confidence > 0.7 else 'fair' if confidence > 0.5 else 'poor',
            'confidence_score': round(confidence, 3),
            'consistency_score': round(consistency, 3),
            'suitable_for_training': confidence > 0.7 and consistency > 0.6
        }
    
    def _detect_emotional_tone(self, text: str) -> Dict:
        """Basic emotional tone detection from text"""
        # Simplified emotion detection - in production, use sentiment analysis library
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'happy', 'excited']
        negative_words = ['bad', 'terrible', 'awful', 'sad', 'angry', 'frustrated', 'disappointed']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            tone = 'positive'
        elif negative_count > positive_count:
            tone = 'negative'
        else:
            tone = 'neutral'
        
        return {
            'primary_tone': tone,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count,
            'confidence': abs(positive_count - negative_count) / max(len(text.split()), 1)
        }
    
    def _analyze_speaking_patterns(self, words: List[Dict]) -> Dict:
        """Analyze speaking patterns from word-level timing"""
        if not words:
            return {'pattern_type': 'unknown', 'pause_frequency': 'unknown'}
        
        # Calculate pauses between words
        pauses = []
        for i in range(1, len(words)):
            if 'end' in words[i-1] and 'start' in words[i]:
                pause = words[i]['start'] - words[i-1]['end']
                if pause > 0.1:  # Only count significant pauses
                    pauses.append(pause)
        
        avg_pause = sum(pauses) / len(pauses) if pauses else 0
        
        return {
            'average_pause_duration': round(avg_pause, 3),
            'pause_frequency': len(pauses) / len(words) if words else 0,
            'speaking_rhythm': 'rhythmic' if avg_pause > 0.3 else 'flowing' if avg_pause > 0.1 else 'rapid',
            'total_pauses': len(pauses)
        }
    
    def _assess_background_noise(self, transcription: Dict) -> Dict:
        """Assess background noise from transcription confidence"""
        segments = transcription.get('segments', [])
        
        if not segments:
            return {'noise_level': 'unknown', 'quality': 'unknown'}
        
        # Use no_speech_prob as proxy for background noise
        noise_indicators = [seg.get('no_speech_prob', 0) for seg in segments]
        avg_noise = sum(noise_indicators) / len(noise_indicators)
        
        return {
            'noise_level': 'high' if avg_noise > 0.3 else 'medium' if avg_noise > 0.1 else 'low',
            'noise_score': round(avg_noise, 3),
            'quality': 'clean' if avg_noise < 0.1 else 'acceptable' if avg_noise < 0.3 else 'noisy'
        }

class DescriptWorkflowManager:
    """
    Manages complete Descript workflows for LoRA training data processing
    """
    
    def __init__(self, descript_integration: DescriptIntegration):
        self.descript = descript_integration
        self.workflows = {}
        
    async def process_training_data(self, audio_file_path: str, clone_id: int) -> Dict:
        """
        Complete workflow for processing audio training data
        
        Args:
            audio_file_path: Path to audio file
            clone_id: Digital clone ID
            
        Returns:
            Complete processing results
        """
        try:
            logger.info(f"Starting training data processing for clone {clone_id}")
            
            # Step 1: Transcribe audio
            transcription = await self.descript.transcribe_audio(audio_file_path)
            
            # Step 2: Analyze voice characteristics
            voice_analysis = await self.descript.analyze_voice_characteristics(audio_file_path)
            
            # Step 3: Generate processing metadata
            metadata = {
                'clone_id': clone_id,
                'processing_timestamp': datetime.utcnow().isoformat(),
                'file_path': audio_file_path,
                'quality_assessment': {
                    'transcription_confidence': transcription.get('confidence', 0),
                    'voice_quality': voice_analysis.get('audio_quality', {}),
                    'recommended_for_training': voice_analysis.get('audio_quality', {}).get('recommended_for_training', False)
                },
                'processing_status': 'completed'
            }
            
            result = {
                'transcription': transcription,
                'voice_analysis': voice_analysis,
                'metadata': metadata,
                'training_recommendations': self._generate_training_recommendations(voice_analysis)
            }
            
            logger.info(f"Training data processing completed for clone {clone_id}")
            return result
            
        except Exception as e:
            logger.error(f"Training data processing failed: {str(e)}")
            raise DescriptAPIError(f"Processing failed: {str(e)}")
    
    def _generate_training_recommendations(self, voice_analysis: Dict) -> Dict:
        """Generate recommendations for LoRA training based on voice analysis"""
        
        quality = voice_analysis.get('audio_quality', {})
        speech_rate = voice_analysis.get('speech_rate', {})
        
        recommendations = {
            'use_for_training': quality.get('recommended_for_training', False),
            'training_weight': 1.0,  # Default weight
            'preprocessing_needed': [],
            'optimization_suggestions': []
        }
        
        # Adjust training weight based on quality
        confidence = quality.get('clarity_score', 0)
        if confidence > 0.9:
            recommendations['training_weight'] = 1.2  # High quality - increase weight
        elif confidence < 0.7:
            recommendations['training_weight'] = 0.8  # Lower quality - decrease weight
        
        # Add preprocessing recommendations
        if quality.get('background_noise', {}).get('noise_level') == 'high':
            recommendations['preprocessing_needed'].append('noise_reduction')
        
        if speech_rate.get('speech_pace') == 'fast':
            recommendations['preprocessing_needed'].append('speed_normalization')
        
        # Add optimization suggestions
        if confidence < 0.8:
            recommendations['optimization_suggestions'].append('Consider re-recording in quieter environment')
        
        if speech_rate.get('words_per_minute', 0) > 180:
            recommendations['optimization_suggestions'].append('Speak slightly slower for better model training')
        
        return recommendations

# Factory functions for easy integration
def create_descript_integration(descript_token: Optional[str] = None, openai_api_key: Optional[str] = None) -> DescriptIntegration:
    """Create Descript integration instance"""
    return DescriptIntegration(descript_token, openai_api_key)

def create_descript_workflow_manager(descript_integration: DescriptIntegration) -> DescriptWorkflowManager:
    """Create Descript workflow manager"""
    return DescriptWorkflowManager(descript_integration)

# Usage example
if __name__ == "__main__":
    async def main():
        # Initialize Descript integration
        descript = create_descript_integration()
        workflow_manager = create_descript_workflow_manager(descript)
        
        # Example usage
        try:
            # Process training data
            result = await workflow_manager.process_training_data(
                "/path/to/audio.mp3", 
                clone_id=1
            )
            print("Processing completed:", result['metadata']['processing_status'])
            
        except DescriptAPIError as e:
            print(f"Error: {e}")
    
    # Run example
    asyncio.run(main())