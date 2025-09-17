"""
Airtable Sync Scheduler for Dr. Dédé's AI Empire Platform
Automated sync workflows with scheduling and error handling
"""

import os
import asyncio
import schedule
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MimeMultipart

from airtable_sync_service import (
    AirtableSyncService, SyncConfiguration, SyncDirection, ConflictStrategy,
    create_sync_service
)
from airtable_base_manager import create_base_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncJobStatus(Enum):
    """Sync job status options"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SyncJob:
    """Definition for a scheduled sync job"""
    id: str
    name: str
    description: str
    base_id: str
    tables: List[str]
    schedule_type: str  # 'interval', 'cron', 'once'
    schedule_config: Dict[str, Any]
    sync_config: SyncConfiguration
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: SyncJobStatus = SyncJobStatus.PENDING
    error_count: int = 0
    success_count: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class SyncJobResult:
    """Result of a sync job execution"""
    job_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: SyncJobStatus
    tables_synced: Dict[str, Any]
    total_records: int
    success_records: int
    failed_records: int
    conflicts_detected: int
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    
    def __post_init__(self):
        if self.end_time and self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()


class AirtableSyncScheduler:
    """
    Scheduler for automated Airtable synchronization workflows
    """
    
    def __init__(self):
        self.sync_jobs: Dict[str, SyncJob] = {}
        self.job_results: List[SyncJobResult] = []
        self.sync_services: Dict[str, AirtableSyncService] = {}
        self.base_manager = create_base_manager()
        
        # Scheduler configuration
        self.scheduler_running = False
        self.scheduler_thread = None
        self.max_concurrent_jobs = 3
        self.job_timeout_minutes = 60
        self.max_error_count = 5
        self.cleanup_retention_days = 30
        
        # Notification configuration
        self.notification_config = {
            'email_enabled': False,
            'email_smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'email_smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email_username': os.getenv('EMAIL_USERNAME'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            'email_recipients': os.getenv('NOTIFICATION_EMAILS', '').split(','),
            'webhook_enabled': False,
            'webhook_url': os.getenv('SYNC_WEBHOOK_URL')
        }
        
        # Initialize scheduler
        self._initialize_scheduler()
    
    def _initialize_scheduler(self):
        """Initialize the job scheduler"""
        try:
            # Create default sync jobs if none exist
            if not self.sync_jobs:
                self._create_default_jobs()
            
            logger.info("Sync scheduler initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing scheduler: {e}")
    
    def _create_default_jobs(self):
        """Create default sync jobs for common scenarios"""
        
        # Revenue tracking sync (every 30 minutes during business hours)
        revenue_job = SyncJob(
            id="revenue_sync_30min",
            name="Revenue Streams Sync",
            description="Sync revenue streams data every 30 minutes during business hours",
            base_id=os.getenv('AIRTABLE_CRM_BASE_ID', ''),
            tables=['revenue_streams', 'kpi_metrics'],
            schedule_type='interval',
            schedule_config={
                'interval_minutes': 30,
                'business_hours_only': True,
                'start_hour': 8,
                'end_hour': 18,
                'weekdays_only': True
            },
            sync_config=SyncConfiguration(
                enabled_tables=['revenue_streams', 'kpi_metrics'],
                sync_direction=SyncDirection.BIDIRECTIONAL,
                conflict_strategy=ConflictStrategy.TIMESTAMP_BASED,
                batch_size=10
            )
        )
        
        # Executive opportunities sync (every 2 hours)
        exec_job = SyncJob(
            id="exec_opportunities_2h",
            name="Executive Opportunities Sync",
            description="Sync executive opportunities and AI agent data every 2 hours",
            base_id=os.getenv('AIRTABLE_CRM_BASE_ID', ''),
            tables=['executive_opportunities', 'ai_agents'],
            schedule_type='interval',
            schedule_config={
                'interval_minutes': 120
            },
            sync_config=SyncConfiguration(
                enabled_tables=['executive_opportunities', 'ai_agents'],
                sync_direction=SyncDirection.BIDIRECTIONAL,
                conflict_strategy=ConflictStrategy.SMART_MERGE,
                batch_size=15
            )
        )
        
        # Healthcare sync (daily at 6 AM)
        healthcare_job = SyncJob(
            id="healthcare_daily",
            name="Healthcare Daily Sync",
            description="Daily sync of healthcare providers and appointments",
            base_id=os.getenv('AIRTABLE_CRM_BASE_ID', ''),
            tables=['healthcare_providers', 'healthcare_appointments'],
            schedule_type='cron',
            schedule_config={
                'hour': 6,
                'minute': 0
            },
            sync_config=SyncConfiguration(
                enabled_tables=['healthcare_providers', 'healthcare_appointments'],
                sync_direction=SyncDirection.BIDIRECTIONAL,
                conflict_strategy=ConflictStrategy.LOCAL_WINS,
                batch_size=20
            )
        )
        
        # Full sync (weekly on Sunday at 2 AM)
        full_sync_job = SyncJob(
            id="full_sync_weekly",
            name="Weekly Full Sync",
            description="Complete synchronization of all CRM data",
            base_id=os.getenv('AIRTABLE_CRM_BASE_ID', ''),
            tables=[
                'revenue_streams', 'ai_agents', 'executive_opportunities',
                'healthcare_providers', 'healthcare_appointments', 'retreat_events'
            ],
            schedule_type='cron',
            schedule_config={
                'day_of_week': 'sunday',
                'hour': 2,
                'minute': 0
            },
            sync_config=SyncConfiguration(
                enabled_tables=[
                    'revenue_streams', 'ai_agents', 'executive_opportunities',
                    'healthcare_providers', 'healthcare_appointments', 'retreat_events'
                ],
                sync_direction=SyncDirection.BIDIRECTIONAL,
                conflict_strategy=ConflictStrategy.TIMESTAMP_BASED,
                batch_size=25,
                backup_before_sync=True
            )
        )
        
        # Add jobs to scheduler
        default_jobs = [revenue_job, exec_job, healthcare_job, full_sync_job]
        for job in default_jobs:
            self.add_sync_job(job)
        
        logger.info(f"Created {len(default_jobs)} default sync jobs")
    
    def add_sync_job(self, job: SyncJob) -> bool:
        """Add a new sync job to the scheduler"""
        try:
            # Validate job configuration
            validation_result = self._validate_job(job)
            if not validation_result['valid']:
                logger.error(f"Invalid job configuration: {validation_result['errors']}")
                return False
            
            # Update timestamp
            job.updated_at = datetime.utcnow()
            
            # Add to jobs dictionary
            self.sync_jobs[job.id] = job
            
            # Schedule the job
            self._schedule_job(job)
            
            logger.info(f"Added sync job: {job.name} ({job.id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding sync job {job.id}: {e}")
            return False
    
    def _validate_job(self, job: SyncJob) -> Dict[str, Any]:
        """Validate job configuration"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required fields validation
        if not job.id:
            validation['errors'].append("Job ID is required")
        if not job.name:
            validation['errors'].append("Job name is required")
        if not job.base_id:
            validation['errors'].append("Base ID is required")
        if not job.tables:
            validation['errors'].append("At least one table must be specified")
        
        # Schedule validation
        if job.schedule_type == 'interval':
            if 'interval_minutes' not in job.schedule_config:
                validation['errors'].append("Interval minutes must be specified for interval jobs")
            elif job.schedule_config['interval_minutes'] < 5:
                validation['warnings'].append("Interval less than 5 minutes may hit rate limits")
        
        elif job.schedule_type == 'cron':
            required_fields = ['hour', 'minute']
            for field in required_fields:
                if field not in job.schedule_config:
                    validation['errors'].append(f"Cron job missing required field: {field}")
        
        # Base validation
        try:
            if job.base_id:
                base_validation = self.base_manager.validate_base_configuration(job.base_id)
                if not base_validation['is_valid']:
                    validation['warnings'].append(f"Base configuration issues: {base_validation['issues']}")
        except Exception as e:
            validation['warnings'].append(f"Could not validate base: {str(e)}")
        
        validation['valid'] = len(validation['errors']) == 0
        return validation
    
    def _schedule_job(self, job: SyncJob):
        """Schedule a job with the appropriate timing"""
        if not job.enabled:
            return
        
        if job.schedule_type == 'interval':
            interval_minutes = job.schedule_config['interval_minutes']
            
            # Handle business hours restriction
            if job.schedule_config.get('business_hours_only'):
                def business_hours_wrapper():
                    current_hour = datetime.now().hour
                    current_weekday = datetime.now().weekday()
                    
                    start_hour = job.schedule_config.get('start_hour', 8)
                    end_hour = job.schedule_config.get('end_hour', 18)
                    weekdays_only = job.schedule_config.get('weekdays_only', False)
                    
                    # Check business hours
                    if current_hour < start_hour or current_hour >= end_hour:
                        logger.debug(f"Skipping job {job.id} - outside business hours")
                        return
                    
                    # Check weekdays
                    if weekdays_only and current_weekday >= 5:  # 0-6, where 5-6 are weekend
                        logger.debug(f"Skipping job {job.id} - weekend")
                        return
                    
                    self._execute_job(job.id)
                
                schedule.every(interval_minutes).minutes.do(business_hours_wrapper)
            else:
                schedule.every(interval_minutes).minutes.do(lambda: self._execute_job(job.id))
        
        elif job.schedule_type == 'cron':
            hour = job.schedule_config['hour']
            minute = job.schedule_config.get('minute', 0)
            
            if 'day_of_week' in job.schedule_config:
                day = job.schedule_config['day_of_week']
                schedule_obj = getattr(schedule.every(), day)
                schedule_obj.at(f"{hour:02d}:{minute:02d}").do(lambda: self._execute_job(job.id))
            else:
                schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(lambda: self._execute_job(job.id))
        
        elif job.schedule_type == 'once':
            # Execute immediately for one-time jobs
            self._execute_job(job.id)
        
        # Update next run time
        job.next_run = self._calculate_next_run(job)
    
    def _calculate_next_run(self, job: SyncJob) -> Optional[datetime]:
        """Calculate the next run time for a job"""
        try:
            if job.schedule_type == 'interval':
                interval_minutes = job.schedule_config['interval_minutes']
                next_run = datetime.utcnow() + timedelta(minutes=interval_minutes)
                
                # Adjust for business hours if needed
                if job.schedule_config.get('business_hours_only'):
                    start_hour = job.schedule_config.get('start_hour', 8)
                    end_hour = job.schedule_config.get('end_hour', 18)
                    
                    while (next_run.hour < start_hour or next_run.hour >= end_hour or
                           (job.schedule_config.get('weekdays_only') and next_run.weekday() >= 5)):
                        next_run += timedelta(minutes=interval_minutes)
                
                return next_run
            
            elif job.schedule_type == 'cron':
                # Calculate next cron run time
                hour = job.schedule_config['hour']
                minute = job.schedule_config.get('minute', 0)
                
                next_run = datetime.utcnow().replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if next_run <= datetime.utcnow():
                    if 'day_of_week' in job.schedule_config:
                        # Weekly schedule
                        next_run += timedelta(days=7)
                    else:
                        # Daily schedule
                        next_run += timedelta(days=1)
                
                return next_run
            
            elif job.schedule_type == 'once':
                return None  # One-time jobs don't have a next run
                
        except Exception as e:
            logger.error(f"Error calculating next run for job {job.id}: {e}")
            return None
    
    def _execute_job(self, job_id: str):
        """Execute a sync job"""
        if job_id not in self.sync_jobs:
            logger.error(f"Job {job_id} not found")
            return
        
        job = self.sync_jobs[job_id]
        
        # Check if job is already running
        if job.status == SyncJobStatus.RUNNING:
            logger.warning(f"Job {job_id} is already running, skipping")
            return
        
        # Start job execution
        job.status = SyncJobStatus.RUNNING
        job.last_run = datetime.utcnow()
        
        result = SyncJobResult(
            job_id=job_id,
            start_time=datetime.utcnow(),
            end_time=None,
            status=SyncJobStatus.RUNNING,
            tables_synced={},
            total_records=0,
            success_records=0,
            failed_records=0,
            conflicts_detected=0
        )
        
        try:
            logger.info(f"Starting sync job: {job.name} ({job_id})")
            
            # Get or create sync service for this base
            sync_service = self._get_sync_service(job.base_id, job.sync_config)
            
            # Execute sync for specified tables
            for table in job.tables:
                if table in job.sync_config.enabled_tables:
                    table_results = sync_service.sync_bidirectional(table)
                    result.tables_synced[table] = table_results
                    
                    # Count results
                    for direction_results in table_results.values():
                        for sync_result in direction_results:
                            result.total_records += 1
                            if sync_result.success:
                                result.success_records += 1
                            else:
                                result.failed_records += 1
            
            # Get conflict count
            result.conflicts_detected = len([
                c for c in sync_service.conflict_log 
                if c.detected_at >= result.start_time
            ])
            
            # Mark job as completed
            job.status = SyncJobStatus.COMPLETED
            job.success_count += 1
            job.error_count = 0  # Reset error count on success
            result.status = SyncJobStatus.COMPLETED
            
            logger.info(f"Sync job completed: {job.name} - {result.success_records} successful, {result.failed_records} failed")
            
        except Exception as e:
            # Mark job as failed
            job.status = SyncJobStatus.FAILED
            job.error_count += 1
            result.status = SyncJobStatus.FAILED
            result.error_message = str(e)
            
            logger.error(f"Sync job failed: {job.name} - {str(e)}")
            
            # Disable job if too many failures
            if job.error_count >= self.max_error_count:
                job.enabled = False
                logger.warning(f"Disabled job {job_id} due to too many failures ({job.error_count})")
        
        finally:
            # Finalize result
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            
            # Store result
            self.job_results.append(result)
            
            # Update next run time
            job.next_run = self._calculate_next_run(job)
            job.updated_at = datetime.utcnow()
            
            # Send notifications if configured
            self._send_notifications(job, result)
            
            # Cleanup old results
            self._cleanup_old_results()
    
    def _get_sync_service(self, base_id: str, sync_config: SyncConfiguration) -> AirtableSyncService:
        """Get or create a sync service for a base"""
        if base_id not in self.sync_services:
            self.sync_services[base_id] = create_sync_service(base_id, sync_config)
        return self.sync_services[base_id]
    
    def _send_notifications(self, job: SyncJob, result: SyncJobResult):
        """Send notifications about job completion"""
        try:
            # Send email notifications
            if (self.notification_config['email_enabled'] and 
                self.notification_config['email_recipients']):
                self._send_email_notification(job, result)
            
            # Send webhook notifications
            if (self.notification_config['webhook_enabled'] and 
                self.notification_config['webhook_url']):
                self._send_webhook_notification(job, result)
                
        except Exception as e:
            logger.error(f"Error sending notifications for job {job.id}: {e}")
    
    def _send_email_notification(self, job: SyncJob, result: SyncJobResult):
        """Send email notification about job completion"""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.notification_config['email_username']
            msg['To'] = ', '.join(self.notification_config['email_recipients'])
            
            if result.status == SyncJobStatus.COMPLETED:
                msg['Subject'] = f"✅ Airtable Sync Completed: {job.name}"
                status_emoji = "✅"
                status_color = "green"
            else:
                msg['Subject'] = f"❌ Airtable Sync Failed: {job.name}"
                status_emoji = "❌"
                status_color = "red"
            
            # Create HTML body
            html_body = f"""
            <html>
            <body>
                <h2>{status_emoji} Sync Job: {job.name}</h2>
                <p><strong>Status:</strong> <span style="color: {status_color};">{result.status.value}</span></p>
                <p><strong>Duration:</strong> {result.duration_seconds:.1f} seconds</p>
                <p><strong>Records Processed:</strong> {result.total_records}</p>
                <p><strong>Successful:</strong> {result.success_records}</p>
                <p><strong>Failed:</strong> {result.failed_records}</p>
                <p><strong>Conflicts:</strong> {result.conflicts_detected}</p>
                
                <h3>Tables Synced:</h3>
                <ul>
                {''.join([f'<li>{table}</li>' for table in result.tables_synced.keys()])}
                </ul>
                
                {f'<p><strong>Error:</strong> {result.error_message}</p>' if result.error_message else ''}
                
                <p><em>Job executed at: {result.start_time.isoformat()}</em></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            server = smtplib.SMTP(
                self.notification_config['email_smtp_server'],
                self.notification_config['email_smtp_port']
            )
            server.starttls()
            server.login(
                self.notification_config['email_username'],
                self.notification_config['email_password']
            )
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent for job {job.id}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def _send_webhook_notification(self, job: SyncJob, result: SyncJobResult):
        """Send webhook notification about job completion"""
        try:
            import requests
            
            webhook_data = {
                'job_id': job.id,
                'job_name': job.name,
                'status': result.status.value,
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat() if result.end_time else None,
                'duration_seconds': result.duration_seconds,
                'total_records': result.total_records,
                'success_records': result.success_records,
                'failed_records': result.failed_records,
                'conflicts_detected': result.conflicts_detected,
                'tables_synced': list(result.tables_synced.keys()),
                'error_message': result.error_message
            }
            
            response = requests.post(
                self.notification_config['webhook_url'],
                json=webhook_data,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Webhook notification sent for job {job.id}")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    def _cleanup_old_results(self):
        """Clean up old job results"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.cleanup_retention_days)
            
            # Remove old results
            self.job_results = [
                result for result in self.job_results
                if result.start_time > cutoff_date
            ]
            
        except Exception as e:
            logger.error(f"Error cleaning up old results: {e}")
    
    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.scheduler_running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler_running = True
        
        def run_scheduler():
            logger.info("Airtable sync scheduler started")
            while self.scheduler_running:
                try:
                    schedule.run_pending()
                    time.sleep(10)  # Check every 10 seconds
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}")
                    time.sleep(60)  # Wait a bit longer on error
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.scheduler_running:
            logger.warning("Scheduler is not running")
            return
        
        self.scheduler_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Airtable sync scheduler stopped")
    
    def get_job_status(self, job_id: str = None) -> Dict[str, Any]:
        """Get status of specific job or all jobs"""
        if job_id:
            if job_id not in self.sync_jobs:
                return {'error': f'Job {job_id} not found'}
            
            job = self.sync_jobs[job_id]
            recent_results = [
                r for r in self.job_results 
                if r.job_id == job_id
            ][-5:]  # Last 5 results
            
            return {
                'job': asdict(job),
                'recent_results': [asdict(r) for r in recent_results]
            }
        else:
            return {
                'scheduler_running': self.scheduler_running,
                'total_jobs': len(self.sync_jobs),
                'enabled_jobs': len([j for j in self.sync_jobs.values() if j.enabled]),
                'jobs': {job_id: asdict(job) for job_id, job in self.sync_jobs.items()},
                'recent_results': [asdict(r) for r in self.job_results[-10:]]
            }
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing job"""
        if job_id not in self.sync_jobs:
            logger.error(f"Job {job_id} not found")
            return False
        
        try:
            job = self.sync_jobs[job_id]
            
            # Update allowed fields
            allowed_fields = ['name', 'description', 'enabled', 'schedule_config', 'sync_config']
            for field, value in updates.items():
                if field in allowed_fields and hasattr(job, field):
                    setattr(job, field, value)
            
            job.updated_at = datetime.utcnow()
            
            # Re-schedule if needed
            if job.enabled:
                self._schedule_job(job)
            
            logger.info(f"Updated job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler"""
        if job_id not in self.sync_jobs:
            logger.error(f"Job {job_id} not found")
            return False
        
        try:
            # Remove from schedule
            schedule.clear(job_id)
            
            # Remove from jobs
            del self.sync_jobs[job_id]
            
            logger.info(f"Removed job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return False


# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> AirtableSyncScheduler:
    """Get the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AirtableSyncScheduler()
    return _scheduler_instance


# Example usage
if __name__ == "__main__":
    # Create and start scheduler
    scheduler = get_scheduler()
    
    # Start scheduler
    scheduler.start_scheduler()
    
    try:
        # Keep running
        while True:
            time.sleep(60)
            status = scheduler.get_job_status()
            print(f"Scheduler status: {status['enabled_jobs']} jobs enabled")
    except KeyboardInterrupt:
        scheduler.stop_scheduler()
        print("Scheduler stopped")