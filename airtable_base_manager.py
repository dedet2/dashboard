"""
Airtable Base Management for Dr. Dédé's AI Empire Platform
Automated base setup and schema management for CRM tables
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from airtable_integration import AirtableAPIWrapper, create_airtable_client, AirtableAPIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FieldDefinition:
    """Definition for an Airtable field"""
    name: str
    type: str  # text, number, currency, date, etc.
    options: Dict[str, Any] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}


@dataclass
class TableDefinition:
    """Definition for an Airtable table"""
    name: str
    description: Optional[str]
    fields: List[FieldDefinition]
    primary_field: str = "Name"


@dataclass
class BaseDefinition:
    """Definition for an Airtable base"""
    name: str
    description: Optional[str]
    tables: List[TableDefinition]
    workspace_id: Optional[str] = None


class AirtableBaseManager:
    """
    Manages Airtable base creation, schema setup, and maintenance
    """
    
    def __init__(self, airtable_client: AirtableAPIWrapper):
        self.airtable = airtable_client
        
        # Define CRM schema templates
        self.crm_schema = self._initialize_crm_schema()
        
        # Track managed bases
        self.managed_bases = {}
    
    def _initialize_crm_schema(self) -> BaseDefinition:
        """Initialize the complete CRM schema definition"""
        
        # Revenue Streams Table
        revenue_streams_table = TableDefinition(
            name="Revenue Streams",
            description="Track multiple revenue streams and their performance",
            fields=[
                FieldDefinition("Stream Name", "singleLineText", {"maxLength": 200}),
                FieldDefinition("Current Month Revenue", "currency", {
                    "precision": 2,
                    "symbol": "$"
                }),
                FieldDefinition("Target Month Revenue", "currency", {
                    "precision": 2,
                    "symbol": "$"
                }),
                FieldDefinition("Target YTD", "currency", {
                    "precision": 2,
                    "symbol": "$"
                }),
                FieldDefinition("YTD Revenue", "currency", {
                    "precision": 2,
                    "symbol": "$"
                }),
                FieldDefinition("Growth Rate", "percent", {"precision": 2}),
                FieldDefinition("Revenue Sources", "multipleSelects", {
                    "choices": [
                        {"name": "Speaking Engagements", "color": "blueLight1"},
                        {"name": "Consulting", "color": "greenLight1"},
                        {"name": "Board Positions", "color": "purpleLight1"},
                        {"name": "Retreats", "color": "orangeLight1"},
                        {"name": "AI Services", "color": "redLight1"},
                        {"name": "Partnerships", "color": "yellowLight1"}
                    ]
                }),
                FieldDefinition("Projections", "longText"),
                FieldDefinition("Last Updated", "dateTime"),
                FieldDefinition("Status", "singleSelect", {
                    "choices": [
                        {"name": "Active", "color": "greenLight1"},
                        {"name": "Pending", "color": "yellowLight1"},
                        {"name": "Paused", "color": "redLight1"}
                    ]
                })
            ],
            primary_field="Stream Name"
        )
        
        # AI Agents Table
        ai_agents_table = TableDefinition(
            name="AI Agents",
            description="Monitor and manage AI agent ecosystem",
            fields=[
                FieldDefinition("Agent Name", "singleLineText", {"maxLength": 200}),
                FieldDefinition("Tier", "singleSelect", {
                    "choices": [
                        {"name": "Revenue Generation", "color": "greenLight1"},
                        {"name": "Authority Building", "color": "blueLight1"},
                        {"name": "Operational Excellence", "color": "purpleLight1"}
                    ]
                }),
                FieldDefinition("Function", "longText"),
                FieldDefinition("Tools", "multipleSelects", {
                    "choices": [
                        {"name": "Apollo", "color": "blueLight1"},
                        {"name": "LinkedIn Sales Navigator", "color": "purpleLight1"},
                        {"name": "Perplexity", "color": "greenLight1"},
                        {"name": "Mindstudio", "color": "orangeLight1"},
                        {"name": "Make.com", "color": "redLight1"}
                    ]
                }),
                FieldDefinition("Status", "singleSelect", {
                    "choices": [
                        {"name": "Active", "color": "greenLight1"},
                        {"name": "Inactive", "color": "redLight1"},
                        {"name": "Maintenance", "color": "yellowLight1"}
                    ]
                }),
                FieldDefinition("Performance Score", "number", {
                    "precision": 1,
                    "validationMode": "between",
                    "validationRange": {"min": 0, "max": 100}
                }),
                FieldDefinition("Last Activity", "dateTime"),
                FieldDefinition("Next Scheduled", "dateTime"),
                FieldDefinition("Revenue Target", "singleLineText"),
                FieldDefinition("Weekly Goal", "singleLineText"),
                FieldDefinition("Success Rate", "percent", {"precision": 2})
            ],
            primary_field="Agent Name"
        )
        
        # Executive Opportunities Table
        executive_opportunities_table = TableDefinition(
            name="Executive Opportunities",
            description="Track executive positions, board roles, and speaking opportunities",
            fields=[
                FieldDefinition("Position Title", "singleLineText", {"maxLength": 200}),
                FieldDefinition("Company", "singleLineText", {"maxLength": 200}),
                FieldDefinition("Opportunity Type", "singleSelect", {
                    "choices": [
                        {"name": "Board Director", "color": "purpleLight1"},
                        {"name": "Executive Position", "color": "blueLight1"},
                        {"name": "Speaking Opportunity", "color": "greenLight1"},
                        {"name": "Advisory Role", "color": "orangeLight1"},
                        {"name": "Consulting Project", "color": "redLight1"}
                    ]
                }),
                FieldDefinition("Compensation Range", "singleLineText"),
                FieldDefinition("Location", "singleLineText"),
                FieldDefinition("Status", "singleSelect", {
                    "choices": [
                        {"name": "Prospect", "color": "yellowLight1"},
                        {"name": "Applied", "color": "blueLight1"},
                        {"name": "Interview", "color": "orangeLight1"},
                        {"name": "Offer", "color": "greenLight1"},
                        {"name": "Accepted", "color": "greenBright"},
                        {"name": "Rejected", "color": "redLight1"},
                        {"name": "Withdrawn", "color": "grayLight1"}
                    ]
                }),
                FieldDefinition("AI Match Score", "number", {
                    "precision": 1,
                    "validationMode": "between",
                    "validationRange": {"min": 0, "max": 100}
                }),
                FieldDefinition("Requirements", "multipleSelects", {
                    "choices": [
                        {"name": "Risk Management", "color": "redLight1"},
                        {"name": "AI Governance", "color": "blueLight1"},
                        {"name": "Board Experience", "color": "purpleLight1"},
                        {"name": "Technology Leadership", "color": "greenLight1"},
                        {"name": "Financial Expertise", "color": "orangeLight1"}
                    ]
                }),
                FieldDefinition("Application Date", "date"),
                FieldDefinition("Next Step", "singleLineText"),
                FieldDefinition("Notes", "longText"),
                FieldDefinition("Conversion Probability", "percent", {"precision": 2}),
                FieldDefinition("Source", "singleSelect", {
                    "choices": [
                        {"name": "Apollo", "color": "blueLight1"},
                        {"name": "LinkedIn", "color": "purpleLight1"},
                        {"name": "Network", "color": "greenLight1"},
                        {"name": "Direct Outreach", "color": "orangeLight1"}
                    ]
                })
            ],
            primary_field="Position Title"
        )
        
        # Healthcare Providers Table
        healthcare_providers_table = TableDefinition(
            name="Healthcare Providers",
            description="Manage healthcare provider network and appointments",
            fields=[
                FieldDefinition("Provider Name", "singleLineText", {"maxLength": 200}),
                FieldDefinition("Specialty", "singleSelect", {
                    "choices": [
                        {"name": "Primary Care", "color": "blueLight1"},
                        {"name": "Cardiology", "color": "redLight1"},
                        {"name": "Dermatology", "color": "orangeLight1"},
                        {"name": "Mental Health", "color": "purpleLight1"},
                        {"name": "Ophthalmology", "color": "greenLight1"},
                        {"name": "Orthopedics", "color": "yellowLight1"}
                    ]
                }),
                FieldDefinition("Phone", "phoneNumber"),
                FieldDefinition("Address", "multilineText"),
                FieldDefinition("Rating", "number", {
                    "precision": 1,
                    "validationMode": "between",
                    "validationRange": {"min": 1, "max": 5}
                }),
                FieldDefinition("Insurance Accepted", "multipleSelects", {
                    "choices": [
                        {"name": "Blue Cross Blue Shield", "color": "blueLight1"},
                        {"name": "Aetna", "color": "purpleLight1"},
                        {"name": "UnitedHealth", "color": "greenLight1"},
                        {"name": "Cigna", "color": "orangeLight1"},
                        {"name": "Medicare", "color": "redLight1"}
                    ]
                }),
                FieldDefinition("Next Available", "singleLineText"),
                FieldDefinition("Notes", "longText"),
                FieldDefinition("Preferred Provider", "checkbox")
            ],
            primary_field="Provider Name"
        )
        
        # Healthcare Appointments Table
        healthcare_appointments_table = TableDefinition(
            name="Healthcare Appointments",
            description="Track upcoming and past healthcare appointments",
            fields=[
                FieldDefinition("Appointment Title", "singleLineText", {"maxLength": 200}),
                FieldDefinition("Provider", "singleLineText"),
                FieldDefinition("Date", "date"),
                FieldDefinition("Time", "singleLineText"),
                FieldDefinition("Purpose", "singleSelect", {
                    "choices": [
                        {"name": "Annual Checkup", "color": "blueLight1"},
                        {"name": "Follow-up", "color": "greenLight1"},
                        {"name": "Consultation", "color": "orangeLight1"},
                        {"name": "Procedure", "color": "redLight1"},
                        {"name": "Emergency", "color": "redBright"}
                    ]
                }),
                FieldDefinition("Status", "singleSelect", {
                    "choices": [
                        {"name": "Scheduled", "color": "yellowLight1"},
                        {"name": "Confirmed", "color": "blueLight1"},
                        {"name": "Completed", "color": "greenLight1"},
                        {"name": "Cancelled", "color": "redLight1"},
                        {"name": "Rescheduled", "color": "orangeLight1"}
                    ]
                }),
                FieldDefinition("Notes", "longText"),
                FieldDefinition("Reminder Set", "checkbox"),
                FieldDefinition("Priority", "singleSelect", {
                    "choices": [
                        {"name": "High", "color": "redLight1"},
                        {"name": "Medium", "color": "yellowLight1"},
                        {"name": "Low", "color": "greenLight1"}
                    ]
                })
            ],
            primary_field="Appointment Title"
        )
        
        # Retreat Events Table
        retreat_events_table = TableDefinition(
            name="Retreat Events",
            description="Manage luxury retreat events and registrations",
            fields=[
                FieldDefinition("Event Name", "singleLineText", {"maxLength": 200}),
                FieldDefinition("Event Type", "singleSelect", {
                    "choices": [
                        {"name": "Rest as Resistance", "color": "purpleLight1"},
                        {"name": "Leadership Retreat", "color": "blueLight1"},
                        {"name": "Wellness Weekend", "color": "greenLight1"},
                        {"name": "Executive Intensive", "color": "orangeLight1"}
                    ]
                }),
                FieldDefinition("Dates", "singleLineText"),
                FieldDefinition("Location", "singleLineText"),
                FieldDefinition("Capacity", "number"),
                FieldDefinition("Registered", "number"),
                FieldDefinition("Available Spots", "formula", {
                    "expression": "{Capacity} - {Registered}"
                }),
                FieldDefinition("Pricing", "currency", {
                    "precision": 2,
                    "symbol": "$"
                }),
                FieldDefinition("Status", "singleSelect", {
                    "choices": [
                        {"name": "Planning", "color": "yellowLight1"},
                        {"name": "Open Registration", "color": "blueLight1"},
                        {"name": "Full", "color": "orangeLight1"},
                        {"name": "In Progress", "color": "greenLight1"},
                        {"name": "Completed", "color": "grayLight1"},
                        {"name": "Cancelled", "color": "redLight1"}
                    ]
                }),
                FieldDefinition("Projected Revenue", "currency", {
                    "precision": 2,
                    "symbol": "$"
                }),
                FieldDefinition("Focus Areas", "multipleSelects", {
                    "choices": [
                        {"name": "Stress Management", "color": "blueLight1"},
                        {"name": "Leadership Development", "color": "purpleLight1"},
                        {"name": "Wellness Practices", "color": "greenLight1"},
                        {"name": "Network Building", "color": "orangeLight1"}
                    ]
                }),
                FieldDefinition("Registration Link", "url")
            ],
            primary_field="Event Name"
        )
        
        # KPI Metrics Table
        kpi_metrics_table = TableDefinition(
            name="KPI Metrics",
            description="Track key performance indicators across the empire",
            fields=[
                FieldDefinition("Metric Name", "singleLineText", {"maxLength": 200}),
                FieldDefinition("Current Value", "number", {"precision": 2}),
                FieldDefinition("Target Value", "number", {"precision": 2}),
                FieldDefinition("Unit", "singleLineText"),
                FieldDefinition("Category", "singleSelect", {
                    "choices": [
                        {"name": "Revenue", "color": "greenLight1"},
                        {"name": "Marketing", "color": "blueLight1"},
                        {"name": "Operations", "color": "purpleLight1"},
                        {"name": "Health", "color": "orangeLight1"},
                        {"name": "Growth", "color": "yellowLight1"}
                    ]
                }),
                FieldDefinition("Progress", "percent", {"precision": 1}),
                FieldDefinition("Trend", "singleSelect", {
                    "choices": [
                        {"name": "Increasing", "color": "greenLight1"},
                        {"name": "Stable", "color": "yellowLight1"},
                        {"name": "Decreasing", "color": "redLight1"}
                    ]
                }),
                FieldDefinition("Last Updated", "dateTime"),
                FieldDefinition("Empire Focus", "singleLineText")
            ],
            primary_field="Metric Name"
        )
        
        return BaseDefinition(
            name="Dr. Dédé's AI Empire CRM",
            description="Comprehensive CRM system for managing the $50M+ AI Empire",
            tables=[
                revenue_streams_table,
                ai_agents_table,
                executive_opportunities_table,
                healthcare_providers_table,
                healthcare_appointments_table,
                retreat_events_table,
                kpi_metrics_table
            ]
        )
    
    def create_base_from_template(self, workspace_id: str = None) -> Dict[str, Any]:
        """Create a new Airtable base from the CRM template"""
        logger.info("Creating new Airtable base from CRM template")
        
        try:
            # Note: Airtable API doesn't support programmatic base creation
            # This method provides the schema definition for manual setup
            # or for future API support
            
            base_schema = {
                "name": self.crm_schema.name,
                "description": self.crm_schema.description,
                "workspace_id": workspace_id,
                "tables": []
            }
            
            for table in self.crm_schema.tables:
                table_schema = {
                    "name": table.name,
                    "description": table.description,
                    "fields": []
                }
                
                for field in table.fields:
                    field_schema = {
                        "name": field.name,
                        "type": field.type,
                        "options": field.options,
                        "description": field.description
                    }
                    table_schema["fields"].append(field_schema)
                
                base_schema["tables"].append(table_schema)
            
            logger.info(f"Generated schema for base: {base_schema['name']}")
            return base_schema
            
        except Exception as e:
            logger.error(f"Error creating base schema: {e}")
            raise
    
    def setup_existing_base(self, base_id: str) -> Dict[str, Any]:
        """Setup and configure an existing Airtable base with CRM schema"""
        logger.info(f"Setting up existing base: {base_id}")
        
        self.airtable.set_base_id(base_id)
        setup_results = {
            "base_id": base_id,
            "tables_created": [],
            "tables_updated": [],
            "errors": []
        }
        
        try:
            # Get current base schema
            current_schema = self.airtable.get_base_schema(base_id)
            existing_tables = {table["name"]: table for table in current_schema.get("tables", [])}
            
            # Note: Airtable API has limited support for schema modification
            # This method validates the schema and provides setup guidance
            
            for table_def in self.crm_schema.tables:
                try:
                    if table_def.name in existing_tables:
                        # Table exists, validate fields
                        validation_result = self._validate_table_schema(
                            table_def, existing_tables[table_def.name]
                        )
                        setup_results["tables_updated"].append({
                            "table": table_def.name,
                            "validation": validation_result
                        })
                    else:
                        # Table doesn't exist - needs manual creation
                        setup_results["tables_created"].append({
                            "table": table_def.name,
                            "schema": self._table_to_dict(table_def),
                            "status": "needs_manual_creation"
                        })
                
                except Exception as e:
                    error_msg = f"Error processing table {table_def.name}: {str(e)}"
                    setup_results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Store base configuration
            self.managed_bases[base_id] = {
                "setup_date": datetime.utcnow(),
                "schema_version": "1.0",
                "last_validated": datetime.utcnow()
            }
            
            logger.info(f"Base setup completed: {len(setup_results['tables_created'])} tables to create, {len(setup_results['tables_updated'])} tables validated")
            return setup_results
            
        except AirtableAPIError as e:
            error_msg = f"Airtable API error during base setup: {str(e)}"
            setup_results["errors"].append(error_msg)
            logger.error(error_msg)
            return setup_results
        except Exception as e:
            error_msg = f"Unexpected error during base setup: {str(e)}"
            setup_results["errors"].append(error_msg)
            logger.error(error_msg)
            return setup_results
    
    def _validate_table_schema(self, table_def: TableDefinition, existing_table: Dict) -> Dict[str, Any]:
        """Validate existing table schema against template"""
        validation = {
            "table_name": table_def.name,
            "matches_template": True,
            "missing_fields": [],
            "extra_fields": [],
            "field_type_mismatches": []
        }
        
        existing_fields = {field["name"]: field for field in existing_table.get("fields", [])}
        template_fields = {field.name: field for field in table_def.fields}
        
        # Check for missing fields
        for field_name, field_def in template_fields.items():
            if field_name not in existing_fields:
                validation["missing_fields"].append({
                    "name": field_name,
                    "type": field_def.type,
                    "options": field_def.options
                })
                validation["matches_template"] = False
        
        # Check for type mismatches
        for field_name, existing_field in existing_fields.items():
            if field_name in template_fields:
                template_field = template_fields[field_name]
                if existing_field.get("type") != template_field.type:
                    validation["field_type_mismatches"].append({
                        "field": field_name,
                        "expected_type": template_field.type,
                        "actual_type": existing_field.get("type")
                    })
                    validation["matches_template"] = False
        
        # Check for extra fields (not necessarily an error)
        for field_name in existing_fields:
            if field_name not in template_fields:
                validation["extra_fields"].append(field_name)
        
        return validation
    
    def _table_to_dict(self, table_def: TableDefinition) -> Dict[str, Any]:
        """Convert table definition to dictionary"""
        return {
            "name": table_def.name,
            "description": table_def.description,
            "primary_field": table_def.primary_field,
            "fields": [
                {
                    "name": field.name,
                    "type": field.type,
                    "options": field.options,
                    "description": field.description
                }
                for field in table_def.fields
            ]
        }
    
    def validate_base_configuration(self, base_id: str) -> Dict[str, Any]:
        """Validate that a base is properly configured for CRM sync"""
        logger.info(f"Validating base configuration: {base_id}")
        
        validation_result = {
            "base_id": base_id,
            "is_valid": True,
            "issues": [],
            "recommendations": [],
            "table_validations": {}
        }
        
        try:
            self.airtable.set_base_id(base_id)
            
            # Get current schema
            schema = self.airtable.get_base_schema(base_id)
            existing_tables = {table["name"]: table for table in schema.get("tables", [])}
            
            # Validate each required table
            for table_def in self.crm_schema.tables:
                table_validation = self._validate_table_schema(table_def, existing_tables.get(table_def.name, {}))
                validation_result["table_validations"][table_def.name] = table_validation
                
                if not table_validation["matches_template"]:
                    validation_result["is_valid"] = False
                    
                    if table_def.name not in existing_tables:
                        validation_result["issues"].append(f"Missing required table: {table_def.name}")
                    else:
                        if table_validation["missing_fields"]:
                            validation_result["issues"].append(f"Table {table_def.name} missing fields: {[f['name'] for f in table_validation['missing_fields']]}")
                        
                        if table_validation["field_type_mismatches"]:
                            validation_result["issues"].append(f"Table {table_def.name} has field type mismatches: {table_validation['field_type_mismatches']}")
            
            # Generate recommendations
            if not validation_result["is_valid"]:
                validation_result["recommendations"].extend([
                    "Use the setup_existing_base() method to get detailed setup instructions",
                    "Create missing tables manually in Airtable using the provided schema",
                    "Ensure field types match the template requirements",
                    "Run validation again after making changes"
                ])
            
            logger.info(f"Base validation completed: {'Valid' if validation_result['is_valid'] else 'Issues found'}")
            return validation_result
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Error during validation: {str(e)}")
            logger.error(f"Error validating base: {e}")
            return validation_result
    
    def get_setup_instructions(self, base_id: str = None) -> Dict[str, Any]:
        """Generate detailed setup instructions for manual base configuration"""
        instructions = {
            "overview": "Manual setup instructions for Dr. Dédé's AI Empire CRM",
            "base_configuration": {
                "name": self.crm_schema.name,
                "description": self.crm_schema.description
            },
            "tables": [],
            "automation_suggestions": [],
            "best_practices": []
        }
        
        # Generate table creation instructions
        for table_def in self.crm_schema.tables:
            table_instructions = {
                "name": table_def.name,
                "description": table_def.description,
                "primary_field": table_def.primary_field,
                "fields": []
            }
            
            for field in table_def.fields:
                field_instruction = {
                    "name": field.name,
                    "type": field.type,
                    "description": field.description or f"Field for storing {field.name.lower()}",
                    "configuration": field.options
                }
                table_instructions["fields"].append(field_instruction)
            
            instructions["tables"].append(table_instructions)
        
        # Add automation suggestions
        instructions["automation_suggestions"] = [
            "Set up automations to send notifications when new opportunities are added",
            "Create views to filter opportunities by status and priority",
            "Set up recurring reminders for healthcare appointments",
            "Configure email notifications for retreat registrations",
            "Create dashboard views for revenue tracking"
        ]
        
        # Add best practices
        instructions["best_practices"] = [
            "Use consistent naming conventions across all tables",
            "Set up proper permissions for team access",
            "Create backup automations for critical data",
            "Regularly validate data integrity",
            "Use linked records between related tables where appropriate"
        ]
        
        return instructions
    
    def export_schema_json(self, filepath: str = None) -> str:
        """Export the complete CRM schema as JSON"""
        schema_dict = {
            "version": "1.0",
            "created_date": datetime.utcnow().isoformat(),
            "base_definition": {
                "name": self.crm_schema.name,
                "description": self.crm_schema.description,
                "tables": [self._table_to_dict(table) for table in self.crm_schema.tables]
            }
        }
        
        schema_json = json.dumps(schema_dict, indent=2, default=str)
        
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(schema_json)
                logger.info(f"Schema exported to: {filepath}")
            except Exception as e:
                logger.error(f"Error exporting schema to file: {e}")
        
        return schema_json
    
    def get_managed_bases(self) -> Dict[str, Any]:
        """Get information about all managed bases"""
        return {
            "total_bases": len(self.managed_bases),
            "bases": {
                base_id: {
                    **config,
                    "setup_date": config["setup_date"].isoformat(),
                    "last_validated": config["last_validated"].isoformat()
                }
                for base_id, config in self.managed_bases.items()
            }
        }


def create_base_manager() -> AirtableBaseManager:
    """Factory function to create a base manager"""
    airtable_client = create_airtable_client()
    return AirtableBaseManager(airtable_client)


# Example usage
if __name__ == "__main__":
    # Create base manager
    manager = create_base_manager()
    
    # Export schema for manual setup
    schema_json = manager.export_schema_json("crm_schema.json")
    print("CRM schema exported to crm_schema.json")
    
    # Get setup instructions
    instructions = manager.get_setup_instructions()
    print(f"Setup instructions include {len(instructions['tables'])} tables")
    
    # Example base validation (replace with actual base ID)
    # base_id = "appXXXXXXXXXXXXXX"
    # validation = manager.validate_base_configuration(base_id)
    # print(f"Base validation: {'Valid' if validation['is_valid'] else 'Issues found'}")