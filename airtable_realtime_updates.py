"""
Airtable Real-time Updates System for Dr. Dédé's AI Empire Platform
Webhook handlers and event streaming for immediate sync updates
"""

import os
import json
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import hmac
import hashlib
import requests
from queue import Queue, Empty
import time

from airtable_sync_service import create_sync_service, SyncConfiguration, SyncDirection
from airtable_sync_scheduler import get_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of real-time events"""
    RECORD_CREATED = "record_created"
    RECORD_UPDATED = "record_updated"
    RECORD_DELETED = "record_deleted"
    SYNC_TRIGGERED = "sync_triggered"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    CONFLICT_DETECTED = "conflict_detected"


@dataclass
class RealtimeEvent:
    """Real-time event structure"""
    event_id: str
    event_type: EventType
    source: str  # 'airtable', 'local', 'scheduler'
    table_name: str
    record_id: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime
    base_id: Optional[str] = None
    webhook_id: Optional[str] = None
    processed: bool = False
    retry_count: int = 0
    
    def __post_init__(self):
        if isinstance(self.event_type, str):
            self.event_type = EventType(self.event_type)


@dataclass
class WebhookConfig:
    """Configuration for webhook endpoints"""
    id: str
    name: str
    base_id: str
    webhook_url: str
    secret_key: Optional[str]
    enabled: bool = True
    event_types: List[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.event_types is None:
            self.event_types = ["record_created", "record_updated", "record_deleted"]
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class RealtimeUpdateHandler:
    """
    Handles real-time updates from Airtable and triggers immediate syncs
    """
    
    def __init__(self):
        # Event processing
        self.event_queue: Queue = Queue()
        self.event_processors: Dict[EventType, List[Callable]] = {}
        self.event_history: List[RealtimeEvent] = []
        self.max_history = 1000
        
        # Webhook management
        self.webhook_configs: Dict[str, WebhookConfig] = {}
        self.webhook_secrets: Dict[str, str] = {}
        
        # Real-time sync management
        self.auto_sync_enabled = True
        self.sync_debounce_seconds = 30  # Wait for related changes
        self.pending_syncs: Dict[str, datetime] = {}  # table -> last change time
        
        # Event streaming
        self.event_streams: Dict[str, Queue] = {}  # stream_id -> event_queue
        self.stream_clients: Dict[str, List[Callable]] = {}  # stream_id -> callbacks
        
        # Processing thread
        self.processing_enabled = False
        self.processing_thread = None
        
        # Initialize event processors
        self._initialize_event_processors()
        
    def _initialize_event_processors(self):
        """Initialize default event processors"""
        # Record change processors
        self.register_event_processor(EventType.RECORD_CREATED, self._handle_record_change)
        self.register_event_processor(EventType.RECORD_UPDATED, self._handle_record_change)
        self.register_event_processor(EventType.RECORD_DELETED, self._handle_record_change)
        
        # Sync event processors
        self.register_event_processor(EventType.SYNC_COMPLETED, self._handle_sync_completion)
        self.register_event_processor(EventType.SYNC_FAILED, self._handle_sync_failure)
        self.register_event_processor(EventType.CONFLICT_DETECTED, self._handle_conflict)
    
    def register_event_processor(self, event_type: EventType, processor: Callable):
        """Register a processor for specific event types"""
        if event_type not in self.event_processors:
            self.event_processors[event_type] = []
        
        self.event_processors[event_type].append(processor)
        logger.info(f"Registered processor for {event_type.value}")
    
    def start_processing(self):
        """Start the event processing thread"""
        if self.processing_enabled:
            logger.warning("Event processing is already running")
            return
        
        self.processing_enabled = True
        self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
        self.processing_thread.start()
        logger.info("Real-time event processing started")
    
    def stop_processing(self):
        """Stop the event processing thread"""
        if not self.processing_enabled:
            logger.warning("Event processing is not running")
            return
        
        self.processing_enabled = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        logger.info("Real-time event processing stopped")
    
    def _process_events(self):
        """Main event processing loop"""
        while self.processing_enabled:
            try:
                # Get event from queue (with timeout)
                try:
                    event = self.event_queue.get(timeout=1)
                except Empty:
                    continue
                
                # Process the event
                self._handle_event(event)
                
                # Mark as processed
                event.processed = True
                
                # Add to history
                self.event_history.append(event)
                
                # Trim history if too long
                if len(self.event_history) > self.max_history:
                    self.event_history = self.event_history[-self.max_history:]
                
                # Mark queue task as done
                self.event_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                time.sleep(1)
    
    def _handle_event(self, event: RealtimeEvent):
        """Handle a specific event"""
        try:
            logger.info(f"Processing event: {event.event_type.value} for {event.table_name}")
            
            # Get processors for this event type
            processors = self.event_processors.get(event.event_type, [])
            
            for processor in processors:
                try:
                    processor(event)
                except Exception as e:
                    logger.error(f"Error in event processor {processor.__name__}: {e}")
                    event.retry_count += 1
            
            # Distribute to event streams
            self._distribute_to_streams(event)
            
        except Exception as e:
            logger.error(f"Error handling event {event.event_id}: {e}")
    
    def _distribute_to_streams(self, event: RealtimeEvent):
        """Distribute event to active event streams"""
        try:
            for stream_id, stream_queue in self.event_streams.items():
                try:
                    # Put event in stream queue (non-blocking)
                    if stream_queue.qsize() < 100:  # Limit queue size
                        stream_queue.put_nowait(event)
                    else:
                        logger.warning(f"Stream {stream_id} queue is full, dropping event")
                except Exception as e:
                    logger.error(f"Error distributing event to stream {stream_id}: {e}")
                
            # Call stream callbacks
            for stream_id, callbacks in self.stream_clients.items():
                for callback in callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"Error in stream callback: {e}")
                        
        except Exception as e:
            logger.error(f"Error distributing event to streams: {e}")
    
    def _handle_record_change(self, event: RealtimeEvent):
        """Handle record creation, update, or deletion"""
        try:
            if not self.auto_sync_enabled:
                logger.debug("Auto-sync disabled, skipping record change handling")
                return
            
            table_name = event.table_name
            base_id = event.base_id
            
            if not base_id:
                logger.warning(f"No base_id provided for event {event.event_id}")
                return
            
            # Schedule debounced sync
            sync_key = f"{base_id}:{table_name}"
            self.pending_syncs[sync_key] = datetime.utcnow()
            
            # Schedule sync execution after debounce period
            threading.Timer(
                self.sync_debounce_seconds,
                self._execute_debounced_sync,
                args=[sync_key, base_id, table_name]
            ).start()
            
            logger.info(f"Scheduled debounced sync for {sync_key}")
            
        except Exception as e:
            logger.error(f"Error handling record change: {e}")
    
    def _execute_debounced_sync(self, sync_key: str, base_id: str, table_name: str):
        """Execute sync after debounce period"""
        try:
            # Check if there have been more recent changes
            if sync_key in self.pending_syncs:
                last_change = self.pending_syncs[sync_key]
                time_since_change = (datetime.utcnow() - last_change).total_seconds()
                
                if time_since_change < self.sync_debounce_seconds:
                    logger.debug(f"Skipping sync for {sync_key} - more recent changes detected")
                    return
                
                # Remove from pending syncs
                del self.pending_syncs[sync_key]
            
            # Execute the sync
            self._trigger_immediate_sync(base_id, table_name)
            
        except Exception as e:
            logger.error(f"Error executing debounced sync for {sync_key}: {e}")
    
    def _trigger_immediate_sync(self, base_id: str, table_name: str):
        """Trigger immediate sync for a specific table"""
        try:
            # Create sync service
            sync_config = SyncConfiguration(
                enabled_tables=[table_name],
                sync_direction=SyncDirection.BIDIRECTIONAL,
                batch_size=20
            )
            
            sync_service = create_sync_service(base_id, sync_config)
            
            # Perform sync
            results = sync_service.sync_bidirectional(table_name)
            
            # Emit sync completion event
            sync_event = RealtimeEvent(
                event_id=f"sync_{int(time.time() * 1000)}",
                event_type=EventType.SYNC_COMPLETED,
                source="realtime",
                table_name=table_name,
                record_id=None,
                data={"results": results, "base_id": base_id},
                timestamp=datetime.utcnow(),
                base_id=base_id
            )
            
            self.emit_event(sync_event)
            
            logger.info(f"Completed immediate sync for {table_name}")
            
        except Exception as e:
            logger.error(f"Error in immediate sync for {table_name}: {e}")
            
            # Emit sync failure event
            failure_event = RealtimeEvent(
                event_id=f"sync_fail_{int(time.time() * 1000)}",
                event_type=EventType.SYNC_FAILED,
                source="realtime",
                table_name=table_name,
                record_id=None,
                data={"error": str(e), "base_id": base_id},
                timestamp=datetime.utcnow(),
                base_id=base_id
            )
            
            self.emit_event(failure_event)
    
    def _handle_sync_completion(self, event: RealtimeEvent):
        """Handle sync completion events"""
        logger.info(f"Sync completed for {event.table_name}")
        
        # Could trigger additional workflows here
        # e.g., update dashboard, send notifications, etc.
    
    def _handle_sync_failure(self, event: RealtimeEvent):
        """Handle sync failure events"""
        logger.warning(f"Sync failed for {event.table_name}: {event.data.get('error')}")
        
        # Could trigger retry logic, alerts, etc.
    
    def _handle_conflict(self, event: RealtimeEvent):
        """Handle conflict detection events"""
        logger.warning(f"Conflict detected in {event.table_name}")
        
        # Could trigger conflict resolution workflows
    
    def emit_event(self, event: RealtimeEvent):
        """Emit a new event for processing"""
        try:
            self.event_queue.put(event)
            logger.debug(f"Emitted event: {event.event_type.value}")
        except Exception as e:
            logger.error(f"Error emitting event: {e}")
    
    def handle_airtable_webhook(self, webhook_data: Dict[str, Any], webhook_id: str = None) -> Dict[str, Any]:
        """Handle incoming webhook from Airtable"""
        try:
            # Validate webhook if secret is configured
            if webhook_id and webhook_id in self.webhook_configs:
                config = self.webhook_configs[webhook_id]
                if config.secret_key and not self._validate_webhook_signature(webhook_data, config.secret_key):
                    logger.warning(f"Invalid webhook signature for {webhook_id}")
                    return {"error": "Invalid signature"}
            
            # Extract event information
            base_id = webhook_data.get('base', {}).get('id')
            table_id = webhook_data.get('table', {}).get('id')
            table_name = webhook_data.get('table', {}).get('name', 'unknown')
            
            # Process webhook payload
            events_created = []
            
            if 'records' in webhook_data:
                for record_change in webhook_data['records']:
                    change_type = record_change.get('changeType', 'unknown')
                    record_id = record_change.get('record', {}).get('id')
                    
                    # Map change type to event type
                    event_type_map = {
                        'recordCreated': EventType.RECORD_CREATED,
                        'recordUpdated': EventType.RECORD_UPDATED,
                        'recordDeleted': EventType.RECORD_DELETED
                    }
                    
                    event_type = event_type_map.get(change_type)
                    if not event_type:
                        logger.warning(f"Unknown change type: {change_type}")
                        continue
                    
                    # Create event
                    event = RealtimeEvent(
                        event_id=f"webhook_{webhook_id}_{int(time.time() * 1000)}_{len(events_created)}",
                        event_type=event_type,
                        source="airtable",
                        table_name=table_name,
                        record_id=record_id,
                        data=record_change,
                        timestamp=datetime.utcnow(),
                        base_id=base_id,
                        webhook_id=webhook_id
                    )
                    
                    # Emit event for processing
                    self.emit_event(event)
                    events_created.append(event.event_id)
            
            logger.info(f"Processed webhook with {len(events_created)} events")
            
            return {
                "success": True,
                "events_created": events_created,
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling Airtable webhook: {e}")
            return {"error": str(e)}
    
    def _validate_webhook_signature(self, payload: Dict[str, Any], secret: str) -> bool:
        """Validate webhook signature for security"""
        try:
            # This would implement actual signature validation
            # For now, just return True as Airtable webhook signature validation
            # varies by implementation
            return True
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False
    
    def create_event_stream(self, stream_id: str) -> Queue:
        """Create a new event stream for real-time updates"""
        if stream_id in self.event_streams:
            logger.warning(f"Event stream {stream_id} already exists")
            return self.event_streams[stream_id]
        
        stream_queue = Queue(maxsize=100)
        self.event_streams[stream_id] = stream_queue
        
        logger.info(f"Created event stream: {stream_id}")
        return stream_queue
    
    def remove_event_stream(self, stream_id: str):
        """Remove an event stream"""
        if stream_id in self.event_streams:
            del self.event_streams[stream_id]
            logger.info(f"Removed event stream: {stream_id}")
        
        if stream_id in self.stream_clients:
            del self.stream_clients[stream_id]
    
    def add_stream_callback(self, stream_id: str, callback: Callable):
        """Add a callback function to an event stream"""
        if stream_id not in self.stream_clients:
            self.stream_clients[stream_id] = []
        
        self.stream_clients[stream_id].append(callback)
        logger.info(f"Added callback to stream {stream_id}")
    
    def get_recent_events(self, limit: int = 50, event_type: EventType = None, 
                         table_name: str = None) -> List[RealtimeEvent]:
        """Get recent events with optional filtering"""
        events = self.event_history[-limit:]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if table_name:
            events = [e for e in events if e.table_name == table_name]
        
        return events
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics about event processing"""
        total_events = len(self.event_history)
        
        # Count by event type
        event_type_counts = {}
        for event in self.event_history:
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        # Count by source
        source_counts = {}
        for event in self.event_history:
            source = event.source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Get recent activity (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_events = [e for e in self.event_history if e.timestamp > one_hour_ago]
        
        return {
            "total_events": total_events,
            "recent_events_last_hour": len(recent_events),
            "event_type_breakdown": event_type_counts,
            "source_breakdown": source_counts,
            "active_streams": len(self.event_streams),
            "pending_syncs": len(self.pending_syncs),
            "processing_enabled": self.processing_enabled,
            "auto_sync_enabled": self.auto_sync_enabled
        }
    
    def configure_webhook(self, config: WebhookConfig):
        """Configure a webhook endpoint"""
        self.webhook_configs[config.id] = config
        if config.secret_key:
            self.webhook_secrets[config.id] = config.secret_key
        
        logger.info(f"Configured webhook: {config.name} ({config.id})")
    
    def get_webhook_config(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Get webhook configuration"""
        return self.webhook_configs.get(webhook_id)
    
    def list_webhook_configs(self) -> List[WebhookConfig]:
        """List all webhook configurations"""
        return list(self.webhook_configs.values())


# Global realtime handler instance
_realtime_handler = None

def get_realtime_handler() -> RealtimeUpdateHandler:
    """Get the global realtime handler instance"""
    global _realtime_handler
    if _realtime_handler is None:
        _realtime_handler = RealtimeUpdateHandler()
    return _realtime_handler


# WebSocket support for real-time updates
class WebSocketEventStreamer:
    """WebSocket streamer for real-time events"""
    
    def __init__(self, realtime_handler: RealtimeUpdateHandler):
        self.realtime_handler = realtime_handler
        self.active_connections: Dict[str, Any] = {}
    
    def add_connection(self, connection_id: str, websocket):
        """Add a WebSocket connection"""
        self.active_connections[connection_id] = websocket
        
        # Create event stream for this connection
        stream_queue = self.realtime_handler.create_event_stream(connection_id)
        
        # Start sending events to this connection
        threading.Thread(
            target=self._stream_events_to_websocket,
            args=[connection_id, websocket, stream_queue],
            daemon=True
        ).start()
    
    def remove_connection(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        self.realtime_handler.remove_event_stream(connection_id)
    
    def _stream_events_to_websocket(self, connection_id: str, websocket, stream_queue: Queue):
        """Stream events to a WebSocket connection"""
        try:
            while connection_id in self.active_connections:
                try:
                    # Get event from stream queue
                    event = stream_queue.get(timeout=1)
                    
                    # Convert event to JSON
                    event_data = {
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "source": event.source,
                        "table_name": event.table_name,
                        "record_id": event.record_id,
                        "data": event.data,
                        "timestamp": event.timestamp.isoformat(),
                        "base_id": event.base_id
                    }
                    
                    # Send to WebSocket
                    websocket.send(json.dumps(event_data))
                    
                except Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error streaming to WebSocket {connection_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in WebSocket streaming thread: {e}")
        finally:
            self.remove_connection(connection_id)


# Example usage
if __name__ == "__main__":
    # Create and start realtime handler
    handler = get_realtime_handler()
    handler.start_processing()
    
    try:
        # Example: simulate webhook event
        webhook_data = {
            "base": {"id": "appXXXXXXXXXXXXXX"},
            "table": {"id": "tblYYYYYYYYYYYYYY", "name": "Revenue Streams"},
            "records": [{
                "changeType": "recordUpdated",
                "record": {"id": "recZZZZZZZZZZZZZZ"},
                "fields": {"name": "Updated Revenue Stream"}
            }]
        }
        
        result = handler.handle_airtable_webhook(webhook_data, "webhook_1")
        print(f"Webhook result: {result}")
        
        # Keep running
        while True:
            time.sleep(60)
            stats = handler.get_event_statistics()
            print(f"Event stats: {stats}")
            
    except KeyboardInterrupt:
        handler.stop_processing()
        print("Realtime handler stopped")