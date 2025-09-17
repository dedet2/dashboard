"""
Airtable CRM Integration for Dr. Dédé's AI Empire Platform
Comprehensive API wrapper for bi-directional data synchronization
"""

import os
import time
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import quote
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirtableAPIError(Exception):
    """Custom exception for Airtable API errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


@dataclass
class AirtableRecord:
    """Standardized Airtable record structure"""
    id: Optional[str] = None
    fields: Dict[str, Any] = None
    created_time: Optional[str] = None
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = {}


@dataclass
class SyncResult:
    """Result of a sync operation"""
    operation: str  # 'create', 'update', 'delete'
    record_id: str
    table_name: str
    success: bool
    error_message: Optional[str] = None
    local_id: Optional[str] = None
    airtable_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ConflictResolution:
    """Configuration for handling sync conflicts"""
    strategy: str  # 'local_wins', 'airtable_wins', 'merge', 'manual'
    merge_rules: Dict[str, str] = None  # Field-specific merge rules
    timestamp_field: str = 'last_updated'
    
    def __post_init__(self):
        if self.merge_rules is None:
            self.merge_rules = {}


class AirtableAPIWrapper:
    """
    Comprehensive Airtable API wrapper for CRM integration
    """
    
    def __init__(self, api_key: str, base_id: str = None):
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.airtable.com/v0"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 5 requests per second max
        self.requests_per_second = 5
        self.daily_request_count = 0
        self.daily_request_reset = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # CRM table mappings
        self.table_mappings = {
            'revenue_streams': 'Revenue Streams',
            'ai_agents': 'AI Agents',
            'executive_opportunities': 'Executive Opportunities',
            'healthcare_providers': 'Healthcare Providers',
            'healthcare_appointments': 'Healthcare Appointments',
            'retreat_events': 'Retreat Events',
            'kpi_metrics': 'KPI Metrics',
            'milestones': 'Milestones',
            'energy_tracking': 'Energy Tracking',
            'wellness_goals': 'Wellness Goals'
        }
        
        # Field mappings for data transformation
        self.field_mappings = self._initialize_field_mappings()
        
        # Sync tracking
        self.sync_log = []
        self.last_sync_times = {}
        
    def _initialize_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize field mappings between database and Airtable"""
        return {
            'revenue_streams': {
                'id': 'ID',
                'name': 'Stream Name',
                'current_month': 'Current Month Revenue',
                'target_month': 'Target Month Revenue', 
                'target_ytd': 'Target YTD',
                'ytd': 'YTD Revenue',
                'growth_rate': 'Growth Rate',
                'sources': 'Revenue Sources',
                'projections': 'Projections',
                'last_updated': 'Last Updated'
            },
            'ai_agents': {
                'id': 'ID',
                'name': 'Agent Name',
                'tier': 'Tier',
                'function': 'Function',
                'tools': 'Tools',
                'status': 'Status',
                'performance': 'Performance Metrics',
                'last_activity': 'Last Activity',
                'next_scheduled': 'Next Scheduled',
                'revenue_target': 'Revenue Target'
            },
            'executive_opportunities': {
                'id': 'ID',
                'type': 'Opportunity Type',
                'title': 'Position Title',
                'company': 'Company',
                'compensation_range': 'Compensation Range',
                'location': 'Location',
                'status': 'Status',
                'ai_match_score': 'AI Match Score',
                'requirements': 'Requirements',
                'application_date': 'Application Date',
                'next_step': 'Next Step',
                'notes': 'Notes'
            },
            'healthcare_providers': {
                'id': 'ID',
                'name': 'Provider Name',
                'specialty': 'Specialty',
                'phone': 'Phone',
                'address': 'Address',
                'rating': 'Rating',
                'insurance_accepted': 'Insurance Accepted',
                'next_available': 'Next Available',
                'notes': 'Notes'
            },
            'retreat_events': {
                'id': 'ID',
                'name': 'Event Name',
                'type': 'Event Type',
                'dates': 'Dates',
                'location': 'Location',
                'capacity': 'Capacity',
                'registered': 'Registered',
                'pricing': 'Pricing',
                'status': 'Status',
                'revenue_projected': 'Projected Revenue'
            }
        }
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None, params: Dict = None) -> Dict:
        """
        Make authenticated request to Airtable API with rate limiting and error handling
        """
        # Rate limiting
        self._handle_rate_limiting()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data, params=params)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise AirtableAPIError(f"Unsupported HTTP method: {method}")
            
            self.last_request_time = time.time()
            self.daily_request_count += 1
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 30))
                logger.warning(f"Airtable API rate limit hit. Waiting {retry_after} seconds.")
                time.sleep(retry_after)
                return self._make_request(endpoint, method, data, params)
            
            # Handle API errors
            if not response.ok:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
                raise AirtableAPIError(
                    f"Airtable API error: {error_message}",
                    status_code=response.status_code,
                    response_data=error_data
                )
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in Airtable API request: {e}")
            raise AirtableAPIError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Airtable API: {e}")
            raise AirtableAPIError(f"Invalid JSON response: {str(e)}")
    
    def _handle_rate_limiting(self):
        """Handle rate limiting to stay within API limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # Enforce minimum interval between requests
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        # Reset daily counter if needed
        now = datetime.utcnow()
        if now >= self.daily_request_reset + timedelta(days=1):
            self.daily_request_count = 0
            self.daily_request_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Log rate limiting status
        if self.daily_request_count > 0 and self.daily_request_count % 1000 == 0:
            logger.info(f"Airtable API requests today: {self.daily_request_count}")
    
    def set_base_id(self, base_id: str):
        """Set the Airtable base ID for operations"""
        self.base_id = base_id
        logger.info(f"Airtable base ID set to: {base_id}")
    
    def list_bases(self) -> List[Dict]:
        """List all accessible Airtable bases"""
        try:
            response = self._make_request("meta/bases")
            return response.get('bases', [])
        except AirtableAPIError as e:
            logger.error(f"Error listing Airtable bases: {e}")
            raise
    
    def get_base_schema(self, base_id: str = None) -> Dict:
        """Get the schema for a specific base"""
        target_base_id = base_id or self.base_id
        if not target_base_id:
            raise AirtableAPIError("No base ID provided")
        
        try:
            response = self._make_request(f"meta/bases/{target_base_id}/tables")
            return response
        except AirtableAPIError as e:
            logger.error(f"Error getting base schema: {e}")
            raise
    
    def list_records(self, table_name: str, filter_formula: str = None, 
                    sort: List[Dict] = None, max_records: int = None, 
                    page_size: int = 100) -> List[AirtableRecord]:
        """List records from a table with optional filtering and sorting"""
        if not self.base_id:
            raise AirtableAPIError("No base ID set")
        
        params = {'pageSize': min(page_size, 100)}
        if filter_formula:
            params['filterByFormula'] = filter_formula
        if sort:
            params['sort'] = sort
        if max_records:
            params['maxRecords'] = max_records
        
        all_records = []
        offset = None
        
        try:
            while True:
                if offset:
                    params['offset'] = offset
                
                response = self._make_request(f"{self.base_id}/{quote(table_name)}", params=params)
                records = response.get('records', [])
                
                for record in records:
                    all_records.append(AirtableRecord(
                        id=record.get('id'),
                        fields=record.get('fields', {}),
                        created_time=record.get('createdTime')
                    ))
                
                offset = response.get('offset')
                if not offset or (max_records and len(all_records) >= max_records):
                    break
                
                # Respect pagination limits
                time.sleep(0.1)
            
            return all_records[:max_records] if max_records else all_records
            
        except AirtableAPIError as e:
            logger.error(f"Error listing records from table {table_name}: {e}")
            raise
    
    def get_record(self, table_name: str, record_id: str) -> Optional[AirtableRecord]:
        """Get a specific record by ID"""
        if not self.base_id:
            raise AirtableAPIError("No base ID set")
        
        try:
            response = self._make_request(f"{self.base_id}/{quote(table_name)}/{record_id}")
            return AirtableRecord(
                id=response.get('id'),
                fields=response.get('fields', {}),
                created_time=response.get('createdTime')
            )
        except AirtableAPIError as e:
            if e.status_code == 404:
                return None
            logger.error(f"Error getting record {record_id} from table {table_name}: {e}")
            raise
    
    def create_record(self, table_name: str, fields: Dict[str, Any]) -> AirtableRecord:
        """Create a new record in a table"""
        if not self.base_id:
            raise AirtableAPIError("No base ID set")
        
        data = {'fields': fields}
        
        try:
            response = self._make_request(f"{self.base_id}/{quote(table_name)}", 'POST', data)
            return AirtableRecord(
                id=response.get('id'),
                fields=response.get('fields', {}),
                created_time=response.get('createdTime')
            )
        except AirtableAPIError as e:
            logger.error(f"Error creating record in table {table_name}: {e}")
            raise
    
    def update_record(self, table_name: str, record_id: str, fields: Dict[str, Any]) -> AirtableRecord:
        """Update an existing record"""
        if not self.base_id:
            raise AirtableAPIError("No base ID set")
        
        data = {'fields': fields}
        
        try:
            response = self._make_request(f"{self.base_id}/{quote(table_name)}/{record_id}", 'PATCH', data)
            return AirtableRecord(
                id=response.get('id'),
                fields=response.get('fields', {}),
                created_time=response.get('createdTime')
            )
        except AirtableAPIError as e:
            logger.error(f"Error updating record {record_id} in table {table_name}: {e}")
            raise
    
    def delete_record(self, table_name: str, record_id: str) -> bool:
        """Delete a record from a table"""
        if not self.base_id:
            raise AirtableAPIError("No base ID set")
        
        try:
            self._make_request(f"{self.base_id}/{quote(table_name)}/{record_id}", 'DELETE')
            return True
        except AirtableAPIError as e:
            logger.error(f"Error deleting record {record_id} from table {table_name}: {e}")
            raise
    
    def batch_create_records(self, table_name: str, records: List[Dict[str, Any]], 
                           batch_size: int = 10) -> List[AirtableRecord]:
        """Create multiple records in batches"""
        if not self.base_id:
            raise AirtableAPIError("No base ID set")
        
        created_records = []
        
        # Process in batches of 10 (Airtable limit)
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_data = {
                'records': [{'fields': record} for record in batch]
            }
            
            try:
                response = self._make_request(f"{self.base_id}/{quote(table_name)}", 'POST', batch_data)
                
                for record in response.get('records', []):
                    created_records.append(AirtableRecord(
                        id=record.get('id'),
                        fields=record.get('fields', {}),
                        created_time=record.get('createdTime')
                    ))
                
                # Small delay between batches
                if i + batch_size < len(records):
                    time.sleep(0.2)
                    
            except AirtableAPIError as e:
                logger.error(f"Error in batch create (batch {i//batch_size + 1}): {e}")
                raise
        
        return created_records
    
    def batch_update_records(self, table_name: str, updates: List[Dict[str, Any]], 
                           batch_size: int = 10) -> List[AirtableRecord]:
        """Update multiple records in batches"""
        if not self.base_id:
            raise AirtableAPIError("No base ID set")
        
        updated_records = []
        
        # Process in batches of 10 (Airtable limit)
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            batch_data = {
                'records': [{'id': update['id'], 'fields': update['fields']} for update in batch]
            }
            
            try:
                response = self._make_request(f"{self.base_id}/{quote(table_name)}", 'PATCH', batch_data)
                
                for record in response.get('records', []):
                    updated_records.append(AirtableRecord(
                        id=record.get('id'),
                        fields=record.get('fields', {}),
                        created_time=record.get('createdTime')
                    ))
                
                # Small delay between batches
                if i + batch_size < len(updates):
                    time.sleep(0.2)
                    
            except AirtableAPIError as e:
                logger.error(f"Error in batch update (batch {i//batch_size + 1}): {e}")
                raise
        
        return updated_records
    
    def transform_db_to_airtable(self, table_type: str, db_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform database record to Airtable format"""
        if table_type not in self.field_mappings:
            logger.warning(f"No field mapping found for table type: {table_type}")
            return db_record
        
        field_map = self.field_mappings[table_type]
        airtable_fields = {}
        
        for db_field, airtable_field in field_map.items():
            if db_field in db_record and db_record[db_field] is not None:
                value = db_record[db_field]
                
                # Convert datetime to string
                if isinstance(value, datetime):
                    value = value.isoformat()
                # Convert lists/dicts to JSON strings for Airtable
                elif isinstance(value, (list, dict)):
                    value = json.dumps(value)
                
                airtable_fields[airtable_field] = value
        
        return airtable_fields
    
    def transform_airtable_to_db(self, table_type: str, airtable_record: AirtableRecord) -> Dict[str, Any]:
        """Transform Airtable record to database format"""
        if table_type not in self.field_mappings:
            logger.warning(f"No field mapping found for table type: {table_type}")
            return airtable_record.fields
        
        field_map = self.field_mappings[table_type]
        db_fields = {}
        
        # Reverse the field mapping
        reverse_map = {v: k for k, v in field_map.items()}
        
        for airtable_field, db_field in reverse_map.items():
            if airtable_field in airtable_record.fields:
                value = airtable_record.fields[airtable_field]
                
                # Handle datetime parsing
                if db_field in ['last_updated', 'last_activity', 'next_scheduled', 'created_at', 'updated_at']:
                    try:
                        if isinstance(value, str):
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        logger.warning(f"Could not parse datetime field {db_field}: {value}")
                        continue
                
                # Handle JSON fields
                elif db_field in ['tools', 'performance', 'sources', 'projections', 'requirements']:
                    try:
                        if isinstance(value, str):
                            value = json.loads(value)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse JSON field {db_field}: {value}")
                        continue
                
                db_fields[db_field] = value
        
        return db_fields
    
    def validate_api_key(self) -> bool:
        """Validate the Airtable API key"""
        try:
            self.list_bases()
            return True
        except AirtableAPIError:
            return False
        except Exception:
            return False
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get statistics about sync operations"""
        total_operations = len(self.sync_log)
        successful_operations = sum(1 for result in self.sync_log if result.success)
        failed_operations = total_operations - successful_operations
        
        operation_counts = {}
        for result in self.sync_log:
            operation_counts[result.operation] = operation_counts.get(result.operation, 0) + 1
        
        return {
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'failed_operations': failed_operations,
            'success_rate': (successful_operations / total_operations * 100) if total_operations > 0 else 0,
            'operation_breakdown': operation_counts,
            'last_sync_times': self.last_sync_times,
            'daily_api_requests': self.daily_request_count
        }


def create_airtable_client(api_key: str = None, base_id: str = None) -> AirtableAPIWrapper:
    """
    Factory function to create an Airtable API client with environment configuration
    """
    if not api_key:
        api_key = os.getenv('AIRTABLE_API_KEY')
    
    if not api_key:
        raise ValueError("Airtable API key is required. Set AIRTABLE_API_KEY environment variable.")
    
    client = AirtableAPIWrapper(api_key, base_id)
    
    # Validate API key
    if not client.validate_api_key():
        raise ValueError("Invalid Airtable API key provided")
    
    logger.info("Airtable API client created and validated successfully")
    return client


# Example usage
if __name__ == "__main__":
    # Create client
    client = create_airtable_client()
    
    # List available bases
    bases = client.list_bases()
    print(f"Available bases: {len(bases)}")
    
    for base in bases:
        print(f"- {base.get('name')} ({base.get('id')})")