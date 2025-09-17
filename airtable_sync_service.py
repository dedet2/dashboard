"""
Airtable CRM Sync Service for Dr. Dédé's AI Empire Platform
Bi-directional data synchronization with conflict resolution
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from airtable_integration import (
    AirtableAPIWrapper, AirtableRecord, SyncResult, ConflictResolution,
    create_airtable_client, AirtableAPIError
)
from database import (
    db, RevenueStream, AIAgent, ExecutiveOpportunity, HealthcareProvider,
    HealthcareAppointment, RetreatEvent, KPIMetric, Milestone, EnergyTracking,
    WellnessGoal, HealthMetric
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Sync direction options"""
    PUSH_TO_AIRTABLE = "push_to_airtable"
    PULL_FROM_AIRTABLE = "pull_from_airtable"
    BIDIRECTIONAL = "bidirectional"


class ConflictStrategy(Enum):
    """Conflict resolution strategies"""
    LOCAL_WINS = "local_wins"
    AIRTABLE_WINS = "airtable_wins"
    MERGE_SMART = "merge_smart"
    MANUAL_REVIEW = "manual_review"
    TIMESTAMP_BASED = "timestamp_based"


@dataclass
class SyncConfiguration:
    """Configuration for sync operations"""
    enabled_tables: List[str]
    sync_direction: SyncDirection
    conflict_strategy: ConflictStrategy
    batch_size: int = 10
    sync_interval_minutes: int = 15
    max_retries: int = 3
    backup_before_sync: bool = True
    validate_data: bool = True
    webhook_url: Optional[str] = None
    notification_email: Optional[str] = None


