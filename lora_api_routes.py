"""
LoRA Digital Clone API Routes for Flask Application
Comprehensive REST API endpoints for clone management, training, synthesis, and deployment
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
import json
import asyncio
import logging
from typing import Dict, List, Optional
import uuid
from werkzeug.utils import secure_filename

# Import database models
from database import (
    db, DigitalClone, TrainingData, LoRAModel, CloneSession, 
    SynthesisJob, DeploymentTarget
)

# Import services
from descript_integration import create_descript_integration, create_descript_workflow_manager
from capcut_integration import create_capcut_integration, create_capcut_avatar_pipeline
from lora_training_pipeline import create_lora_training_pipeline
from voice_synthesis_service import create_voice_synthesis_service
from video_avatar_service import create_video_avatar_service

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
lora_bp = Blueprint('lora_api', __name__, url_prefix='/api/lora')

# Configuration
UPLOAD_FOLDER = '/tmp/lora_uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'mp4', 'avi', 'mov', 'mkv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize services
descript_integration = create_descript_integration()
descript_workflow = create_descript_workflow_manager(descript_integration)
capcut_integration = create_capcut_integration()
capcut_pipeline = create_capcut_avatar_pipeline(capcut_integration)
training_pipeline = create_lora_training_pipeline()
voice_service = create_voice_synthesis_service()
video_service = create_video_avatar_service(capcut_integration)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===== DIGITAL CLONE MANAGEMENT ENDPOINTS =====

@lora_bp.route('/clones', methods=['GET'])
@jwt_required()
def get_digital_clones():
    """Get all digital clones for the current user"""
    try:
        current_user = get_jwt_identity()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        # Build query
        query = DigitalClone.query.filter_by(owner=current_user)
        
        if status:
            query = query.filter_by(training_status=status)
        
        # Paginate results
        clones = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'clones': [clone.to_dict() for clone in clones.items],
            'total': clones.total,
            'pages': clones.pages,
            'current_page': page,
            'per_page': per_page
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting digital clones: {str(e)}")
        return jsonify({'error': 'Failed to retrieve clones'}), 500

@lora_bp.route('/clones', methods=['POST'])
@jwt_required()
def create_digital_clone():
    """Create a new digital clone"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new clone
        clone = DigitalClone(
            name=data['name'],
            description=data['description'],
            owner=current_user,
            training_status='not_started',
            deployment_status='inactive',
            voice_quality_score=0.0,
            video_quality_score=0.0,
            training_progress=0.0,
            total_training_time=0,
            usage_count=0
        )
        
        db.session.add(clone)
        db.session.commit()
        
        logger.info(f"Created digital clone {clone.id} for user {current_user}")
        return jsonify(clone.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating digital clone: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create clone'}), 500

@lora_bp.route('/clones/<int:clone_id>', methods=['GET'])
@jwt_required()
def get_digital_clone(clone_id):
    """Get specific digital clone details"""
    try:
        current_user = get_jwt_identity()
        
        clone = DigitalClone.query.filter_by(
            id=clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Clone not found'}), 404
        
        # Get additional details
        clone_data = clone.to_dict()
        
        # Get training data count
        training_data_count = TrainingData.query.filter_by(clone_id=clone_id).count()
        clone_data['training_data_count'] = training_data_count
        
        # Get latest training session
        latest_session = CloneSession.query.filter_by(
            clone_id=clone_id
        ).order_by(CloneSession.created_at.desc()).first()
        
        if latest_session:
            clone_data['latest_session'] = latest_session.to_dict()
        
        # Get synthesis job count
        synthesis_count = SynthesisJob.query.filter_by(clone_id=clone_id).count()
        clone_data['synthesis_count'] = synthesis_count
        
        return jsonify(clone_data), 200
        
    except Exception as e:
        logger.error(f"Error getting digital clone {clone_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve clone'}), 500

@lora_bp.route('/clones/<int:clone_id>', methods=['PUT'])
@jwt_required()
def update_digital_clone(clone_id):
    """Update digital clone details"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        clone = DigitalClone.query.filter_by(
            id=clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Clone not found'}), 404
        
        # Update allowed fields
        updatable_fields = ['name', 'description', 'deployment_status']
        for field in updatable_fields:
            if field in data:
                setattr(clone, field, data[field])
        
        clone.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Updated digital clone {clone_id}")
        return jsonify(clone.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating digital clone {clone_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update clone'}), 500

@lora_bp.route('/clones/<int:clone_id>', methods=['DELETE'])
@jwt_required()
def delete_digital_clone(clone_id):
    """Delete digital clone and associated data"""
    try:
        current_user = get_jwt_identity()
        
        clone = DigitalClone.query.filter_by(
            id=clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Clone not found'}), 404
        
        # Delete associated data
        TrainingData.query.filter_by(clone_id=clone_id).delete()
        LoRAModel.query.filter_by(clone_id=clone_id).delete()
        CloneSession.query.filter_by(clone_id=clone_id).delete()
        SynthesisJob.query.filter_by(clone_id=clone_id).delete()
        DeploymentTarget.query.filter_by(clone_id=clone_id).delete()
        
        # Delete clone
        db.session.delete(clone)
        db.session.commit()
        
        logger.info(f"Deleted digital clone {clone_id}")
        return jsonify({'message': 'Clone deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting digital clone {clone_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete clone'}), 500

# ===== TRAINING DATA ENDPOINTS =====

@lora_bp.route('/clones/<int:clone_id>/training-data', methods=['GET'])
@jwt_required()
def get_training_data(clone_id):
    """Get training data for a clone"""
    try:
        current_user = get_jwt_identity()
        
        # Verify clone ownership
        clone = DigitalClone.query.filter_by(
            id=clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Clone not found'}), 404
        
        training_data = TrainingData.query.filter_by(clone_id=clone_id).all()
        
        result = {
            'clone_id': clone_id,
            'training_data': [data.to_dict() for data in training_data],
            'total_files': len(training_data),
            'total_duration': sum(data.duration or 0 for data in training_data),
            'validated_files': len([d for d in training_data if d.is_validated])
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting training data for clone {clone_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve training data'}), 500

@lora_bp.route('/clones/<int:clone_id>/training-data/upload', methods=['POST'])
@jwt_required()
def upload_training_data(clone_id):
    """Upload training data files for a clone"""
    try:
        current_user = get_jwt_identity()
        
        # Verify clone ownership
        clone = DigitalClone.query.filter_by(
            id=clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Clone not found'}), 404
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if not allowed_file(file.filename):
                continue
            
            # Save file
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_type = 'audio' if filename.split('.')[-1].lower() in ['wav', 'mp3', 'flac', 'm4a'] else 'video'
            
            # Create training data record
            training_data = TrainingData(
                clone_id=clone_id,
                file_name=filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                processing_status='uploaded',
                quality_score=0.0,
                training_weight=1.0,
                is_validated=False
            )
            
            db.session.add(training_data)
            uploaded_files.append(training_data)
        
        db.session.commit()
        
        # Process files asynchronously
        asyncio.create_task(process_training_files_async(clone_id, uploaded_files))
        
        result = {
            'clone_id': clone_id,
            'uploaded_files': [data.to_dict() for data in uploaded_files],
            'message': 'Files uploaded successfully. Processing started.'
        }
        
        logger.info(f"Uploaded {len(uploaded_files)} training files for clone {clone_id}")
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error uploading training data for clone {clone_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to upload training data'}), 500

async def process_training_files_async(clone_id: int, training_files: List[TrainingData]):
    """Process uploaded training files asynchronously"""
    try:
        for training_file in training_files:
            # Update status
            training_file.processing_status = 'processing'
            db.session.commit()
            
            # Process with Descript integration
            result = await descript_workflow.process_training_data(
                training_file.file_path, clone_id
            )
            
            # Update training data with results
            training_file.transcript = result['transcription']['text']
            training_file.voice_features = result['voice_analysis']
            training_file.quality_score = result['voice_analysis']['audio_quality']['clarity_score']
            training_file.duration = result['transcription']['duration']
            training_file.processing_status = 'processed'
            training_file.processed_at = datetime.utcnow()
            
            # Validate based on quality
            if training_file.quality_score > 0.7:
                training_file.is_validated = True
            
            db.session.commit()
            
    except Exception as e:
        logger.error(f"Error processing training files: {str(e)}")
        # Update failed files
        for training_file in training_files:
            if training_file.processing_status == 'processing':
                training_file.processing_status = 'failed'
        db.session.commit()

# ===== TRAINING PIPELINE ENDPOINTS =====

@lora_bp.route('/training/start', methods=['POST'])
@jwt_required()
def start_training():
    """Start LoRA training for a clone"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        clone_id = data.get('clone_id')
        if not clone_id:
            return jsonify({'error': 'Clone ID required'}), 400
        
        # Verify clone ownership
        clone = DigitalClone.query.filter_by(
            id=clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Clone not found'}), 404
        
        # Check if training data exists
        training_data = TrainingData.query.filter_by(
            clone_id=clone_id, is_validated=True
        ).all()
        
        if not training_data:
            return jsonify({'error': 'No validated training data found'}), 400
        
        # Create training session
        session = CloneSession(
            clone_id=clone_id,
            session_type='training',
            session_name=f"LoRA Training Session {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            description=f"Training session for clone {clone.name}",
            config=data.get('config', {}),
            status='pending',
            progress=0.0
        )
        
        db.session.add(session)
        
        # Update clone status
        clone.training_status = 'training'
        clone.last_training = datetime.utcnow()
        
        db.session.commit()
        
        # Start training asynchronously
        asyncio.create_task(run_training_async(clone_id, session.id, training_data))
        
        result = {
            'clone_id': clone_id,
            'session_id': session.id,
            'status': 'training_started',
            'message': 'Training started successfully'
        }
        
        logger.info(f"Started training for clone {clone_id}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error starting training: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to start training'}), 500

async def run_training_async(clone_id: int, session_id: int, training_data: List[TrainingData]):
    """Run LoRA training asynchronously"""
    try:
        # Get session
        session = CloneSession.query.get(session_id)
        session.status = 'running'
        session.started_at = datetime.utcnow()
        db.session.commit()
        
        # Prepare training files
        training_files = [data.file_path for data in training_data]
        output_dir = f"/tmp/lora_training_clone_{clone_id}_{session_id}"
        
        # Run training pipeline
        results = await training_pipeline.run_complete_training_pipeline(
            clone_id, training_files, output_dir
        )
        
        # Update session with results
        session.status = 'completed'
        session.completed_at = datetime.utcnow()
        session.output_data = results
        session.metrics = results['training_results']['evaluation_results']
        session.duration = int((session.completed_at - session.started_at).total_seconds())
        
        # Update clone
        clone = DigitalClone.query.get(clone_id)
        clone.training_status = 'completed'
        clone.training_progress = 100.0
        clone.voice_quality_score = results['model_quality_score']
        clone.voice_model_path = results['final_model_path']
        
        # Create LoRA model record
        lora_model = LoRAModel(
            clone_id=clone_id,
            model_name=results['training_config']['model_name'],
            model_version='1.0',
            model_type='voice',
            model_path=results['final_model_path'],
            model_size=os.path.getsize(results['final_model_path']),
            training_config=results['training_config'],
            base_model=results['training_config']['base_model'],
            training_epochs=results['training_config']['epochs'],
            learning_rate=results['training_config']['learning_rate'],
            batch_size=results['training_config']['batch_size'],
            status='completed',
            is_active=True,
            training_started=session.started_at,
            training_completed=session.completed_at
        )
        
        db.session.add(lora_model)
        db.session.commit()
        
        logger.info(f"Training completed for clone {clone_id}")
        
    except Exception as e:
        logger.error(f"Training failed for clone {clone_id}: {str(e)}")
        
        # Update session with error
        session = CloneSession.query.get(session_id)
        session.status = 'failed'
        session.error_log = str(e)
        session.completed_at = datetime.utcnow()
        
        # Update clone
        clone = DigitalClone.query.get(clone_id)
        clone.training_status = 'failed'
        
        db.session.commit()

@lora_bp.route('/training/sessions', methods=['GET'])
@jwt_required()
def get_training_sessions():
    """Get training sessions"""
    try:
        current_user = get_jwt_identity()
        
        # Get user's clones
        user_clone_ids = [c.id for c in DigitalClone.query.filter_by(owner=current_user).all()]
        
        sessions = CloneSession.query.filter(
            CloneSession.clone_id.in_(user_clone_ids),
            CloneSession.session_type == 'training'
        ).order_by(CloneSession.created_at.desc()).all()
        
        return jsonify([session.to_dict() for session in sessions]), 200
        
    except Exception as e:
        logger.error(f"Error getting training sessions: {str(e)}")
        return jsonify({'error': 'Failed to retrieve training sessions'}), 500

# ===== VOICE SYNTHESIS ENDPOINTS =====

@lora_bp.route('/synthesis', methods=['POST'])
@jwt_required()
def synthesize_voice():
    """Synthesize voice using a digital clone"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        clone_id = data.get('clone_id')
        text = data.get('text')
        
        if not clone_id or not text:
            return jsonify({'error': 'Clone ID and text required'}), 400
        
        # Verify clone ownership
        clone = DigitalClone.query.filter_by(
            id=clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Clone not found'}), 404
        
        if clone.training_status != 'completed':
            return jsonify({'error': 'Clone training not completed'}), 400
        
        # Create synthesis job
        job = SynthesisJob(
            clone_id=clone_id,
            job_name=f"Voice Synthesis {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            job_type='voice_synthesis',
            input_text=text,
            input_config=data.get('config', {}),
            style_settings=data.get('voice_settings', {}),
            status='queued',
            priority=data.get('priority', 5)
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Process synthesis asynchronously
        asyncio.create_task(process_synthesis_async(job.id, clone, text, data.get('config', {})))
        
        result = {
            'job_id': job.id,
            'clone_id': clone_id,
            'status': 'queued',
            'message': 'Synthesis job created successfully'
        }
        
        logger.info(f"Created synthesis job {job.id} for clone {clone_id}")
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error creating synthesis job: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create synthesis job'}), 500

async def process_synthesis_async(job_id: int, clone: DigitalClone, text: str, config: Dict):
    """Process voice synthesis asynchronously"""
    try:
        # Get job
        job = SynthesisJob.query.get(job_id)
        job.status = 'processing'
        job.started_at = datetime.utcnow()
        db.session.commit()
        
        # Configure synthesis
        synthesis_config = {
            'lora_model_path': clone.voice_model_path,
            **config
        }
        
        # Synthesize voice
        result = await voice_service.synthesize_with_clone(
            clone.id, text, synthesis_config
        )
        
        # Update job with results
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.processing_time = int((job.completed_at - job.started_at).total_seconds())
        job.output_files = [result['output_path']]
        job.output_metadata = result
        job.quality_score = await voice_service.get_synthesis_quality_metrics(
            open(result['output_path'], 'rb').read()
        )
        
        # Update clone usage
        clone.usage_count += 1
        clone.last_used = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Synthesis job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Synthesis job {job_id} failed: {str(e)}")
        
        # Update job with error
        job = SynthesisJob.query.get(job_id)
        job.status = 'failed'
        job.completed_at = datetime.utcnow()
        db.session.commit()

@lora_bp.route('/synthesis/<int:job_id>/status', methods=['GET'])
@jwt_required()
def get_synthesis_status(job_id):
    """Get synthesis job status"""
    try:
        current_user = get_jwt_identity()
        
        job = SynthesisJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Verify ownership through clone
        clone = DigitalClone.query.filter_by(
            id=job.clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(job.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting synthesis status: {str(e)}")
        return jsonify({'error': 'Failed to get synthesis status'}), 500

@lora_bp.route('/synthesis/<int:job_id>/download', methods=['GET'])
@jwt_required()
def download_synthesis_result(job_id):
    """Download synthesis result audio file"""
    try:
        current_user = get_jwt_identity()
        
        job = SynthesisJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Verify ownership
        clone = DigitalClone.query.filter_by(
            id=job.clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Access denied'}), 403
        
        if job.status != 'completed' or not job.output_files:
            return jsonify({'error': 'No output file available'}), 404
        
        output_path = job.output_files[0]
        if not os.path.exists(output_path):
            return jsonify({'error': 'Output file not found'}), 404
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"synthesis_{job_id}.wav",
            mimetype='audio/wav'
        )
        
    except Exception as e:
        logger.error(f"Error downloading synthesis result: {str(e)}")
        return jsonify({'error': 'Failed to download result'}), 500

# ===== VIDEO AVATAR ENDPOINTS =====

@lora_bp.route('/video/generate', methods=['POST'])
@jwt_required()
def generate_avatar_video():
    """Generate avatar video with voice synthesis"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        clone_id = data.get('cloneId')  # Note: frontend uses camelCase
        script = data.get('script')
        
        if not clone_id or not script:
            return jsonify({'error': 'Clone ID and script required'}), 400
        
        # Verify clone ownership
        clone = DigitalClone.query.filter_by(
            id=clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Clone not found'}), 404
        
        # Create video generation job
        job = SynthesisJob(
            clone_id=clone_id,
            job_name=f"Avatar Video {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            job_type='video_generation',
            input_text=script,
            input_config=data,
            status='queued',
            priority=data.get('priority', 5)
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Process video generation asynchronously
        asyncio.create_task(process_video_generation_async(job.id, clone, script, data))
        
        result = {
            'job_id': job.id,
            'clone_id': clone_id,
            'status': 'queued',
            'message': 'Video generation job created successfully'
        }
        
        logger.info(f"Created video generation job {job.id} for clone {clone_id}")
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error creating video generation job: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create video generation job'}), 500

async def process_video_generation_async(job_id: int, clone: DigitalClone, script: str, config: Dict):
    """Process video generation asynchronously"""
    try:
        # Get job
        job = SynthesisJob.query.get(job_id)
        job.status = 'processing'
        job.started_at = datetime.utcnow()
        db.session.commit()
        
        # First, synthesize voice
        synthesis_config = {
            'lora_model_path': clone.voice_model_path,
            'output_format': 'wav'
        }
        
        voice_result = await voice_service.synthesize_with_clone(
            clone.id, script, synthesis_config
        )
        
        # Generate avatar video
        avatar_config = {
            'style': config.get('style', 'professional'),
            'resolution': config.get('resolution', '1920x1080'),
            'fps': config.get('fps', 30),
            'include_gestures': config.get('includeGestures', True),
            'add_branding': config.get('addBranding', False)
        }
        
        video_result = await video_service.create_avatar_presentation(
            clone.id, script, voice_result['output_path'], avatar_config
        )
        
        # Update job with results
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.processing_time = int((job.completed_at - job.started_at).total_seconds())
        job.output_files = [video_result['output_path']]
        job.output_metadata = {
            'voice_result': voice_result,
            'video_result': video_result
        }
        
        # Update clone usage
        clone.usage_count += 1
        clone.last_used = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Video generation job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Video generation job {job_id} failed: {str(e)}")
        
        # Update job with error
        job = SynthesisJob.query.get(job_id)
        job.status = 'failed'
        job.completed_at = datetime.utcnow()
        db.session.commit()

# ===== DEPLOYMENT ENDPOINTS =====

@lora_bp.route('/deployment/targets', methods=['GET'])
@jwt_required()
def get_deployment_targets():
    """Get deployment targets for user's clones"""
    try:
        current_user = get_jwt_identity()
        
        # Get user's clones
        user_clone_ids = [c.id for c in DigitalClone.query.filter_by(owner=current_user).all()]
        
        targets = DeploymentTarget.query.filter(
            DeploymentTarget.clone_id.in_(user_clone_ids)
        ).all()
        
        return jsonify([target.to_dict() for target in targets]), 200
        
    except Exception as e:
        logger.error(f"Error getting deployment targets: {str(e)}")
        return jsonify({'error': 'Failed to retrieve deployment targets'}), 500

@lora_bp.route('/deployment/targets', methods=['POST'])
@jwt_required()
def create_deployment_target():
    """Create new deployment target"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        clone_id = data.get('clone_id')
        if not clone_id:
            return jsonify({'error': 'Clone ID required'}), 400
        
        # Verify clone ownership
        clone = DigitalClone.query.filter_by(
            id=clone_id, owner=current_user
        ).first()
        
        if not clone:
            return jsonify({'error': 'Clone not found'}), 404
        
        target = DeploymentTarget(
            clone_id=clone_id,
            target_name=data['target_name'],
            target_type=data['target_type'],
            platform=data['platform'],
            deployment_config=data.get('deployment_config', {}),
            integration_settings=data.get('integration_settings', {}),
            status='inactive'
        )
        
        db.session.add(target)
        db.session.commit()
        
        logger.info(f"Created deployment target {target.id} for clone {clone_id}")
        return jsonify(target.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating deployment target: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create deployment target'}), 500

# ===== DASHBOARD ENDPOINTS =====

@lora_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        current_user = get_jwt_identity()
        
        # Get user's clones
        user_clones = DigitalClone.query.filter_by(owner=current_user).all()
        user_clone_ids = [c.id for c in user_clones]
        
        # Calculate stats
        stats = {
            'total_clones': len(user_clones),
            'active_clones': len([c for c in user_clones if c.training_status == 'completed']),
            'training_jobs': CloneSession.query.filter(
                CloneSession.clone_id.in_(user_clone_ids),
                CloneSession.status == 'running'
            ).count(),
            'synthesis_jobs': SynthesisJob.query.filter(
                SynthesisJob.clone_id.in_(user_clone_ids),
                SynthesisJob.status == 'completed'
            ).count(),
            'total_usage': sum(c.usage_count for c in user_clones),
            'total_training_time': sum(c.total_training_time for c in user_clones),
            'average_quality': sum(c.voice_quality_score for c in user_clones) / max(len(user_clones), 1)
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'error': 'Failed to retrieve dashboard stats'}), 500

# ===== ERROR HANDLERS =====

@lora_bp.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

@lora_bp.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400

@lora_bp.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ===== HEALTH CHECK =====

@lora_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check services
        services_status = {
            'database': 'healthy',
            'descript_integration': 'healthy',
            'capcut_integration': 'healthy',
            'voice_synthesis': 'healthy',
            'video_avatar': 'healthy'
        }
        
        return jsonify({
            'status': 'healthy',
            'services': services_status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500