@dataclass
class ChangeRecord:
    """Track changes for sync purposes"""
    table_name: str
    record_id: str
    local_id: Optional[str]
    airtable_id: Optional[str]
    operation: str  # 'create', 'update', 'delete'
    changes: Dict[str, Any]
    timestamp: datetime
    sync_status: str = 'pending'  # 'pending', 'synced', 'failed', 'conflict'
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class ConflictRecord:
    """Record conflicts that need resolution"""
    table_name: str
    local_record: Dict[str, Any]
    airtable_record: Dict[str, Any]
    conflict_fields: List[str]
    detected_at: datetime
    resolution_strategy: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class AirtableSyncService:
    """
    Comprehensive service for bi-directional Airtable synchronization
    """
    
    def __init__(self, airtable_client: AirtableAPIWrapper, base_id: str, 
                 sync_config: SyncConfiguration = None):
        self.airtable = airtable_client
        self.base_id = base_id
        self.airtable.set_base_id(base_id)
        
        # Default sync configuration
        self.config = sync_config or SyncConfiguration(
            enabled_tables=[
                'revenue_streams', 'ai_agents', 'executive_opportunities',
                'healthcare_providers', 'healthcare_appointments', 'retreat_events'
            ],
            sync_direction=SyncDirection.BIDIRECTIONAL,
            conflict_strategy=ConflictStrategy.TIMESTAMP_BASED
        )
        
        # Model mappings
        self.model_mapping = {
            'revenue_streams': RevenueStream,
            'ai_agents': AIAgent,
            'executive_opportunities': ExecutiveOpportunity,
            'healthcare_providers': HealthcareProvider,
            'healthcare_appointments': HealthcareAppointment,
            'retreat_events': RetreatEvent,
            'kpi_metrics': KPIMetric,
            'milestones': Milestone,
            'energy_tracking': EnergyTracking,
            'wellness_goals': WellnessGoal,
            'health_metrics': HealthMetric
        }
        
        # Sync tracking
        self.sync_log: List[ChangeRecord] = []
        self.conflict_log: List[ConflictRecord] = []
        self.last_sync_timestamps: Dict[str, datetime] = {}
        
        # Load sync state
        self._load_sync_state()
    
    def _load_sync_state(self):
        """Load previous sync state from persistent storage"""
        try:
            # In a production system, this would load from database
            # For now, we'll initialize with current time
            current_time = datetime.utcnow()
            for table in self.config.enabled_tables:
                self.last_sync_timestamps[table] = current_time - timedelta(hours=1)
            logger.info("Sync state initialized")
        except Exception as e:
            logger.error(f"Error loading sync state: {e}")
    
    def _save_sync_state(self):
        """Save sync state to persistent storage"""
        try:
            # In a production system, this would save to database
            logger.info("Sync state saved")
        except Exception as e:
            logger.error(f"Error saving sync state: {e}")
    
    def generate_record_hash(self, record: Dict[str, Any]) -> str:
        """Generate hash for record to detect changes"""
        # Create a normalized string representation
        normalized = json.dumps(record, sort_keys=True, default=str)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def detect_local_changes(self, table_name: str, since: datetime = None) -> List[ChangeRecord]:
        """Detect changes in local database since last sync"""
        if table_name not in self.model_mapping:
            logger.warning(f"No model mapping for table: {table_name}")
            return []
        
        model = self.model_mapping[table_name]
        since = since or self.last_sync_timestamps.get(table_name, datetime.utcnow() - timedelta(hours=1))
        
        changes = []
        
        try:
            # Find records updated since last sync
            if hasattr(model, 'updated_at'):
                updated_records = model.query.filter(model.updated_at > since).all()
            elif hasattr(model, 'last_updated'):
                updated_records = model.query.filter(model.last_updated > since).all()
            else:
                # Fallback - get all records for comparison
                updated_records = model.query.all()
            
            for record in updated_records:
                if hasattr(record, 'to_dict'):
                    record_dict = record.to_dict()
                else:
                    record_dict = {c.name: getattr(record, c.name) for c in record.__table__.columns}
                
                change = ChangeRecord(
                    table_name=table_name,
                    record_id=str(record.id),
                    local_id=str(record.id),
                    airtable_id=getattr(record, 'airtable_id', None),
                    operation='update',  # We'll determine create vs update later
                    changes=record_dict,
                    timestamp=datetime.utcnow()
                )
                changes.append(change)
            
            logger.info(f"Detected {len(changes)} local changes in {table_name}")
            return changes
            
        except Exception as e:
            logger.error(f"Error detecting local changes in {table_name}: {e}")
            return []
    
    def detect_airtable_changes(self, table_name: str, since: datetime = None) -> List[ChangeRecord]:
        """Detect changes in Airtable since last sync"""
        if table_name not in self.airtable.table_mappings:
            logger.warning(f"No Airtable table mapping for: {table_name}")
            return []
        
        airtable_table = self.airtable.table_mappings[table_name]
        since = since or self.last_sync_timestamps.get(table_name, datetime.utcnow() - timedelta(hours=1))
        
        changes = []
        
        try:
            # Build filter formula for records modified since last sync
            filter_formula = f"IS_AFTER({{Last Modified}}, '{since.isoformat()}')"
            
            # Get updated records from Airtable
            airtable_records = self.airtable.list_records(
                table_name=airtable_table,
                filter_formula=filter_formula
            )
            
            for record in airtable_records:
                # Transform to database format
                db_format = self.airtable.transform_airtable_to_db(table_name, record)
                
                change = ChangeRecord(
                    table_name=table_name,
                    record_id=record.id,
                    local_id=db_format.get('id'),
                    airtable_id=record.id,
                    operation='update',  # We'll determine create vs update later
                    changes=db_format,
                    timestamp=datetime.utcnow()
                )
                changes.append(change)
            
            logger.info(f"Detected {len(changes)} Airtable changes in {table_name}")
            return changes
            
        except AirtableAPIError as e:
            if "Invalid formula" in str(e):
                # Fallback to getting all records if filter fails
                logger.warning(f"Filter formula failed for {table_name}, using timestamp comparison")
                return self._fallback_airtable_changes(table_name, since)
            else:
                logger.error(f"Error detecting Airtable changes in {table_name}: {e}")
                return []
    
    def _fallback_airtable_changes(self, table_name: str, since: datetime) -> List[ChangeRecord]:
        """Fallback method for detecting Airtable changes"""
        airtable_table = self.airtable.table_mappings[table_name]
        changes = []
        
        try:
            # Get all records and filter by timestamp
            all_records = self.airtable.list_records(table_name=airtable_table)
            
            for record in all_records:
                # Check if record was modified since last sync
                if record.created_time:
                    created_time = datetime.fromisoformat(record.created_time.replace('Z', '+00:00'))
                    if created_time > since:
                        db_format = self.airtable.transform_airtable_to_db(table_name, record)
                        
                        change = ChangeRecord(
                            table_name=table_name,
                            record_id=record.id,
                            local_id=db_format.get('id'),
                            airtable_id=record.id,
                            operation='update',
                            changes=db_format,
                            timestamp=datetime.utcnow()
                        )
                        changes.append(change)
            
            return changes
            
        except Exception as e:
            logger.error(f"Error in fallback Airtable change detection for {table_name}: {e}")
            return []
    
    def resolve_conflicts(self, local_record: Dict[str, Any], 
                         airtable_record: Dict[str, Any], 
                         table_name: str) -> Tuple[Dict[str, Any], List[str]]:
        """Resolve conflicts between local and Airtable records"""
        
        # Find conflicting fields
        conflict_fields = []
        for field in local_record:
            if field in airtable_record and local_record[field] != airtable_record[field]:
                conflict_fields.append(field)
        
        if not conflict_fields:
            return local_record, []
        
        # Log the conflict
        conflict = ConflictRecord(
            table_name=table_name,
            local_record=local_record,
            airtable_record=airtable_record,
            conflict_fields=conflict_fields,
            detected_at=datetime.utcnow()
        )
        self.conflict_log.append(conflict)
        
        # Apply resolution strategy
        if self.config.conflict_strategy == ConflictStrategy.LOCAL_WINS:
            resolved_record = local_record.copy()
            resolution_strategy = "local_wins"
            
        elif self.config.conflict_strategy == ConflictStrategy.AIRTABLE_WINS:
            resolved_record = airtable_record.copy()
            resolution_strategy = "airtable_wins"
            
        elif self.config.conflict_strategy == ConflictStrategy.TIMESTAMP_BASED:
            resolved_record = self._resolve_by_timestamp(local_record, airtable_record)
            resolution_strategy = "timestamp_based"
            
        elif self.config.conflict_strategy == ConflictStrategy.MERGE_SMART:
            resolved_record = self._smart_merge(local_record, airtable_record, conflict_fields)
            resolution_strategy = "smart_merge"
            
        else:  # MANUAL_REVIEW
            # For manual review, we'll return the local record and flag for review
            resolved_record = local_record.copy()
            resolution_strategy = "manual_review_required"
        
        # Update conflict record
        conflict.resolution_strategy = resolution_strategy
        conflict.resolved_at = datetime.utcnow()
        
        logger.info(f"Resolved conflict in {table_name} using {resolution_strategy} strategy")
        return resolved_record, conflict_fields
    
    def _resolve_by_timestamp(self, local_record: Dict[str, Any], 
                             airtable_record: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict by choosing the most recently updated record"""
        local_timestamp = self._extract_timestamp(local_record)
        airtable_timestamp = self._extract_timestamp(airtable_record)
        
        if local_timestamp and airtable_timestamp:
            return local_record if local_timestamp > airtable_timestamp else airtable_record
        elif local_timestamp:
            return local_record
        elif airtable_timestamp:
            return airtable_record
        else:
            # No timestamps available, default to local
            return local_record
    
    def _extract_timestamp(self, record: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from record for comparison"""
        timestamp_fields = ['updated_at', 'last_updated', 'last_activity', 'modified_time']
        
        for field in timestamp_fields:
            if field in record and record[field]:
                if isinstance(record[field], datetime):
                    return record[field]
                elif isinstance(record[field], str):
                    try:
                        return datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                    except ValueError:
                        continue
        
        return None
    
    def _smart_merge(self, local_record: Dict[str, Any], 
                    airtable_record: Dict[str, Any], 
                    conflict_fields: List[str]) -> Dict[str, Any]:
        """Intelligent merge of conflicting records"""
        merged = local_record.copy()
        
        for field in conflict_fields:
            local_val = local_record.get(field)
            airtable_val = airtable_record.get(field)
            
            # Merge strategies by field type
            if field in ['notes', 'description']:
                # Concatenate text fields
                if local_val and airtable_val:
                    merged[field] = f"{local_val}\n\n[Airtable]: {airtable_val}"
                else:
                    merged[field] = local_val or airtable_val
                    
            elif field in ['tags', 'categories', 'tools', 'sources']:
                # Merge lists/arrays
                if isinstance(local_val, list) and isinstance(airtable_val, list):
                    merged[field] = list(set(local_val + airtable_val))
                else:
                    merged[field] = local_val or airtable_val
                    
            elif field in ['revenue', 'compensation', 'price']:
                # Take higher value for monetary fields
                if local_val and airtable_val:
                    try:
                        local_num = float(str(local_val).replace('$', '').replace(',', ''))
                        airtable_num = float(str(airtable_val).replace('$', '').replace(',', ''))
                        merged[field] = local_val if local_num > airtable_num else airtable_val
                    except ValueError:
                        merged[field] = local_val
                else:
                    merged[field] = local_val or airtable_val
                    
            else:
                # Default: use timestamp-based resolution for other fields
                local_time = self._extract_timestamp(local_record)
                airtable_time = self._extract_timestamp(airtable_record)
                
                if local_time and airtable_time:
                    merged[field] = local_val if local_time > airtable_time else airtable_val
                else:
                    merged[field] = local_val or airtable_val
        
        return merged
    
    def sync_table_to_airtable(self, table_name: str) -> List[SyncResult]:
        """Sync a specific table from local database to Airtable"""
        logger.info(f"Starting sync of {table_name} to Airtable")
        
        results = []
        
        try:
            # Get local changes
            local_changes = self.detect_local_changes(table_name)
            airtable_table = self.airtable.table_mappings.get(table_name)
            
            if not airtable_table:
                logger.error(f"No Airtable table mapping for {table_name}")
                return results
            
            # Process changes in batches
            for i in range(0, len(local_changes), self.config.batch_size):
                batch = local_changes[i:i + self.config.batch_size]
                batch_results = []
                
                for change in batch:
                    try:
                        # Transform to Airtable format
                        airtable_fields = self.airtable.transform_db_to_airtable(table_name, change.changes)
                        
                        if change.airtable_id:
                            # Update existing record
                            updated_record = self.airtable.update_record(
                                table_name=airtable_table,
                                record_id=change.airtable_id,
                                fields=airtable_fields
                            )
                            operation = 'update'
                            airtable_id = updated_record.id
                        else:
                            # Create new record
                            created_record = self.airtable.create_record(
                                table_name=airtable_table,
                                fields=airtable_fields
                            )
                            operation = 'create'
                            airtable_id = created_record.id
                            
                            # Update local record with Airtable ID
                            self._update_local_airtable_id(table_name, change.local_id, airtable_id)
                        
                        result = SyncResult(
                            operation=operation,
                            record_id=change.record_id,
                            table_name=table_name,
                            success=True,
                            local_id=change.local_id,
                            airtable_id=airtable_id
                        )
                        batch_results.append(result)
                        
                    except AirtableAPIError as e:
                        result = SyncResult(
                            operation='failed',
                            record_id=change.record_id,
                            table_name=table_name,
                            success=False,
                            error_message=str(e),
                            local_id=change.local_id
                        )
                        batch_results.append(result)
                        logger.error(f"Failed to sync record {change.record_id}: {e}")
                
                results.extend(batch_results)
                
                # Small delay between batches
                if i + self.config.batch_size < len(local_changes):
                    import time
                    time.sleep(0.5)
            
            # Update sync timestamp
            self.last_sync_timestamps[table_name] = datetime.utcnow()
            self._save_sync_state()
            
            logger.info(f"Completed sync of {table_name} to Airtable: {len([r for r in results if r.success])} successful, {len([r for r in results if not r.success])} failed")
            
        except Exception as e:
            logger.error(f"Error syncing {table_name} to Airtable: {e}")
            result = SyncResult(
                operation='error',
                record_id='unknown',
                table_name=table_name,
                success=False,
                error_message=str(e)
            )
            results.append(result)
        
        return results
    
    def sync_table_from_airtable(self, table_name: str) -> List[SyncResult]:
        """Sync a specific table from Airtable to local database"""
        logger.info(f"Starting sync of {table_name} from Airtable")
        
        results = []
        
        try:
            # Get Airtable changes
            airtable_changes = self.detect_airtable_changes(table_name)
            model = self.model_mapping.get(table_name)
            
            if not model:
                logger.error(f"No model mapping for {table_name}")
                return results
            
            # Process changes
            for change in airtable_changes:
                try:
                    # Check if record exists locally
                    local_record = None
                    if change.local_id:
                        local_record = model.query.filter_by(id=change.local_id).first()
                    
                    if local_record:
                        # Check for conflicts
                        if hasattr(local_record, 'to_dict'):
                            local_dict = local_record.to_dict()
                        else:
                            local_dict = {c.name: getattr(local_record, c.name) for c in local_record.__table__.columns}
                        
                        resolved_data, conflict_fields = self.resolve_conflicts(
                            local_dict, change.changes, table_name
                        )
                        
                        # Update local record
                        for field, value in resolved_data.items():
                            if hasattr(local_record, field):
                                setattr(local_record, field, value)
                        
                        db.session.commit()
                        operation = 'update'
                        record_id = str(local_record.id)
                        
                    else:
                        # Create new local record
                        new_record = model(**change.changes)
                        db.session.add(new_record)
                        db.session.commit()
                        operation = 'create'
                        record_id = str(new_record.id)
                    
                    result = SyncResult(
                        operation=operation,
                        record_id=record_id,
                        table_name=table_name,
                        success=True,
                        airtable_id=change.airtable_id,
                        local_id=record_id
                    )
                    results.append(result)
                    
                except IntegrityError as e:
                    db.session.rollback()
                    result = SyncResult(
                        operation='failed',
                        record_id=change.record_id,
                        table_name=table_name,
                        success=False,
                        error_message=f"Database integrity error: {str(e)}",
                        airtable_id=change.airtable_id
                    )
                    results.append(result)
                    logger.error(f"Integrity error syncing record {change.record_id}: {e}")
                    
                except Exception as e:
                    db.session.rollback()
                    result = SyncResult(
                        operation='failed',
                        record_id=change.record_id,
                        table_name=table_name,
                        success=False,
                        error_message=str(e),
                        airtable_id=change.airtable_id
                    )
                    results.append(result)
                    logger.error(f"Failed to sync record {change.record_id}: {e}")
            
            # Update sync timestamp
            self.last_sync_timestamps[table_name] = datetime.utcnow()
            self._save_sync_state()
            
            logger.info(f"Completed sync of {table_name} from Airtable: {len([r for r in results if r.success])} successful, {len([r for r in results if not r.success])} failed")
            
        except Exception as e:
            logger.error(f"Error syncing {table_name} from Airtable: {e}")
            result = SyncResult(
                operation='error',
                record_id='unknown',
                table_name=table_name,
                success=False,
                error_message=str(e)
            )
            results.append(result)
        
        return results
    
    def sync_bidirectional(self, table_name: str) -> Dict[str, List[SyncResult]]:
        """Perform bidirectional sync for a table"""
        logger.info(f"Starting bidirectional sync for {table_name}")
        
        results = {
            'to_airtable': [],
            'from_airtable': []
        }
        
        try:
            # Sync to Airtable first
            if self.config.sync_direction in [SyncDirection.PUSH_TO_AIRTABLE, SyncDirection.BIDIRECTIONAL]:
                results['to_airtable'] = self.sync_table_to_airtable(table_name)
            
            # Then sync from Airtable
            if self.config.sync_direction in [SyncDirection.PULL_FROM_AIRTABLE, SyncDirection.BIDIRECTIONAL]:
                results['from_airtable'] = self.sync_table_from_airtable(table_name)
            
        except Exception as e:
            logger.error(f"Error in bidirectional sync for {table_name}: {e}")
        
        return results
    
    def sync_all_tables(self) -> Dict[str, Any]:
        """Sync all enabled tables"""
        logger.info("Starting full sync of all enabled tables")
        
        sync_summary = {
            'start_time': datetime.utcnow(),
            'tables_synced': {},
            'total_success': 0,
            'total_failed': 0,
            'conflicts_detected': 0,
            'errors': []
        }
        
        for table_name in self.config.enabled_tables:
            try:
                logger.info(f"Syncing table: {table_name}")
                
                if self.config.sync_direction == SyncDirection.BIDIRECTIONAL:
                    table_results = self.sync_bidirectional(table_name)
                    sync_summary['tables_synced'][table_name] = table_results
                    
                    # Count results
                    for direction_results in table_results.values():
                        sync_summary['total_success'] += len([r for r in direction_results if r.success])
                        sync_summary['total_failed'] += len([r for r in direction_results if not r.success])
                        
                elif self.config.sync_direction == SyncDirection.PUSH_TO_AIRTABLE:
                    results = self.sync_table_to_airtable(table_name)
                    sync_summary['tables_synced'][table_name] = {'to_airtable': results}
                    sync_summary['total_success'] += len([r for r in results if r.success])
                    sync_summary['total_failed'] += len([r for r in results if not r.success])
                    
                else:  # PULL_FROM_AIRTABLE
                    results = self.sync_table_from_airtable(table_name)
                    sync_summary['tables_synced'][table_name] = {'from_airtable': results}
                    sync_summary['total_success'] += len([r for r in results if r.success])
                    sync_summary['total_failed'] += len([r for r in results if not r.success])
                
            except Exception as e:
                error_msg = f"Failed to sync table {table_name}: {str(e)}"
                sync_summary['errors'].append(error_msg)
                logger.error(error_msg)
        
        sync_summary['end_time'] = datetime.utcnow()
        sync_summary['duration_minutes'] = (sync_summary['end_time'] - sync_summary['start_time']).total_seconds() / 60
        sync_summary['conflicts_detected'] = len([c for c in self.conflict_log if c.detected_at >= sync_summary['start_time']])
        
        logger.info(f"Full sync completed: {sync_summary['total_success']} successful, {sync_summary['total_failed']} failed, {sync_summary['conflicts_detected']} conflicts")
        
        return sync_summary
    
    def _update_local_airtable_id(self, table_name: str, local_id: str, airtable_id: str):
        """Update local record with Airtable ID for future syncs"""
        model = self.model_mapping.get(table_name)
        if model:
            try:
                record = model.query.filter_by(id=local_id).first()
                if record and hasattr(record, 'airtable_id'):
                    record.airtable_id = airtable_id
                    db.session.commit()
            except Exception as e:
                logger.error(f"Failed to update local record with Airtable ID: {e}")
                db.session.rollback()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics"""
        return {
            'config': asdict(self.config),
            'last_sync_timestamps': {k: v.isoformat() for k, v in self.last_sync_timestamps.items()},
            'total_sync_operations': len(self.sync_log),
            'active_conflicts': len([c for c in self.conflict_log if not c.resolved_at]),
            'resolved_conflicts': len([c for c in self.conflict_log if c.resolved_at]),
            'airtable_stats': self.airtable.get_sync_statistics()
        }
    
    def get_conflict_summary(self) -> List[Dict[str, Any]]:
        """Get summary of conflicts that need attention"""
        unresolved_conflicts = [c for c in self.conflict_log if not c.resolved_at]
        
        return [
            {
                'table_name': conflict.table_name,
                'conflict_fields': conflict.conflict_fields,
                'detected_at': conflict.detected_at.isoformat(),
                'local_record': conflict.local_record,
                'airtable_record': conflict.airtable_record
            }
            for conflict in unresolved_conflicts
        ]


def create_sync_service(base_id: str, sync_config: SyncConfiguration = None) -> AirtableSyncService:
    """Factory function to create sync service with default configuration"""
    airtable_client = create_airtable_client()
    return AirtableSyncService(airtable_client, base_id, sync_config)


# Example usage
if __name__ == "__main__":
    # Create sync service
    config = SyncConfiguration(
        enabled_tables=['revenue_streams', 'ai_agents', 'executive_opportunities'],
        sync_direction=SyncDirection.BIDIRECTIONAL,
        conflict_strategy=ConflictStrategy.TIMESTAMP_BASED,
        sync_interval_minutes=30
    )
    
    sync_service = create_sync_service("appXXXXXXXXXXXXXX", config)
    
    # Perform full sync
    results = sync_service.sync_all_tables()
    print(f"Sync completed: {results['total_success']} successful, {results['total_failed']} failed")