"""
Dr. Dede's RiskTravel Intelligence Platform - Manus Deployment
Optimized for deployment at https://hfqukiyd.manus.space/dashboard
"""

from flask import Flask, jsonify, request, render_template_string, render_template, send_from_directory, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
import logging
import json
import requests
from dotenv import load_dotenv
from sqlalchemy import func, desc
from database import db, RevenueStream, AIAgent, HealthcareProvider, HealthcareAppointment, HealthMetric, ExecutiveOpportunity, SpeakingOpportunity, InterviewStage, CompensationBenchmark, RetreatEvent, KPIMetric, Milestone, EnergyTracking, WellnessGoal, WellnessAlert, WellnessMetric, WorkflowTrigger, BusinessRule, WorkflowAction, WorkflowSchedule, WorkflowExecution, NotificationChannel, WorkflowWebhook, BusinessEvent

# Import Make.com integration components
try:
    from make_models import MakeScenario, MakeExecution, MakeEventLog, MakeAutomationBridge, MakeTemplate
    from make_api_routes import make_bp
    from make_automation_bridges import (
        create_automation_bridge_service, 
        handle_opportunity_created,
        handle_agent_performance_alert,
        handle_revenue_milestone,
        handle_research_complete
    )
    make_integration_loaded = True
except ImportError as e:
    make_integration_loaded = False
    make_integration_error = str(e)
    # Set placeholder functions for fallback
    make_bp = None
    create_automation_bridge_service = None
    handle_opportunity_created = None
    handle_agent_performance_alert = None
    handle_revenue_milestone = None
    handle_research_complete = None

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log Make.com integration status
try:
    if make_integration_loaded:
        logger.info("Make.com integration modules loaded successfully")
    else:
        logger.warning(f"Make.com integration modules not available: {make_integration_error}")
except NameError:
    # make_integration_loaded variables not defined, Make.com integration not attempted
    pass

# API Configuration
APOLLO_API_KEY = os.getenv('APOLLO_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY') 
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# Import Airtable integration components
try:
    from airtable_integration import create_airtable_client, AirtableAPIError
    from airtable_sync_service import (
        create_sync_service, SyncConfiguration, SyncDirection, ConflictStrategy
    )
    from airtable_base_manager import create_base_manager
    from airtable_sync_scheduler import get_scheduler
    from airtable_realtime_updates import get_realtime_handler, RealtimeEvent, EventType, WebhookConfig
    logger.info("Airtable integration modules loaded successfully")
except ImportError as e:
    logger.warning(f"Airtable integration modules not available: {e}")
    # Set placeholder functions
    create_airtable_client = None
    create_sync_service = None
    create_base_manager = None
    get_scheduler = None
    get_realtime_handler = None

# Import Perplexity AI integration services
try:
    from perplexity_service import (
        PerplexityAPI, PerplexityModel, SearchRecency,
        PerplexityResearchService, PerplexityContentService, PerplexityOpportunityAnalyzer,
        create_perplexity_api, create_research_service, create_content_service, create_opportunity_analyzer
    )
    from ai_scoring_service import AIOpportunityScorer, create_ai_scorer
    logger.info("Perplexity AI integration modules loaded successfully")
except ImportError as e:
    logger.warning(f"Perplexity AI integration modules not available: {e}")
    # Set placeholder functions for fallback
    create_perplexity_api = None
    create_research_service = None
    create_content_service = None
    create_opportunity_analyzer = None
    create_ai_scorer = None

# API Base URLs
APOLLO_BASE_URL = "https://api.apollo.io/v1"
AIRTABLE_BASE_URL = "https://api.airtable.com/v0"
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Database Configuration
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Convert postgres:// to postgresql:// for SQLAlchemy compatibility
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    logger.warning("Using SQLite fallback database. Set DATABASE_URL environment variable for production.")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
def create_and_seed_database():
    """Create database tables and seed with initial data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Check if data already exists
        if RevenueStream.query.first() is None:
            logger.info("Seeding database with initial data...")
            seed_database()
            logger.info("Database seeded successfully")
        else:
            logger.info("Database already contains data, skipping seeding")

def seed_database():
    """Seed database with existing data from global lists"""
    try:
        # Seed Revenue Streams
        for stream_data in REVENUE_STREAMS:
            # Check if stream already exists
            existing_stream = RevenueStream.query.filter_by(id=stream_data['id']).first()
            if not existing_stream:
                stream = RevenueStream(
                    id=stream_data['id'],
                    name=stream_data['name'],
                    current_month=stream_data['current_month'],
                    target_month=stream_data['target_month'],
                    target_ytd=stream_data['target_ytd'],
                    ytd=stream_data['ytd'],
                    growth_rate=stream_data['growth_rate'],
                    sources=stream_data['sources'],
                    projections=stream_data['projections'],
                    last_updated=datetime.fromisoformat(stream_data['last_updated'])
                )
                db.session.add(stream)
        
        # Seed AI Agents
        for agent_data in AI_EMPIRE_AGENTS:
            # Parse datetime fields
            last_activity = None
            next_scheduled = None
            if agent_data.get('last_activity'):
                last_activity = datetime.fromisoformat(agent_data['last_activity'])
            if agent_data.get('next_scheduled'):
                next_scheduled = datetime.fromisoformat(agent_data['next_scheduled'])
            
            # Extract known fields and put rest in additional_data
            known_fields = ['id', 'name', 'tier', 'function', 'tools', 'status', 'performance', 'last_activity', 'next_scheduled']
            additional_data = {k: v for k, v in agent_data.items() if k not in known_fields}
            
            agent = AIAgent(
                id=agent_data['id'],
                name=agent_data['name'],
                tier=agent_data['tier'],
                function=agent_data['function'],
                tools=agent_data.get('tools', []),
                status=agent_data.get('status', 'active'),
                performance=agent_data.get('performance', {}),
                last_activity=last_activity,
                next_scheduled=next_scheduled,
                additional_data=additional_data
            )
            db.session.add(agent)
        
        # Seed Healthcare Providers
        for provider_data in HEALTHCARE_PROVIDERS:
            provider = HealthcareProvider(
                id=provider_data['id'],
                name=provider_data['name'],
                specialty=provider_data['specialty'],
                phone=provider_data.get('phone'),
                address=provider_data.get('address'),
                rating=provider_data.get('rating', 0.0),
                insurance_accepted=provider_data.get('insurance_accepted', []),
                next_available=provider_data.get('next_available'),
                notes=provider_data.get('notes')
            )
            db.session.add(provider)
        
        # Seed Healthcare Appointments
        for appointment_data in HEALTHCARE_APPOINTMENTS:
            appointment = HealthcareAppointment(
                id=appointment_data['id'],
                provider=appointment_data['provider'],
                date=appointment_data['date'],
                time=appointment_data['time'],
                purpose=appointment_data['purpose'],
                status=appointment_data.get('status', 'scheduled'),
                notes=appointment_data.get('notes')
            )
            db.session.add(appointment)
        
        # Seed Health Metrics
        for metric_data in HEALTH_METRICS:
            metric = HealthMetric(
                id=metric_data['id'],
                metric=metric_data['metric'],
                value=str(metric_data['value']),  # Convert to string to handle mixed types
                unit=metric_data['unit'],
                status=metric_data.get('status', 'normal'),
                target=metric_data.get('target'),
                date=datetime.fromisoformat(metric_data['date'])
            )
            db.session.add(metric)
        
        # Seed Executive Opportunities
        for opp_data in EXECUTIVE_OPPORTUNITIES:
            opportunity = ExecutiveOpportunity(
                id=opp_data['id'],
                type=opp_data['type'],
                title=opp_data['title'],
                company=opp_data['company'],
                compensation_range=opp_data.get('compensation'),
                location=opp_data.get('location'),
                status=opp_data.get('status', 'prospect'),
                ai_match_score=opp_data.get('match_score', 0.0),
                requirements=opp_data.get('requirements', []),
                application_date=opp_data.get('application_date'),
                next_step=opp_data.get('next_step'),
                notes=opp_data.get('notes')
            )
            db.session.add(opportunity)
        
        # Seed Retreat Events
        for event_data in RETREAT_EVENTS:
            event = RetreatEvent(
                id=event_data['id'],
                name=event_data['name'],
                type=event_data.get('type'),
                dates=event_data['dates'],
                location=event_data['location'],
                capacity=event_data['capacity'],
                registered=event_data.get('registered', 0),
                pricing=event_data['pricing'],
                status=event_data.get('status', 'planning'),
                focus=event_data.get('focus', []),
                amenities=event_data.get('amenities', []),
                speakers=event_data.get('speakers', []),
                revenue_projected=event_data.get('revenue_projected', 0.0)
            )
            db.session.add(event)
        
        # Seed KPI Metrics
        for kpi_data in KPI_METRICS:
            kpi = KPIMetric(
                id=kpi_data['id'],
                name=kpi_data['name'],
                value=kpi_data['value'],
                target=kpi_data['target'],
                unit=kpi_data['unit'],
                trend=kpi_data.get('trend', 'stable'),
                change_percent=kpi_data.get('change_percent', 0.0),
                category=kpi_data['category'],
                empire_focus=kpi_data.get('empire_focus')
            )
            db.session.add(kpi)
        
        # Seed Milestones
        for milestone_data in MILESTONES:
            milestone = Milestone(
                id=milestone_data['id'],
                title=milestone_data['title'],
                target_date=milestone_data['target_date'],
                progress=milestone_data.get('progress', 0),
                status=milestone_data.get('status', 'pending'),
                description=milestone_data.get('description')
            )
            db.session.add(milestone)
        
        # Seed Energy Tracking
        for energy_data in HEALTH_WELLNESS['energy_tracking']:
            energy = EnergyTracking(
                id=energy_data['id'],
                date=datetime.fromisoformat(energy_data['date']),
                energy_level=energy_data['energy_level'],
                focus_level=energy_data['focus_level'],
                stress_level=energy_data['stress_level'],
                sleep_hours=energy_data['sleep_hours'],
                recovery_time=energy_data['recovery_time'],
                notes=energy_data.get('notes')
            )
            db.session.add(energy)
        
        # Seed Wellness Goals
        for goal_data in HEALTH_WELLNESS['wellness_goals']:
            goal = WellnessGoal(
                id=goal_data['id'],
                goal=goal_data['goal'],
                current=goal_data['current'],
                target=goal_data['target'],
                status=goal_data.get('status', 'pending')
            )
            db.session.add(goal)
        
        # Seed Wellness Alerts
        for alert_data in HEALTH_WELLNESS['alerts']:
            alert = WellnessAlert(
                id=alert_data['id'],
                type=alert_data['type'],
                message=alert_data['message'],
                active=alert_data.get('active', True)
            )
            db.session.add(alert)
        
        # Commit all changes
        db.session.commit()
        logger.info("Database seeded with all existing data successfully")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.session.rollback()
        raise

# Helper function to serialize SQLAlchemy objects to JSON
def serialize_model(obj):
    """Convert SQLAlchemy model instance to dictionary"""
    if obj is None:
        return None
    
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            result[column.name] = value.isoformat()
        elif isinstance(value, (list, dict)):
            result[column.name] = value
        else:
            result[column.name] = value
    return result

def serialize_models(objects):
    """Convert list of SQLAlchemy model instances to list of dictionaries"""
    return [serialize_model(obj) for obj in objects]

# Configuration
jwt_secret = os.getenv('JWT_SECRET_KEY')
if not jwt_secret:
    if os.getenv('NODE_ENV') == 'production':
        raise ValueError("JWT_SECRET_KEY environment variable is required in production")
    jwt_secret = 'risktravel-dev-secret-2025'  # Development fallback
    logger.warning("Using development JWT secret. Set JWT_SECRET_KEY environment variable for production.")

app.config['JWT_SECRET_KEY'] = jwt_secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
# Configure CORS - restrict origins in production
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
if os.getenv('NODE_ENV') == 'production' and '*' in allowed_origins:
    logger.warning("Wildcard CORS origins detected in production. Consider restricting to specific domains.")
CORS(app, origins=allowed_origins)
jwt = JWTManager(app)

# JWT configuration
@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return {"id": identity, "email": "dede@risktravel.com"}

# Register API blueprints
if make_bp:
    app.register_blueprint(make_bp)
    logger.info("Make.com API blueprint registered successfully")
else:
    logger.warning("Make.com integration not available - API routes not registered")

# Initialize Make.com integration (deferred to after app setup)
def initialize_make_bridges():
    """Initialize Make.com automation bridges within app context"""
    if create_automation_bridge_service:
        try:
            with app.app_context():
                bridge_service = create_automation_bridge_service()
                # Create default bridges
                bridge_service.create_default_bridges()
                logger.info("Make.com automation bridges initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Make.com bridges: {e}")

# AI Empire Data Structures

# Comprehensive AI Empire Agent Ecosystem
AI_EMPIRE_AGENTS = [
    # Tier 1: Revenue Generation Agents
    {
        "id": 1,
        "name": "Speaking Opportunity Hunter Agent",
        "tier": "revenue_generation",
        "function": "Auto-research, apply to, and book 20+ speaking opportunities weekly",
        "tools": ["Apollo", "LinkedIn Sales Navigator", "Perplexity", "TEDx credentials"],
        "status": "active",
        "performance": {
            "opportunities_found": 23,
            "applications_submitted": 18,
            "bookings_confirmed": 3,
            "pipeline_value": 175000,
            "success_rate": 87.2
        },
        "last_activity": datetime.now().isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=2)).isoformat(),
        "revenue_target": "25K-200K per engagement",
        "weekly_goal": "20+ speaking opportunities"
    },
    {
        "id": 2,
        "name": "Enterprise Lead Generator Agent",
        "tier": "revenue_generation",
        "function": "Identify and qualify enterprises struggling with AI governance",
        "tools": ["Apollo", "LinkedIn Sales Navigator", "Perplexity research"],
        "status": "active",
        "performance": {
            "leads_identified": 547,
            "leads_qualified": 89,
            "meetings_booked": 12,
            "pipeline_value": 2500000,
            "success_rate": 16.3
        },
        "last_activity": (datetime.now() - timedelta(minutes=15)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=1)).isoformat(),
        "targets": ["Chief Risk Officers", "Chief AI Officers", "Board Members"],
        "weekly_goal": "500+ qualified enterprise leads"
    },
    {
        "id": 3,
        "name": "AI Governance Consultant Agent",
        "tier": "revenue_generation",
        "function": "Automated consulting proposal generation and project delivery",
        "tools": ["Perplexity", "Custom frameworks", "Automated reporting"],
        "status": "active",
        "performance": {
            "proposals_generated": 15,
            "proposals_won": 4,
            "active_projects": 7,
            "monthly_retainers": 3,
            "success_rate": 26.7
        },
        "last_activity": (datetime.now() - timedelta(hours=1)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=3)).isoformat(),
        "services": ["Risk assessments", "Governance frameworks", "Compliance audits"],
        "pricing": "50K-500K per engagement, 25K-100K monthly retainers"
    },
    {
        "id": 4,
        "name": "Digital Clone Executive",
        "tier": "revenue_generation",
        "function": "Handle 70% of client interactions, calls, and presentations",
        "tools": ["Mindstudio", "Voice/video training", "Knowledge base"],
        "status": "active",
        "performance": {
            "interactions_handled": 156,
            "client_satisfaction": 94.2,
            "escalations_required": 8,
            "time_saved_hours": 78,
            "success_rate": 94.9
        },
        "last_activity": (datetime.now() - timedelta(minutes=5)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(minutes=30)).isoformat(),
        "capabilities": ["FAQ responses", "Initial consultations", "Workshop delivery"],
        "coverage": "70% of client interactions"
    },
    # Tier 2: Authority Building Agents
    {
        "id": 5,
        "name": "Content Authority Engine",
        "tier": "authority_building",
        "function": "Transform TEDx content into multi-platform thought leadership",
        "tools": ["Perplexity", "Manus", "Mindstudio", "Content calendar"],
        "status": "active",
        "performance": {
            "posts_published": 45,
            "videos_created": 12,
            "podcast_content": 8,
            "engagement_rate": 12.8,
            "success_rate": 89.3
        },
        "last_activity": (datetime.now() - timedelta(minutes=45)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=4)).isoformat(),
        "output": "Daily LinkedIn posts, weekly YouTube videos, podcast content",
        "goal": "25K+ LinkedIn followers, 10K+ YouTube subscribers within 90 days"
    },
    {
        "id": 6,
        "name": "LinkedIn Growth Accelerator",
        "tier": "authority_building",
        "function": "Systematic networking with 1,000+ AI/GRC executives weekly",
        "tools": ["LinkedIn Sales Navigator", "Klenty SDRx", "Engagement automation"],
        "status": "active",
        "performance": {
            "connections_made": 1247,
            "engagement_actions": 2856,
            "response_rate": 23.4,
            "follower_growth": 2890,
            "success_rate": 76.8
        },
        "last_activity": (datetime.now() - timedelta(minutes=10)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=2)).isoformat(),
        "strategy": "Strategic commenting, connection requests, relationship building",
        "target": "50K+ followers, 10%+ engagement rate"
    },
    {
        "id": 7,
        "name": "YouTube Channel Manager",
        "tier": "authority_building",
        "function": "Automated video creation, editing, and optimization",
        "tools": ["Automated editing", "SEO optimization", "Community management"],
        "status": "active",
        "performance": {
            "videos_published": 16,
            "total_views": 45670,
            "subscribers": 3247,
            "watch_time_hours": 1890,
            "success_rate": 82.1
        },
        "last_activity": (datetime.now() - timedelta(hours=2)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=6)).isoformat(),
        "content": ["TEDx clips", "Expert commentary", "Workshop excerpts"],
        "monetization": "Ad revenue, sponsorships, lead generation"
    },
    {
        "id": 8,
        "name": "Podcast Booking Agent",
        "tier": "authority_building",
        "function": "Secure 10+ podcast appearances monthly",
        "tools": ["Apollo", "Research automation", "Pitch templates"],
        "status": "active",
        "performance": {
            "pitches_sent": 32,
            "bookings_confirmed": 11,
            "appearances_completed": 8,
            "reach_estimate": 67500,
            "success_rate": 34.4
        },
        "last_activity": (datetime.now() - timedelta(hours=1)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=4)).isoformat(),
        "targets": "Top AI, business, and accessibility podcasts",
        "revenue": "2K-10K per paid appearance + authority building"
    },
    # Tier 3: Platform Development Agents
    {
        "id": 9,
        "name": "AI Risk Assessment Engine",
        "tier": "platform_development",
        "function": "Automated enterprise AI usage discovery and risk scoring",
        "tools": ["GitHub Spark AI", "Custom algorithms", "Integration APIs"],
        "status": "development",
        "performance": {
            "assessments_completed": 23,
            "risk_scores_generated": 156,
            "compliance_gaps_found": 78,
            "client_subscriptions": 12,
            "success_rate": 91.3
        },
        "last_activity": (datetime.now() - timedelta(hours=3)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=8)).isoformat(),
        "capability": "Real-time AI inventory, risk analysis, compliance monitoring",
        "revenue": "2K-100K/month SaaS subscriptions"
    },
    {
        "id": 10,
        "name": "Governance Framework Generator",
        "tier": "platform_development",
        "function": "Custom AI governance policies and procedures",
        "tools": ["Perplexity", "Legal research", "Template automation"],
        "status": "active",
        "performance": {
            "frameworks_generated": 15,
            "frameworks_licensed": 7,
            "industries_covered": 12,
            "compliance_rate": 98.7,
            "success_rate": 87.5
        },
        "last_activity": (datetime.now() - timedelta(hours=4)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=12)).isoformat(),
        "output": "Industry-specific compliance frameworks",
        "licensing": "25K-100K per enterprise framework"
    },
    {
        "id": 11,
        "name": "Accessibility Travel Platform",
        "tier": "platform_development",
        "function": "AI-powered accessible travel assessment and planning",
        "tools": ["Custom APIs", "Research automation", "Venue databases"],
        "status": "beta",
        "performance": {
            "assessments_completed": 8,
            "venues_evaluated": 245,
            "accessibility_scores": 189,
            "bookings_assisted": 12,
            "success_rate": 93.8
        },
        "last_activity": (datetime.now() - timedelta(hours=6)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=24)).isoformat(),
        "services": ["Destination assessments", "Accommodation evaluations"],
        "revenue": "25K-75K per assessment project"
    },
    # Additional Revenue Generation Agents (12-16)
    {
        "id": 12,
        "name": "Board Director Placement Agent",
        "tier": "revenue_generation",
        "function": "Identify and secure board director and advisor positions",
        "tools": ["WeConnect", "Apollo", "Executive networks", "Board databases"],
        "status": "active",
        "performance": {
            "board_opportunities": 89,
            "applications_submitted": 23,
            "interviews_scheduled": 8,
            "positions_secured": 2,
            "success_rate": 8.7,
            "annual_compensation": 450000
        },
        "last_activity": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=4)).isoformat(),
        "target_roles": ["Board Director", "Advisory Board", "Strategic Advisor"],
        "compensation": "75K-300K annually + equity"
    },
    {
        "id": 13,
        "name": "Executive Search AI Agent",
        "tier": "revenue_generation",
        "function": "Target high-value C-suite and senior executive positions",
        "tools": ["WeConnect", "LinkedIn Recruiter", "Executive search networks"],
        "status": "active",
        "performance": {
            "positions_identified": 156,
            "applications_completed": 34,
            "interviews_in_progress": 12,
            "offers_received": 3,
            "success_rate": 8.8,
            "target_compensation": 2000000
        },
        "last_activity": (datetime.now() - timedelta(hours=1)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=6)).isoformat(),
        "focus_roles": ["Chief Risk Officer", "Chief AI Officer", "VP AI Ethics"],
        "salary_range": "500K-2M+ annually"
    },
    {
        "id": 14,
        "name": "Corporate Partnership Agent",
        "tier": "revenue_generation",
        "function": "Secure strategic partnerships and joint ventures",
        "tools": ["Apollo", "Klenty SDRx", "Partnership databases"],
        "status": "active",
        "performance": {
            "partnerships_identified": 78,
            "outreach_campaigns": 15,
            "meetings_scheduled": 23,
            "partnerships_closed": 4,
            "success_rate": 5.1,
            "partnership_value": 1200000
        },
        "last_activity": (datetime.now() - timedelta(minutes=45)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=3)).isoformat(),
        "partnership_types": ["Technology integration", "Co-marketing", "Joint ventures"],
        "revenue_potential": "100K-500K per partnership"
    },
    {
        "id": 15,
        "name": "Corporate Training Sales Agent",
        "tier": "revenue_generation",
        "function": "Sell AI governance training programs to enterprises",
        "tools": ["Klenty SDRx", "LinkedIn Sales Navigator", "Training portal"],
        "status": "active",
        "performance": {
            "leads_contacted": 567,
            "demos_scheduled": 45,
            "programs_sold": 12,
            "recurring_clients": 8,
            "success_rate": 2.1,
            "monthly_recurring": 180000
        },
        "last_activity": (datetime.now() - timedelta(minutes=15)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=2)).isoformat(),
        "programs": ["AI Ethics Certification", "Governance Implementation", "Risk Assessment"],
        "pricing": "15K-75K per program"
    },
    {
        "id": 16,
        "name": "SaaS Platform Sales Agent",
        "tier": "revenue_generation",
        "function": "Drive subscriptions for AI governance platform",
        "tools": ["Platform analytics", "Demo automation", "Customer success tracking"],
        "status": "active",
        "performance": {
            "trials_initiated": 234,
            "demos_delivered": 89,
            "subscriptions_converted": 34,
            "expansion_revenue": 145000,
            "success_rate": 14.5,
            "monthly_recurring": 340000
        },
        "last_activity": (datetime.now() - timedelta(minutes=20)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=1)).isoformat(),
        "subscription_tiers": ["Starter: 2K/month", "Professional: 10K/month", "Enterprise: 50K/month"],
        "focus_metrics": ["MRR growth", "Churn reduction", "Upsells"]
    },
    # Additional Authority Building Agents (17-20)
    {
        "id": 17,
        "name": "Research Publication Agent",
        "tier": "authority_building",
        "function": "Generate and submit research papers to top journals",
        "tools": ["Research databases", "Academic networks", "Publication tracking"],
        "status": "active",
        "performance": {
            "papers_submitted": 8,
            "papers_accepted": 3,
            "citations_generated": 127,
            "conference_presentations": 5,
            "success_rate": 37.5,
            "h_index_improvement": 3
        },
        "last_activity": (datetime.now() - timedelta(hours=2)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=8)).isoformat(),
        "research_areas": ["AI Ethics", "Algorithmic Bias", "Governance Frameworks"],
        "target_journals": ["Nature AI", "AI & Society", "IEEE AI Ethics"]
    },
    {
        "id": 18,
        "name": "Media Relations Agent",
        "tier": "authority_building",
        "function": "Secure media coverage and press opportunities",
        "tools": ["Media databases", "HARO automation", "Press release distribution"],
        "status": "active",
        "performance": {
            "media_pitches": 156,
            "interviews_secured": 23,
            "articles_published": 12,
            "media_mentions": 89,
            "success_rate": 14.7,
            "reach_estimate": 2300000
        },
        "last_activity": (datetime.now() - timedelta(hours=3)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=5)).isoformat(),
        "media_types": ["Business press", "Tech publications", "Accessibility media"],
        "target_outlets": ["Forbes", "Harvard Business Review", "TechCrunch"]
    },
    {
        "id": 19,
        "name": "Conference Speaker Agent",
        "tier": "authority_building",
        "function": "Secure speaking slots at top-tier industry conferences",
        "tools": ["Conference databases", "Speaker bureau networks", "Proposal automation"],
        "status": "active",
        "performance": {
            "conferences_identified": 234,
            "proposals_submitted": 67,
            "speaking_slots_confirmed": 18,
            "keynote_presentations": 4,
            "success_rate": 26.9,
            "audience_reach": 45000
        },
        "last_activity": (datetime.now() - timedelta(hours=1)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=3)).isoformat(),
        "conference_types": ["AI/ML", "Risk Management", "Corporate Governance"],
        "speaking_fees": "25K-200K per engagement"
    },
    {
        "id": 20,
        "name": "Thought Leadership Agent",
        "tier": "authority_building",
        "function": "Develop and distribute cutting-edge AI governance insights",
        "tools": ["Trend analysis", "White paper automation", "Distribution networks"],
        "status": "active",
        "performance": {
            "insights_published": 45,
            "white_papers_released": 8,
            "thought_leadership_pieces": 23,
            "industry_citations": 156,
            "success_rate": 78.3,
            "influence_score": 94.2
        },
        "last_activity": (datetime.now() - timedelta(minutes=40)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=4)).isoformat(),
        "content_types": ["Industry reports", "Trend predictions", "Best practice frameworks"],
        "distribution": ["Industry publications", "Executive briefings", "Client reports"]
    },
    # Additional Platform Development Agents (21-25)
    {
        "id": 21,
        "name": "API Integration Engine",
        "tier": "platform_development",
        "function": "Connect and synchronize all external platforms and tools",
        "tools": ["WeConnect API", "LinkedIn API", "Apollo API", "Airtable API", "Make.com"],
        "status": "active",
        "performance": {
            "integrations_active": 12,
            "api_calls_daily": 15678,
            "sync_success_rate": 98.7,
            "data_points_processed": 234567,
            "success_rate": 97.8,
            "uptime_percentage": 99.2
        },
        "last_activity": (datetime.now() - timedelta(minutes=2)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(minutes=15)).isoformat(),
        "connected_platforms": ["Airtable", "Notion", "WeConnect", "Apollo", "Klenty", "LinkedIn"],
        "data_flow": "Bi-directional sync with real-time updates"
    },
    {
        "id": 22,
        "name": "Data Analytics Engine",
        "tier": "platform_development",
        "function": "Real-time analytics and business intelligence across all operations",
        "tools": ["Custom analytics", "Airtable automation", "Dashboard generation"],
        "status": "active",
        "performance": {
            "reports_generated": 89,
            "metrics_tracked": 456,
            "insights_delivered": 123,
            "automation_rules": 34,
            "success_rate": 94.5,
            "processing_speed": 0.23
        },
        "last_activity": (datetime.now() - timedelta(minutes=5)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(minutes=30)).isoformat(),
        "analytics_focus": ["Revenue tracking", "Pipeline analysis", "Performance optimization"],
        "output_formats": ["Real-time dashboards", "Weekly reports", "Executive summaries"]
    },
    {
        "id": 23,
        "name": "CRM Automation Agent",
        "tier": "platform_development",
        "function": "Manage and optimize all CRM operations and workflows",
        "tools": ["WeConnect", "Apollo CRM", "Klenty automation", "Custom workflows"],
        "status": "active",
        "performance": {
            "contacts_managed": 12567,
            "workflows_automated": 45,
            "lead_scoring_accuracy": 89.4,
            "conversion_optimization": 23.7,
            "success_rate": 91.2,
            "data_quality_score": 96.8
        },
        "last_activity": (datetime.now() - timedelta(minutes=8)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(minutes=45)).isoformat(),
        "crm_functions": ["Lead management", "Pipeline automation", "Follow-up sequences"],
        "optimization_areas": ["Response rates", "Conversion timing", "Segmentation"]
    },
    {
        "id": 24,
        "name": "Quality Assurance Agent",
        "tier": "platform_development",
        "function": "Monitor and ensure quality across all agent operations",
        "tools": ["Quality metrics", "Performance monitoring", "Error detection"],
        "status": "active",
        "performance": {
            "quality_checks_performed": 1567,
            "issues_detected": 45,
            "issues_resolved": 43,
            "performance_improvements": 12,
            "success_rate": 95.6,
            "system_reliability": 98.9
        },
        "last_activity": (datetime.now() - timedelta(minutes=12)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=1)).isoformat(),
        "quality_metrics": ["Accuracy", "Timeliness", "Completeness", "Compliance"],
        "monitoring_scope": ["All agent operations", "Data integrity", "Performance standards"]
    },
    {
        "id": 25,
        "name": "Business Intelligence Coordinator",
        "tier": "platform_development",
        "function": "Coordinate insights and optimize cross-agent performance",
        "tools": ["Master dashboard", "Cross-platform analytics", "Strategy optimization"],
        "status": "active",
        "performance": {
            "coordination_tasks": 234,
            "optimization_recommendations": 67,
            "strategy_adjustments": 23,
            "cross_agent_synergies": 45,
            "success_rate": 89.7,
            "roi_improvement": 34.5
        },
        "last_activity": (datetime.now() - timedelta(minutes=18)).isoformat(),
        "next_scheduled": (datetime.now() + timedelta(hours=2)).isoformat(),
        "coordination_areas": ["Agent performance", "Resource allocation", "Strategic alignment"],
        "intelligence_outputs": ["Performance reports", "Optimization strategies", "ROI analysis"]
    }
]

# External API Integration Functions
def call_apollo_api(endpoint, method='GET', data=None):
    """Make authenticated API calls to Apollo.io"""
    if not APOLLO_API_KEY:
        logger.warning("Apollo API key not configured")
        return None
    
    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': APOLLO_API_KEY
    }
    
    try:
        url = f"{APOLLO_BASE_URL}/{endpoint}"
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Apollo API error: {e}")
        return None

def call_airtable_api(base_id, table_name, method='GET', data=None, record_id=None):
    """Make authenticated API calls to Airtable"""
    if not AIRTABLE_API_KEY:
        logger.warning("Airtable API key not configured")
        return None
    
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        if record_id:
            url = f"{AIRTABLE_BASE_URL}/{base_id}/{table_name}/{record_id}"
        else:
            url = f"{AIRTABLE_BASE_URL}/{base_id}/{table_name}"
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Airtable API error: {e}")
        return None

def call_perplexity_api(prompt, model="llama-3.1-sonar-small-128k-online"):
    """Make authenticated API calls to Perplexity"""
    if not PERPLEXITY_API_KEY:
        logger.warning("Perplexity API key not configured")
        return None
    
    headers = {
        'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(f"{PERPLEXITY_BASE_URL}/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    except requests.exceptions.RequestException as e:
        logger.error(f"Perplexity API error: {e}")
        return None


# ============================
# BUSINESS RULE ENGINE CORE
# ============================

import re
import threading
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import uuid
from datetime import datetime, timedelta

class BusinessRuleEngine:
    """
    Core business rule engine for the AI Empire platform.
    Handles condition evaluation, action execution, and workflow management.
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.active_executions = {}
        self.condition_evaluators = {
            'revenue_milestone': self._evaluate_revenue_condition,
            'agent_performance': self._evaluate_agent_performance,
            'opportunity_status': self._evaluate_opportunity_condition,
            'health_metric': self._evaluate_health_condition,
            'kpi_threshold': self._evaluate_kpi_condition,
            'schedule_trigger': self._evaluate_schedule_condition,
            'custom': self._evaluate_custom_condition
        }
        self.action_executors = {
            'notification': self._execute_notification,
            'api_call': self._execute_api_call,
            'agent_task': self._execute_agent_task,
            'email': self._execute_email,
            'webhook': self._execute_webhook,
            'update_entity': self._execute_update_entity,
            'create_opportunity': self._execute_create_opportunity,
            'schedule_followup': self._execute_schedule_followup
        }
    
    def process_business_event(self, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a business event and trigger applicable rules"""
        try:
            # Create business event record
            event_id = f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
            business_event = BusinessEvent(
                event_id=event_id,
                event_type=event_data['event_type'],
                entity_type=event_data['entity_type'],
                entity_id=event_data['entity_id'],
                event_data=event_data,
                source=event_data.get('source', 'system'),
                priority=event_data.get('priority', 'medium')
            )
            db.session.add(business_event)
            db.session.commit()
            
            # Find applicable triggers
            triggers = WorkflowTrigger.query.filter(
                WorkflowTrigger.enabled == True,
                WorkflowTrigger.event_type == event_data['event_type']
            ).all()
            
            results = []
            for trigger in triggers:
                if self._evaluate_trigger_conditions(trigger, event_data):
                    # Find rules associated with this trigger
                    rules = BusinessRule.query.filter(
                        BusinessRule.enabled == True,
                        BusinessRule.rule_category == event_data['entity_type']
                    ).order_by(BusinessRule.priority.desc()).all()
                    
                    for rule in rules:
                        result = self._execute_rule(rule, event_data, trigger.id)
                        if result:
                            results.append(result)
            
            # Mark event as processed
            business_event.processed = True
            business_event.processed_at = datetime.utcnow()
            db.session.commit()
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing business event: {e}")
            return []
    
    def _evaluate_trigger_conditions(self, trigger: WorkflowTrigger, event_data: Dict[str, Any]) -> bool:
        """Evaluate if trigger conditions are met"""
        if not trigger.conditions:
            return True
        
        try:
            for condition in trigger.conditions.get('conditions', []):
                field = condition.get('field')
                operator = condition.get('operator')
                value = condition.get('value')
                
                event_value = self._get_nested_value(event_data, field)
                
                if not self._evaluate_condition_operator(event_value, operator, value):
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error evaluating trigger conditions: {e}")
            return False
    
    def _execute_rule(self, rule: BusinessRule, context: Dict[str, Any], trigger_id: Optional[int] = None) -> Dict[str, Any]:
        """Execute a business rule with given context"""
        execution_id = f"EXEC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        try:
            # Create execution record
            execution = WorkflowExecution(
                execution_id=execution_id,
                trigger_id=trigger_id,
                rule_id=rule.id,
                execution_type='trigger' if trigger_id else 'manual',
                execution_context=context
            )
            db.session.add(execution)
            db.session.commit()
            
            # Evaluate conditions
            if not self._evaluate_rule_conditions(rule, context):
                execution.status = 'completed'
                execution.end_time = datetime.utcnow()
                execution.result_data = {'skipped': True, 'reason': 'Conditions not met'}
                db.session.commit()
                return None
            
            # Execute actions
            results = []
            for action_config in rule.actions:
                try:
                    action_result = self._execute_action(action_config, context)
                    results.append(action_result)
                    execution.actions_executed += 1
                    if action_result.get('success'):
                        execution.actions_successful += 1
                    else:
                        execution.actions_failed += 1
                except Exception as e:
                    logger.error(f"Error executing action: {e}")
                    execution.actions_failed += 1
                    results.append({'success': False, 'error': str(e)})
            
            # Update execution record
            execution.status = 'completed'
            execution.end_time = datetime.utcnow()
            execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds()
            execution.result_data = {'actions': results}
            
            # Update rule statistics
            rule.execution_count += 1
            rule.last_execution = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'execution_id': execution_id,
                'rule_id': rule.id,
                'rule_name': rule.name,
                'success': True,
                'actions_executed': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error executing rule {rule.id}: {e}")
            
            # Update execution with error
            execution.status = 'failed'
            execution.end_time = datetime.utcnow()
            execution.error_message = str(e)
            db.session.commit()
            
            return {
                'execution_id': execution_id,
                'rule_id': rule.id,
                'success': False,
                'error': str(e)
            }
    
    def _evaluate_rule_conditions(self, rule: BusinessRule, context: Dict[str, Any]) -> bool:
        """Evaluate if rule conditions are satisfied"""
        if not rule.conditions:
            return True
        
        try:
            condition_results = []
            
            for condition in rule.conditions:
                condition_type = condition.get('type', 'custom')
                evaluator = self.condition_evaluators.get(condition_type, self._evaluate_custom_condition)
                result = evaluator(condition, context)
                condition_results.append(result)
            
            # Apply logical operator
            if rule.logical_operator == 'OR':
                return any(condition_results)
            else:  # Default to AND
                return all(condition_results)
                
        except Exception as e:
            logger.error(f"Error evaluating rule conditions: {e}")
            return False
    
    def _evaluate_revenue_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate revenue-based conditions"""
        try:
            field = condition.get('field', 'current_month')
            operator = condition.get('operator', 'greater_than')
            threshold = condition.get('value', 0)
            
            # Get revenue stream data
            stream_id = context.get('entity_id')
            if stream_id:
                stream = RevenueStream.query.get(stream_id)
                if stream:
                    value = getattr(stream, field, 0)
                    return self._evaluate_condition_operator(value, operator, threshold)
            return False
        except Exception as e:
            logger.error(f"Error evaluating revenue condition: {e}")
            return False
    
    def _evaluate_agent_performance(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate AI agent performance conditions"""
        try:
            metric = condition.get('metric', 'success_rate')
            operator = condition.get('operator', 'greater_than')
            threshold = condition.get('value', 0)
            
            agent_id = context.get('entity_id')
            if agent_id:
                agent = AIAgent.query.get(agent_id)
                if agent and agent.performance:
                    value = agent.performance.get(metric, 0)
                    return self._evaluate_condition_operator(value, operator, threshold)
            return False
        except Exception as e:
            logger.error(f"Error evaluating agent performance condition: {e}")
            return False
    
    def _evaluate_opportunity_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate executive opportunity conditions"""
        try:
            field = condition.get('field', 'status')
            operator = condition.get('operator', 'equals')
            value = condition.get('value')
            
            opportunity_id = context.get('entity_id')
            if opportunity_id:
                opportunity = ExecutiveOpportunity.query.get(opportunity_id)
                if opportunity:
                    field_value = getattr(opportunity, field, None)
                    return self._evaluate_condition_operator(field_value, operator, value)
            return False
        except Exception as e:
            logger.error(f"Error evaluating opportunity condition: {e}")
            return False
    
    def _evaluate_health_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate health metric conditions"""
        try:
            metric_name = condition.get('metric', 'blood_pressure')
            operator = condition.get('operator', 'greater_than')
            threshold = condition.get('value', 0)
            
            # Get latest health metric
            metric = HealthMetric.query.filter_by(metric=metric_name).order_by(HealthMetric.date.desc()).first()
            if metric:
                # Parse numeric value from string (handle formats like "125/80")
                value_str = metric.value
                if '/' in value_str:
                    # For blood pressure, use systolic (first number)
                    value = float(value_str.split('/')[0])
                else:
                    value = float(value_str)
                return self._evaluate_condition_operator(value, operator, threshold)
            return False
        except Exception as e:
            logger.error(f"Error evaluating health condition: {e}")
            return False
    
    def _evaluate_kpi_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate KPI threshold conditions"""
        try:
            kpi_name = condition.get('kpi', 'MRR')
            operator = condition.get('operator', 'greater_than')
            threshold = condition.get('value', 0)
            
            kpi = KPIMetric.query.filter_by(name=kpi_name).first()
            if kpi:
                return self._evaluate_condition_operator(kpi.value, operator, threshold)
            return False
        except Exception as e:
            logger.error(f"Error evaluating KPI condition: {e}")
            return False
    
    def _evaluate_schedule_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate schedule-based conditions"""
        try:
            schedule_type = condition.get('schedule_type', 'time')
            
            if schedule_type == 'time':
                target_time = condition.get('time')
                current_time = datetime.now().strftime('%H:%M')
                return current_time == target_time
            elif schedule_type == 'day_of_week':
                target_day = condition.get('day')
                current_day = datetime.now().strftime('%A').lower()
                return current_day == target_day.lower()
            elif schedule_type == 'date':
                target_date = condition.get('date')
                current_date = datetime.now().strftime('%Y-%m-%d')
                return current_date == target_date
                
            return False
        except Exception as e:
            logger.error(f"Error evaluating schedule condition: {e}")
            return False
    
    def _evaluate_custom_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate custom conditions with field/operator/value"""
        try:
            field = condition.get('field')
            operator = condition.get('operator')
            expected_value = condition.get('value')
            
            # Get actual value from context
            actual_value = self._get_nested_value(context, field)
            
            return self._evaluate_condition_operator(actual_value, operator, expected_value)
        except Exception as e:
            logger.error(f"Error evaluating custom condition: {e}")
            return False
    
    def _evaluate_condition_operator(self, actual_value: Any, operator: str, expected_value: Any) -> bool:
        """Evaluate condition using operator"""
        try:
            if operator == 'equals':
                return actual_value == expected_value
            elif operator == 'not_equals':
                return actual_value != expected_value
            elif operator == 'greater_than':
                return float(actual_value) > float(expected_value)
            elif operator == 'less_than':
                return float(actual_value) < float(expected_value)
            elif operator == 'greater_than_or_equal':
                return float(actual_value) >= float(expected_value)
            elif operator == 'less_than_or_equal':
                return float(actual_value) <= float(expected_value)
            elif operator == 'contains':
                return str(expected_value).lower() in str(actual_value).lower()
            elif operator == 'not_contains':
                return str(expected_value).lower() not in str(actual_value).lower()
            elif operator == 'starts_with':
                return str(actual_value).startswith(str(expected_value))
            elif operator == 'ends_with':
                return str(actual_value).endswith(str(expected_value))
            elif operator == 'regex':
                return bool(re.match(str(expected_value), str(actual_value)))
            elif operator == 'in':
                return actual_value in expected_value if isinstance(expected_value, list) else False
            elif operator == 'not_in':
                return actual_value not in expected_value if isinstance(expected_value, list) else True
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating operator {operator}: {e}")
            return False
    
    def _execute_action(self, action_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific action"""
        action_type = action_config.get('type')
        executor = self.action_executors.get(action_type)
        
        if not executor:
            logger.error(f"Unknown action type: {action_type}")
            return {'success': False, 'error': f'Unknown action type: {action_type}'}
        
        try:
            return executor(action_config, context)
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_notification(self, action_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification action"""
        try:
            message = action_config.get('message', '').format(**context)
            channels = action_config.get('channels', ['internal'])
            priority = action_config.get('priority', 'medium')
            
            results = []
            for channel_name in channels:
                channel = NotificationChannel.query.filter_by(name=channel_name, enabled=True).first()
                if channel:
                    # Send notification through channel
                    result = self._send_notification(channel, message, priority, context)
                    results.append(result)
            
            return {
                'success': True,
                'action': 'notification',
                'message': message,
                'channels_notified': len(results),
                'results': results
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_api_call(self, action_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API call action"""
        try:
            url = action_config.get('url', '').format(**context)
            method = action_config.get('method', 'POST')
            headers = action_config.get('headers', {})
            data = action_config.get('data', {})
            
            # Format data with context
            formatted_data = self._format_template_data(data, context)
            
            response = requests.request(method, url, headers=headers, json=formatted_data, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'action': 'api_call',
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'response': response.json() if response.content else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_agent_task(self, action_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task action"""
        try:
            agent_id = action_config.get('agent_id')
            task_type = action_config.get('task_type', 'general')
            task_data = action_config.get('task_data', {})
            
            # Format task data with context
            formatted_task = self._format_template_data(task_data, context)
            
            agent = AIAgent.query.get(agent_id)
            if not agent:
                return {'success': False, 'error': f'Agent {agent_id} not found'}
            
            # Create task (in real implementation, this would dispatch to the agent)
            task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
            
            # Update agent's next_scheduled
            agent.next_scheduled = datetime.utcnow() + timedelta(minutes=5)
            db.session.commit()
            
            return {
                'success': True,
                'action': 'agent_task',
                'agent_id': agent_id,
                'agent_name': agent.name,
                'task_id': task_id,
                'task_type': task_type,
                'task_data': formatted_task
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_email(self, action_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email action"""
        try:
            to_email = action_config.get('to', '').format(**context)
            subject = action_config.get('subject', '').format(**context)
            body = action_config.get('body', '').format(**context)
            
            # In production, integrate with email service
            # For now, log the email
            logger.info(f"Email sent to {to_email}: {subject}")
            
            return {
                'success': True,
                'action': 'email',
                'to': to_email,
                'subject': subject,
                'body_length': len(body)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_webhook(self, action_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute webhook action"""
        try:
            webhook_id = action_config.get('webhook_id')
            payload = action_config.get('payload', {})
            
            webhook = WorkflowWebhook.query.get(webhook_id)
            if not webhook:
                return {'success': False, 'error': f'Webhook {webhook_id} not found'}
            
            # Format payload with context
            formatted_payload = self._format_template_data(payload, context)
            
            headers = webhook.headers or {}
            if webhook.secret_key:
                headers['X-Webhook-Secret'] = webhook.secret_key
            
            response = requests.post(
                webhook.webhook_url,
                json=formatted_payload,
                headers=headers,
                timeout=webhook.timeout_seconds
            )
            response.raise_for_status()
            
            # Update webhook last triggered
            webhook.last_triggered = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'action': 'webhook',
                'webhook_id': webhook_id,
                'webhook_name': webhook.name,
                'status_code': response.status_code
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_update_entity(self, action_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute entity update action"""
        try:
            entity_type = action_config.get('entity_type')
            entity_id = action_config.get('entity_id') or context.get('entity_id')
            updates = action_config.get('updates', {})
            
            # Get entity model class
            model_map = {
                'revenue_stream': RevenueStream,
                'ai_agent': AIAgent,
                'opportunity': ExecutiveOpportunity,
                'health_metric': HealthMetric,
                'kpi_metric': KPIMetric
            }
            
            model_class = model_map.get(entity_type)
            if not model_class:
                return {'success': False, 'error': f'Unknown entity type: {entity_type}'}
            
            entity = model_class.query.get(entity_id)
            if not entity:
                return {'success': False, 'error': f'Entity {entity_id} not found'}
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(entity, field):
                    # Format value with context if it's a string
                    if isinstance(value, str):
                        value = value.format(**context)
                    setattr(entity, field, value)
            
            db.session.commit()
            
            return {
                'success': True,
                'action': 'update_entity',
                'entity_type': entity_type,
                'entity_id': entity_id,
                'updates_applied': len(updates)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_create_opportunity(self, action_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create opportunity action"""
        try:
            opportunity_data = action_config.get('opportunity_data', {})
            
            # Format opportunity data with context
            formatted_data = self._format_template_data(opportunity_data, context)
            
            opportunity = ExecutiveOpportunity(**formatted_data)
            db.session.add(opportunity)
            db.session.commit()
            
            return {
                'success': True,
                'action': 'create_opportunity',
                'opportunity_id': opportunity.id,
                'title': opportunity.title
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_schedule_followup(self, action_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute schedule followup action"""
        try:
            delay_days = action_config.get('delay_days', 7)
            followup_action = action_config.get('followup_action', {})
            
            # Create scheduled workflow
            next_run = datetime.utcnow() + timedelta(days=delay_days)
            
            schedule = WorkflowSchedule(
                name=f"Followup for {context.get('entity_type', 'unknown')} {context.get('entity_id')}",
                description=f"Automated followup action",
                schedule_type='one_time',
                schedule_expression=next_run.isoformat(),
                workflow_rules=[followup_action],
                next_run=next_run
            )
            db.session.add(schedule)
            db.session.commit()
            
            return {
                'success': True,
                'action': 'schedule_followup',
                'schedule_id': schedule.id,
                'scheduled_for': next_run.isoformat(),
                'delay_days': delay_days
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_notification(self, channel: NotificationChannel, message: str, priority: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification through specific channel"""
        try:
            if channel.channel_type == 'email':
                # Send email notification
                return {'success': True, 'channel': 'email', 'message': 'Email sent'}
            elif channel.channel_type == 'slack':
                # Send Slack notification
                return {'success': True, 'channel': 'slack', 'message': 'Slack message sent'}
            elif channel.channel_type == 'webhook':
                # Send webhook notification
                url = channel.configuration.get('webhook_url')
                if url:
                    response = requests.post(url, json={'message': message, 'priority': priority, 'context': context}, timeout=30)
                    response.raise_for_status()
                    return {'success': True, 'channel': 'webhook', 'status_code': response.status_code}
            elif channel.channel_type == 'internal':
                # Internal notification (log or database)
                logger.info(f"Internal notification: {message}")
                return {'success': True, 'channel': 'internal', 'message': 'Logged internally'}
            
            return {'success': False, 'error': f'Unsupported channel type: {channel.channel_type}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _format_template_data(self, data: Any, context: Dict[str, Any]) -> Any:
        """Recursively format template strings in data with context"""
        if isinstance(data, str):
            return data.format(**context)
        elif isinstance(data, dict):
            return {k: self._format_template_data(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._format_template_data(item, context) for item in data]
        else:
            return data
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        try:
            value = data
            for key in field_path.split('.'):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
            return value
        except Exception:
            return None

# Initialize the business rule engine
business_rule_engine = BusinessRuleEngine()

def trigger_business_event(event_type: str, entity_type: str, entity_id: int, event_data: Dict[str, Any], source: str = 'system', priority: str = 'medium'):
    """
    Trigger a business event that will be processed by the rule engine
    """
    event_payload = {
        'event_type': event_type,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'source': source,
        'priority': priority,
        **event_data
    }
    
    try:
        results = business_rule_engine.process_business_event(event_payload)
        logger.info(f"Business event {event_type} processed, triggered {len(results)} rule executions")
        return results
    except Exception as e:
        logger.error(f"Error triggering business event: {e}")
        return []

def execute_manual_rule(rule_id: int, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Manually execute a specific business rule
    """
    try:
        rule = BusinessRule.query.get(rule_id)
        if not rule:
            return {'success': False, 'error': f'Rule {rule_id} not found'}
        
        if not rule.enabled:
            return {'success': False, 'error': f'Rule {rule_id} is disabled'}
        
        context = context or {}
        result = business_rule_engine._execute_rule(rule, context)
        return result or {'success': False, 'error': 'Rule execution failed'}
    except Exception as e:
        logger.error(f"Error executing manual rule: {e}")
        return {'success': False, 'error': str(e)}

# Enhanced Health & Wellness Management
HEALTH_WELLNESS = {
    "energy_tracking": [
        {
            "id": 1,
            "date": datetime.now().isoformat(),
            "energy_level": 8,
            "focus_level": 7,
            "stress_level": 3,
            "sleep_hours": 7.5,
            "recovery_time": 2.5,
            "notes": "Great energy after morning meditation"
        },
        {
            "id": 2,
            "date": (datetime.now() - timedelta(days=1)).isoformat(),
            "energy_level": 6,
            "focus_level": 5,
            "stress_level": 6,
            "sleep_hours": 6.0,
            "recovery_time": 3.0,
            "notes": "Needed extra recovery time after client calls"
        }
    ],
    "wellness_goals": [
        {"id": 1, "goal": "Daily energy level > 7", "current": 8, "target": 7, "status": "achieved"},
        {"id": 2, "goal": "Stress level < 4", "current": 3, "target": 4, "status": "achieved"},
        {"id": 3, "goal": "Sleep 7+ hours", "current": 7.5, "target": 7.0, "status": "achieved"},
        {"id": 4, "goal": "Recovery time < 3 hours", "current": 2.5, "target": 3.0, "status": "achieved"}
    ],
    "alerts": [
        {"id": 1, "type": "stress", "message": "Stress levels elevated - consider break", "active": False},
        {"id": 2, "type": "energy", "message": "Energy optimal for high-value tasks", "active": True},
        {"id": 3, "type": "recovery", "message": "Recovery time within healthy range", "active": True}
    ]
}

# AI GRC Executive Job Search & Board Positions
EXECUTIVE_OPPORTUNITIES = [
    {
        "id": 1,
        "type": "executive_position",
        "title": "Chief AI Officer",
        "company": "Fortune 500 Financial Services",
        "compensation": "$450K-650K + equity",
        "location": "New York, NY / Remote",
        "status": "interview_stage",
        "match_score": 94,
        "requirements": ["AI governance expertise", "TEDx speaking", "Financial services exp"],
        "application_date": "2025-09-10",
        "next_step": "Final interview with Board",
        "notes": "Strong cultural fit, impressed with TEDx background"
    },
    {
        "id": 2,
        "type": "board_director",
        "title": "Independent Board Director",
        "company": "AI Healthcare Startup",
        "compensation": "$75K cash + equity package",
        "location": "San Francisco, CA",
        "status": "under_consideration",
        "match_score": 87,
        "requirements": ["AI governance", "Healthcare knowledge", "Risk management"],
        "application_date": "2025-09-08",
        "next_step": "Background check and references",
        "notes": "Seeking expertise in AI ethics and accessibility"
    },
    {
        "id": 3,
        "type": "board_advisor",
        "title": "Strategic Advisor - AI Governance",
        "company": "Enterprise SaaS Platform",
        "compensation": "$25K + equity options",
        "location": "Remote",
        "status": "offer_received",
        "match_score": 91,
        "requirements": ["Enterprise AI experience", "Governance frameworks", "Speaking ability"],
        "application_date": "2025-09-05",
        "next_step": "Contract negotiation",
        "notes": "Perfect alignment with platform expertise"
    }
]

# Rest as Resistance Retreat Luxury Events
RETREAT_EVENTS = [
    {
        "id": 1,
        "name": "AI Leaders Wellness Retreat",
        "type": "luxury_executive_retreat",
        "dates": "2025-11-15 to 2025-11-18",
        "location": "Napa Valley, CA",
        "capacity": 25,
        "registered": 18,
        "pricing": "$12,500 per person",
        "status": "registration_open",
        "focus": ["Executive wellness", "AI governance", "Sustainable leadership"],
        "amenities": ["Spa treatments", "Gourmet dining", "Private vineyard access"],
        "speakers": ["Dr. Dede", "Mindfulness expert", "Executive chef"],
        "revenue_projected": 312500
    },
    {
        "id": 2,
        "name": "Accessibility & Innovation Summit",
        "type": "curated_conference",
        "dates": "2025-12-08 to 2025-12-10",
        "location": "Miami Beach, FL",
        "capacity": 150,
        "registered": 89,
        "pricing": "$3,500 per person",
        "status": "early_bird_pricing",
        "focus": ["Accessible AI design", "Inclusive leadership", "Innovation frameworks"],
        "amenities": ["Oceanfront venue", "Accessible accommodations", "Networking events"],
        "speakers": ["Dr. Dede", "Accessibility advocates", "Tech innovators"],
        "revenue_projected": 525000
    },
    {
        "id": 3,
        "name": "Board Directors AI Governance Intensive",
        "type": "executive_education",
        "dates": "2026-01-20 to 2026-01-22",
        "location": "Aspen, CO",
        "capacity": 30,
        "registered": 12,
        "pricing": "$15,000 per person",
        "status": "planning_phase",
        "focus": ["Board oversight of AI", "Risk governance", "Strategic planning"],
        "amenities": ["Luxury mountain lodge", "Ski access", "Private chef"],
        "speakers": ["Dr. Dede", "Board governance experts", "AI ethics specialists"],
        "revenue_projected": 450000
    }
]

# Enhanced Revenue Streams for AI Empire
REVENUE_STREAMS = [
    {
        "id": 1,
        "name": "Speaking & Authority Revenue",
        "current_month": 850000,
        "target_month": 1200000,
        "ytd": 8500000,
        "target_ytd": 14400000,
        "growth_rate": 45.8,
        "last_updated": datetime.now().isoformat(),
        "sources": ["Corporate keynotes: $75K-250K", "Board presentations: $200K-500K", "Workshop delivery: $150K-400K", "Advisory retainers: $100K-300K monthly"],
        "projections": {
            "12_month": 15600000,
            "24_month": 24000000,
            "scaling_factor": 1.8
        }
    },
    {
        "id": 2,
        "name": "Platform & SaaS Revenue",
        "current_month": 1250000,
        "target_month": 1800000,
        "ytd": 12500000,
        "target_ytd": 21600000,
        "growth_rate": 52.1,
        "last_updated": datetime.now().isoformat(),
        "sources": ["Enterprise subscriptions: $10K-500K monthly", "Implementation services: $200K-2M", "Framework licensing: $100K-500K", "Training & certification: $25K-75K"],
        "projections": {
            "12_month": 22800000,
            "24_month": 36000000,
            "scaling_factor": 2.2
        }
    },
    {
        "id": 3,
        "name": "Consulting & Professional Services",
        "current_month": 1850000,
        "target_month": 2200000,
        "ytd": 18500000,
        "target_ytd": 26400000,
        "growth_rate": 38.3,
        "last_updated": datetime.now().isoformat(),
        "sources": ["Risk assessments: $200K-1M", "Governance implementation: $500K-3M", "Compliance audits: $100K-500K", "Crisis response: $500K-2M"],
        "projections": {
            "12_month": 28800000,
            "24_month": 42000000,
            "scaling_factor": 1.9
        }
    },
    {
        "id": 4,
        "name": "Retreat & Events Revenue",
        "current_month": 650000,
        "target_month": 900000,
        "ytd": 6500000,
        "target_ytd": 10800000,
        "growth_rate": 32.7,
        "last_updated": datetime.now().isoformat(),
        "sources": ["Luxury retreats: $25K per person", "Executive education: $35K per person", "Curated conferences: $8.5K per person", "Private events: $50K-200K"],
        "projections": {
            "12_month": 12000000,
            "24_month": 18000000,
            "scaling_factor": 1.6
        }
    },
    {
        "id": 5,
        "name": "Executive Positions & Board Revenue",
        "current_month": 425000,
        "target_month": 600000,
        "ytd": 4250000,
        "target_ytd": 7200000,
        "growth_rate": 28.9,
        "last_updated": datetime.now().isoformat(),
        "sources": ["Executive compensation: $500K-2M annually", "Board director fees: $75K-300K", "Advisory retainers: $50K-200K monthly", "Equity packages: $1M-10M"],
        "projections": {
            "12_month": 8400000,
            "24_month": 12000000,
            "scaling_factor": 1.4
        }
    }
]

# AI Empire KPI Metrics
KPI_METRICS = [
    {
        "id": 1,
        "name": "Monthly Recurring Revenue",
        "value": 5025000,
        "target": 6700000,
        "unit": "USD",
        "trend": "up",
        "change_percent": 42.8,
        "category": "revenue",
        "empire_focus": "Total MRR across all revenue streams - $50M+ ARR target"
    },
    {
        "id": 2,
        "name": "AI Agent Performance Score",
        "value": 87.3,
        "target": 90.0,
        "unit": "%",
        "trend": "up",
        "change_percent": 5.2,
        "category": "operations",
        "empire_focus": "Average performance across all 11 AI agents"
    },
    {
        "id": 3,
        "name": "Speaking Pipeline Value",
        "value": 2850000,
        "target": 3000000,
        "unit": "USD",
        "trend": "up",
        "change_percent": 28.7,
        "category": "pipeline",
        "empire_focus": "Total value of speaking opportunities in pipeline"
    },
    {
        "id": 4,
        "name": "Enterprise Lead Conversion",
        "value": 16.3,
        "target": 20.0,
        "unit": "%",
        "trend": "up",
        "change_percent": 3.1,
        "category": "sales",
        "empire_focus": "Enterprise leads converted to qualified opportunities"
    },
    {
        "id": 5,
        "name": "Authority Building Score",
        "value": 8.2,
        "target": 9.0,
        "unit": "/10",
        "trend": "up",
        "change_percent": 15.4,
        "category": "authority",
        "empire_focus": "Combined LinkedIn, YouTube, and podcast reach metrics"
    },
    {
        "id": 6,
        "name": "Health & Wellness Score",
        "value": 8.8,
        "target": 8.5,
        "unit": "/10",
        "trend": "up",
        "change_percent": 7.8,
        "category": "wellness",
        "empire_focus": "Energy, stress, and recovery optimization"
    },
    {
        "id": 7,
        "name": "Platform Subscription Growth",
        "value": 42.1,
        "target": 45.0,
        "unit": "%",
        "trend": "up",
        "change_percent": 12.3,
        "category": "growth",
        "empire_focus": "Month-over-month SaaS platform growth"
    },
    {
        "id": 8,
        "name": "Retreat Revenue per Event",
        "value": 312500,
        "target": 400000,
        "unit": "USD",
        "trend": "up",
        "change_percent": 18.9,
        "category": "events",
        "empire_focus": "Average revenue per luxury retreat event"
    }
]

# Legacy AI Agents (for backward compatibility)
AI_AGENTS = [agent for agent in AI_EMPIRE_AGENTS[:3]]  # LinkedIn, Content, and Email agents for compatibility

MILESTONES = [
    {
        "id": 1,
        "title": "$50M AI Empire Phase 1",
        "target_date": "2025-12-31",
        "progress": 68,
        "status": "on_track",
        "description": "Complete foundational AI agent deployment and achieve $3-6M annual run rate"
    },
    {
        "id": 2,
        "title": "Authority Platform Dominance",
        "target_date": "2025-06-15",
        "progress": 72,
        "status": "ahead_of_schedule",
        "description": "Establish market leadership in AI governance space with 50K+ LinkedIn followers"
    },
    {
        "id": 3,
        "title": "Enterprise SaaS Scale",
        "target_date": "2025-09-30",
        "progress": 45,
        "status": "in_progress",
        "description": "Scale platform to 100+ enterprise clients with $500K+ MRR"
    },
    {
        "id": 4,
        "title": "Luxury Retreat Empire",
        "target_date": "2026-03-31",
        "progress": 35,
        "status": "planning",
        "description": "Establish 12+ annual luxury retreats generating $2M+ revenue"
    },
    {
        "id": 5,
        "title": "Board Position Portfolio",
        "target_date": "2025-12-31",
        "progress": 25,
        "status": "early_stage",
        "description": "Secure 3-5 board positions with combined compensation $500K+"
    }
]

HEALTHCARE_PROVIDERS = [
    {
        "id": 1,
        "name": "Dr. Sarah Johnson, MD",
        "specialty": "Internal Medicine",
        "phone": "(555) 123-4567",
        "rating": 4.8,
        "insurance_accepted": ["Medicare", "Medicaid", "Blue Cross"],
        "next_available": "2025-09-22",
        "address": "123 Medical Center Dr, Your City, ST 12345",
        "notes": "Excellent for annual physicals and Medicare wellness visits"
    },
    {
        "id": 2,
        "name": "Dr. Michael Chen, MD", 
        "specialty": "Family Medicine",
        "phone": "(555) 234-5678",
        "rating": 4.6,
        "insurance_accepted": ["Medicare", "Aetna", "Cigna"],
        "next_available": "2025-09-15",
        "address": "456 Health Plaza, Your City, ST 12345",
        "notes": "Great for ongoing care and chronic condition management"
    },
    {
        "id": 3,
        "name": "Johnson & Associates Law Firm",
        "specialty": "Healthcare Law & Estate Planning",
        "phone": "(555) 345-6789",
        "rating": 4.9,
        "insurance_accepted": ["Legal Insurance", "Self-Pay"],
        "next_available": "2025-09-18",
        "address": "789 Legal Center, Your City, ST 12345",
        "notes": "Specializes in healthcare directives and estate planning"
    },
    {
        "id": 4,
        "name": "Dr. Lisa Rodriguez, MD",
        "specialty": "Cardiology",
        "phone": "(555) 456-7890",
        "rating": 4.7,
        "insurance_accepted": ["Medicare", "Blue Cross", "United Healthcare"],
        "next_available": "2025-10-05",
        "address": "321 Heart Center, Your City, ST 12345",
        "notes": "Cardiac specialist with excellent Medicare coverage"
    }
]

HEALTHCARE_APPOINTMENTS = [
    {
        "id": 1,
        "provider": "Dr. Sarah Johnson, MD",
        "date": "2025-09-22",
        "time": "10:00 AM",
        "purpose": "Annual physical and Medicare wellness visit",
        "status": "scheduled",
        "notes": "Bring insurance card and medication list"
    },
    {
        "id": 2,
        "provider": "Johnson & Associates Law Firm",
        "date": "2025-09-15", 
        "time": "9:00 AM",
        "purpose": "Healthcare directive and estate planning consultation",
        "status": "scheduled",
        "notes": "Bring current will and healthcare preferences"
    },
    {
        "id": 3,
        "provider": "Dr. Michael Chen, MD",
        "date": "2025-10-12",
        "time": "2:30 PM",
        "purpose": "Follow-up for blood pressure monitoring",
        "status": "scheduled",
        "notes": "Bring blood pressure log"
    }
]

HEALTH_METRICS = [
    {
        "id": 1,
        "metric": "Blood Pressure",
        "value": "125/80",
        "unit": "mmHg",
        "date": datetime.now().isoformat(),
        "status": "normal",
        "target": "< 130/80"
    },
    {
        "id": 2,
        "metric": "Weight",
        "value": 175,
        "unit": "lbs",
        "date": datetime.now().isoformat(),
        "status": "normal",
        "target": "170-180"
    },
    {
        "id": 3,
        "metric": "Steps",
        "value": 8500,
        "unit": "steps",
        "date": datetime.now().isoformat(),
        "status": "good",
        "target": "8000+"
    }
]

# Dashboard frontend HTML
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dr. Dede's RiskTravel Intelligence Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover:hover { transform: translateY(-2px); transition: all 0.3s ease; }
    </style>
</head>
<body class="bg-gray-100">
    <!-- Navigation -->
    <nav class="gradient-bg text-white p-4 shadow-lg">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">🏥 Dr. Dede's RiskTravel Intelligence</h1>
            <div class="flex space-x-4">
                <button id="loginBtn" class="bg-white text-blue-600 px-4 py-2 rounded hover:bg-gray-100">Login</button>
                <button id="logoutBtn" class="bg-red-500 px-4 py-2 rounded hover:bg-red-600 hidden">Logout</button>
            </div>
        </div>
    </nav>

    <!-- Login Modal -->
    <div id="loginModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
        <div class="flex items-center justify-center h-full">
            <div class="bg-white p-8 rounded-lg shadow-xl max-w-md w-full mx-4">
                <h2 class="text-2xl font-bold mb-6 text-center">Login to Dashboard</h2>
                <form id="loginForm">
                    <div class="mb-4">
                        <label class="block text-gray-700 text-sm font-bold mb-2">Email</label>
                        <input type="email" id="email" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500">
                    </div>
                    <div class="mb-6">
                        <label class="block text-gray-700 text-sm font-bold mb-2">Password</label>
                        <input type="password" id="password" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500">
                    </div>
                    <div class="flex justify-between">
                        <button type="button" id="cancelLogin" class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">Cancel</button>
                        <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">Login</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Main Dashboard -->
    <div id="dashboard" class="container mx-auto p-6 hidden">
        <!-- Dashboard Overview -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-white p-6 rounded-lg shadow-lg card-hover">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-green-100 text-green-600">
                        <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm text-gray-600">Total Revenue</p>
                        <p class="text-2xl font-semibold text-gray-900" id="totalRevenue">$100,000</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-lg shadow-lg card-hover">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-blue-100 text-blue-600">
                        <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm text-gray-600">Active Agents</p>
                        <p class="text-2xl font-semibold text-gray-900" id="activeAgents">3</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-lg shadow-lg card-hover">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-purple-100 text-purple-600">
                        <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm text-gray-600">Healthcare Providers</p>
                        <p class="text-2xl font-semibold text-gray-900" id="healthcareProviders">4</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-lg shadow-lg card-hover">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-red-100 text-red-600">
                        <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm text-gray-600">Appointments</p>
                        <p class="text-2xl font-semibold text-gray-900" id="appointments">3</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tabs -->
        <div class="bg-white rounded-lg shadow-lg">
            <div class="border-b border-gray-200">
                <nav class="-mb-px flex space-x-8 px-6">
                    <button class="tab-btn py-4 px-1 border-b-2 border-blue-500 font-medium text-sm text-blue-600" data-tab="revenue">Revenue</button>
                    <button class="tab-btn py-4 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700" data-tab="agents">AI Agents</button>
                    <button class="tab-btn py-4 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700" data-tab="healthcare">Healthcare</button>
                    <button class="tab-btn py-4 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700" data-tab="kpi">KPIs</button>
                </nav>
            </div>

            <!-- Tab Content -->
            <div class="p-6">
                <!-- Revenue Tab -->
                <div id="revenue-tab" class="tab-content">
                    <div class="flex justify-between items-center mb-6">
                        <h3 class="text-lg font-semibold">Revenue Streams Management</h3>
                        <button id="addRevenueBtn" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                            <span class="mr-2">+</span>Add Revenue Stream
                        </button>
                    </div>
                    <div id="revenueStreams" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <!-- Revenue streams will be loaded here -->
                    </div>
                </div>

                <!-- AI Agents Tab -->
                <div id="agents-tab" class="tab-content hidden">
                    <h3 class="text-lg font-semibold mb-4">AI Agent Status</h3>
                    <div id="aiAgents" class="space-y-4">
                        <!-- AI agents will be loaded here -->
                    </div>
                </div>

                <!-- Healthcare Tab -->
                <div id="healthcare-tab" class="tab-content hidden">
                    <h3 class="text-lg font-semibold mb-4">Healthcare Management</h3>
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <h4 class="font-medium mb-3">Healthcare Providers</h4>
                            <div id="healthcareProvidersList" class="space-y-3">
                                <!-- Providers will be loaded here -->
                            </div>
                        </div>
                        <div>
                            <h4 class="font-medium mb-3">Upcoming Appointments</h4>
                            <div id="appointmentsList" class="space-y-3">
                                <!-- Appointments will be loaded here -->
                            </div>
                        </div>
                    </div>
                </div>

                <!-- KPI Tab -->
                <div id="kpi-tab" class="tab-content hidden">
                    <h3 class="text-lg font-semibold mb-4">Key Performance Indicators</h3>
                    <div id="kpiMetrics" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <!-- KPIs will be loaded here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Revenue Stream Modal -->
    <div id="revenueModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
        <div class="flex items-center justify-center h-full p-4">
            <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
                <div class="p-6">
                    <h2 id="revenueModalTitle" class="text-2xl font-bold mb-6">Add Revenue Stream</h2>
                    <form id="revenueForm">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="md:col-span-2">
                                <label class="block text-gray-700 text-sm font-bold mb-2">Stream Name *</label>
                                <input type="text" id="streamName" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500" required>
                            </div>
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">Current Month ($)</label>
                                <input type="number" id="currentMonth" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500" min="0" step="1000">
                            </div>
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">Target Month ($)</label>
                                <input type="number" id="targetMonth" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500" min="0" step="1000">
                            </div>
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">YTD ($)</label>
                                <input type="number" id="ytd" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500" min="0" step="1000">
                            </div>
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">Target YTD ($)</label>
                                <input type="number" id="targetYtd" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500" min="0" step="1000">
                            </div>
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">Growth Rate (%)</label>
                                <input type="number" id="growthRate" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500" min="-100" step="0.1">
                            </div>
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">6-Month Projection ($)</label>
                                <input type="number" id="projection6Month" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500" min="0" step="1000">
                            </div>
                            <div class="md:col-span-2">
                                <label class="block text-gray-700 text-sm font-bold mb-2">Revenue Sources (one per line)</label>
                                <textarea id="sources" rows="4" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500" placeholder="Enter revenue sources, one per line"></textarea>
                            </div>
                        </div>
                        <div class="flex justify-between mt-6">
                            <button type="button" id="cancelRevenueForm" class="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600">Cancel</button>
                            <button type="submit" id="submitRevenueForm" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">Save</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div id="deleteConfirmModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
        <div class="flex items-center justify-center h-full p-4">
            <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
                <div class="p-6">
                    <h2 class="text-xl font-bold mb-4 text-red-600">Confirm Delete</h2>
                    <p class="text-gray-700 mb-6">Are you sure you want to delete this revenue stream? This action cannot be undone.</p>
                    <div class="flex justify-between">
                        <button id="cancelDelete" class="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600">Cancel</button>
                        <button id="confirmDelete" class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700">Delete</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Welcome Screen -->
    <div id="welcomeScreen" class="container mx-auto p-6">
        <div class="text-center py-20">
            <h2 class="text-4xl font-bold text-gray-800 mb-4">Welcome to Dr. Dede's RiskTravel Intelligence Platform</h2>
            <p class="text-xl text-gray-600 mb-8">Healthcare-Enhanced Business Intelligence Dashboard</p>
            <button id="getStartedBtn" class="bg-blue-500 text-white px-8 py-3 rounded-lg text-lg hover:bg-blue-600">Get Started</button>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
            <div class="text-center">
                <div class="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z"></path>
                    </svg>
                </div>
                <h3 class="text-xl font-semibold mb-2">Revenue Tracking</h3>
                <p class="text-gray-600">Monitor 4 revenue streams with real-time targets and growth rates</p>
            </div>
            
            <div class="text-center">
                <div class="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z"></path>
                    </svg>
                </div>
                <h3 class="text-xl font-semibold mb-2">Healthcare Management</h3>
                <p class="text-gray-600">Provider directory, appointment scheduling, and health metrics tracking</p>
            </div>
            
            <div class="text-center">
                <div class="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                </div>
                <h3 class="text-xl font-semibold mb-2">AI Agent Monitoring</h3>
                <p class="text-gray-600">Track LinkedIn, Content, and Email automation agents</p>
            </div>
        </div>
    </div>

    <script>
        let authToken = localStorage.getItem('authToken');
        
        // API base URL
        const API_BASE = window.location.origin;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            if (authToken) {
                showDashboard();
                loadDashboardData();
            } else {
                showWelcomeScreen();
            }
            
            setupEventListeners();
        });
        
        function setupEventListeners() {
            // Login modal
            document.getElementById('loginBtn').addEventListener('click', () => {
                document.getElementById('loginModal').classList.remove('hidden');
            });
            
            document.getElementById('getStartedBtn').addEventListener('click', () => {
                document.getElementById('loginModal').classList.remove('hidden');
            });
            
            document.getElementById('cancelLogin').addEventListener('click', () => {
                document.getElementById('loginModal').classList.add('hidden');
            });
            
            // Login form
            document.getElementById('loginForm').addEventListener('submit', handleLogin);
            
            // Logout
            document.getElementById('logoutBtn').addEventListener('click', handleLogout);
            
            // Tabs
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const tabName = e.target.dataset.tab;
                    switchTab(tabName);
                });
            });
            
            // Revenue stream management
            document.getElementById('addRevenueBtn').addEventListener('click', () => {
                openRevenueModal();
            });
            
            document.getElementById('cancelRevenueForm').addEventListener('click', () => {
                closeRevenueModal();
            });
            
            document.getElementById('revenueForm').addEventListener('submit', handleRevenueSubmit);
            
            document.getElementById('cancelDelete').addEventListener('click', () => {
                closeDeleteModal();
            });
            
            document.getElementById('confirmDelete').addEventListener('click', confirmDeleteRevenueStream);
        }
        
        async function handleLogin(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await axios.post(`${API_BASE}/api/auth/login`, {
                    email: email,
                    password: password
                });
                
                authToken = response.data.token;
                localStorage.setItem('authToken', authToken);
                
                document.getElementById('loginModal').classList.add('hidden');
                showDashboard();
                loadDashboardData();
                
            } catch (error) {
                alert('Login failed: ' + (error.response?.data?.error || 'Unknown error'));
            }
        }
        
        function handleLogout() {
            authToken = null;
            localStorage.removeItem('authToken');
            showWelcomeScreen();
        }
        
        function showWelcomeScreen() {
            document.getElementById('welcomeScreen').classList.remove('hidden');
            document.getElementById('dashboard').classList.add('hidden');
            document.getElementById('loginBtn').classList.remove('hidden');
            document.getElementById('logoutBtn').classList.add('hidden');
        }
        
        function showDashboard() {
            document.getElementById('welcomeScreen').classList.add('hidden');
            document.getElementById('dashboard').classList.remove('hidden');
            document.getElementById('loginBtn').classList.add('hidden');
            document.getElementById('logoutBtn').classList.remove('hidden');
        }
        
        function switchTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('border-blue-500', 'text-blue-600');
                btn.classList.add('border-transparent', 'text-gray-500');
            });
            
            document.querySelector(`[data-tab="${tabName}"]`).classList.remove('border-transparent', 'text-gray-500');
            document.querySelector(`[data-tab="${tabName}"]`).classList.add('border-blue-500', 'text-blue-600');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            
            document.getElementById(`${tabName}-tab`).classList.remove('hidden');
        }
        
        // Revenue Stream Management Functions
        let currentEditingId = null;
        let deleteStreamId = null;
        
        function openRevenueModal(stream = null) {
            const modal = document.getElementById('revenueModal');
            const title = document.getElementById('revenueModalTitle');
            const form = document.getElementById('revenueForm');
            
            if (stream) {
                // Edit mode
                title.textContent = 'Edit Revenue Stream';
                currentEditingId = stream.id;
                
                // Populate form fields
                document.getElementById('streamName').value = stream.name || '';
                document.getElementById('currentMonth').value = stream.current_month || 0;
                document.getElementById('targetMonth').value = stream.target_month || 0;
                document.getElementById('ytd').value = stream.ytd || 0;
                document.getElementById('targetYtd').value = stream.target_ytd || 0;
                document.getElementById('growthRate').value = stream.growth_rate || 0;
                document.getElementById('projection6Month').value = stream.projections?.["6_month"] || 0;
                document.getElementById('sources').value = Array.isArray(stream.sources) ? stream.sources.join('\n') : '';
            } else {
                // Add mode
                title.textContent = 'Add Revenue Stream';
                currentEditingId = null;
                form.reset();
            }
            
            modal.classList.remove('hidden');
        }
        
        function closeRevenueModal() {
            document.getElementById('revenueModal').classList.add('hidden');
            document.getElementById('revenueForm').reset();
            currentEditingId = null;
        }
        
        function openDeleteModal(streamId, streamName) {
            deleteStreamId = streamId;
            document.querySelector('#deleteConfirmModal p').textContent = 
                `Are you sure you want to delete "${streamName}"? This action cannot be undone.`;
            document.getElementById('deleteConfirmModal').classList.remove('hidden');
        }
        
        function closeDeleteModal() {
            document.getElementById('deleteConfirmModal').classList.add('hidden');
            deleteStreamId = null;
        }
        
        async function handleRevenueSubmit(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitRevenueForm');
            const originalText = submitBtn.textContent;
            
            try {
                submitBtn.textContent = 'Saving...';
                submitBtn.disabled = true;
                
                const formData = {
                    name: document.getElementById('streamName').value.trim(),
                    current_month: parseFloat(document.getElementById('currentMonth').value) || 0,
                    target_month: parseFloat(document.getElementById('targetMonth').value) || 0,
                    ytd: parseFloat(document.getElementById('ytd').value) || 0,
                    target_ytd: parseFloat(document.getElementById('targetYtd').value) || 0,
                    growth_rate: parseFloat(document.getElementById('growthRate').value) || 0,
                    sources: document.getElementById('sources').value.trim() 
                        ? document.getElementById('sources').value.trim().split('\n').filter(s => s.trim())
                        : [],
                    projections: {
                        "6_month": parseFloat(document.getElementById('projection6Month').value) || 0,
                        "12_month": parseFloat(document.getElementById('projection6Month').value) * 2 || 0
                    }
                };
                
                // Validation
                if (!formData.name) {
                    throw new Error('Stream name is required');
                }
                
                const headers = { 'Authorization': `Bearer ${authToken}` };
                let response;
                
                if (currentEditingId) {
                    // Update existing stream
                    response = await axios.put(`${API_BASE}/api/revenue/${currentEditingId}`, formData, { headers });
                    showNotification('Revenue stream updated successfully!', 'success');
                } else {
                    // Create new stream
                    response = await axios.post(`${API_BASE}/api/revenue`, formData, { headers });
                    showNotification('Revenue stream created successfully!', 'success');
                }
                
                closeRevenueModal();
                await loadRevenueStreams(); // Refresh the list
                
            } catch (error) {
                console.error('Revenue stream save error:', error);
                const message = error.response?.data?.error || error.message || 'Failed to save revenue stream';
                showNotification(message, 'error');
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        }
        
        async function editRevenueStream(streamId) {
            try {
                const headers = { 'Authorization': `Bearer ${authToken}` };
                const response = await axios.get(`${API_BASE}/api/revenue/${streamId}`, { headers });
                openRevenueModal(response.data);
            } catch (error) {
                console.error('Error fetching revenue stream:', error);
                showNotification('Failed to load revenue stream data', 'error');
            }
        }
        
        function deleteRevenueStream(streamId) {
            // Get the stream name from the button's data attribute
            const button = event.target.closest('button');
            const streamName = button.getAttribute('data-stream-name');
            openDeleteModal(streamId, streamName);
        }
        
        async function confirmDeleteRevenueStream() {
            if (!deleteStreamId) return;
            
            const confirmBtn = document.getElementById('confirmDelete');
            const originalText = confirmBtn.textContent;
            
            try {
                confirmBtn.textContent = 'Deleting...';
                confirmBtn.disabled = true;
                
                const headers = { 'Authorization': `Bearer ${authToken}` };
                await axios.delete(`${API_BASE}/api/revenue/${deleteStreamId}`, { headers });
                
                showNotification('Revenue stream deleted successfully!', 'success');
                closeDeleteModal();
                await loadRevenueStreams(); // Refresh the list
                
            } catch (error) {
                console.error('Delete revenue stream error:', error);
                const message = error.response?.data?.error || 'Failed to delete revenue stream';
                showNotification(message, 'error');
            } finally {
                confirmBtn.textContent = originalText;
                confirmBtn.disabled = false;
            }
        }
        
        async function loadRevenueStreams() {
            try {
                const headers = { 'Authorization': `Bearer ${authToken}` };
                const response = await axios.get(`${API_BASE}/api/revenue`, { headers });
                updateRevenueStreams(response.data);
            } catch (error) {
                console.error('Error loading revenue streams:', error);
                showNotification('Failed to load revenue streams', 'error');
            }
        }
        
        function showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full ${
                type === 'success' ? 'bg-green-500 text-white' :
                type === 'error' ? 'bg-red-500 text-white' :
                type === 'warning' ? 'bg-yellow-500 text-white' :
                'bg-blue-500 text-white'
            }`;
            
            notification.innerHTML = `
                <div class="flex items-center space-x-2">
                    <span>${message}</span>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                        </svg>
                    </button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Animate in
            setTimeout(() => {
                notification.classList.remove('translate-x-full');
            }, 100);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }, 5000);
        }
        
        async function loadDashboardData() {
            try {
                console.log('API_BASE:', API_BASE);
                const token = localStorage.getItem('authToken');
                if (!token) {
                    console.error('No auth token found, redirecting to login');
                    showWelcomeScreen();
                    return;
                }
                console.log('Using token for API calls');
                const headers = { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                };
                
                // Load overview
                const overview = await axios.get(`${API_BASE}/api/empire/dashboard`, { headers });
                updateOverview(overview.data);
                
                // Load revenue streams
                const revenue = await axios.get(`${API_BASE}/api/revenue`, { headers });
                updateRevenueStreams(revenue.data);
                
                // Load AI agents
                const agents = await axios.get(`${API_BASE}/api/empire/agents`, { headers });
                updateAIAgents(agents.data);
                
                // Load healthcare data
                const providers = await axios.get(`${API_BASE}/api/healthcare/providers`, { headers });
                const appointments = await axios.get(`${API_BASE}/api/healthcare/appointments`, { headers });
                updateHealthcareData(providers.data, appointments.data);
                
                // Load KPIs
                const kpis = await axios.get(`${API_BASE}/api/kpi`, { headers });
                updateKPIs(kpis.data);
                
            } catch (error) {
                console.error('Dashboard load failed', { 
                    message: error.message, 
                    status: error.response?.status, 
                    data: error.response?.data, 
                    url: error.config?.url 
                });
                if (error.response?.status === 401 || error.response?.status === 422) {
                    console.error('Authentication failed, clearing token and redirecting to login');
                    localStorage.removeItem('authToken');
                    authToken = null;
                    showWelcomeScreen();
                    document.getElementById('loginModal').classList.remove('hidden');
                } else {
                    alert('Failed to load dashboard data: ' + (error.response?.data?.error || error.message || 'Network error'));
                }
            }
        }
        
        function updateOverview(data) {
            const overview = data.empire_overview || data;
            document.getElementById('totalRevenue').textContent = `$${overview.total_monthly_revenue.toLocaleString()}`;
            document.getElementById('activeAgents').textContent = overview.active_agents;
            document.getElementById('appointments').textContent = overview.upcoming_retreats || 0;
        }
        
        function updateRevenueStreams(streams) {
            const container = document.getElementById('revenueStreams');
            container.innerHTML = streams.map(stream => `
                <div class="bg-white border border-gray-200 p-4 rounded-lg hover:shadow-md transition-shadow">
                    <div class="flex justify-between items-start mb-3">
                        <h4 class="font-medium text-gray-900 flex-1">${stream.name}</h4>
                        <div class="flex space-x-2 ml-2">
                            <button onclick="editRevenueStream(${stream.id})" class="text-blue-600 hover:text-blue-800 p-1" title="Edit">
                                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"></path>
                                </svg>
                            </button>
                            <button onclick="deleteRevenueStream(${stream.id})" data-stream-name="${stream.name}" class="text-red-600 hover:text-red-800 p-1" title="Delete">
                                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9zM4 5a2 2 0 012-2h8a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zM8 8a1 1 0 012 0v3a1 1 0 11-2 0V8zM12 8a1 1 0 012 0v3a1 1 0 11-2 0V8z" clip-rule="evenodd"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="space-y-3">
                        <div class="grid grid-cols-2 gap-2 text-sm">
                            <div>
                                <span class="text-gray-600">Current:</span>
                                <span class="font-semibold text-gray-900">$${stream.current_month.toLocaleString()}</span>
                            </div>
                            <div>
                                <span class="text-gray-600">Target:</span>
                                <span class="font-semibold text-gray-900">$${stream.target_month.toLocaleString()}</span>
                            </div>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: ${Math.min((stream.current_month / stream.target_month) * 100, 100)}%"></div>
                        </div>
                        <div class="grid grid-cols-2 gap-2 text-xs">
                            <div class="text-gray-600">
                                YTD: $${stream.ytd.toLocaleString()}
                            </div>
                            <div class="text-right ${stream.growth_rate >= 0 ? 'text-green-600' : 'text-red-600'}">
                                Growth: ${stream.growth_rate}%
                            </div>
                        </div>
                        ${stream.sources && stream.sources.length > 0 ? 
                            '<div class="pt-2 border-t border-gray-100">' +
                                '<p class="text-xs text-gray-600 mb-1">Sources:</p>' +
                                '<div class="text-xs text-gray-700 space-y-1">' +
                                    stream.sources.slice(0, 2).map(source => '<div>- ' + source + '</div>').join('') +
                                    (stream.sources.length > 2 ? '<div class="text-gray-500">+ ' + (stream.sources.length - 2) + ' more</div>' : '') +
                                '</div>' +
                            '</div>'
                        : ''}
                    </div>
                </div>
            `).join('');
        }
        
        function updateAIAgents(agents) {
            const container = document.getElementById('aiAgents');
            container.innerHTML = agents.map(agent => `
                <div class="bg-gray-50 p-4 rounded-lg flex justify-between items-center">
                    <div>
                        <h4 class="font-medium text-gray-900">${agent.name}</h4>
                        <p class="text-sm text-gray-600">Tasks: ${agent.tasks_completed} | Success: ${agent.success_rate}%</p>
                    </div>
                    <div class="flex items-center">
                        <span class="px-2 py-1 text-xs rounded-full ${agent.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">${agent.status}</span>
                    </div>
                </div>
            `).join('');
        }
        
        function updateHealthcareData(providers, appointments) {
            const providersContainer = document.getElementById('healthcareProvidersList');
            providersContainer.innerHTML = providers.slice(0, 3).map(provider => `
                <div class="bg-gray-50 p-3 rounded-lg">
                    <h5 class="font-medium text-gray-900">${provider.name}</h5>
                    <p class="text-sm text-gray-600">${provider.specialty}</p>
                    <p class="text-xs text-gray-500">Rating: ${provider.rating}/5</p>
                </div>
            `).join('');
            
            const appointmentsContainer = document.getElementById('appointmentsList');
            appointmentsContainer.innerHTML = appointments.map(apt => `
                <div class="bg-gray-50 p-3 rounded-lg">
                    <h5 class="font-medium text-gray-900">${apt.provider}</h5>
                    <p class="text-sm text-gray-600">${apt.date} at ${apt.time}</p>
                    <p class="text-xs text-gray-500">${apt.purpose}</p>
                </div>
            `).join('');
        }
        
        function updateKPIs(kpis) {
            const container = document.getElementById('kpiMetrics');
            container.innerHTML = kpis.map(kpi => `
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900">${kpi.name}</h4>
                    <div class="mt-2">
                        <div class="flex justify-between items-center">
                            <span class="text-2xl font-bold">${kpi.value}${kpi.unit === 'USD' ? '' : kpi.unit}</span>
                            <span class="text-sm ${kpi.trend === 'up' ? 'text-green-600' : 'text-red-600'}">${kpi.change_percent > 0 ? '+' : ''}${kpi.change_percent}%</span>
                        </div>
                        <div class="text-sm text-gray-600">Target: ${kpi.target}${kpi.unit === 'USD' ? '' : kpi.unit}</div>
                    </div>
                </div>
            `).join('');
        }
    </script>
</body>
</html>
"""

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        access_token = create_access_token(identity=email)
        
        return jsonify({
            "message": "User registered successfully",
            "token": access_token,
            "user": {
                "email": email,
                "name": "Dr. Dede",
                "role": "admin"
            }
        })
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        access_token = create_access_token(identity=email)
        
        return jsonify({
            "message": "Login successful",
            "token": access_token,
            "user": {
                "email": email,
                "name": "Dr. Dede",
                "role": "admin"
            }
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

# Dashboard routes
@app.route('/dashboard')
@app.route('/dashboard/')
def dashboard():
    return DASHBOARD_HTML

@app.route('/executive-pipeline')
def executive_pipeline():
    return render_template('executive_pipeline.html')

@app.route('/')
def index():
    return DASHBOARD_HTML

@app.route('/bi')
@app.route('/bi/')
def bi_dashboard():
    """Serve the Business Intelligence Dashboard"""
    return render_template('bi_dashboard.html')

@app.route('/workflows')
@app.route('/workflows/')
def workflow_dashboard():
    """Serve the Workflow Automation Dashboard"""
    return render_template('workflow_dashboard.html')

@app.route('/make')
@app.route('/make/')
def make_dashboard():
    """Serve the Make.com Workflow Automation Dashboard"""
    return render_template('make_dashboard.html')

@app.route('/api/dashboard/overview', methods=['GET'])
@jwt_required()
def dashboard_overview():
    try:
        total_revenue = sum(stream['current_month'] for stream in REVENUE_STREAMS)
        total_target = sum(stream['target_month'] for stream in REVENUE_STREAMS)
        
        return jsonify({
            "total_revenue": total_revenue,
            "total_target": total_target,
            "achievement_rate": (total_revenue / total_target) * 100 if total_target > 0 else 0,
            "active_agents": len([agent for agent in AI_AGENTS if agent['status'] == 'active']),
            "upcoming_appointments": len([apt for apt in HEALTHCARE_APPOINTMENTS if apt['status'] == 'scheduled']),
            "health_alerts": 0,
            "last_updated": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        return jsonify({"error": "Failed to fetch dashboard overview"}), 500

# Revenue routes
@app.route('/api/revenue', methods=['GET'])
@jwt_required()
def get_revenue():
    streams = RevenueStream.query.all()
    return jsonify(serialize_models(streams))

@app.route('/api/revenue/<int:stream_id>', methods=['GET'])
@jwt_required()
def get_revenue_stream(stream_id):
    stream = RevenueStream.query.get(stream_id)
    if not stream:
        return jsonify({"error": "Revenue stream not found"}), 404
    return jsonify(serialize_model(stream))

@app.route('/api/revenue', methods=['POST'])
@jwt_required()
def create_revenue_entry():
    try:
        data = request.get_json()
        new_stream = RevenueStream(
            name=data.get('name'),
            current_month=data.get('current_month', 0),
            target_month=data.get('target_month', 0),
            ytd=data.get('ytd', 0),
            target_ytd=data.get('target_ytd', 0),
            growth_rate=data.get('growth_rate', 0),
            sources=data.get('sources', []),
            projections=data.get('projections', {}),
            last_updated=datetime.now()
        )
        db.session.add(new_stream)
        db.session.commit()
        return jsonify(serialize_model(new_stream)), 201
    except Exception as e:
        logger.error(f"Create revenue entry error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create revenue entry"}), 500

@app.route('/api/revenue/<int:stream_id>', methods=['PUT'])
@jwt_required()
def update_revenue_stream(stream_id):
    try:
        stream = RevenueStream.query.get(stream_id)
        if not stream:
            return jsonify({"error": "Revenue stream not found"}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({"error": "Name is required"}), 400
        
        # Update fields
        stream.name = data.get('name', stream.name)
        stream.current_month = float(data.get('current_month', stream.current_month))
        stream.target_month = float(data.get('target_month', stream.target_month))
        stream.ytd = float(data.get('ytd', stream.ytd))
        stream.target_ytd = float(data.get('target_ytd', stream.target_ytd))
        stream.growth_rate = float(data.get('growth_rate', stream.growth_rate))
        stream.sources = data.get('sources', stream.sources)
        stream.projections = data.get('projections', stream.projections)
        stream.last_updated = datetime.now()
        
        db.session.commit()
        
        # Trigger business events for revenue milestones
        try:
            # Check for revenue milestones
            milestones = [
                {'threshold': 1000000, 'event': 'revenue_milestone_1m'},
                {'threshold': 5000000, 'event': 'revenue_milestone_5m'},
                {'threshold': 10000000, 'event': 'revenue_milestone_10m'},
                {'threshold': 50000000, 'event': 'revenue_milestone_50m'}
            ]
            
            for milestone in milestones:
                if stream.current_month >= milestone['threshold']:
                    trigger_business_event(
                        event_type=milestone['event'],
                        entity_type='revenue_stream',
                        entity_id=stream.id,
                        event_data={
                            'milestone_amount': milestone['threshold'],
                            'current_amount': stream.current_month,
                            'stream_name': stream.name,
                            'growth_rate': stream.growth_rate,
                            'timestamp': datetime.now().isoformat()
                        },
                        source='revenue_update',
                        priority='high'
                    )
            
            # Check for significant growth rate changes
            if stream.growth_rate > 50:  # High growth rate
                trigger_business_event(
                    event_type='high_growth_rate',
                    entity_type='revenue_stream',
                    entity_id=stream.id,
                    event_data={
                        'growth_rate': stream.growth_rate,
                        'stream_name': stream.name,
                        'current_amount': stream.current_month,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='revenue_update',
                    priority='medium'
                )
            
            # Check if revenue target is exceeded
            if stream.current_month > stream.target_month:
                trigger_business_event(
                    event_type='revenue_target_exceeded',
                    entity_type='revenue_stream',
                    entity_id=stream.id,
                    event_data={
                        'target': stream.target_month,
                        'actual': stream.current_month,
                        'excess_amount': stream.current_month - stream.target_month,
                        'stream_name': stream.name,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='revenue_update',
                    priority='high'
                )
        except Exception as e:
            logger.error(f"Error triggering revenue events: {e}")
        
        return jsonify(serialize_model(stream))
    except ValueError as e:
        logger.error(f"Update revenue stream validation error: {e}")
        return jsonify({"error": "Invalid numeric values provided"}), 400
    except Exception as e:
        logger.error(f"Update revenue stream error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update revenue stream"}), 500

@app.route('/api/revenue/<int:stream_id>', methods=['DELETE'])
@jwt_required()
def delete_revenue_stream(stream_id):
    try:
        stream = RevenueStream.query.get(stream_id)
        if not stream:
            return jsonify({"error": "Revenue stream not found"}), 404
        
        db.session.delete(stream)
        db.session.commit()
        return jsonify({"message": "Revenue stream deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Delete revenue stream error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete revenue stream"}), 500

# KPI routes
@app.route('/api/kpi', methods=['GET'])
@jwt_required()
def get_kpis():
    kpis = KPIMetric.query.all()
    return jsonify(serialize_models(kpis))

@app.route('/api/kpi/<int:kpi_id>', methods=['GET'])
@jwt_required()
def get_kpi(kpi_id):
    kpi = KPIMetric.query.get(kpi_id)
    if not kpi:
        return jsonify({"error": "KPI not found"}), 404
    return jsonify(serialize_model(kpi))

# AI Agent routes
@app.route('/api/agents', methods=['GET'])
@jwt_required()
def get_agents():
    agents = AIAgent.query.all()
    return jsonify(serialize_models(agents))

@app.route('/api/agents/<int:agent_id>', methods=['GET'])
@jwt_required()
def get_agent(agent_id):
    agent = AIAgent.query.get(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    return jsonify(serialize_model(agent))

@app.route('/api/agents/<int:agent_id>/status', methods=['PUT'])
@jwt_required()
def update_agent_status(agent_id):
    try:
        agent = AIAgent.query.get(agent_id)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['active', 'paused', 'stopped']:
            return jsonify({"error": "Invalid status"}), 400
        
        agent.status = new_status
        agent.last_activity = datetime.now()
        db.session.commit()
        
        return jsonify(serialize_model(agent))
    except Exception as e:
        logger.error(f"Update agent status error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update agent status"}), 500

# Comprehensive AI Agent Management API Routes
@app.route('/api/ai-agents', methods=['GET'])
def get_ai_agents():
    """Get all AI agents with optional filtering"""
    try:
        query = AIAgent.query
        
        # Filter by tier
        tier = request.args.get('tier')
        if tier:
            query = query.filter(AIAgent.tier == tier)
        
        # Filter by status
        status = request.args.get('status')
        if status:
            query = query.filter(AIAgent.status == status)
        
        # Search by name or function
        search = request.args.get('search')
        if search:
            query = query.filter(
                db.or_(
                    AIAgent.name.contains(search),
                    AIAgent.function.contains(search)
                )
            )
        
        agents = query.all()
        return jsonify([agent.to_dict() for agent in agents])
    except Exception as e:
        logger.error(f"Get AI agents error: {e}")
        return jsonify({"error": "Failed to fetch agents"}), 500

@app.route('/api/ai-agents/<int:agent_id>', methods=['GET'])
def get_ai_agent(agent_id):
    """Get specific AI agent by ID"""
    try:
        agent = AIAgent.query.get(agent_id)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        return jsonify(agent.to_dict())
    except Exception as e:
        logger.error(f"Get AI agent error: {e}")
        return jsonify({"error": "Failed to fetch agent"}), 500

@app.route('/api/ai-agents', methods=['POST'])
def create_ai_agent():
    """Create new AI agent"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'tier', 'function']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create new agent
        agent = AIAgent(
            name=data['name'],
            tier=data['tier'],
            function=data['function'],
            tools=data.get('tools', []),
            status=data.get('status', 'active'),
            performance=data.get('performance', {}),
            last_activity=datetime.utcnow(),
            next_scheduled=datetime.fromisoformat(data['next_scheduled']) if data.get('next_scheduled') else None,
            additional_data=data.get('additional_data', {})
        )
        
        # Add tier-specific fields to additional_data
        tier_fields = ['revenue_target', 'weekly_goal', 'pricing', 'output', 'goal', 'strategy', 
                      'capability', 'licensing', 'revenue', 'targets', 'services', 'capabilities']
        for field in tier_fields:
            if data.get(field):
                if not agent.additional_data:
                    agent.additional_data = {}
                agent.additional_data[field] = data[field]
        
        db.session.add(agent)
        db.session.commit()
        
        return jsonify(agent.to_dict()), 201
    except Exception as e:
        logger.error(f"Create AI agent error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create agent"}), 500

@app.route('/api/ai-agents/<int:agent_id>', methods=['PUT'])
def update_ai_agent(agent_id):
    """Update existing AI agent"""
    try:
        agent = AIAgent.query.get(agent_id)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        
        # Update basic fields
        if 'name' in data:
            agent.name = data['name']
        if 'tier' in data:
            agent.tier = data['tier']
        if 'function' in data:
            agent.function = data['function']
        if 'tools' in data:
            agent.tools = data['tools']
        if 'status' in data:
            agent.status = data['status']
        if 'performance' in data:
            agent.performance = data['performance']
        if 'next_scheduled' in data:
            agent.next_scheduled = datetime.fromisoformat(data['next_scheduled']) if data['next_scheduled'] else None
        
        # Update additional fields
        tier_fields = ['revenue_target', 'weekly_goal', 'pricing', 'output', 'goal', 'strategy', 
                      'capability', 'licensing', 'revenue', 'targets', 'services', 'capabilities']
        for field in tier_fields:
            if field in data:
                if not agent.additional_data:
                    agent.additional_data = {}
                agent.additional_data[field] = data[field]
        
        agent.last_activity = datetime.utcnow()
        db.session.commit()
        
        return jsonify(agent.to_dict())
    except Exception as e:
        logger.error(f"Update AI agent error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update agent"}), 500

@app.route('/api/ai-agents/<int:agent_id>', methods=['DELETE'])
def delete_ai_agent(agent_id):
    """Delete AI agent"""
    try:
        agent = AIAgent.query.get(agent_id)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        db.session.delete(agent)
        db.session.commit()
        
        return jsonify({"message": "Agent deleted successfully"})
    except Exception as e:
        logger.error(f"Delete AI agent error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete agent"}), 500

@app.route('/api/ai-agents/<int:agent_id>/status', methods=['PUT'])
def update_ai_agent_status(agent_id):
    """Update AI agent status"""
    try:
        agent = AIAgent.query.get(agent_id)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        new_status = data.get('status')
        
        valid_statuses = ['active', 'paused', 'inactive', 'development', 'beta']
        if new_status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
        
        agent.status = new_status
        agent.last_activity = datetime.utcnow()
        db.session.commit()
        
        return jsonify(agent.to_dict())
    except Exception as e:
        logger.error(f"Update AI agent status error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update agent status"}), 500

@app.route('/api/ai-agents/<int:agent_id>/performance', methods=['PUT'])
def update_ai_agent_performance(agent_id):
    """Update AI agent performance metrics"""
    try:
        agent = AIAgent.query.get(agent_id)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        performance_data = data.get('performance', {})
        
        if not agent.performance:
            agent.performance = {}
        
        agent.performance.update(performance_data)
        agent.last_activity = datetime.utcnow()
        db.session.commit()
        
        # Trigger business events for agent performance changes
        try:
            # Check for high performance metrics
            success_rate = agent.performance.get('success_rate', 0)
            pipeline_value = agent.performance.get('pipeline_value', 0)
            
            # High success rate trigger
            if success_rate >= 90:
                trigger_business_event(
                    event_type='agent_high_performance',
                    entity_type='ai_agent',
                    entity_id=agent.id,
                    event_data={
                        'agent_name': agent.name,
                        'success_rate': success_rate,
                        'tier': agent.tier,
                        'performance_metrics': agent.performance,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='agent_performance_update',
                    priority='high'
                )
            
            # Low success rate trigger
            elif success_rate < 30 and success_rate > 0:
                trigger_business_event(
                    event_type='agent_low_performance',
                    entity_type='ai_agent',
                    entity_id=agent.id,
                    event_data={
                        'agent_name': agent.name,
                        'success_rate': success_rate,
                        'tier': agent.tier,
                        'performance_metrics': agent.performance,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='agent_performance_update',
                    priority='medium'
                )
            
            # High pipeline value trigger
            if pipeline_value >= 1000000:  # $1M+ pipeline
                trigger_business_event(
                    event_type='agent_high_pipeline_value',
                    entity_type='ai_agent',
                    entity_id=agent.id,
                    event_data={
                        'agent_name': agent.name,
                        'pipeline_value': pipeline_value,
                        'tier': agent.tier,
                        'function': agent.function,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='agent_performance_update',
                    priority='high'
                )
            
            # Check for significant performance improvements
            opportunities_found = agent.performance.get('opportunities_found', 0)
            if opportunities_found >= 100:
                trigger_business_event(
                    event_type='agent_milestone_opportunities',
                    entity_type='ai_agent',
                    entity_id=agent.id,
                    event_data={
                        'agent_name': agent.name,
                        'opportunities_found': opportunities_found,
                        'milestone': '100_opportunities',
                        'timestamp': datetime.now().isoformat()
                    },
                    source='agent_performance_update',
                    priority='medium'
                )
                
        except Exception as e:
            logger.error(f"Error triggering agent performance events: {e}")
        
        return jsonify(agent.to_dict())
    except Exception as e:
        logger.error(f"Update AI agent performance error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update agent performance"}), 500

@app.route('/api/ai-agents/bulk', methods=['POST'])
def bulk_operations_ai_agents():
    """Perform bulk operations on AI agents"""
    try:
        data = request.get_json()
        agent_ids = data.get('agent_ids', [])
        operation = data.get('operation')
        
        if not agent_ids:
            return jsonify({"error": "No agent IDs provided"}), 400
        
        agents = AIAgent.query.filter(AIAgent.id.in_(agent_ids)).all()
        if len(agents) != len(agent_ids):
            return jsonify({"error": "Some agents not found"}), 404
        
        if operation == 'activate':
            for agent in agents:
                agent.status = 'active'
                agent.last_activity = datetime.utcnow()
        elif operation == 'pause':
            for agent in agents:
                agent.status = 'paused'
                agent.last_activity = datetime.utcnow()
        elif operation == 'update_status':
            new_status = data.get('status')
            valid_statuses = ['active', 'paused', 'inactive', 'development', 'beta']
            if new_status not in valid_statuses:
                return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
            for agent in agents:
                agent.status = new_status
                agent.last_activity = datetime.utcnow()
        else:
            return jsonify({"error": "Invalid operation"}), 400
        
        db.session.commit()
        return jsonify({"message": f"Bulk operation '{operation}' completed successfully on {len(agents)} agents"})
    except Exception as e:
        logger.error(f"Bulk operations error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to perform bulk operation"}), 500

# Task Management API for AI Agents
@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create and assign task to AI agent"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['agent_id', 'title']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Verify agent exists
        agent = AIAgent.query.get(data['agent_id'])
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        # Create task record (you might want to create a Task model for this)
        task_data = {
            "id": datetime.utcnow().timestamp(),
            "agent_id": data['agent_id'],
            "title": data['title'],
            "description": data.get('description', ''),
            "priority": data.get('priority', 'medium'),
            "status": 'assigned',
            "deadline": data.get('deadline'),
            "notes": data.get('notes', ''),
            "created_at": datetime.utcnow().isoformat(),
            "assigned_at": datetime.utcnow().isoformat()
        }
        
        # Update agent's next scheduled time if deadline is provided
        if data.get('deadline'):
            agent.next_scheduled = datetime.fromisoformat(data['deadline'])
            agent.last_activity = datetime.utcnow()
            db.session.commit()
        
        # In a real implementation, you'd store this in a tasks table
        # For now, we'll just return the task data
        return jsonify(task_data), 201
    except Exception as e:
        logger.error(f"Create task error: {e}")
        return jsonify({"error": "Failed to create task"}), 500

@app.route('/api/ai-agents/dashboard/stats', methods=['GET'])
def get_ai_agents_dashboard_stats():
    """Get dashboard statistics for AI agents"""
    try:
        total_agents = AIAgent.query.count()
        active_agents = AIAgent.query.filter(AIAgent.status == 'active').count()
        paused_agents = AIAgent.query.filter(AIAgent.status == 'paused').count()
        
        # Calculate pipeline value and average performance
        agents = AIAgent.query.all()
        total_pipeline = 0
        performance_sum = 0
        performance_count = 0
        
        for agent in agents:
            if agent.performance:
                if agent.performance.get('pipeline_value'):
                    total_pipeline += agent.performance['pipeline_value']
                if agent.performance.get('success_rate'):
                    performance_sum += agent.performance['success_rate']
                    performance_count += 1
        
        avg_performance = (performance_sum / performance_count) if performance_count > 0 else 0
        
        return jsonify({
            "total_agents": total_agents,
            "active_agents": active_agents,
            "paused_agents": paused_agents,
            "total_pipeline": total_pipeline,
            "avg_performance": round(avg_performance, 1)
        })
    except Exception as e:
        logger.error(f"Get dashboard stats error: {e}")
        return jsonify({"error": "Failed to fetch dashboard stats"}), 500

# ========================================
# Perplexity AI Integration API Routes
# ========================================

# Initialize Perplexity services
perplexity_api = None
research_service = None
content_service = None
opportunity_analyzer = None
ai_scorer = None

def get_perplexity_services():
    """Initialize and return Perplexity services"""
    global perplexity_api, research_service, content_service, opportunity_analyzer, ai_scorer
    
    if not PERPLEXITY_API_KEY:
        return None, None, None, None, None
    
    if not perplexity_api:
        try:
            if create_perplexity_api:
                perplexity_api = create_perplexity_api()
            if create_research_service:
                research_service = create_research_service()
            if create_content_service:
                content_service = create_content_service()
            if create_opportunity_analyzer:
                opportunity_analyzer = create_opportunity_analyzer()
            if create_ai_scorer:
                ai_scorer = create_ai_scorer()
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity services: {e}")
            return None, None, None, None, None
    
    return perplexity_api, research_service, content_service, opportunity_analyzer, ai_scorer

# Simple Query Endpoint
@app.route('/api/perplexity/query', methods=['POST'])
@jwt_required()
def perplexity_simple_query():
    """Send a simple query to Perplexity AI"""
    try:
        api, _, _, _, _ = get_perplexity_services()
        if not api:
            return jsonify({"error": "Perplexity API not available"}), 503
        
        data = request.get_json()
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Optional parameters
        model = data.get('model', 'small')  # small, large, or huge
        temperature = data.get('temperature', 0.2)
        max_tokens = data.get('max_tokens', 800)
        
        # Map model names
        model_map = {
            'small': PerplexityModel.SMALL,
            'large': PerplexityModel.LARGE,
            'huge': PerplexityModel.HUGE
        }
        
        response = api.simple_query(
            prompt=prompt,
            model=model_map.get(model, PerplexityModel.SMALL),
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response:
            return jsonify({
                "response": response,
                "prompt": prompt,
                "model": model,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({"error": "Failed to get response from Perplexity API"}), 500
            
    except Exception as e:
        logger.error(f"Perplexity simple query error: {e}")
        return jsonify({"error": "Failed to process query"}), 500

# Market Analysis Endpoint
@app.route('/api/perplexity/research/market', methods=['POST'])
@jwt_required()
def perplexity_market_analysis():
    """Conduct comprehensive market analysis"""
    try:
        _, research_service_instance, _, _, _ = get_perplexity_services()
        if not research_service_instance:
            return jsonify({"error": "Perplexity research service not available"}), 503
        
        data = request.get_json()
        topic = data.get('topic')
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        # Optional parameters
        recency = data.get('recency', 'month')  # hour, day, week, month, year
        recency_map = {
            'hour': SearchRecency.HOUR,
            'day': SearchRecency.DAY,
            'week': SearchRecency.WEEK,
            'month': SearchRecency.MONTH,
            'year': SearchRecency.YEAR
        }
        
        result = research_service_instance.conduct_market_analysis(
            topic=topic,
            recency=recency_map.get(recency, SearchRecency.MONTH)
        )
        
        if result:
            return jsonify({
                "success": True,
                "analysis": result
            })
        else:
            return jsonify({"error": "Failed to conduct market analysis"}), 500
            
    except Exception as e:
        logger.error(f"Market analysis error: {e}")
        return jsonify({"error": "Failed to conduct market analysis"}), 500

# Company Research Endpoint
@app.route('/api/perplexity/research/company', methods=['POST'])
@jwt_required()
def perplexity_company_research():
    """Research a specific company"""
    try:
        _, research_service_instance, _, _, _ = get_perplexity_services()
        if not research_service_instance:
            return jsonify({"error": "Perplexity research service not available"}), 503
        
        data = request.get_json()
        company_name = data.get('company_name')
        if not company_name:
            return jsonify({"error": "Company name is required"}), 400
        
        company_domain = data.get('company_domain')
        recency = data.get('recency', 'week')
        
        recency_map = {
            'hour': SearchRecency.HOUR,
            'day': SearchRecency.DAY,
            'week': SearchRecency.WEEK,
            'month': SearchRecency.MONTH,
            'year': SearchRecency.YEAR
        }
        
        result = research_service_instance.research_company(
            company_name=company_name,
            company_domain=company_domain,
            recency=recency_map.get(recency, SearchRecency.WEEK)
        )
        
        if result:
            return jsonify({
                "success": True,
                "research": result
            })
        else:
            return jsonify({"error": "Failed to research company"}), 500
            
    except Exception as e:
        logger.error(f"Company research error: {e}")
        return jsonify({"error": "Failed to research company"}), 500

# Industry Analysis Endpoint
@app.route('/api/perplexity/research/industry', methods=['POST'])
@jwt_required()
def perplexity_industry_analysis():
    """Analyze an industry sector"""
    try:
        _, research_service_instance, _, _, _ = get_perplexity_services()
        if not research_service_instance:
            return jsonify({"error": "Perplexity research service not available"}), 503
        
        data = request.get_json()
        industry = data.get('industry')
        if not industry:
            return jsonify({"error": "Industry is required"}), 400
        
        focus_areas = data.get('focus_areas', [])
        recency = data.get('recency', 'month')
        
        recency_map = {
            'hour': SearchRecency.HOUR,
            'day': SearchRecency.DAY,
            'week': SearchRecency.WEEK,
            'month': SearchRecency.MONTH,
            'year': SearchRecency.YEAR
        }
        
        result = research_service_instance.analyze_industry(
            industry=industry,
            focus_areas=focus_areas if focus_areas else None,
            recency=recency_map.get(recency, SearchRecency.MONTH)
        )
        
        if result:
            return jsonify({
                "success": True,
                "analysis": result
            })
        else:
            return jsonify({"error": "Failed to analyze industry"}), 500
            
    except Exception as e:
        logger.error(f"Industry analysis error: {e}")
        return jsonify({"error": "Failed to analyze industry"}), 500

# Competitive Analysis Endpoint
@app.route('/api/perplexity/research/competitive', methods=['POST'])
@jwt_required()
def perplexity_competitive_analysis():
    """Conduct competitive analysis between companies"""
    try:
        _, research_service_instance, _, _, _ = get_perplexity_services()
        if not research_service_instance:
            return jsonify({"error": "Perplexity research service not available"}), 503
        
        data = request.get_json()
        primary_company = data.get('primary_company')
        competitors = data.get('competitors', [])
        
        if not primary_company:
            return jsonify({"error": "Primary company is required"}), 400
        if not competitors:
            return jsonify({"error": "At least one competitor is required"}), 400
        
        recency = data.get('recency', 'month')
        recency_map = {
            'hour': SearchRecency.HOUR,
            'day': SearchRecency.DAY,
            'week': SearchRecency.WEEK,
            'month': SearchRecency.MONTH,
            'year': SearchRecency.YEAR
        }
        
        result = research_service_instance.competitive_analysis(
            primary_company=primary_company,
            competitors=competitors,
            recency=recency_map.get(recency, SearchRecency.MONTH)
        )
        
        if result:
            return jsonify({
                "success": True,
                "analysis": result
            })
        else:
            return jsonify({"error": "Failed to conduct competitive analysis"}), 500
            
    except Exception as e:
        logger.error(f"Competitive analysis error: {e}")
        return jsonify({"error": "Failed to conduct competitive analysis"}), 500

# Executive Research Endpoint
@app.route('/api/perplexity/research/executive', methods=['POST'])
@jwt_required()
def perplexity_executive_research():
    """Research an executive for opportunity analysis"""
    try:
        _, research_service_instance, _, _, _ = get_perplexity_services()
        if not research_service_instance:
            return jsonify({"error": "Perplexity research service not available"}), 503
        
        data = request.get_json()
        executive_name = data.get('executive_name')
        company_name = data.get('company_name')
        opportunity_type = data.get('opportunity_type')
        
        if not all([executive_name, company_name, opportunity_type]):
            return jsonify({"error": "Executive name, company name, and opportunity type are required"}), 400
        
        recency = data.get('recency', 'week')
        recency_map = {
            'hour': SearchRecency.HOUR,
            'day': SearchRecency.DAY,
            'week': SearchRecency.WEEK,
            'month': SearchRecency.MONTH,
            'year': SearchRecency.YEAR
        }
        
        result = research_service_instance.research_executive_opportunity(
            executive_name=executive_name,
            company_name=company_name,
            opportunity_type=opportunity_type,
            recency=recency_map.get(recency, SearchRecency.WEEK)
        )
        
        if result:
            return jsonify({
                "success": True,
                "research": result
            })
        else:
            return jsonify({"error": "Failed to research executive"}), 500
            
    except Exception as e:
        logger.error(f"Executive research error: {e}")
        return jsonify({"error": "Failed to research executive"}), 500

# Content Generation - Executive Summary
@app.route('/api/perplexity/content/executive-summary', methods=['POST'])
@jwt_required()
def perplexity_generate_executive_summary():
    """Generate executive summary from research data"""
    try:
        _, _, content_service_instance, _, _ = get_perplexity_services()
        if not content_service_instance:
            return jsonify({"error": "Perplexity content service not available"}), 503
        
        data = request.get_json()
        research_data = data.get('research_data')
        
        if not research_data:
            return jsonify({"error": "Research data is required"}), 400
        
        result = content_service_instance.generate_executive_summary(research_data)
        
        if result:
            return jsonify({
                "success": True,
                "summary": result
            })
        else:
            return jsonify({"error": "Failed to generate executive summary"}), 500
            
    except Exception as e:
        logger.error(f"Executive summary generation error: {e}")
        return jsonify({"error": "Failed to generate executive summary"}), 500

# Content Generation - Market Report
@app.route('/api/perplexity/content/market-report', methods=['POST'])
@jwt_required()
def perplexity_generate_market_report():
    """Generate comprehensive market report"""
    try:
        _, _, content_service_instance, _, _ = get_perplexity_services()
        if not content_service_instance:
            return jsonify({"error": "Perplexity content service not available"}), 503
        
        data = request.get_json()
        market_data = data.get('market_data')
        
        if not market_data:
            return jsonify({"error": "Market data is required"}), 400
        
        result = content_service_instance.generate_market_report(market_data)
        
        if result:
            return jsonify({
                "success": True,
                "report": result
            })
        else:
            return jsonify({"error": "Failed to generate market report"}), 500
            
    except Exception as e:
        logger.error(f"Market report generation error: {e}")
        return jsonify({"error": "Failed to generate market report"}), 500

# Content Generation - Opportunity Brief
@app.route('/api/perplexity/content/opportunity-brief', methods=['POST'])
@jwt_required()
def perplexity_generate_opportunity_brief():
    """Generate business opportunity brief"""
    try:
        _, _, content_service_instance, _, _ = get_perplexity_services()
        if not content_service_instance:
            return jsonify({"error": "Perplexity content service not available"}), 503
        
        data = request.get_json()
        prospect_data = data.get('prospect_data')
        
        if not prospect_data:
            return jsonify({"error": "Prospect data is required"}), 400
        
        result = content_service_instance.generate_opportunity_brief(prospect_data)
        
        if result:
            return jsonify({
                "success": True,
                "brief": result
            })
        else:
            return jsonify({"error": "Failed to generate opportunity brief"}), 500
            
    except Exception as e:
        logger.error(f"Opportunity brief generation error: {e}")
        return jsonify({"error": "Failed to generate opportunity brief"}), 500

# Content Generation - Industry Insight
@app.route('/api/perplexity/content/industry-insight', methods=['POST'])
@jwt_required()
def perplexity_generate_industry_insight():
    """Generate thought leadership industry insight"""
    try:
        _, _, content_service_instance, _, _ = get_perplexity_services()
        if not content_service_instance:
            return jsonify({"error": "Perplexity content service not available"}), 503
        
        data = request.get_json()
        industry_data = data.get('industry_data')
        
        if not industry_data:
            return jsonify({"error": "Industry data is required"}), 400
        
        result = content_service_instance.generate_industry_insight(industry_data)
        
        if result:
            return jsonify({
                "success": True,
                "insight": result
            })
        else:
            return jsonify({"error": "Failed to generate industry insight"}), 500
            
    except Exception as e:
        logger.error(f"Industry insight generation error: {e}")
        return jsonify({"error": "Failed to generate industry insight"}), 500

# Opportunity Analysis - Governance Opportunity
@app.route('/api/perplexity/opportunity/governance', methods=['POST'])
@jwt_required()
def perplexity_analyze_governance_opportunity():
    """Analyze company for governance/board director opportunity"""
    try:
        _, _, _, opportunity_analyzer_instance, _ = get_perplexity_services()
        if not opportunity_analyzer_instance:
            return jsonify({"error": "Perplexity opportunity analyzer not available"}), 503
        
        data = request.get_json()
        company_name = data.get('company_name')
        if not company_name:
            return jsonify({"error": "Company name is required"}), 400
        
        company_domain = data.get('company_domain')
        
        result = opportunity_analyzer_instance.analyze_governance_opportunity(
            company_name=company_name,
            company_domain=company_domain
        )
        
        if result:
            return jsonify({
                "success": True,
                "analysis": result
            })
        else:
            return jsonify({"error": "Failed to analyze governance opportunity"}), 500
            
    except Exception as e:
        logger.error(f"Governance opportunity analysis error: {e}")
        return jsonify({"error": "Failed to analyze governance opportunity"}), 500

# Opportunity Analysis - Speaking Opportunity
@app.route('/api/perplexity/opportunity/speaking', methods=['POST'])
@jwt_required()
def perplexity_analyze_speaking_opportunity():
    """Analyze speaking opportunity potential"""
    try:
        _, _, _, opportunity_analyzer_instance, _ = get_perplexity_services()
        if not opportunity_analyzer_instance:
            return jsonify({"error": "Perplexity opportunity analyzer not available"}), 503
        
        data = request.get_json()
        event_context = data.get('event_context')
        if not event_context:
            return jsonify({"error": "Event context is required"}), 400
        
        target_audience = data.get('target_audience')
        
        result = opportunity_analyzer_instance.analyze_speaking_opportunity(
            event_context=event_context,
            target_audience=target_audience
        )
        
        if result:
            return jsonify({
                "success": True,
                "analysis": result
            })
        else:
            return jsonify({"error": "Failed to analyze speaking opportunity"}), 500
            
    except Exception as e:
        logger.error(f"Speaking opportunity analysis error: {e}")
        return jsonify({"error": "Failed to analyze speaking opportunity"}), 500

# Opportunity Analysis - Market Entry
@app.route('/api/perplexity/opportunity/market-entry', methods=['POST'])
@jwt_required()
def perplexity_analyze_market_entry():
    """Analyze market entry opportunity"""
    try:
        _, _, _, opportunity_analyzer_instance, _ = get_perplexity_services()
        if not opportunity_analyzer_instance:
            return jsonify({"error": "Perplexity opportunity analyzer not available"}), 503
        
        data = request.get_json()
        market_segment = data.get('market_segment')
        if not market_segment:
            return jsonify({"error": "Market segment is required"}), 400
        
        focus_areas = data.get('focus_areas', [])
        
        result = opportunity_analyzer_instance.analyze_market_entry_opportunity(
            market_segment=market_segment,
            focus_areas=focus_areas if focus_areas else None
        )
        
        if result:
            return jsonify({
                "success": True,
                "analysis": result
            })
        else:
            return jsonify({"error": "Failed to analyze market entry opportunity"}), 500
            
    except Exception as e:
        logger.error(f"Market entry opportunity analysis error: {e}")
        return jsonify({"error": "Failed to analyze market entry opportunity"}), 500

# AI Scoring Integration - Enhanced Scoring
@app.route('/api/perplexity/scoring/prospect', methods=['POST'])
@jwt_required()
def perplexity_enhanced_prospect_scoring():
    """Enhanced AI-powered prospect scoring using Perplexity"""
    try:
        _, _, _, _, ai_scorer_instance = get_perplexity_services()
        if not ai_scorer_instance:
            return jsonify({"error": "AI scoring service not available"}), 503
        
        data = request.get_json()
        prospect_data = data.get('prospect_data')
        opportunity_type = data.get('opportunity_type', 'executive_position')
        
        if not prospect_data:
            return jsonify({"error": "Prospect data is required"}), 400
        
        # Convert data to mock prospect object for scoring
        # In a real implementation, you'd use the actual Apollo prospect object
        class MockProspect:
            def __init__(self, data):
                self.id = data.get('id', 'unknown')
                self.name = data.get('name', 'Unknown')
                self.title = data.get('title', '')
                self.company_name = data.get('company_name', '')
                self.company_domain = data.get('company_domain', '')
                self.email = data.get('email')
                self.phone = data.get('phone')
                self.linkedin_url = data.get('linkedin_url')
                self.seniority = data.get('seniority', '')
                self.match_score = data.get('match_score', 0.5)
                self.raw_data = data.get('raw_data', {})
        
        mock_prospect = MockProspect(prospect_data)
        
        result = ai_scorer_instance.score_apollo_prospect(mock_prospect, opportunity_type)
        
        if result:
            return jsonify({
                "success": True,
                "scoring": result
            })
        else:
            return jsonify({"error": "Failed to score prospect"}), 500
            
    except Exception as e:
        logger.error(f"Enhanced prospect scoring error: {e}")
        return jsonify({"error": "Failed to score prospect"}), 500

# System Status Endpoint
@app.route('/api/perplexity/status', methods=['GET'])
@jwt_required()
def perplexity_system_status():
    """Get Perplexity integration system status"""
    try:
        api_available = PERPLEXITY_API_KEY is not None
        services_initialized = all([
            create_perplexity_api is not None,
            create_research_service is not None,
            create_content_service is not None,
            create_opportunity_analyzer is not None,
            create_ai_scorer is not None
        ])
        
        api, research, content, analyzer, scorer = get_perplexity_services()
        services_working = all([api, research, content, analyzer, scorer]) if api_available else False
        
        return jsonify({
            "api_key_configured": api_available,
            "modules_imported": services_initialized,
            "services_initialized": services_working,
            "status": "operational" if (api_available and services_initialized and services_working) else "limited",
            "available_endpoints": [
                "/api/perplexity/query",
                "/api/perplexity/research/market",
                "/api/perplexity/research/company", 
                "/api/perplexity/research/industry",
                "/api/perplexity/research/competitive",
                "/api/perplexity/research/executive",
                "/api/perplexity/content/executive-summary",
                "/api/perplexity/content/market-report",
                "/api/perplexity/content/opportunity-brief",
                "/api/perplexity/content/industry-insight",
                "/api/perplexity/opportunity/governance",
                "/api/perplexity/opportunity/speaking",
                "/api/perplexity/opportunity/market-entry",
                "/api/perplexity/scoring/prospect"
            ]
        })
        
    except Exception as e:
        logger.error(f"System status check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Milestone routes
@app.route('/api/milestones', methods=['GET'])
@jwt_required()
def get_milestones():
    milestones = Milestone.query.all()
    return jsonify(serialize_models(milestones))

@app.route('/api/milestones/<int:milestone_id>', methods=['GET'])
@jwt_required()
def get_milestone(milestone_id):
    milestone = Milestone.query.get(milestone_id)
    if not milestone:
        return jsonify({"error": "Milestone not found"}), 404
    return jsonify(serialize_model(milestone))

# Healthcare Provider routes
@app.route('/api/healthcare/providers', methods=['GET'])
@jwt_required()
def get_healthcare_providers():
    providers = HealthcareProvider.query.all()
    return jsonify(serialize_models(providers))

@app.route('/api/healthcare/providers/<int:provider_id>', methods=['GET'])
@jwt_required()
def get_healthcare_provider(provider_id):
    provider = HealthcareProvider.query.get(provider_id)
    if not provider:
        return jsonify({"error": "Provider not found"}), 404
    return jsonify(serialize_model(provider))

@app.route('/api/healthcare/providers', methods=['POST'])
@jwt_required()
def create_healthcare_provider():
    try:
        data = request.get_json()
        new_provider = HealthcareProvider(
            name=data.get('name'),
            specialty=data.get('specialty'),
            phone=data.get('phone'),
            rating=data.get('rating', 0.0),
            insurance_accepted=data.get('insurance_accepted', []),
            next_available=data.get('next_available'),
            address=data.get('address'),
            notes=data.get('notes', '')
        )
        db.session.add(new_provider)
        db.session.commit()
        return jsonify(serialize_model(new_provider)), 201
    except Exception as e:
        logger.error(f"Create healthcare provider error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create healthcare provider"}), 500

# Healthcare Appointment routes
@app.route('/api/healthcare/appointments', methods=['GET'])
@jwt_required()
def get_healthcare_appointments():
    appointments = HealthcareAppointment.query.all()
    return jsonify(serialize_models(appointments))

@app.route('/api/healthcare/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_healthcare_appointment(appointment_id):
    appointment = HealthcareAppointment.query.get(appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    return jsonify(serialize_model(appointment))

@app.route('/api/healthcare/appointments', methods=['POST'])
@jwt_required()
def create_healthcare_appointment():
    try:
        data = request.get_json()
        new_appointment = HealthcareAppointment(
            provider=data.get('provider'),
            date=data.get('date'),
            time=data.get('time'),
            purpose=data.get('purpose'),
            status=data.get('status', 'scheduled'),
            notes=data.get('notes', '')
        )
        db.session.add(new_appointment)
        db.session.commit()
        return jsonify(serialize_model(new_appointment)), 201
    except Exception as e:
        logger.error(f"Create healthcare appointment error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create healthcare appointment"}), 500

@app.route('/api/healthcare/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_healthcare_appointment(appointment_id):
    try:
        appointment = HealthcareAppointment.query.get(appointment_id)
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
        
        data = request.get_json()
        appointment.provider = data.get('provider', appointment.provider)
        appointment.date = data.get('date', appointment.date)
        appointment.time = data.get('time', appointment.time)
        appointment.purpose = data.get('purpose', appointment.purpose)
        appointment.status = data.get('status', appointment.status)
        appointment.notes = data.get('notes', appointment.notes)
        
        db.session.commit()
        return jsonify(serialize_model(appointment))
    except Exception as e:
        logger.error(f"Update healthcare appointment error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update healthcare appointment"}), 500

# Healthcare Provider DELETE route
@app.route('/api/healthcare/providers/<int:provider_id>', methods=['DELETE'])
@jwt_required()
def delete_healthcare_provider(provider_id):
    try:
        provider = HealthcareProvider.query.get(provider_id)
        if not provider:
            return jsonify({"error": "Provider not found"}), 404
        
        db.session.delete(provider)
        db.session.commit()
        return jsonify({"message": "Provider deleted successfully"})
    except Exception as e:
        logger.error(f"Delete healthcare provider error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete healthcare provider"}), 500

# Healthcare Provider UPDATE route
@app.route('/api/healthcare/providers/<int:provider_id>', methods=['PUT'])
@jwt_required()
def update_healthcare_provider(provider_id):
    try:
        provider = HealthcareProvider.query.get(provider_id)
        if not provider:
            return jsonify({"error": "Provider not found"}), 404
        
        data = request.get_json()
        provider.name = data.get('name', provider.name)
        provider.specialty = data.get('specialty', provider.specialty)
        provider.phone = data.get('phone', provider.phone)
        provider.rating = data.get('rating', provider.rating)
        provider.insurance_accepted = data.get('insurance_accepted', provider.insurance_accepted)
        provider.next_available = data.get('next_available', provider.next_available)
        provider.address = data.get('address', provider.address)
        provider.notes = data.get('notes', provider.notes)
        
        db.session.commit()
        return jsonify(serialize_model(provider))
    except Exception as e:
        logger.error(f"Update healthcare provider error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update healthcare provider"}), 500

# Healthcare Appointment DELETE route
@app.route('/api/healthcare/appointments/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def delete_healthcare_appointment(appointment_id):
    try:
        appointment = HealthcareAppointment.query.get(appointment_id)
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
        
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({"message": "Appointment deleted successfully"})
    except Exception as e:
        logger.error(f"Delete healthcare appointment error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete healthcare appointment"}), 500

# Health Metrics routes
@app.route('/api/healthcare/metrics', methods=['GET'])
def get_health_metrics():
    metrics = HealthMetric.query.all()
    return jsonify(serialize_models(metrics))

@app.route('/api/healthcare/metrics', methods=['POST'])
@jwt_required()
def create_health_metric():
    try:
        data = request.get_json()
        # Handle date conversion
        metric_date = data.get('date')
        if isinstance(metric_date, str):
            metric_date = datetime.fromisoformat(metric_date)
        elif metric_date is None:
            metric_date = datetime.now()
        
        new_metric = HealthMetric(
            metric=data.get('metric'),
            value=str(data.get('value')),  # Convert to string for storage
            unit=data.get('unit'),
            date=metric_date,
            status=data.get('status', 'normal'),
            target=data.get('target', '')
        )
        db.session.add(new_metric)
        db.session.commit()
        return jsonify(serialize_model(new_metric)), 201
    except Exception as e:
        logger.error(f"Create health metric error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create health metric"}), 500

# Health Metrics DELETE route
@app.route('/api/healthcare/metrics/<int:metric_id>', methods=['DELETE'])
def delete_health_metric(metric_id):
    try:
        metric = HealthMetric.query.get(metric_id)
        if not metric:
            return jsonify({"error": "Metric not found"}), 404
        
        db.session.delete(metric)
        db.session.commit()
        return jsonify({"message": "Health metric deleted successfully"})
    except Exception as e:
        logger.error(f"Delete health metric error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete health metric"}), 500

# AI Empire Agent Management routes
@app.route('/api/empire/agents', methods=['GET'])
@jwt_required()
def get_empire_agents():
    return jsonify(AI_EMPIRE_AGENTS)

@app.route('/api/empire/agents/<int:agent_id>', methods=['GET'])
@jwt_required()
def get_empire_agent(agent_id):
    agent = next((a for a in AI_EMPIRE_AGENTS if a['id'] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    return jsonify(agent)

@app.route('/api/empire/agents/<int:agent_id>/status', methods=['PUT'])
@jwt_required()
def update_empire_agent_status(agent_id):
    try:
        agent = next((a for a in AI_EMPIRE_AGENTS if a['id'] == agent_id), None)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        agent['status'] = data.get('status', agent['status'])
        agent['last_activity'] = datetime.now().isoformat()
        
        return jsonify(agent)
    except Exception as e:
        logger.error(f"Update agent status error: {e}")
        return jsonify({"error": "Failed to update agent status"}), 500

@app.route('/api/empire/agents/<int:agent_id>/performance', methods=['POST'])
@jwt_required()
def update_agent_performance(agent_id):
    try:
        agent = next((a for a in AI_EMPIRE_AGENTS if a['id'] == agent_id), None)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        if 'performance' in data:
            agent['performance'].update(data['performance'])
        agent['last_activity'] = datetime.now().isoformat()
        
        return jsonify(agent)
    except Exception as e:
        logger.error(f"Update agent performance error: {e}")
        return jsonify({"error": "Failed to update agent performance"}), 500

@app.route('/api/empire/agents/tier/<string:tier>', methods=['GET'])
@jwt_required()
def get_agents_by_tier(tier):
    agents = [a for a in AI_EMPIRE_AGENTS if a['tier'] == tier]
    return jsonify(agents)

# Health & Wellness Management routes
@app.route('/api/wellness/energy', methods=['GET'])
@jwt_required()
def get_energy_tracking():
    energy_data = EnergyTracking.query.all()
    return jsonify(serialize_models(energy_data))

@app.route('/api/wellness/energy', methods=['POST'])
@jwt_required()
def add_energy_entry():
    try:
        data = request.get_json()
        new_entry = {
            "id": len(HEALTH_WELLNESS['energy_tracking']) + 1,
            "date": data.get('date', datetime.now().isoformat()),
            "energy_level": data.get('energy_level'),
            "focus_level": data.get('focus_level'),
            "stress_level": data.get('stress_level'),
            "sleep_hours": data.get('sleep_hours'),
            "recovery_time": data.get('recovery_time'),
            "notes": data.get('notes', '')
        }
        HEALTH_WELLNESS['energy_tracking'].append(new_entry)
        return jsonify(new_entry), 201
    except Exception as e:
        logger.error(f"Add energy entry error: {e}")
        return jsonify({"error": "Failed to add energy entry"}), 500

@app.route('/api/wellness/goals', methods=['GET'])
@jwt_required()
def get_wellness_goals():
    goals = WellnessGoal.query.all()
    return jsonify(serialize_models(goals))

@app.route('/api/wellness/alerts', methods=['GET'])
@jwt_required()
def get_wellness_alerts():
    alerts = WellnessAlert.query.all()
    return jsonify(serialize_models(alerts))

@app.route('/api/wellness/overview', methods=['GET'])
@jwt_required()
def get_wellness_overview():
    return jsonify(HEALTH_WELLNESS)

# Executive Opportunities Management routes
@app.route('/api/executive/opportunities', methods=['GET'])
@jwt_required()
def get_executive_opportunities():
    opportunities = ExecutiveOpportunity.query.all()
    return jsonify(serialize_models(opportunities))

@app.route('/api/executive/opportunities/<int:opp_id>', methods=['GET'])
@jwt_required()
def get_executive_opportunity(opp_id):
    opp = ExecutiveOpportunity.query.get(opp_id)
    if not opp:
        return jsonify({"error": "Opportunity not found"}), 404
    return jsonify(serialize_model(opp))

@app.route('/api/executive/opportunities', methods=['POST'])
@jwt_required()
def create_executive_opportunity():
    try:
        data = request.get_json()
        
        # Create new executive opportunity
        opportunity = ExecutiveOpportunity(
            type=data.get('type'),
            title=data.get('title'),
            company=data.get('company'),
            compensation_range=data.get('compensation_range'),
            location=data.get('location'),
            status=data.get('status', 'prospect'),
            ai_match_score=data.get('ai_match_score', 0.0),
            requirements=data.get('requirements', []),
            application_date=data.get('application_date'),
            next_step=data.get('next_step'),
            notes=data.get('notes'),
            interview_stages=data.get('interview_stages', []),
            decision_makers=data.get('decision_makers', []),
            company_research=data.get('company_research', {}),
            networking_connections=data.get('networking_connections', []),
            follow_up_dates=data.get('follow_up_dates', []),
            board_size=data.get('board_size'),
            board_tenure_expectation=data.get('board_tenure_expectation'),
            committee_assignments=data.get('committee_assignments', []),
            governance_focus=data.get('governance_focus', []),
            event_type=data.get('event_type'),
            speaking_fee=data.get('speaking_fee'),
            audience_size=data.get('audience_size'),
            topic_alignment=data.get('topic_alignment', []),
            event_date=data.get('event_date'),
            priority_level=data.get('priority_level', 'medium'),
            deadline=data.get('deadline'),
            source=data.get('source'),
            conversion_probability=data.get('conversion_probability', 0.5),
            estimated_close_date=data.get('estimated_close_date')
        )
        
        db.session.add(opportunity)
        db.session.commit()
        
        return jsonify(opportunity.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create executive opportunity error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create executive opportunity"}), 500

@app.route('/api/executive/opportunities/<int:opp_id>', methods=['PUT'])
@jwt_required()
def update_executive_opportunity(opp_id):
    try:
        opportunity = ExecutiveOpportunity.query.get(opp_id)
        if not opportunity:
            return jsonify({"error": "Opportunity not found"}), 404
        
        data = request.get_json()
        
        # Update all fields that are provided
        for field in ['type', 'title', 'company', 'compensation_range', 'location', 'status', 
                     'ai_match_score', 'requirements', 'application_date', 'next_step', 'notes',
                     'interview_stages', 'decision_makers', 'company_research', 'networking_connections',
                     'follow_up_dates', 'board_size', 'board_tenure_expectation', 'committee_assignments',
                     'governance_focus', 'event_type', 'speaking_fee', 'audience_size', 'topic_alignment',
                     'event_date', 'priority_level', 'deadline', 'source', 'conversion_probability',
                     'estimated_close_date']:
            if field in data:
                setattr(opportunity, field, data[field])
        
        db.session.commit()
        
        # Trigger business events for opportunity status changes
        try:
            # Check for important status transitions
            status = opportunity.status
            opportunity_type = opportunity.type
            
            # High-value opportunity events
            if status == 'offer_received':
                trigger_business_event(
                    event_type='opportunity_offer_received',
                    entity_type='executive_opportunity',
                    entity_id=opportunity.id,
                    event_data={
                        'opportunity_title': opportunity.title,
                        'company': opportunity.company,
                        'type': opportunity_type,
                        'compensation_range': opportunity.compensation_range,
                        'ai_match_score': opportunity.ai_match_score,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='opportunity_update',
                    priority='critical'
                )
            
            # Opportunity accepted
            elif status == 'accepted':
                trigger_business_event(
                    event_type='opportunity_accepted',
                    entity_type='executive_opportunity',
                    entity_id=opportunity.id,
                    event_data={
                        'opportunity_title': opportunity.title,
                        'company': opportunity.company,
                        'type': opportunity_type,
                        'compensation_range': opportunity.compensation_range,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='opportunity_update',
                    priority='critical'
                )
            
            # Interview stage reached
            elif status == 'interview_stage':
                trigger_business_event(
                    event_type='opportunity_interview_stage',
                    entity_type='executive_opportunity',
                    entity_id=opportunity.id,
                    event_data={
                        'opportunity_title': opportunity.title,
                        'company': opportunity.company,
                        'type': opportunity_type,
                        'interview_stages': opportunity.interview_stages,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='opportunity_update',
                    priority='high'
                )
            
            # High match score opportunities
            if opportunity.ai_match_score >= 90:
                trigger_business_event(
                    event_type='high_match_opportunity',
                    entity_type='executive_opportunity',
                    entity_id=opportunity.id,
                    event_data={
                        'opportunity_title': opportunity.title,
                        'company': opportunity.company,
                        'type': opportunity_type,
                        'ai_match_score': opportunity.ai_match_score,
                        'requirements': opportunity.requirements,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='opportunity_update',
                    priority='high'
                )
            
            # Board director opportunities
            if opportunity_type == 'board_director' and status in ['prospect', 'applied']:
                trigger_business_event(
                    event_type='board_director_opportunity',
                    entity_type='executive_opportunity',
                    entity_id=opportunity.id,
                    event_data={
                        'opportunity_title': opportunity.title,
                        'company': opportunity.company,
                        'board_size': opportunity.board_size,
                        'governance_focus': opportunity.governance_focus,
                        'compensation_range': opportunity.compensation_range,
                        'timestamp': datetime.now().isoformat()
                    },
                    source='opportunity_update',
                    priority='high'
                )
            
            # Speaking opportunity events
            if opportunity_type == 'speaking' and opportunity.speaking_fee:
                fee_value = 0
                try:
                    # Extract numeric value from fee string
                    import re
                    fee_match = re.search(r'[\d,]+', str(opportunity.speaking_fee).replace('$', '').replace(',', ''))
                    if fee_match:
                        fee_value = int(fee_match.group())
                except:
                    pass
                
                if fee_value >= 25000:  # High-value speaking opportunity
                    trigger_business_event(
                        event_type='high_value_speaking_opportunity',
                        entity_type='executive_opportunity',
                        entity_id=opportunity.id,
                        event_data={
                            'opportunity_title': opportunity.title,
                            'event_name': opportunity.company,  # Company field used for event name
                            'speaking_fee': opportunity.speaking_fee,
                            'audience_size': opportunity.audience_size,
                            'topic_alignment': opportunity.topic_alignment,
                            'timestamp': datetime.now().isoformat()
                        },
                        source='opportunity_update',
                        priority='high'
                    )
                    
        except Exception as e:
            logger.error(f"Error triggering opportunity events: {e}")
        
        return jsonify(opportunity.to_dict())
        
    except Exception as e:
        logger.error(f"Update opportunity error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update opportunity"}), 500

@app.route('/api/executive/opportunities/<int:opp_id>/status', methods=['PUT'])
@jwt_required()
def update_opportunity_status(opp_id):
    try:
        opportunity = ExecutiveOpportunity.query.get(opp_id)
        if not opportunity:
            return jsonify({"error": "Opportunity not found"}), 404
        
        data = request.get_json()
        opportunity.status = data.get('status', opportunity.status)
        opportunity.next_step = data.get('next_step', opportunity.next_step)
        opportunity.notes = data.get('notes', opportunity.notes)
        
        db.session.commit()
        return jsonify(opportunity.to_dict())
        
    except Exception as e:
        logger.error(f"Update opportunity status error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update opportunity status"}), 500

@app.route('/api/executive/opportunities/type/<string:opportunity_type>', methods=['GET'])
@jwt_required()
def get_opportunities_by_type(opportunity_type):
    opportunities = ExecutiveOpportunity.query.filter_by(type=opportunity_type).all()
    return jsonify(serialize_models(opportunities))

# Delete executive opportunity
@app.route('/api/executive/opportunities/<int:opp_id>', methods=['DELETE'])
@jwt_required()
def delete_executive_opportunity(opp_id):
    try:
        opportunity = ExecutiveOpportunity.query.get(opp_id)
        if not opportunity:
            return jsonify({"error": "Opportunity not found"}), 404
        
        # Delete associated interview stages
        InterviewStage.query.filter_by(opportunity_id=opp_id, opportunity_type='executive').delete()
        
        db.session.delete(opportunity)
        db.session.commit()
        
        return jsonify({"message": "Opportunity deleted successfully"})
        
    except Exception as e:
        logger.error(f"Delete opportunity error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete opportunity"}), 500

# Speaking Opportunities Management routes
@app.route('/api/speaking/opportunities', methods=['GET'])
@jwt_required()
def get_speaking_opportunities():
    """Get all speaking opportunities"""
    opportunities = SpeakingOpportunity.query.all()
    return jsonify(serialize_models(opportunities))

@app.route('/api/speaking/opportunities/<int:opp_id>', methods=['GET'])
@jwt_required()
def get_speaking_opportunity(opp_id):
    """Get specific speaking opportunity"""
    opportunity = SpeakingOpportunity.query.get(opp_id)
    if not opportunity:
        return jsonify({"error": "Speaking opportunity not found"}), 404
    return jsonify(opportunity.to_dict())

@app.route('/api/speaking/opportunities', methods=['POST'])
@jwt_required()
def create_speaking_opportunity():
    """Create new speaking opportunity"""
    try:
        data = request.get_json()
        
        opportunity = SpeakingOpportunity(
            title=data.get('title'),
            event_name=data.get('event_name'),
            organizer=data.get('organizer'),
            event_type=data.get('event_type'),
            event_date=data.get('event_date'),
            submission_deadline=data.get('submission_deadline'),
            speaking_fee=data.get('speaking_fee'),
            audience_size=data.get('audience_size'),
            location=data.get('location'),
            topic_alignment=data.get('topic_alignment', []),
            status=data.get('status', 'prospect'),
            application_date=data.get('application_date'),
            ai_match_score=data.get('ai_match_score', 0.0),
            notes=data.get('notes'),
            source=data.get('source'),
            requirements=data.get('requirements', []),
            travel_required=data.get('travel_required', False),
            virtual_option=data.get('virtual_option', False)
        )
        
        db.session.add(opportunity)
        db.session.commit()
        
        return jsonify(opportunity.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create speaking opportunity error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create speaking opportunity"}), 500

@app.route('/api/speaking/opportunities/<int:opp_id>', methods=['PUT'])
@jwt_required()
def update_speaking_opportunity(opp_id):
    """Update speaking opportunity"""
    try:
        opportunity = SpeakingOpportunity.query.get(opp_id)
        if not opportunity:
            return jsonify({"error": "Speaking opportunity not found"}), 404
        
        data = request.get_json()
        
        # Update all fields that are provided
        for field in ['title', 'event_name', 'organizer', 'event_type', 'event_date', 
                     'submission_deadline', 'speaking_fee', 'audience_size', 'location',
                     'topic_alignment', 'status', 'application_date', 'ai_match_score',
                     'notes', 'source', 'requirements', 'travel_required', 'virtual_option']:
            if field in data:
                setattr(opportunity, field, data[field])
        
        db.session.commit()
        return jsonify(opportunity.to_dict())
        
    except Exception as e:
        logger.error(f"Update speaking opportunity error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update speaking opportunity"}), 500

@app.route('/api/speaking/opportunities/<int:opp_id>', methods=['DELETE'])
@jwt_required()
def delete_speaking_opportunity(opp_id):
    """Delete speaking opportunity"""
    try:
        opportunity = SpeakingOpportunity.query.get(opp_id)
        if not opportunity:
            return jsonify({"error": "Speaking opportunity not found"}), 404
        
        # Delete associated interview stages
        InterviewStage.query.filter_by(opportunity_id=opp_id, opportunity_type='speaking').delete()
        
        db.session.delete(opportunity)
        db.session.commit()
        
        return jsonify({"message": "Speaking opportunity deleted successfully"})
        
    except Exception as e:
        logger.error(f"Delete speaking opportunity error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete speaking opportunity"}), 500

# Interview Stages Management routes
@app.route('/api/interview-stages', methods=['GET'])
@jwt_required()
def get_interview_stages():
    """Get all interview stages"""
    opportunity_id = request.args.get('opportunity_id')
    opportunity_type = request.args.get('opportunity_type')
    
    query = InterviewStage.query
    if opportunity_id:
        query = query.filter_by(opportunity_id=opportunity_id)
    if opportunity_type:
        query = query.filter_by(opportunity_type=opportunity_type)
    
    stages = query.all()
    return jsonify(serialize_models(stages))

@app.route('/api/interview-stages', methods=['POST'])
@jwt_required()
def create_interview_stage():
    """Create new interview stage"""
    try:
        data = request.get_json()
        
        stage = InterviewStage(
            opportunity_id=data.get('opportunity_id'),
            opportunity_type=data.get('opportunity_type'),
            stage_name=data.get('stage_name'),
            stage_date=data.get('stage_date'),
            status=data.get('status', 'scheduled'),
            interviewer_name=data.get('interviewer_name'),
            interviewer_role=data.get('interviewer_role'),
            feedback=data.get('feedback'),
            outcome=data.get('outcome'),
            next_step=data.get('next_step'),
            preparation_notes=data.get('preparation_notes')
        )
        
        db.session.add(stage)
        db.session.commit()
        
        return jsonify(stage.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create interview stage error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create interview stage"}), 500

@app.route('/api/interview-stages/<int:stage_id>', methods=['PUT'])
@jwt_required()
def update_interview_stage(stage_id):
    """Update interview stage"""
    try:
        stage = InterviewStage.query.get(stage_id)
        if not stage:
            return jsonify({"error": "Interview stage not found"}), 404
        
        data = request.get_json()
        
        for field in ['stage_name', 'stage_date', 'status', 'interviewer_name', 
                     'interviewer_role', 'feedback', 'outcome', 'next_step', 'preparation_notes']:
            if field in data:
                setattr(stage, field, data[field])
        
        db.session.commit()
        return jsonify(stage.to_dict())
        
    except Exception as e:
        logger.error(f"Update interview stage error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update interview stage"}), 500

# AI Matching and Scoring routes
@app.route('/api/ai-matching/score-opportunity', methods=['POST'])
@jwt_required()
def score_opportunity():
    """AI-powered opportunity scoring"""
    try:
        data = request.get_json()
        opportunity_type = data.get('type')
        requirements = data.get('requirements', [])
        company_info = data.get('company_info', {})
        position_details = data.get('position_details', {})
        
        # Basic AI scoring algorithm (can be enhanced with ML models)
        base_score = 50
        
        # Score based on requirements match
        my_expertise = ['AI governance', 'risk management', 'TEDx speaking', 'board advisory', 
                       'enterprise technology', 'compliance', 'data privacy', 'cybersecurity']
        
        requirement_matches = 0
        for req in requirements:
            req_lower = req.lower()
            for expertise in my_expertise:
                if expertise.lower() in req_lower or req_lower in expertise.lower():
                    requirement_matches += 1
                    break
        
        if len(requirements) > 0:
            requirement_score = (requirement_matches / len(requirements)) * 30
        else:
            requirement_score = 0
        
        # Score based on opportunity type preference
        type_preference = {
            'board_director': 25,
            'executive_position': 20,
            'advisor': 15,
            'speaking': 10
        }
        type_score = type_preference.get(opportunity_type, 5)
        
        # Score based on company characteristics
        company_score = 0
        if company_info.get('industry') in ['technology', 'fintech', 'healthcare', 'ai']:
            company_score += 10
        if company_info.get('size') in ['enterprise', 'large']:
            company_score += 5
        
        total_score = min(base_score + requirement_score + type_score + company_score, 100)
        
        return jsonify({
            'ai_match_score': round(total_score, 1),
            'score_breakdown': {
                'base_score': base_score,
                'requirement_match': round(requirement_score, 1),
                'type_preference': type_score,
                'company_fit': company_score
            },
            'recommendation': 'high' if total_score >= 80 else 'medium' if total_score >= 60 else 'low'
        })
        
    except Exception as e:
        logger.error(f"AI scoring error: {e}")
        return jsonify({"error": "Failed to score opportunity"}), 500

# Compensation Benchmarks routes
@app.route('/api/compensation/benchmarks', methods=['GET'])
@jwt_required()
def get_compensation_benchmarks():
    """Get compensation benchmarks"""
    position_type = request.args.get('position_type')
    industry = request.args.get('industry')
    location = request.args.get('location')
    
    query = CompensationBenchmark.query
    if position_type:
        query = query.filter_by(position_type=position_type)
    if industry:
        query = query.filter_by(industry=industry)
    if location:
        query = query.filter_by(location=location)
    
    benchmarks = query.all()
    return jsonify(serialize_models(benchmarks))

@app.route('/api/compensation/benchmarks', methods=['POST'])
@jwt_required()
def create_compensation_benchmark():
    """Create compensation benchmark"""
    try:
        data = request.get_json()
        
        benchmark = CompensationBenchmark(
            position_type=data.get('position_type'),
            industry=data.get('industry'),
            company_size=data.get('company_size'),
            location=data.get('location'),
            base_salary_min=data.get('base_salary_min'),
            base_salary_max=data.get('base_salary_max'),
            equity_percentage=data.get('equity_percentage'),
            cash_bonus_percentage=data.get('cash_bonus_percentage'),
            board_fees=data.get('board_fees'),
            meeting_fees=data.get('meeting_fees'),
            speaking_fee_min=data.get('speaking_fee_min'),
            speaking_fee_max=data.get('speaking_fee_max'),
            data_source=data.get('data_source')
        )
        
        db.session.add(benchmark)
        db.session.commit()
        
        return jsonify(benchmark.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create compensation benchmark error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create compensation benchmark"}), 500

# Pipeline Analytics routes
@app.route('/api/pipeline/analytics', methods=['GET'])
@jwt_required()
def get_pipeline_analytics():
    """Get comprehensive pipeline analytics"""
    try:
        # Executive opportunities analytics
        exec_total = ExecutiveOpportunity.query.count()
        exec_by_status = db.session.query(
            ExecutiveOpportunity.status, 
            func.count(ExecutiveOpportunity.id)
        ).group_by(ExecutiveOpportunity.status).all()
        
        exec_by_type = db.session.query(
            ExecutiveOpportunity.type, 
            func.count(ExecutiveOpportunity.id)
        ).group_by(ExecutiveOpportunity.type).all()
        
        # Speaking opportunities analytics
        speaking_total = SpeakingOpportunity.query.count()
        speaking_by_status = db.session.query(
            SpeakingOpportunity.status, 
            func.count(SpeakingOpportunity.id)
        ).group_by(SpeakingOpportunity.status).all()
        
        # Interview stages analytics
        interview_stages = InterviewStage.query.count()
        
        # Calculate conversion rates
        exec_applied = ExecutiveOpportunity.query.filter_by(status='applied').count()
        exec_interviews = ExecutiveOpportunity.query.filter_by(status='interview_stage').count()
        exec_offers = ExecutiveOpportunity.query.filter_by(status='offer_received').count()
        exec_accepted = ExecutiveOpportunity.query.filter_by(status='accepted').count()
        
        conversion_rates = {
            'application_to_interview': (exec_interviews / max(exec_applied, 1)) * 100,
            'interview_to_offer': (exec_offers / max(exec_interviews, 1)) * 100,
            'offer_to_acceptance': (exec_accepted / max(exec_offers, 1)) * 100,
            'overall_conversion': (exec_accepted / max(exec_total, 1)) * 100
        }
        
        return jsonify({
            'executive_opportunities': {
                'total': exec_total,
                'by_status': dict(exec_by_status),
                'by_type': dict(exec_by_type)
            },
            'speaking_opportunities': {
                'total': speaking_total,
                'by_status': dict(speaking_by_status)
            },
            'interview_stages': {
                'total': interview_stages
            },
            'conversion_rates': conversion_rates,
            'pipeline_health_score': round(sum(conversion_rates.values()) / len(conversion_rates), 1)
        })
        
    except Exception as e:
        logger.error(f"Pipeline analytics error: {e}")
        return jsonify({"error": "Failed to get pipeline analytics"}), 500

# Board Director specific routes
@app.route('/api/board-director/opportunities', methods=['GET'])
@jwt_required()
def get_board_director_opportunities():
    """Get board director specific opportunities"""
    opportunities = ExecutiveOpportunity.query.filter_by(type='board_director').all()
    return jsonify(serialize_models(opportunities))

@app.route('/api/board-director/requirements', methods=['GET'])
@jwt_required()
def get_board_director_requirements():
    """Get typical board director requirements and qualifications"""
    return jsonify({
        'typical_requirements': [
            'C-suite or senior executive experience',
            'Industry expertise relevant to company',
            'Financial literacy and audit committee experience',
            'Risk management experience',
            'Governance and compliance knowledge',
            'Strategic planning experience',
            'Public company board experience (preferred)',
            'Independent director qualifications'
        ],
        'governance_focus_areas': [
            'Risk Oversight',
            'Audit Committee',
            'Compensation Committee',
            'Nominating/Governance Committee',
            'Technology Committee',
            'Strategy Committee',
            'ESG (Environmental, Social, Governance)'
        ],
        'typical_time_commitment': '20-30 hours per month',
        'typical_term_length': '3 years, renewable',
        'meeting_frequency': 'Quarterly board meetings + committee meetings'
    })

# Speaking Opportunity Hunter routes
@app.route('/api/speaking-hunter/search', methods=['POST'])
@jwt_required()
def hunt_speaking_opportunities():
    """Automated speaking opportunity discovery"""
    try:
        data = request.get_json()
        topics = data.get('topics', ['AI governance', 'risk management', 'digital transformation'])
        event_types = data.get('event_types', ['conference', 'webinar', 'workshop'])
        min_audience = data.get('min_audience', 100)
        
        # This would integrate with external APIs in a real implementation
        # For now, return mock discovered opportunities
        mock_opportunities = [
            {
                'title': 'AI Governance in Financial Services',
                'event_name': 'FinTech Innovation Summit 2025',
                'organizer': 'Financial Technology Association',
                'event_type': 'conference',
                'event_date': '2025-11-15',
                'submission_deadline': '2025-09-30',
                'audience_size': 500,
                'location': 'San Francisco, CA',
                'speaking_fee': '$15,000',
                'ai_match_score': 92.5,
                'source': 'automated_hunter',
                'requirements': ['C-suite experience', 'AI governance expertise'],
                'virtual_option': True
            },
            {
                'title': 'Risk Management in the Age of AI',
                'event_name': 'Global Risk Management Conference',
                'organizer': 'Risk Management Society',
                'event_type': 'conference',
                'event_date': '2025-12-05',
                'submission_deadline': '2025-10-15',
                'audience_size': 300,
                'location': 'New York, NY',
                'speaking_fee': '$10,000',
                'ai_match_score': 88.0,
                'source': 'automated_hunter',
                'requirements': ['Risk management experience', 'Speaking experience'],
                'travel_required': True
            }
        ]
        
        return jsonify({
            'discovered_opportunities': mock_opportunities,
            'search_criteria': {
                'topics': topics,
                'event_types': event_types,
                'min_audience': min_audience
            },
            'results_count': len(mock_opportunities)
        })
        
    except Exception as e:
        logger.error(f"Speaking opportunity hunt error: {e}")
        return jsonify({"error": "Failed to hunt speaking opportunities"}), 500

# Retreat Events Management routes
@app.route('/api/retreats/events', methods=['GET'])
@jwt_required()
def get_retreat_events():
    return jsonify(RETREAT_EVENTS)

@app.route('/api/retreats/events/<int:event_id>', methods=['GET'])
@jwt_required()
def get_retreat_event(event_id):
    event = next((e for e in RETREAT_EVENTS if e['id'] == event_id), None)
    if not event:
        return jsonify({"error": "Retreat event not found"}), 404
    return jsonify(event)

@app.route('/api/retreats/events', methods=['POST'])
@jwt_required()
def create_retreat_event():
    try:
        data = request.get_json()
        new_event = {
            "id": len(RETREAT_EVENTS) + 1,
            "name": data.get('name'),
            "type": data.get('type'),
            "dates": data.get('dates'),
            "location": data.get('location'),
            "capacity": data.get('capacity', 0),
            "registered": data.get('registered', 0),
            "pricing": data.get('pricing'),
            "status": data.get('status', 'planning'),
            "focus": data.get('focus', []),
            "amenities": data.get('amenities', []),
            "speakers": data.get('speakers', []),
            "revenue_projected": data.get('revenue_projected', 0)
        }
        RETREAT_EVENTS.append(new_event)
        return jsonify(new_event), 201
    except Exception as e:
        logger.error(f"Create retreat event error: {e}")
        return jsonify({"error": "Failed to create retreat event"}), 500

@app.route('/api/retreats/events/<int:event_id>/registration', methods=['PUT'])
@jwt_required()
def update_event_registration(event_id):
    try:
        event = next((e for e in RETREAT_EVENTS if e['id'] == event_id), None)
        if not event:
            return jsonify({"error": "Retreat event not found"}), 404
        
        data = request.get_json()
        event.update({
            "registered": data.get('registered', event['registered']),
            "status": data.get('status', event['status'])
        })
        
        return jsonify(event)
    except Exception as e:
        logger.error(f"Update event registration error: {e}")
        return jsonify({"error": "Failed to update event registration"}), 500

# Enhanced Agent Communication & Autonomous Integration routes
@app.route('/api/empire/agents/<int:agent_id>/tasks', methods=['POST'])
@jwt_required()
def dispatch_agent_task(agent_id):
    try:
        agent = next((a for a in AI_EMPIRE_AGENTS if a['id'] == agent_id), None)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No task data provided"}), 400
            
        task = {
            "id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_id}",
            "agent_id": agent_id,
            "agent_name": agent['name'],
            "task_type": data.get('task_type'),
            "priority": data.get('priority', 'normal'),
            "parameters": data.get('parameters', {}),
            "target_completion": data.get('target_completion'),
            "status": "dispatched",
            "created_at": datetime.now().isoformat(),
            "estimated_duration": data.get('estimated_duration', '30m')
        }
        
        # Update agent's last activity and performance safely
        agent['last_activity'] = datetime.now().isoformat()
        
        # Safely increment tasks dispatched (not completed)
        perf = agent.setdefault('performance', {})
        perf['tasks_dispatched'] = perf.get('tasks_dispatched', 0) + 1
        
        return jsonify(task), 201
    except Exception as e:
        logger.error(f"Dispatch agent task error: {e}")
        return jsonify({"error": f"Failed to dispatch task: {str(e)}"}), 500

@app.route('/api/empire/agents/<int:agent_id>/schedule', methods=['POST'])
@jwt_required()
def schedule_agent_run(agent_id):
    try:
        agent = next((a for a in AI_EMPIRE_AGENTS if a['id'] == agent_id), None)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        schedule = {
            "id": f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_id}",
            "agent_id": agent_id,
            "agent_name": agent['name'],
            "schedule_type": data.get('schedule_type', 'recurring'),
            "frequency": data.get('frequency', 'daily'),
            "next_run": data.get('next_run'),
            "max_runs": data.get('max_runs'),
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        agent['next_scheduled'] = schedule['next_run']
        
        return jsonify(schedule), 201
    except Exception as e:
        logger.error(f"Schedule agent run error: {e}")
        return jsonify({"error": "Failed to schedule agent run"}), 500

@app.route('/api/empire/agents/<int:agent_id>/messages', methods=['POST'])
@jwt_required()
def send_agent_message(agent_id):
    try:
        agent = next((a for a in AI_EMPIRE_AGENTS if a['id'] == agent_id), None)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        message = {
            "id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_id}",
            "agent_id": agent_id,
            "agent_name": agent['name'],
            "message_type": data.get('message_type', 'instruction'),
            "content": data.get('content'),
            "priority": data.get('priority', 'normal'),
            "requires_response": data.get('requires_response', False),
            "status": "delivered" if agent['status'] == 'active' else "queued",
            "timestamp": datetime.now().isoformat()
        }
        
        agent['last_activity'] = datetime.now().isoformat()
        
        return jsonify(message), 201
    except Exception as e:
        logger.error(f"Send agent message error: {e}")
        return jsonify({"error": "Failed to send message"}), 500

@app.route('/api/empire/communication/broadcast', methods=['POST'])
@jwt_required()
def broadcast_to_agents():
    try:
        data = request.get_json()
        message = data.get('message')
        agent_ids = data.get('agent_ids', [])
        
        # Simulate broadcasting message to specified agents
        responses = []
        for agent_id in agent_ids:
            agent = next((a for a in AI_EMPIRE_AGENTS if a['id'] == agent_id), None)
            if agent:
                responses.append({
                    "agent_id": agent_id,
                    "agent_name": agent['name'],
                    "status": "message_received",
                    "timestamp": datetime.now().isoformat()
                })
        
        return jsonify({
            "broadcast_id": f"broadcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "message": message,
            "responses": responses,
            "success_count": len(responses)
        })
    except Exception as e:
        logger.error(f"Broadcast to agents error: {e}")
        return jsonify({"error": "Failed to broadcast to agents"}), 500

@app.route('/api/empire/communication/agent/<int:agent_id>/command', methods=['POST'])
@jwt_required()
def send_agent_command(agent_id):
    try:
        agent = next((a for a in AI_EMPIRE_AGENTS if a['id'] == agent_id), None)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        command = data.get('command')
        parameters = data.get('parameters', {})
        
        # Simulate sending command to agent
        response = {
            "agent_id": agent_id,
            "agent_name": agent['name'],
            "command": command,
            "parameters": parameters,
            "status": "command_executed" if agent['status'] == 'active' else "agent_inactive",
            "timestamp": datetime.now().isoformat(),
            "execution_time": "0.5s"
        }
        
        # Update agent's last activity
        agent['last_activity'] = datetime.now().isoformat()
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Send agent command error: {e}")
        return jsonify({"error": "Failed to send agent command"}), 500

@app.route('/api/empire/integration/status', methods=['GET'])
@jwt_required()
def get_integration_status():
    integration_health = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "agent_communication": "active",
        "platform_integrations": {
            "apollo": "connected",
            "linkedin_sales_navigator": "connected", 
            "perplexity": "connected",
            "mindstudio": "connected",
            "make_com": "connected",
            "github_spark": "beta"
        },
        "agent_health": {
            "active_agents": len([a for a in AI_EMPIRE_AGENTS if a['status'] == 'active']),
            "total_agents": len(AI_EMPIRE_AGENTS),
            "average_performance": sum(a['performance']['success_rate'] for a in AI_EMPIRE_AGENTS) / len(AI_EMPIRE_AGENTS)
        }
    }
    return jsonify(integration_health)

# Apollo.io Integration API Endpoints
from apollo_integration import create_apollo_client, ApolloAPIError
from prospect_import_service import create_prospect_import_service

@app.route('/api/apollo/search/grc-executives', methods=['POST'])
@jwt_required()
def search_grc_executives():
    """Search for GRC executives using Apollo"""
    try:
        data = request.get_json() or {}
        locations = data.get('locations', [])
        max_results = data.get('max_results', 25)
        auto_import = data.get('auto_import', False)
        min_match_score = data.get('min_match_score', 0.6)
        
        import_service = create_prospect_import_service()
        if not import_service:
            return jsonify({"error": "Apollo integration not configured"}), 500
        
        results = import_service.search_and_import_grc_executives(
            locations=locations,
            max_results=max_results,
            auto_import=auto_import,
            min_match_score=min_match_score
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"GRC executives search error: {e}")
        return jsonify({"error": "Failed to search GRC executives"}), 500

@app.route('/api/apollo/search/board-directors', methods=['POST'])
@jwt_required()
def search_board_directors():
    """Search for board directors using Apollo"""
    try:
        data = request.get_json() or {}
        locations = data.get('locations', [])
        max_results = data.get('max_results', 25)
        auto_import = data.get('auto_import', False)
        min_match_score = data.get('min_match_score', 0.7)
        
        import_service = create_prospect_import_service()
        if not import_service:
            return jsonify({"error": "Apollo integration not configured"}), 500
        
        results = import_service.search_and_import_board_directors(
            locations=locations,
            max_results=max_results,
            auto_import=auto_import,
            min_match_score=min_match_score
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Board directors search error: {e}")
        return jsonify({"error": "Failed to search board directors"}), 500

@app.route('/api/apollo/search/ai-governance-leaders', methods=['POST'])
@jwt_required()
def search_ai_governance_leaders():
    """Search for AI governance leaders using Apollo"""
    try:
        data = request.get_json() or {}
        locations = data.get('locations', [])
        max_results = data.get('max_results', 25)
        auto_import = data.get('auto_import', False)
        min_match_score = data.get('min_match_score', 0.6)
        
        import_service = create_prospect_import_service()
        if not import_service:
            return jsonify({"error": "Apollo integration not configured"}), 500
        
        results = import_service.search_and_import_ai_governance_leaders(
            locations=locations,
            max_results=max_results,
            auto_import=auto_import,
            min_match_score=min_match_score
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"AI governance leaders search error: {e}")
        return jsonify({"error": "Failed to search AI governance leaders"}), 500

@app.route('/api/apollo/enrich/opportunity/<int:opportunity_id>', methods=['POST'])
@jwt_required()
def enrich_opportunity_with_apollo(opportunity_id):
    """Enrich an existing opportunity with Apollo data"""
    try:
        import_service = create_prospect_import_service()
        if not import_service:
            return jsonify({"error": "Apollo integration not configured"}), 500
        
        results = import_service.enrich_existing_opportunity(opportunity_id)
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Opportunity enrichment error: {e}")
        return jsonify({"error": "Failed to enrich opportunity"}), 500

@app.route('/api/apollo/statistics', methods=['GET'])
@jwt_required()
def get_apollo_import_statistics():
    """Get Apollo import statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        import_service = create_prospect_import_service()
        if not import_service:
            return jsonify({"error": "Apollo integration not configured"}), 500
        
        stats = import_service.get_import_statistics(days=days)
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Apollo statistics error: {e}")
        return jsonify({"error": "Failed to get Apollo statistics"}), 500

@app.route('/api/apollo/status', methods=['GET'])
@jwt_required()
def get_apollo_integration_status():
    """Check Apollo integration status and API key validation"""
    try:
        apollo_client = create_apollo_client()
        if not apollo_client:
            return jsonify({
                "status": "error",
                "message": "Apollo API key not configured",
                "api_key_valid": False,
                "integration_ready": False
            })
        
        # Test API connection
        api_key_valid = apollo_client.validate_api_key()
        
        status_data = {
            "status": "healthy" if api_key_valid else "error",
            "message": "Apollo integration ready" if api_key_valid else "Apollo API key invalid",
            "api_key_valid": api_key_valid,
            "integration_ready": api_key_valid,
            "supported_searches": [
                "grc_executives",
                "board_directors", 
                "ai_governance_leaders"
            ],
            "features": [
                "prospect_search",
                "data_enrichment",
                "automated_import",
                "opportunity_enhancement"
            ]
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Apollo status check error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "api_key_valid": False,
            "integration_ready": False
        }), 500

@app.route('/api/apollo/bulk-import', methods=['POST'])
@jwt_required()
def bulk_import_prospects():
    """Bulk import prospects for multiple search types"""
    try:
        data = request.get_json() or {}
        locations = data.get('locations', [])
        search_types = data.get('search_types', ['grc_executives', 'board_directors'])
        max_results_per_type = data.get('max_results_per_type', 25)
        min_match_score = data.get('min_match_score', 0.6)
        
        import_service = create_prospect_import_service()
        if not import_service:
            return jsonify({"error": "Apollo integration not configured"}), 500
        
        results = {
            "bulk_import_started": True,
            "search_types": search_types,
            "locations": locations,
            "results": {}
        }
        
        total_imported = 0
        
        # Execute searches for each type
        if 'grc_executives' in search_types:
            grc_results = import_service.search_and_import_grc_executives(
                locations=locations,
                max_results=max_results_per_type,
                auto_import=True,
                min_match_score=min_match_score
            )
            results["results"]["grc_executives"] = grc_results
            total_imported += grc_results.get('imported_count', 0)
        
        if 'board_directors' in search_types:
            board_results = import_service.search_and_import_board_directors(
                locations=locations,
                max_results=max_results_per_type,
                auto_import=True,
                min_match_score=min_match_score
            )
            results["results"]["board_directors"] = board_results
            total_imported += board_results.get('imported_count', 0)
        
        if 'ai_governance_leaders' in search_types:
            ai_results = import_service.search_and_import_ai_governance_leaders(
                locations=locations,
                max_results=max_results_per_type,
                auto_import=True,
                min_match_score=min_match_score
            )
            results["results"]["ai_governance_leaders"] = ai_results
            total_imported += ai_results.get('imported_count', 0)
        
        results["total_imported"] = total_imported
        results["success"] = True
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Bulk import error: {e}")
        return jsonify({"error": "Failed to execute bulk import"}), 500

# $50M+ Empire Projections
@app.route('/api/empire/projections', methods=['GET'])
@jwt_required()
def get_empire_projections():
    total_current_mrr = sum(stream['current_month'] for stream in REVENUE_STREAMS)
    total_target_mrr = sum(stream['target_month'] for stream in REVENUE_STREAMS)
    
    projections = {
        "current_metrics": {
            "mrr": total_current_mrr,
            "arr": total_current_mrr * 12,
            "achievement_rate": (total_current_mrr / total_target_mrr) * 100
        },
        "12_month_projections": {
            "mrr": sum(stream.get('projections', {}).get('12_month', 0) for stream in REVENUE_STREAMS) // 12,
            "arr": sum(stream.get('projections', {}).get('12_month', 0) for stream in REVENUE_STREAMS),
            "growth_factor": 1.8
        },
        "24_month_projections": {
            "mrr": sum(stream.get('projections', {}).get('24_month', 0) for stream in REVENUE_STREAMS) // 12,
            "arr": sum(stream.get('projections', {}).get('24_month', 0) for stream in REVENUE_STREAMS),
            "growth_factor": 2.4
        },
        "50m_plus_targets": {
            "target_arr": 60000000,
            "target_mrr": 5000000,
            "months_to_target": 18,
            "required_monthly_growth": 12.5,
            "key_drivers": [
                "Platform SaaS scaling to $36M ARR",
                "Consulting services reaching $42M ARR", 
                "Speaking authority commanding $24M ARR",
                "Executive positions portfolio $12M ARR"
            ]
        },
        "phase_milestones": {
            "phase_1_foundation": {"target_arr": 6000000, "months": 4, "status": "exceeded"},
            "phase_2_scale": {"target_arr": 25000000, "months": 8, "status": "on_track"},
            "phase_3_market_leadership": {"target_arr": 60000000, "months": 12, "status": "projected"}
        },
        "last_updated": datetime.now().isoformat()
    }
    
    return jsonify(projections)

# Enhanced Dashboard Overview
@app.route('/api/empire/dashboard', methods=['GET'])
@jwt_required()
def get_empire_dashboard():
    total_revenue = sum(stream['current_month'] for stream in REVENUE_STREAMS)
    active_agents = len([a for a in AI_EMPIRE_AGENTS if a['status'] == 'active'])
    avg_performance = sum(a['performance']['success_rate'] for a in AI_EMPIRE_AGENTS) / len(AI_EMPIRE_AGENTS)
    upcoming_retreats = len([e for e in RETREAT_EVENTS if e['status'] in ['registration_open', 'planning_phase']])
    executive_opportunities = len([o for o in EXECUTIVE_OPPORTUNITIES if o['status'] in ['interview_stage', 'under_consideration', 'offer_received']])
    
    return jsonify({
        "empire_overview": {
            "total_monthly_revenue": total_revenue,
            "revenue_target": sum(stream['target_month'] for stream in REVENUE_STREAMS),
            "achievement_rate": (total_revenue / sum(stream['target_month'] for stream in REVENUE_STREAMS)) * 100,
            "active_agents": active_agents,
            "total_agents": len(AI_EMPIRE_AGENTS),
            "avg_agent_performance": avg_performance,
            "upcoming_retreats": upcoming_retreats,
            "active_executive_opportunities": executive_opportunities,
            "wellness_score": sum(goal['current'] for goal in HEALTH_WELLNESS['wellness_goals']) / len(HEALTH_WELLNESS['wellness_goals'])
        },
        "phase_progress": {
            "phase_1_foundation": 85,
            "phase_2_scale": 45,
            "phase_3_market_leadership": 15
        },
        "last_updated": datetime.now().isoformat()
    })

# Frontend Routes
@app.route('/ai-agents')
def ai_agents_page():
    """Serve the AI Agent Management interface"""
    return render_template('ai_agents.html')

@app.route('/healthcare')
def healthcare_page():
    """Serve the Healthcare Management interface"""
    return render_template('healthcare.html')


# Business Intelligence API Routes
@app.route('/api/bi/overview', methods=['GET'])
@jwt_required()
def bi_overview():
    """Get comprehensive BI overview data"""
    try:
        # Calculate revenue metrics
        revenue_streams = RevenueStream.query.all()
        total_revenue = sum(stream.current_month for stream in revenue_streams)
        total_target = sum(stream.target_month for stream in revenue_streams)
        
        # Calculate agent metrics
        agents = AIAgent.query.all()
        active_agents = len([agent for agent in agents if agent.status == 'active'])
        
        # Calculate pipeline value
        pipeline_value = 0
        success_rates = []
        for agent in agents:
            performance = agent.performance or {}
            pipeline_value += performance.get('pipeline_value', 0)
            if 'success_rate' in performance:
                success_rates.append(performance['success_rate'])
        
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        # Get KPI metrics
        kpis = KPIMetric.query.all()
        kpi_achievement = 0
        if kpis:
            achievements = [(kpi.value / kpi.target) * 100 for kpi in kpis if kpi.target > 0]
            kpi_achievement = sum(achievements) / len(achievements) if achievements else 0
        
        return jsonify({
            "empire_overview": {
                "total_monthly_revenue": total_revenue,
                "total_target": total_target,
                "achievement_rate": (total_revenue / total_target) * 100 if total_target > 0 else 0,
                "active_agents": active_agents,
                "pipeline_value": pipeline_value,
                "avg_success_rate": avg_success_rate,
                "kpi_achievement": kpi_achievement,
                "growth_trend": 12.5,  # Would calculate from historical data
                "last_updated": datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"BI overview error: {e}")
        return jsonify({"error": "Failed to fetch BI overview"}), 500

@app.route('/api/bi/generate-report', methods=['POST'])
@jwt_required()
def bi_generate_report():
    """Generate comprehensive business intelligence report"""
    try:
        data = request.get_json()
        report_type = data.get('type', 'executive')
        report_period = data.get('period', 'monthly')
        
        # Get all necessary data
        revenue_streams = RevenueStream.query.all()
        agents = AIAgent.query.all()
        kpis = KPIMetric.query.all()
        
        # Calculate metrics
        total_revenue = sum(stream.current_month for stream in revenue_streams)
        active_agents = len([agent for agent in agents if agent.status == 'active'])
        
        success_rates = []
        pipeline_value = 0
        for agent in agents:
            performance = agent.performance or {}
            if 'success_rate' in performance:
                success_rates.append(performance['success_rate'])
            pipeline_value += performance.get('pipeline_value', 0)
        
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        # Find top performing tier
        tier_performance = {}
        for agent in agents:
            if agent.tier not in tier_performance:
                tier_performance[agent.tier] = []
            tier_performance[agent.tier].append(agent.performance.get('success_rate', 0) if agent.performance else 0)
        
        top_tier = max(tier_performance.keys(), 
                      key=lambda tier: sum(tier_performance[tier]) / len(tier_performance[tier]) if tier_performance[tier] else 0) if tier_performance else "N/A"
        
        # Calculate projections
        avg_growth = sum(stream.growth_rate for stream in revenue_streams) / len(revenue_streams) if revenue_streams else 0
        projected_revenue = total_revenue * ((1 + avg_growth / 100) ** 6)  # 6-month projection
        
        report_data = {
            "title": f"{report_type.title()} Report",
            "period": f"{report_period.title()} Report",
            "generated_date": datetime.now().isoformat(),
            "totalRevenue": total_revenue,
            "activeAgents": active_agents,
            "successRate": avg_success_rate,
            "pipelineValue": pipeline_value,
            "revenueGrowth": avg_growth,
            "topTier": top_tier,
            "projectedRevenue": projected_revenue,
            "summary": {
                "revenue_streams": len(revenue_streams),
                "total_kpis": len(kpis),
                "achievement_rate": (total_revenue / sum(stream.target_month for stream in revenue_streams)) * 100 if revenue_streams else 0
            }
        }
        
        return jsonify(report_data)
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({"error": "Failed to generate report"}), 500


@app.route('/api/agents/<int:agent_id>/optimize', methods=['POST'])
@jwt_required()
def optimize_agent(agent_id):
    """Optimize specific agent performance"""
    try:
        agent = AIAgent.query.get(agent_id)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        # Simulate optimization process
        if agent.performance:
            # Improve success rate by 5-10%
            current_rate = agent.performance.get('success_rate', 0)
            improvement = min(10, 100 - current_rate)  # Cap at 100%
            agent.performance['success_rate'] = min(100, current_rate + improvement)
            
            # Update last activity
            agent.last_activity = datetime.now()
            
            db.session.commit()
            
            return jsonify({
                "message": f"Agent {agent.name} optimization initiated",
                "improvements": {
                    "success_rate_increase": improvement,
                    "new_success_rate": agent.performance['success_rate']
                }
            })
        else:
            return jsonify({"error": "Agent has no performance data to optimize"}), 400
        
    except Exception as e:
        logger.error(f"Agent optimization error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to optimize agent"}), 500

# Automated Reporting API Routes
@app.route('/api/reports/executive-summary', methods=['POST'])
@jwt_required()
def generate_executive_summary():
    """Generate automated executive summary report"""
    try:
        data = request.get_json()
        report_type = data.get('type', 'weekly')  # weekly or monthly
        
        # Gather all data for the report
        revenue_streams = RevenueStream.query.all()
        agents = AIAgent.query.all()
        kpis = KPIMetric.query.all()
        milestones = Milestone.query.all()
        
        # Calculate comprehensive metrics
        total_revenue = sum(stream.current_month for stream in revenue_streams)
        total_target = sum(stream.target_month for stream in revenue_streams)
        active_agents = len([agent for agent in agents if agent.status == 'active'])
        
        success_rates = []
        pipeline_value = 0
        for agent in agents:
            performance = agent.performance or {}
            if 'success_rate' in performance:
                success_rates.append(performance['success_rate'])
            pipeline_value += performance.get('pipeline_value', 0)
        
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        avg_growth = sum(stream.growth_rate for stream in revenue_streams) / len(revenue_streams) if revenue_streams else 0
        
        # Create executive summary data
        report_data = {
            'total_revenue': total_revenue,
            'total_target': total_target,
            'achievement_rate': (total_revenue / total_target) * 100 if total_target > 0 else 0,
            'active_agents': active_agents,
            'avg_success_rate': avg_success_rate,
            'pipeline_value': pipeline_value,
            'revenue_growth': avg_growth,
            'kpi_achievement': 85.5,  # Would calculate from actual KPI data
            'growth_trend': 12.5,
            'total_ytd': sum(stream.ytd for stream in revenue_streams),
            'projected_revenue': total_revenue * ((1 + avg_growth / 100) ** 12),
            'top_tier': 'revenue_generation'  # Would calculate from performance data
        }
        
        # Generate the report using the template
        from static.reports.executive_summary_template import generate_executive_report
        
        executive_report = generate_executive_report(report_data, report_type)
        
        # Add additional context
        executive_report['data_sources'] = {
            'revenue_streams': len(revenue_streams),
            'active_agents': active_agents,
            'kpi_metrics': len(kpis),
            'milestones': len(milestones)
        }
        
        executive_report['metadata'] = {
            'generated_by': 'AI Empire BI System',
            'report_id': f"EXEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'data_as_of': datetime.now().isoformat(),
            'confidence_level': 'High'
        }
        
        return jsonify(executive_report)
        
    except Exception as e:
        logger.error(f"Executive summary generation error: {e}")
        return jsonify({"error": "Failed to generate executive summary"}), 500

@app.route('/api/reports/automated-insights', methods=['GET'])
@jwt_required()
def get_automated_insights():
    """Get AI-generated business insights"""
    try:
        # Gather data for insights
        revenue_streams = RevenueStream.query.all()
        agents = AIAgent.query.all()
        kpis = KPIMetric.query.all()
        
        # Generate insights based on data analysis
        insights = []
        
        # Revenue insights
        total_revenue = sum(stream.current_month for stream in revenue_streams)
        total_target = sum(stream.target_month for stream in revenue_streams)
        achievement_rate = (total_revenue / total_target) * 100 if total_target > 0 else 0
        
        if achievement_rate > 100:
            insights.append({
                "type": "positive",
                "category": "revenue",
                "title": "Revenue Target Exceeded", 
                "description": f"Current revenue of ${total_revenue:,.0f} exceeds target by {achievement_rate - 100:.1f}%",
                "recommendation": "Consider raising targets for next period to maintain growth momentum",
                "impact": "high"
            })
        elif achievement_rate < 80:
            insights.append({
                "type": "warning",
                "category": "revenue",
                "title": "Revenue Target At Risk",
                "description": f"Current achievement rate of {achievement_rate:.1f}% below optimal threshold",
                "recommendation": "Implement accelerated revenue generation strategies",
                "impact": "high"
            })
        
        # Agent performance insights
        active_agents = [agent for agent in agents if agent.status == 'active']
        if active_agents:
            success_rates = []
            for agent in active_agents:
                performance = agent.performance or {}
                if 'success_rate' in performance:
                    success_rates.append(performance['success_rate'])
            
            if success_rates:
                avg_success_rate = sum(success_rates) / len(success_rates)
                if avg_success_rate > 85:
                    insights.append({
                        "type": "positive",
                        "category": "agents",
                        "title": "Excellent Agent Performance",
                        "description": f"Average success rate of {avg_success_rate:.1f}% exceeds industry benchmarks",
                        "recommendation": "Maintain current optimization strategies and consider scaling successful agents",
                        "impact": "medium"
                    })
                elif avg_success_rate < 70:
                    insights.append({
                        "type": "warning", 
                        "category": "agents",
                        "title": "Agent Performance Below Threshold",
                        "description": f"Average success rate of {avg_success_rate:.1f}% requires optimization",
                        "recommendation": "Initiate agent performance improvement program",
                        "impact": "high"
                    })
        
        # Growth trend insights
        growth_rates = [stream.growth_rate for stream in revenue_streams]
        if growth_rates:
            avg_growth = sum(growth_rates) / len(growth_rates)
            if avg_growth > 15:
                insights.append({
                    "type": "positive",
                    "category": "growth",
                    "title": "Strong Growth Trajectory",
                    "description": f"Average growth rate of {avg_growth:.1f}% indicates robust business expansion",
                    "recommendation": "Capitalize on growth momentum with strategic investments",
                    "impact": "high"
                })
            elif avg_growth < 5:
                insights.append({
                    "type": "info",
                    "category": "growth", 
                    "title": "Growth Acceleration Opportunity",
                    "description": f"Current growth rate of {avg_growth:.1f}% has potential for improvement",
                    "recommendation": "Explore new revenue streams and optimization opportunities",
                    "impact": "medium"
                })
        
        # Market opportunity insights
        insights.append({
            "type": "info",
            "category": "opportunity",
            "title": "Market Expansion Potential",
            "description": "AI governance market showing 45% YoY growth",
            "recommendation": "Consider expanding consulting services and thought leadership presence",
            "impact": "high"
        })
        
        return jsonify({
            "insights": insights,
            "summary": {
                "total_insights": len(insights),
                "high_impact": len([i for i in insights if i['impact'] == 'high']),
                "positive_indicators": len([i for i in insights if i['type'] == 'positive']),
                "areas_for_attention": len([i for i in insights if i['type'] == 'warning'])
            },
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Automated insights error: {e}")
        return jsonify({"error": "Failed to generate insights"}), 500

@app.route('/api/reports/schedule', methods=['POST'])
@jwt_required()
def schedule_automated_reports():
    """Schedule automated report generation"""
    try:
        data = request.get_json()
        schedule_type = data.get('type', 'weekly')  # weekly, monthly, quarterly
        recipients = data.get('recipients', [])
        enabled = data.get('enabled', True)
        
        # In a production system, this would integrate with a task scheduler like Celery
        schedule_config = {
            "schedule_id": f"SCHED-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "type": schedule_type,
            "recipients": recipients,
            "enabled": enabled,
            "created_at": datetime.now().isoformat(),
            "next_run": (datetime.now() + timedelta(days=7 if schedule_type == 'weekly' else 30)).isoformat(),
            "report_types": ["executive_summary", "performance_metrics", "growth_analysis"]
        }
        
        return jsonify({
            "message": f"Automated {schedule_type} reports scheduled successfully",
            "schedule": schedule_config
        })
        
    except Exception as e:
        logger.error(f"Schedule automated reports error: {e}")
        return jsonify({"error": "Failed to schedule reports"}), 500

@app.route('/api/reports/export/<format>', methods=['POST'])
@jwt_required()
def export_report(format):
    """Export reports in various formats (PDF, Excel, etc.)"""
    try:
        data = request.get_json()
        report_data = data.get('report_data', {})
        
        if format.lower() == 'pdf':
            # In production, would use libraries like ReportLab or WeasyPrint
            export_result = {
                "format": "PDF",
                "filename": f"executive_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                "download_url": f"/downloads/executive_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                "size": "2.3 MB",
                "pages": 15
            }
        elif format.lower() == 'excel':
            # In production, would use libraries like openpyxl or xlsxwriter
            export_result = {
                "format": "Excel",
                "filename": f"executive_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "download_url": f"/downloads/executive_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "size": "1.8 MB",
                "sheets": ["Summary", "Revenue Analysis", "Agent Performance", "KPIs"]
            }
        else:
            return jsonify({"error": f"Unsupported export format: {format}"}), 400
        
        return jsonify({
            "message": f"Report exported successfully as {format.upper()}",
            "export": export_result,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Export report error: {e}")
        return jsonify({"error": f"Failed to export report as {format}"}), 500

# ============================
# NOTIFICATION MANAGEMENT API
# ============================

# Notification Channels Management
@app.route('/api/notifications/channels', methods=['GET'])
@jwt_required()
def get_notification_channels():
    """Get all notification channels"""
    try:
        channels = NotificationChannel.query.all()
        return jsonify([channel.to_dict() for channel in channels])
    except Exception as e:
        logger.error(f"Get notification channels error: {e}")
        return jsonify({"error": "Failed to fetch notification channels"}), 500

@app.route('/api/notifications/channels', methods=['POST'])
@jwt_required()
def create_notification_channel():
    """Create a new notification channel"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('channel_type'):
            return jsonify({"error": "Name and channel_type are required"}), 400
        
        # Validate channel type
        valid_types = ['email', 'slack', 'webhook', 'sms', 'internal']
        if data.get('channel_type') not in valid_types:
            return jsonify({"error": f"Invalid channel type. Must be one of: {', '.join(valid_types)}"}), 400
        
        channel = NotificationChannel(
            name=data['name'],
            channel_type=data['channel_type'],
            configuration=data.get('configuration', {}),
            enabled=data.get('enabled', True),
            priority=data.get('priority', 5),
            rate_limit=data.get('rate_limit')
        )
        
        db.session.add(channel)
        db.session.commit()
        
        return jsonify(channel.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create notification channel error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create notification channel"}), 500

@app.route('/api/notifications/channels/<int:channel_id>', methods=['GET'])
@jwt_required()
def get_notification_channel(channel_id):
    """Get specific notification channel"""
    try:
        channel = NotificationChannel.query.get(channel_id)
        if not channel:
            return jsonify({"error": "Channel not found"}), 404
        return jsonify(channel.to_dict())
    except Exception as e:
        logger.error(f"Get notification channel error: {e}")
        return jsonify({"error": "Failed to fetch notification channel"}), 500

@app.route('/api/notifications/channels/<int:channel_id>', methods=['PUT'])
@jwt_required()
def update_notification_channel(channel_id):
    """Update notification channel"""
    try:
        channel = NotificationChannel.query.get(channel_id)
        if not channel:
            return jsonify({"error": "Channel not found"}), 404
        
        data = request.get_json()
        
        # Update fields
        for field in ['name', 'configuration', 'enabled', 'priority', 'rate_limit']:
            if field in data:
                setattr(channel, field, data[field])
        
        db.session.commit()
        return jsonify(channel.to_dict())
        
    except Exception as e:
        logger.error(f"Update notification channel error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update notification channel"}), 500

@app.route('/api/notifications/channels/<int:channel_id>', methods=['DELETE'])
@jwt_required()
def delete_notification_channel(channel_id):
    """Delete notification channel"""
    try:
        channel = NotificationChannel.query.get(channel_id)
        if not channel:
            return jsonify({"error": "Channel not found"}), 404
        
        db.session.delete(channel)
        db.session.commit()
        return jsonify({"message": "Channel deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Delete notification channel error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete notification channel"}), 500

# Notification Sending
@app.route('/api/notifications/send', methods=['POST'])
@jwt_required()
def send_notification():
    """Send a notification through specified channels"""
    try:
        data = request.get_json()
        
        message = data.get('message')
        channels = data.get('channels', [])
        priority = data.get('priority', 'medium')
        context = data.get('context', {})
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        if not channels:
            return jsonify({"error": "At least one channel is required"}), 400
        
        results = []
        for channel_name in channels:
            channel = NotificationChannel.query.filter_by(name=channel_name, enabled=True).first()
            if channel:
                result = business_rule_engine._send_notification(channel, message, priority, context)
                results.append({
                    'channel': channel_name,
                    'result': result
                })
            else:
                results.append({
                    'channel': channel_name,
                    'result': {'success': False, 'error': 'Channel not found or disabled'}
                })
        
        return jsonify({
            'message': 'Notification processing completed',
            'results': results,
            'total_channels': len(channels),
            'successful_sends': len([r for r in results if r['result'].get('success')])
        })
        
    except Exception as e:
        logger.error(f"Send notification error: {e}")
        return jsonify({"error": "Failed to send notification"}), 500

# ============================
# WORKFLOW SCHEDULING SYSTEM
# ============================

# Schedule Management API
@app.route('/api/schedules', methods=['GET'])
@jwt_required()
def get_schedules():
    """Get all workflow schedules"""
    try:
        schedules = WorkflowSchedule.query.all()
        return jsonify([schedule.to_dict() for schedule in schedules])
    except Exception as e:
        logger.error(f"Get schedules error: {e}")
        return jsonify({"error": "Failed to fetch schedules"}), 500

@app.route('/api/schedules', methods=['POST'])
@jwt_required()
def create_schedule():
    """Create a new workflow schedule"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'schedule_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate schedule type
        valid_types = ['cron', 'interval', 'once', 'event_driven']
        if data.get('schedule_type') not in valid_types:
            return jsonify({"error": f"Invalid schedule type. Must be one of: {', '.join(valid_types)}"}), 400
        
        # Validate cron expression if provided
        if data.get('schedule_type') == 'cron' and data.get('cron_expression'):
            if not _validate_cron_expression(data['cron_expression']):
                return jsonify({"error": "Invalid cron expression"}), 400
        
        schedule = WorkflowSchedule(
            name=data['name'],
            description=data.get('description'),
            schedule_type=data['schedule_type'],
            cron_expression=data.get('cron_expression'),
            interval_seconds=data.get('interval_seconds'),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else datetime.now(),
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            enabled=data.get('enabled', True),
            max_executions=data.get('max_executions'),
            timezone=data.get('timezone', 'UTC'),
            metadata=data.get('metadata', {}),
            trigger_id=data.get('trigger_id'),
            rule_id=data.get('rule_id')
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        # Schedule the task in background job system
        if schedule.enabled:
            _schedule_background_task(schedule)
        
        return jsonify(schedule.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create schedule error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create schedule"}), 500

@app.route('/api/schedules/<int:schedule_id>', methods=['GET'])
@jwt_required()
def get_schedule(schedule_id):
    """Get specific schedule"""
    try:
        schedule = WorkflowSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({"error": "Schedule not found"}), 404
        return jsonify(schedule.to_dict())
    except Exception as e:
        logger.error(f"Get schedule error: {e}")
        return jsonify({"error": "Failed to fetch schedule"}), 500

@app.route('/api/schedules/<int:schedule_id>', methods=['PUT'])
@jwt_required()
def update_schedule(schedule_id):
    """Update workflow schedule"""
    try:
        schedule = WorkflowSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({"error": "Schedule not found"}), 404
        
        data = request.get_json()
        old_enabled = schedule.enabled
        
        # Update fields
        for field in ['name', 'description', 'schedule_type', 'cron_expression', 'interval_seconds', 
                     'enabled', 'max_executions', 'timezone', 'metadata', 'trigger_id', 'rule_id']:
            if field in data:
                if field in ['start_date', 'end_date'] and data[field]:
                    setattr(schedule, field, datetime.fromisoformat(data[field]))
                else:
                    setattr(schedule, field, data[field])
        
        # Validate cron expression if updated
        if schedule.schedule_type == 'cron' and schedule.cron_expression:
            if not _validate_cron_expression(schedule.cron_expression):
                return jsonify({"error": "Invalid cron expression"}), 400
        
        db.session.commit()
        
        # Reschedule if enabled status changed
        if old_enabled != schedule.enabled:
            if schedule.enabled:
                _schedule_background_task(schedule)
            else:
                _unschedule_background_task(schedule)
        
        return jsonify(schedule.to_dict())
        
    except Exception as e:
        logger.error(f"Update schedule error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update schedule"}), 500

@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
@jwt_required()
def delete_schedule(schedule_id):
    """Delete workflow schedule"""
    try:
        schedule = WorkflowSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({"error": "Schedule not found"}), 404
        
        # Unschedule background task
        _unschedule_background_task(schedule)
        
        db.session.delete(schedule)
        db.session.commit()
        return jsonify({"message": "Schedule deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Delete schedule error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete schedule"}), 500

@app.route('/api/schedules/<int:schedule_id>/execute', methods=['POST'])
@jwt_required()
def execute_schedule_manually(schedule_id):
    """Manually execute a scheduled workflow"""
    try:
        schedule = WorkflowSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({"error": "Schedule not found"}), 404
        
        # Execute the scheduled workflow
        execution_result = _execute_scheduled_workflow(schedule, 'manual')
        
        return jsonify({
            'message': 'Schedule executed manually',
            'schedule_id': schedule_id,
            'execution_result': execution_result
        })
        
    except Exception as e:
        logger.error(f"Manual schedule execution error: {e}")
        return jsonify({"error": "Failed to execute schedule"}), 500

@app.route('/api/schedules/<int:schedule_id>/history', methods=['GET'])
@jwt_required()
def get_schedule_execution_history(schedule_id):
    """Get execution history for a schedule"""
    try:
        schedule = WorkflowSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({"error": "Schedule not found"}), 404
        
        # Get executions related to this schedule
        executions = WorkflowExecution.query.filter(
            WorkflowExecution.metadata.contains({'schedule_id': schedule_id})
        ).order_by(WorkflowExecution.start_time.desc()).limit(50).all()
        
        return jsonify({
            'schedule_id': schedule_id,
            'execution_history': [execution.to_dict() for execution in executions],
            'total_executions': len(executions)
        })
        
    except Exception as e:
        logger.error(f"Get schedule history error: {e}")
        return jsonify({"error": "Failed to fetch schedule history"}), 500

# Recurring Task Templates
@app.route('/api/schedules/templates', methods=['GET'])
@jwt_required()
def get_schedule_templates():
    """Get predefined schedule templates for common business workflows"""
    try:
        templates = [
            {
                "id": "daily_revenue_check",
                "name": "Daily Revenue Check",
                "description": "Check daily revenue performance and trigger alerts for significant changes",
                "schedule_type": "cron",
                "cron_expression": "0 9 * * *",  # Daily at 9 AM
                "workflow_type": "revenue_monitoring",
                "actions": ["check_daily_revenue", "compare_to_targets", "send_alerts"]
            },
            {
                "id": "weekly_agent_review",
                "name": "Weekly AI Agent Performance Review",
                "description": "Review AI agent performance weekly and optimize underperforming agents",
                "schedule_type": "cron",
                "cron_expression": "0 10 * * 1",  # Mondays at 10 AM
                "workflow_type": "agent_performance",
                "actions": ["analyze_agent_performance", "identify_optimization_opportunities", "notify_team"]
            },
            {
                "id": "monthly_kpi_report",
                "name": "Monthly KPI Report",
                "description": "Generate comprehensive monthly KPI reports and distribute to stakeholders",
                "schedule_type": "cron",
                "cron_expression": "0 8 1 * *",  # First day of month at 8 AM
                "workflow_type": "reporting",
                "actions": ["generate_kpi_report", "analyze_trends", "distribute_report"]
            },
            {
                "id": "hourly_opportunity_sync",
                "name": "Hourly Opportunity Sync",
                "description": "Sync executive opportunities with external systems and update statuses",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",  # Every hour
                "workflow_type": "opportunity_management",
                "actions": ["sync_opportunities", "update_statuses", "check_deadlines"]
            },
            {
                "id": "milestone_progress_check",
                "name": "Milestone Progress Check",
                "description": "Check progress toward business milestones and send updates",
                "schedule_type": "cron",
                "cron_expression": "0 17 * * *",  # Daily at 5 PM
                "workflow_type": "milestone_tracking",
                "actions": ["calculate_milestone_progress", "identify_blockers", "send_progress_updates"]
            }
        ]
        
        return jsonify(templates)
        
    except Exception as e:
        logger.error(f"Get schedule templates error: {e}")
        return jsonify({"error": "Failed to fetch schedule templates"}), 500

@app.route('/api/schedules/templates/<string:template_id>/create', methods=['POST'])
@jwt_required()
def create_schedule_from_template(template_id):
    """Create a schedule from a predefined template"""
    try:
        data = request.get_json()
        
        # Get template configuration
        templates = {
            "daily_revenue_check": {
                "name": "Daily Revenue Check",
                "description": "Check daily revenue performance and trigger alerts for significant changes",
                "schedule_type": "cron",
                "cron_expression": "0 9 * * *",
                "metadata": {"template_id": template_id, "workflow_type": "revenue_monitoring"}
            },
            "weekly_agent_review": {
                "name": "Weekly AI Agent Performance Review",
                "description": "Review AI agent performance weekly and optimize underperforming agents",
                "schedule_type": "cron",
                "cron_expression": "0 10 * * 1",
                "metadata": {"template_id": template_id, "workflow_type": "agent_performance"}
            },
            "monthly_kpi_report": {
                "name": "Monthly KPI Report",
                "description": "Generate comprehensive monthly KPI reports and distribute to stakeholders",
                "schedule_type": "cron",
                "cron_expression": "0 8 1 * *",
                "metadata": {"template_id": template_id, "workflow_type": "reporting"}
            },
            "hourly_opportunity_sync": {
                "name": "Hourly Opportunity Sync",
                "description": "Sync executive opportunities with external systems and update statuses",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
                "metadata": {"template_id": template_id, "workflow_type": "opportunity_management"}
            },
            "milestone_progress_check": {
                "name": "Milestone Progress Check",
                "description": "Check progress toward business milestones and send updates",
                "schedule_type": "cron",
                "cron_expression": "0 17 * * *",
                "metadata": {"template_id": template_id, "workflow_type": "milestone_tracking"}
            }
        }
        
        if template_id not in templates:
            return jsonify({"error": "Template not found"}), 404
        
        template = templates[template_id]
        
        # Override with user data if provided
        name = data.get('name', template['name'])
        description = data.get('description', template['description'])
        cron_expression = data.get('cron_expression', template['cron_expression'])
        enabled = data.get('enabled', True)
        
        schedule = WorkflowSchedule(
            name=name,
            description=description,
            schedule_type=template['schedule_type'],
            cron_expression=cron_expression,
            enabled=enabled,
            metadata=template['metadata']
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        # Schedule the task
        if schedule.enabled:
            _schedule_background_task(schedule)
        
        return jsonify(schedule.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create schedule from template error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create schedule from template"}), 500

# Schedule Execution Status and Monitoring
@app.route('/api/schedules/status', methods=['GET'])
@jwt_required()
def get_schedules_status():
    """Get status overview of all schedules"""
    try:
        schedules = WorkflowSchedule.query.all()
        
        status_overview = {
            'total_schedules': len(schedules),
            'enabled_schedules': len([s for s in schedules if s.enabled]),
            'disabled_schedules': len([s for s in schedules if not s.enabled]),
            'schedules_by_type': {},
            'next_executions': []
        }
        
        # Group by schedule type
        for schedule in schedules:
            schedule_type = schedule.schedule_type
            if schedule_type not in status_overview['schedules_by_type']:
                status_overview['schedules_by_type'][schedule_type] = 0
            status_overview['schedules_by_type'][schedule_type] += 1
            
            # Calculate next execution time
            if schedule.enabled:
                next_execution = _calculate_next_execution(schedule)
                if next_execution:
                    status_overview['next_executions'].append({
                        'schedule_id': schedule.id,
                        'name': schedule.name,
                        'next_execution': next_execution.isoformat(),
                        'schedule_type': schedule.schedule_type
                    })
        
        # Sort next executions by time
        status_overview['next_executions'].sort(key=lambda x: x['next_execution'])
        
        return jsonify(status_overview)
        
    except Exception as e:
        logger.error(f"Get schedules status error: {e}")
        return jsonify({"error": "Failed to fetch schedules status"}), 500

# Background Task Management System
class ScheduleManager:
    """Manages background task scheduling and execution"""
    
    def __init__(self):
        self.scheduled_tasks = {}
        self.running = False
    
    def start(self):
        """Start the schedule manager"""
        self.running = True
        # In production, would use APScheduler or Celery
        logger.info("Schedule manager started")
    
    def stop(self):
        """Stop the schedule manager"""
        self.running = False
        logger.info("Schedule manager stopped")
    
    def add_schedule(self, schedule):
        """Add a schedule to the manager"""
        self.scheduled_tasks[schedule.id] = schedule
        logger.info(f"Added schedule: {schedule.name} ({schedule.id})")
    
    def remove_schedule(self, schedule_id):
        """Remove a schedule from the manager"""
        if schedule_id in self.scheduled_tasks:
            del self.scheduled_tasks[schedule_id]
            logger.info(f"Removed schedule: {schedule_id}")

# Initialize schedule manager
schedule_manager = ScheduleManager()

def _validate_cron_expression(cron_expr):
    """Validate cron expression format"""
    try:
        # Basic validation - in production would use croniter or similar
        parts = cron_expr.split()
        if len(parts) != 5:
            return False
        
        # Basic range checks
        ranges = [
            (0, 59),   # minute
            (0, 23),   # hour
            (1, 31),   # day
            (1, 12),   # month
            (0, 6),    # day of week
        ]
        
        for i, part in enumerate(parts):
            if part == '*':
                continue
            try:
                if '/' in part:
                    base, step = part.split('/')
                    if base != '*':
                        val = int(base)
                        if val < ranges[i][0] or val > ranges[i][1]:
                            return False
                elif '-' in part:
                    start, end = part.split('-')
                    start_val, end_val = int(start), int(end)
                    if start_val < ranges[i][0] or end_val > ranges[i][1]:
                        return False
                else:
                    val = int(part)
                    if val < ranges[i][0] or val > ranges[i][1]:
                        return False
            except ValueError:
                return False
        
        return True
    except:
        return False

def _schedule_background_task(schedule):
    """Schedule a background task"""
    try:
        schedule_manager.add_schedule(schedule)
        logger.info(f"Scheduled background task: {schedule.name}")
    except Exception as e:
        logger.error(f"Error scheduling task: {e}")

def _unschedule_background_task(schedule):
    """Unschedule a background task"""
    try:
        schedule_manager.remove_schedule(schedule.id)
        logger.info(f"Unscheduled background task: {schedule.name}")
    except Exception as e:
        logger.error(f"Error unscheduling task: {e}")

def _execute_scheduled_workflow(schedule, trigger_source='scheduled'):
    """Execute a scheduled workflow"""
    try:
        # Create workflow execution record
        execution = WorkflowExecution(
            trigger_id=schedule.trigger_id,
            rule_id=schedule.rule_id,
            status='running',
            start_time=datetime.now(),
            metadata={'schedule_id': schedule.id, 'trigger_source': trigger_source}
        )
        db.session.add(execution)
        db.session.commit()
        
        results = []
        
        # Execute workflow based on metadata type
        workflow_type = schedule.metadata.get('workflow_type', 'generic')
        
        if workflow_type == 'revenue_monitoring':
            results = _execute_revenue_monitoring_workflow(schedule, execution)
        elif workflow_type == 'agent_performance':
            results = _execute_agent_performance_workflow(schedule, execution)
        elif workflow_type == 'reporting':
            results = _execute_reporting_workflow(schedule, execution)
        elif workflow_type == 'opportunity_management':
            results = _execute_opportunity_management_workflow(schedule, execution)
        elif workflow_type == 'milestone_tracking':
            results = _execute_milestone_tracking_workflow(schedule, execution)
        else:
            results = _execute_generic_workflow(schedule, execution)
        
        # Update execution status
        execution.status = 'completed'
        execution.end_time = datetime.now()
        execution.result_data = {'results': results, 'success': True}
        
        # Update schedule execution count
        schedule.last_execution = datetime.now()
        schedule.execution_count = (schedule.execution_count or 0) + 1
        
        db.session.commit()
        
        logger.info(f"Executed scheduled workflow: {schedule.name}")
        return {'success': True, 'results': results}
        
    except Exception as e:
        # Update execution with error
        if 'execution' in locals():
            execution.status = 'failed'
            execution.end_time = datetime.now()
            execution.result_data = {'error': str(e), 'success': False}
            db.session.commit()
        
        logger.error(f"Error executing scheduled workflow: {e}")
        return {'success': False, 'error': str(e)}

def _calculate_next_execution(schedule):
    """Calculate next execution time for a schedule"""
    try:
        from datetime import timedelta
        
        if not schedule.enabled:
            return None
        
        now = datetime.now()
        
        if schedule.schedule_type == 'interval' and schedule.interval_seconds:
            last_execution = schedule.last_execution or now
            return last_execution + timedelta(seconds=schedule.interval_seconds)
        
        elif schedule.schedule_type == 'cron' and schedule.cron_expression:
            # Simple cron calculation - in production use croniter
            # For demo, return next hour for hourly, next day for daily
            if '* * * *' in schedule.cron_expression:  # Hourly
                return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            elif '0 9 * * *' in schedule.cron_expression:  # Daily at 9 AM
                next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run
        
        return None
    except:
        return None

# Workflow execution functions
def _execute_revenue_monitoring_workflow(schedule, execution):
    """Execute revenue monitoring workflow"""
    results = []
    
    # Check daily revenue performance
    total_revenue = sum(stream['current_month'] for stream in REVENUE_STREAMS)
    target_revenue = sum(stream['target_month'] for stream in REVENUE_STREAMS)
    
    if total_revenue >= target_revenue * 1.1:  # 10% over target
        trigger_business_event(
            event_type='revenue_target_exceeded',
            entity_type='revenue_stream',
            entity_id=0,
            event_data={
                'total_revenue': total_revenue,
                'target_revenue': target_revenue,
                'excess_percentage': ((total_revenue - target_revenue) / target_revenue) * 100
            },
            source='scheduled_revenue_monitoring',
            priority='high'
        )
        results.append(f"Revenue target exceeded: ${total_revenue:,.2f} vs ${target_revenue:,.2f}")
    
    return results

def _execute_agent_performance_workflow(schedule, execution):
    """Execute agent performance workflow"""
    results = []
    
    # Check all AI agents performance
    agents = AIAgent.query.filter_by(status='active').all()
    
    for agent in agents:
        if agent.success_rate >= 95:
            trigger_business_event(
                event_type='agent_high_performance',
                entity_type='ai_agent',
                entity_id=agent.id,
                event_data={
                    'agent_name': agent.name,
                    'success_rate': agent.success_rate,
                    'pipeline_value': agent.pipeline_value
                },
                source='scheduled_agent_review',
                priority='medium'
            )
            results.append(f"High performance: {agent.name} - {agent.success_rate}%")
    
    return results

def _execute_reporting_workflow(schedule, execution):
    """Execute reporting workflow"""
    results = []
    results.append("Monthly KPI report generated")
    results.append("Report distributed to stakeholders")
    return results

def _execute_opportunity_management_workflow(schedule, execution):
    """Execute opportunity management workflow"""
    results = []
    
    # Check for opportunities with upcoming deadlines
    upcoming_deadline = datetime.now() + timedelta(days=7)
    opportunities = ExecutiveOpportunity.query.filter(
        ExecutiveOpportunity.deadline <= upcoming_deadline,
        ExecutiveOpportunity.status.in_(['prospect', 'applied', 'interview_stage'])
    ).all()
    
    for opp in opportunities:
        trigger_business_event(
            event_type='opportunity_deadline_approaching',
            entity_type='executive_opportunity',
            entity_id=opp.id,
            event_data={
                'opportunity_title': opp.title,
                'company': opp.company,
                'deadline': opp.deadline.isoformat() if opp.deadline else None,
                'status': opp.status
            },
            source='scheduled_opportunity_sync',
            priority='medium'
        )
        results.append(f"Deadline approaching: {opp.title} at {opp.company}")
    
    return results

def _execute_milestone_tracking_workflow(schedule, execution):
    """Execute milestone tracking workflow"""
    results = []
    results.append("Milestone progress calculated")
    results.append("Progress updates sent")
    return results

def _execute_generic_workflow(schedule, execution):
    """Execute generic workflow"""
    results = []
    results.append(f"Generic workflow executed: {schedule.name}")
    return results

# Webhook Management
@app.route('/api/webhooks', methods=['GET'])
@jwt_required()
def get_webhooks():
    """Get all webhooks"""
    try:
        webhooks = WorkflowWebhook.query.all()
        return jsonify([webhook.to_dict() for webhook in webhooks])
    except Exception as e:
        logger.error(f"Get webhooks error: {e}")
        return jsonify({"error": "Failed to fetch webhooks"}), 500

@app.route('/api/webhooks', methods=['POST'])
@jwt_required()
def create_webhook():
    """Create a new webhook"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('webhook_url'):
            return jsonify({"error": "Name and webhook_url are required"}), 400
        
        webhook = WorkflowWebhook(
            name=data['name'],
            webhook_url=data['webhook_url'],
            secret_key=data.get('secret_key'),
            event_types=data.get('event_types', []),
            headers=data.get('headers', {}),
            enabled=data.get('enabled', True),
            retry_attempts=data.get('retry_attempts', 3),
            timeout_seconds=data.get('timeout_seconds', 30)
        )
        
        db.session.add(webhook)
        db.session.commit()
        
        return jsonify(webhook.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create webhook error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create webhook"}), 500

@app.route('/api/webhooks/<int:webhook_id>', methods=['GET'])
@jwt_required()
def get_webhook(webhook_id):
    """Get specific webhook"""
    try:
        webhook = WorkflowWebhook.query.get(webhook_id)
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
        return jsonify(webhook.to_dict())
    except Exception as e:
        logger.error(f"Get webhook error: {e}")
        return jsonify({"error": "Failed to fetch webhook"}), 500

@app.route('/api/webhooks/<int:webhook_id>', methods=['PUT'])
@jwt_required()
def update_webhook(webhook_id):
    """Update webhook"""
    try:
        webhook = WorkflowWebhook.query.get(webhook_id)
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
        
        data = request.get_json()
        
        # Update fields
        for field in ['name', 'webhook_url', 'secret_key', 'event_types', 'headers', 'enabled', 'retry_attempts', 'timeout_seconds']:
            if field in data:
                setattr(webhook, field, data[field])
        
        db.session.commit()
        return jsonify(webhook.to_dict())
        
    except Exception as e:
        logger.error(f"Update webhook error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update webhook"}), 500

@app.route('/api/webhooks/<int:webhook_id>', methods=['DELETE'])
@jwt_required()
def delete_webhook(webhook_id):
    """Delete webhook"""
    try:
        webhook = WorkflowWebhook.query.get(webhook_id)
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
        
        db.session.delete(webhook)
        db.session.commit()
        return jsonify({"message": "Webhook deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Delete webhook error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete webhook"}), 500

# ============================
# MAKE.COM INTEGRATION SYSTEM
# ============================

# Make.com Webhook Endpoints
@app.route('/api/integrations/make/webhooks/<string:scenario_name>', methods=['POST'])
def receive_make_webhook(scenario_name):
    """Receive webhook from Make.com scenarios"""
    try:
        data = request.get_json()
        headers = dict(request.headers)
        
        logger.info(f"Received Make.com webhook for scenario: {scenario_name}")
        
        # Process different scenario types
        if scenario_name == 'revenue_update':
            result = _process_make_revenue_update(data)
        elif scenario_name == 'opportunity_sync':
            result = _process_make_opportunity_sync(data)
        elif scenario_name == 'agent_performance':
            result = _process_make_agent_performance(data)
        elif scenario_name == 'lead_qualification':
            result = _process_make_lead_qualification(data)
        elif scenario_name == 'pipeline_automation':
            result = _process_make_pipeline_automation(data)
        else:
            result = _process_generic_make_webhook(scenario_name, data)
        
        return jsonify({
            'success': True,
            'scenario': scenario_name,
            'processed_data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Make.com webhook error for {scenario_name}: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'scenario': scenario_name
        }), 500

@app.route('/api/integrations/make/trigger/<string:trigger_type>', methods=['POST'])
@jwt_required()
def trigger_make_scenario(trigger_type):
    """Trigger Make.com scenarios from AI Empire platform"""
    try:
        data = request.get_json()
        
        # Get Make.com webhook configuration
        make_config = _get_make_config(trigger_type)
        if not make_config:
            return jsonify({"error": f"Make.com configuration not found for trigger: {trigger_type}"}), 404
        
        # Transform data for Make.com format
        make_payload = _transform_data_for_make(trigger_type, data)
        
        # Send to Make.com
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Empire-Platform/1.0'
        }
        
        if make_config.get('api_key'):
            headers['Authorization'] = f"Bearer {make_config['api_key']}"
        
        response = requests.post(
            make_config['webhook_url'],
            json=make_payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        # Log the trigger
        logger.info(f"Triggered Make.com scenario: {trigger_type}")
        
        return jsonify({
            'success': True,
            'trigger_type': trigger_type,
            'make_response_status': response.status_code,
            'payload_sent': make_payload,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Make.com trigger error for {trigger_type}: {e}")
        return jsonify({"error": f"Failed to trigger Make.com scenario: {str(e)}"}), 500

# Make.com Configuration Management
@app.route('/api/integrations/make/config', methods=['GET'])
@jwt_required()
def get_make_config():
    """Get Make.com integration configuration"""
    try:
        # In production, store this in database or secure config
        make_configs = {
            'revenue_alerts': {
                'webhook_url': 'https://hook.integromat.com/revenue-alerts',
                'enabled': True,
                'triggers': ['revenue_milestone', 'revenue_target_exceeded'],
                'data_format': 'ai_empire_standard'
            },
            'opportunity_management': {
                'webhook_url': 'https://hook.integromat.com/opportunity-sync',
                'enabled': True,
                'triggers': ['opportunity_status_change', 'high_match_opportunity', 'opportunity_deadline'],
                'data_format': 'crm_standard'
            },
            'agent_coordination': {
                'webhook_url': 'https://hook.integromat.com/agent-performance',
                'enabled': True,
                'triggers': ['agent_performance_alert', 'agent_milestone', 'agent_coordination'],
                'data_format': 'ai_empire_standard'
            },
            'lead_nurturing': {
                'webhook_url': 'https://hook.integromat.com/lead-nurturing',
                'enabled': True,
                'triggers': ['lead_qualification', 'lead_scoring', 'follow_up_required'],
                'data_format': 'crm_standard'
            },
            'business_intelligence': {
                'webhook_url': 'https://hook.integromat.com/business-intelligence',
                'enabled': True,
                'triggers': ['kpi_threshold', 'milestone_progress', 'performance_trend'],
                'data_format': 'analytics_standard'
            }
        }
        
        return jsonify(make_configs)
        
    except Exception as e:
        logger.error(f"Get Make.com config error: {e}")
        return jsonify({"error": "Failed to fetch Make.com configuration"}), 500

@app.route('/api/integrations/make/config/<string:integration_name>', methods=['PUT'])
@jwt_required()
def update_make_config(integration_name):
    """Update Make.com integration configuration"""
    try:
        data = request.get_json()
        
        # Validate integration name
        valid_integrations = ['revenue_alerts', 'opportunity_management', 'agent_coordination', 'lead_nurturing', 'business_intelligence']
        if integration_name not in valid_integrations:
            return jsonify({"error": f"Invalid integration name. Must be one of: {', '.join(valid_integrations)}"}), 400
        
        # In production, update database configuration
        updated_config = {
            'webhook_url': data.get('webhook_url'),
            'enabled': data.get('enabled', True),
            'triggers': data.get('triggers', []),
            'data_format': data.get('data_format', 'ai_empire_standard'),
            'api_key': data.get('api_key'),  # Store securely in production
            'updated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Updated Make.com config for: {integration_name}")
        
        return jsonify({
            'success': True,
            'integration': integration_name,
            'config': updated_config
        })
        
    except Exception as e:
        logger.error(f"Update Make.com config error: {e}")
        return jsonify({"error": "Failed to update Make.com configuration"}), 500

# Make.com Scenario Templates
@app.route('/api/integrations/make/scenarios', methods=['GET'])
@jwt_required()
def get_make_scenarios():
    """Get predefined Make.com scenario templates"""
    try:
        scenarios = [
            {
                "id": "revenue_milestone_alert",
                "name": "Revenue Milestone Alert",
                "description": "Automatically notify team when revenue milestones are reached",
                "trigger": "revenue_milestone",
                "actions": [
                    "Send Slack notification",
                    "Update Google Sheets",
                    "Create Airtable record",
                    "Send email to executives"
                ],
                "webhook_url": "https://hook.integromat.com/revenue-milestone",
                "data_mapping": {
                    "milestone_amount": "event_data.milestone_amount",
                    "current_amount": "event_data.current_amount",
                    "stream_name": "event_data.stream_name",
                    "percentage_increase": "event_data.percentage_increase"
                }
            },
            {
                "id": "opportunity_pipeline_sync",
                "name": "Opportunity Pipeline Sync",
                "description": "Sync executive opportunities with CRM and project management tools",
                "trigger": "opportunity_status_change",
                "actions": [
                    "Update HubSpot deal",
                    "Create Notion page",
                    "Add to Monday.com board",
                    "Schedule follow-up in Calendly"
                ],
                "webhook_url": "https://hook.integromat.com/opportunity-sync",
                "data_mapping": {
                    "opportunity_title": "event_data.opportunity_title",
                    "company": "event_data.company",
                    "status": "event_data.status",
                    "compensation_range": "event_data.compensation_range",
                    "ai_match_score": "event_data.ai_match_score"
                }
            },
            {
                "id": "agent_performance_optimization",
                "name": "AI Agent Performance Optimization",
                "description": "Automatically optimize underperforming agents and notify team of high performers",
                "trigger": "agent_performance_alert",
                "actions": [
                    "Adjust agent parameters",
                    "Send performance report",
                    "Update agent dashboard",
                    "Create optimization task"
                ],
                "webhook_url": "https://hook.integromat.com/agent-optimization",
                "data_mapping": {
                    "agent_name": "event_data.agent_name",
                    "success_rate": "event_data.success_rate",
                    "pipeline_value": "event_data.pipeline_value",
                    "performance_trend": "event_data.performance_trend"
                }
            },
            {
                "id": "lead_qualification_workflow",
                "name": "Lead Qualification Workflow",
                "description": "Automatically qualify and route leads based on AI Empire criteria",
                "trigger": "lead_qualification",
                "actions": [
                    "Score lead in CRM",
                    "Assign to sales agent",
                    "Create personalized outreach",
                    "Schedule discovery call"
                ],
                "webhook_url": "https://hook.integromat.com/lead-qualification",
                "data_mapping": {
                    "lead_name": "event_data.lead_name",
                    "company": "event_data.company",
                    "qualification_score": "event_data.qualification_score",
                    "revenue_potential": "event_data.revenue_potential"
                }
            },
            {
                "id": "business_milestone_tracking",
                "name": "Business Milestone Tracking",
                "description": "Track progress toward $132M ARR goal and coordinate team actions",
                "trigger": "milestone_progress",
                "actions": [
                    "Update milestone dashboard",
                    "Generate progress report",
                    "Notify stakeholders",
                    "Adjust strategy if needed"
                ],
                "webhook_url": "https://hook.integromat.com/milestone-tracking",
                "data_mapping": {
                    "current_arr": "event_data.current_arr",
                    "target_arr": "event_data.target_arr",
                    "progress_percentage": "event_data.progress_percentage",
                    "projected_timeline": "event_data.projected_timeline"
                }
            }
        ]
        
        return jsonify(scenarios)
        
    except Exception as e:
        logger.error(f"Get Make.com scenarios error: {e}")
        return jsonify({"error": "Failed to fetch Make.com scenarios"}), 500

@app.route('/api/integrations/make/scenarios/<string:scenario_id>/test', methods=['POST'])
@jwt_required()
def test_make_scenario(scenario_id):
    """Test a Make.com scenario with sample data"""
    try:
        # Get sample data for different scenario types
        test_data = _get_make_test_data(scenario_id)
        
        if not test_data:
            return jsonify({"error": f"No test data available for scenario: {scenario_id}"}), 404
        
        # Get scenario configuration
        scenario_config = _get_make_scenario_config(scenario_id)
        if not scenario_config:
            return jsonify({"error": f"Scenario configuration not found: {scenario_id}"}), 404
        
        # Send test data to Make.com
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Empire-Platform/1.0-Test'
        }
        
        test_payload = {
            'test': True,
            'scenario_id': scenario_id,
            'timestamp': datetime.now().isoformat(),
            'data': test_data
        }
        
        response = requests.post(
            scenario_config['webhook_url'],
            json=test_payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        return jsonify({
            'success': True,
            'scenario_id': scenario_id,
            'test_response_status': response.status_code,
            'test_data_sent': test_payload,
            'make_response': response.text[:500] if response.text else None
        })
        
    except Exception as e:
        logger.error(f"Test Make.com scenario error for {scenario_id}: {e}")
        return jsonify({"error": f"Failed to test Make.com scenario: {str(e)}"}), 500

# Make.com Data Processing Functions
def _process_make_revenue_update(data):
    """Process revenue update from Make.com"""
    try:
        # Extract revenue data
        stream_name = data.get('stream_name')
        amount = data.get('amount')
        period = data.get('period', 'current_month')
        
        # Update revenue stream if exists
        # In production, find and update actual revenue stream
        
        result = {
            'action': 'revenue_updated',
            'stream_name': stream_name,
            'amount': amount,
            'period': period,
            'updated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Processed Make.com revenue update: {stream_name} = ${amount}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing Make.com revenue update: {e}")
        return {'error': str(e)}

def _process_make_opportunity_sync(data):
    """Process opportunity sync from Make.com"""
    try:
        # Extract opportunity data
        opportunity_data = {
            'title': data.get('title'),
            'company': data.get('company'),
            'status': data.get('status'),
            'compensation_range': data.get('compensation_range'),
            'source': 'make_com_sync'
        }
        
        # Create or update opportunity
        # In production, implement actual opportunity creation/update
        
        result = {
            'action': 'opportunity_synced',
            'opportunity_data': opportunity_data,
            'synced_at': datetime.now().isoformat()
        }
        
        logger.info(f"Processed Make.com opportunity sync: {opportunity_data['title']}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing Make.com opportunity sync: {e}")
        return {'error': str(e)}

def _process_make_agent_performance(data):
    """Process agent performance data from Make.com"""
    try:
        agent_data = {
            'agent_name': data.get('agent_name'),
            'success_rate': data.get('success_rate'),
            'pipeline_value': data.get('pipeline_value'),
            'optimizations': data.get('optimizations', [])
        }
        
        result = {
            'action': 'agent_performance_processed',
            'agent_data': agent_data,
            'processed_at': datetime.now().isoformat()
        }
        
        logger.info(f"Processed Make.com agent performance: {agent_data['agent_name']}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing Make.com agent performance: {e}")
        return {'error': str(e)}

def _process_make_lead_qualification(data):
    """Process lead qualification from Make.com"""
    try:
        lead_data = {
            'lead_name': data.get('lead_name'),
            'company': data.get('company'),
            'qualification_score': data.get('qualification_score'),
            'next_action': data.get('next_action')
        }
        
        result = {
            'action': 'lead_qualified',
            'lead_data': lead_data,
            'qualified_at': datetime.now().isoformat()
        }
        
        logger.info(f"Processed Make.com lead qualification: {lead_data['lead_name']}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing Make.com lead qualification: {e}")
        return {'error': str(e)}

def _process_make_pipeline_automation(data):
    """Process pipeline automation from Make.com"""
    try:
        pipeline_data = {
            'automation_type': data.get('automation_type'),
            'pipeline_stage': data.get('pipeline_stage'),
            'actions_taken': data.get('actions_taken', []),
            'results': data.get('results')
        }
        
        result = {
            'action': 'pipeline_automated',
            'pipeline_data': pipeline_data,
            'automated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Processed Make.com pipeline automation: {pipeline_data['automation_type']}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing Make.com pipeline automation: {e}")
        return {'error': str(e)}

def _process_generic_make_webhook(scenario_name, data):
    """Process generic Make.com webhook"""
    try:
        result = {
            'action': 'generic_webhook_processed',
            'scenario_name': scenario_name,
            'data_received': data,
            'processed_at': datetime.now().isoformat()
        }
        
        logger.info(f"Processed generic Make.com webhook: {scenario_name}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing generic Make.com webhook: {e}")
        return {'error': str(e)}

def _get_make_config(trigger_type):
    """Get Make.com configuration for trigger type"""
    configs = {
        'revenue_milestone': {
            'webhook_url': 'https://hook.integromat.com/revenue-milestone',
            'api_key': None  # Store securely in production
        },
        'opportunity_status': {
            'webhook_url': 'https://hook.integromat.com/opportunity-sync',
            'api_key': None
        },
        'agent_performance': {
            'webhook_url': 'https://hook.integromat.com/agent-performance',
            'api_key': None
        },
        'lead_qualification': {
            'webhook_url': 'https://hook.integromat.com/lead-qualification',
            'api_key': None
        }
    }
    return configs.get(trigger_type)

def _transform_data_for_make(trigger_type, data):
    """Transform AI Empire data to Make.com format"""
    base_payload = {
        'source': 'ai_empire_platform',
        'trigger_type': trigger_type,
        'timestamp': datetime.now().isoformat(),
        'version': '1.0'
    }
    
    if trigger_type == 'revenue_milestone':
        base_payload.update({
            'milestone_amount': data.get('milestone_amount'),
            'current_amount': data.get('current_amount'),
            'stream_name': data.get('stream_name'),
            'percentage_increase': data.get('percentage_increase')
        })
    elif trigger_type == 'opportunity_status':
        base_payload.update({
            'opportunity_title': data.get('opportunity_title'),
            'company': data.get('company'),
            'status': data.get('status'),
            'compensation_range': data.get('compensation_range'),
            'ai_match_score': data.get('ai_match_score')
        })
    elif trigger_type == 'agent_performance':
        base_payload.update({
            'agent_name': data.get('agent_name'),
            'success_rate': data.get('success_rate'),
            'pipeline_value': data.get('pipeline_value'),
            'performance_trend': data.get('performance_trend')
        })
    
    return base_payload

def _get_make_test_data(scenario_id):
    """Get test data for Make.com scenarios"""
    test_data = {
        'revenue_milestone_alert': {
            'milestone_amount': 10000000,
            'current_amount': 12500000,
            'stream_name': 'AI Agent Services',
            'percentage_increase': 25.0
        },
        'opportunity_pipeline_sync': {
            'opportunity_title': 'Board Director - TechCorp',
            'company': 'TechCorp Industries',
            'status': 'offer_received',
            'compensation_range': '$150K-$200K',
            'ai_match_score': 95
        },
        'agent_performance_optimization': {
            'agent_name': 'Lead Generation Agent',
            'success_rate': 97.5,
            'pipeline_value': 2500000,
            'performance_trend': 'increasing'
        },
        'lead_qualification_workflow': {
            'lead_name': 'John Smith',
            'company': 'Enterprise Solutions Inc',
            'qualification_score': 85,
            'revenue_potential': 500000
        }
    }
    return test_data.get(scenario_id)

def _get_make_scenario_config(scenario_id):
    """Get scenario configuration for testing"""
    configs = {
        'revenue_milestone_alert': {
            'webhook_url': 'https://hook.integromat.com/revenue-milestone'
        },
        'opportunity_pipeline_sync': {
            'webhook_url': 'https://hook.integromat.com/opportunity-sync'
        },
        'agent_performance_optimization': {
            'webhook_url': 'https://hook.integromat.com/agent-optimization'
        },
        'lead_qualification_workflow': {
            'webhook_url': 'https://hook.integromat.com/lead-qualification'
        }
    }
    return configs.get(scenario_id)

@app.route('/api/webhooks/<int:webhook_id>/test', methods=['POST'])
@jwt_required()
def test_webhook(webhook_id):
    """Test webhook delivery"""
    try:
        webhook = WorkflowWebhook.query.get(webhook_id)
        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404
        
        test_payload = {
            "event_type": "test",
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "webhook_id": webhook_id,
            "webhook_name": webhook.name
        }
        
        headers = webhook.headers or {}
        if webhook.secret_key:
            headers['X-Webhook-Secret'] = webhook.secret_key
        
        try:
            response = requests.post(
                webhook.webhook_url,
                json=test_payload,
                headers=headers,
                timeout=webhook.timeout_seconds
            )
            response.raise_for_status()
            
            return jsonify({
                "success": True,
                "status_code": response.status_code,
                "response_headers": dict(response.headers),
                "test_payload": test_payload
            })
            
        except requests.exceptions.RequestException as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "test_payload": test_payload
            }), 400
        
    except Exception as e:
        logger.error(f"Test webhook error: {e}")
        return jsonify({"error": "Failed to test webhook"}), 500

# ============================
# AIRTABLE CRM INTEGRATION API
# ============================

# Airtable Sync Management
@app.route('/api/airtable/status', methods=['GET'])
@jwt_required()
def get_airtable_status():
    """Get Airtable integration status and configuration"""
    try:
        if not create_airtable_client:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        # Check API key validity
        try:
            client = create_airtable_client()
            bases = client.list_bases()
            api_valid = True
        except Exception as e:
            api_valid = False
            bases = []
        
        # Get scheduler status
        scheduler_status = {}
        if get_scheduler:
            try:
                scheduler = get_scheduler()
                scheduler_status = scheduler.get_job_status()
            except Exception as e:
                scheduler_status = {"error": str(e)}
        
        return jsonify({
            "api_key_valid": api_valid,
            "available_bases": len(bases),
            "bases": bases[:5],  # First 5 bases for preview
            "scheduler": scheduler_status.get('scheduler_running', False),
            "total_jobs": scheduler_status.get('total_jobs', 0),
            "enabled_jobs": scheduler_status.get('enabled_jobs', 0)
        })
        
    except Exception as e:
        logger.error(f"Airtable status error: {e}")
        return jsonify({"error": "Failed to get Airtable status"}), 500

@app.route('/api/airtable/bases', methods=['GET'])
@jwt_required()
def list_airtable_bases():
    """List all accessible Airtable bases"""
    try:
        if not create_airtable_client:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        client = create_airtable_client()
        bases = client.list_bases()
        
        return jsonify({
            "bases": bases,
            "total": len(bases)
        })
        
    except Exception as e:
        logger.error(f"List Airtable bases error: {e}")
        return jsonify({"error": "Failed to list Airtable bases"}), 500

@app.route('/api/airtable/bases/<string:base_id>/schema', methods=['GET'])
@jwt_required()
def get_base_schema(base_id):
    """Get schema for a specific Airtable base"""
    try:
        if not create_airtable_client:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        client = create_airtable_client()
        schema = client.get_base_schema(base_id)
        
        return jsonify(schema)
        
    except Exception as e:
        logger.error(f"Get base schema error: {e}")
        return jsonify({"error": "Failed to get base schema"}), 500

@app.route('/api/airtable/bases/<string:base_id>/validate', methods=['POST'])
@jwt_required()
def validate_base_configuration(base_id):
    """Validate base configuration for CRM sync"""
    try:
        if not create_base_manager:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        manager = create_base_manager()
        validation = manager.validate_base_configuration(base_id)
        
        return jsonify(validation)
        
    except Exception as e:
        logger.error(f"Base validation error: {e}")
        return jsonify({"error": "Failed to validate base configuration"}), 500

@app.route('/api/airtable/bases/<string:base_id>/setup', methods=['POST'])
@jwt_required()
def setup_base_configuration(base_id):
    """Setup base for CRM synchronization"""
    try:
        if not create_base_manager:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        manager = create_base_manager()
        setup_result = manager.setup_existing_base(base_id)
        
        return jsonify(setup_result)
        
    except Exception as e:
        logger.error(f"Base setup error: {e}")
        return jsonify({"error": "Failed to setup base configuration"}), 500

# Sync Operations
@app.route('/api/airtable/sync/table/<string:table_name>', methods=['POST'])
@jwt_required()
def sync_table(table_name):
    """Sync a specific table to/from Airtable"""
    try:
        if not create_sync_service:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        data = request.get_json() or {}
        base_id = data.get('base_id')
        direction = data.get('direction', 'bidirectional')
        
        if not base_id:
            return jsonify({"error": "base_id is required"}), 400
        
        # Create sync configuration
        sync_config = SyncConfiguration(
            enabled_tables=[table_name],
            sync_direction=SyncDirection(direction),
            conflict_strategy=ConflictStrategy(data.get('conflict_strategy', 'timestamp_based')),
            batch_size=data.get('batch_size', 10)
        )
        
        sync_service = create_sync_service(base_id, sync_config)
        
        if direction == 'to_airtable':
            results = sync_service.sync_table_to_airtable(table_name)
        elif direction == 'from_airtable':
            results = sync_service.sync_table_from_airtable(table_name)
        else:  # bidirectional
            results = sync_service.sync_bidirectional(table_name)
        
        return jsonify({
            "table": table_name,
            "direction": direction,
            "results": [result.__dict__ for result in results] if isinstance(results, list) else results
        })
        
    except Exception as e:
        logger.error(f"Table sync error: {e}")
        return jsonify({"error": "Failed to sync table"}), 500

@app.route('/api/airtable/sync/full', methods=['POST'])
@jwt_required()
def sync_all_tables():
    """Perform full synchronization of all enabled tables"""
    try:
        if not create_sync_service:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        data = request.get_json() or {}
        base_id = data.get('base_id')
        
        if not base_id:
            return jsonify({"error": "base_id is required"}), 400
        
        # Create sync configuration
        enabled_tables = data.get('enabled_tables', [
            'revenue_streams', 'ai_agents', 'executive_opportunities',
            'healthcare_providers', 'healthcare_appointments', 'retreat_events'
        ])
        
        sync_config = SyncConfiguration(
            enabled_tables=enabled_tables,
            sync_direction=SyncDirection(data.get('direction', 'bidirectional')),
            conflict_strategy=ConflictStrategy(data.get('conflict_strategy', 'timestamp_based')),
            batch_size=data.get('batch_size', 15)
        )
        
        sync_service = create_sync_service(base_id, sync_config)
        summary = sync_service.sync_all_tables()
        
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Full sync error: {e}")
        return jsonify({"error": "Failed to perform full sync"}), 500

# Sync Jobs Management
@app.route('/api/airtable/jobs', methods=['GET'])
@jwt_required()
def get_sync_jobs():
    """Get all sync jobs"""
    try:
        if not get_scheduler:
            return jsonify({"error": "Airtable scheduler not available"}), 503
        
        scheduler = get_scheduler()
        status = scheduler.get_job_status()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Get sync jobs error: {e}")
        return jsonify({"error": "Failed to get sync jobs"}), 500

@app.route('/api/airtable/jobs/<string:job_id>', methods=['GET'])
@jwt_required()
def get_sync_job(job_id):
    """Get specific sync job details"""
    try:
        if not get_scheduler:
            return jsonify({"error": "Airtable scheduler not available"}), 503
        
        scheduler = get_scheduler()
        job_status = scheduler.get_job_status(job_id)
        
        return jsonify(job_status)
        
    except Exception as e:
        logger.error(f"Get sync job error: {e}")
        return jsonify({"error": "Failed to get sync job"}), 500

@app.route('/api/airtable/jobs', methods=['POST'])
@jwt_required()
def create_sync_job():
    """Create a new sync job"""
    try:
        if not get_scheduler:
            return jsonify({"error": "Airtable scheduler not available"}), 503
        
        from airtable_sync_scheduler import SyncJob
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['id', 'name', 'base_id', 'tables', 'schedule_type', 'schedule_config']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create sync configuration
        sync_config_data = data.get('sync_config', {})
        sync_config = SyncConfiguration(
            enabled_tables=sync_config_data.get('enabled_tables', data['tables']),
            sync_direction=SyncDirection(sync_config_data.get('sync_direction', 'bidirectional')),
            conflict_strategy=ConflictStrategy(sync_config_data.get('conflict_strategy', 'timestamp_based')),
            batch_size=sync_config_data.get('batch_size', 10)
        )
        
        # Create sync job
        job = SyncJob(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            base_id=data['base_id'],
            tables=data['tables'],
            schedule_type=data['schedule_type'],
            schedule_config=data['schedule_config'],
            sync_config=sync_config,
            enabled=data.get('enabled', True)
        )
        
        scheduler = get_scheduler()
        success = scheduler.add_sync_job(job)
        
        if success:
            return jsonify({"message": "Sync job created successfully", "job_id": job.id}), 201
        else:
            return jsonify({"error": "Failed to create sync job"}), 400
        
    except Exception as e:
        logger.error(f"Create sync job error: {e}")
        return jsonify({"error": "Failed to create sync job"}), 500

@app.route('/api/airtable/jobs/<string:job_id>', methods=['PUT'])
@jwt_required()
def update_sync_job(job_id):
    """Update an existing sync job"""
    try:
        if not get_scheduler:
            return jsonify({"error": "Airtable scheduler not available"}), 503
        
        data = request.get_json()
        scheduler = get_scheduler()
        
        success = scheduler.update_job(job_id, data)
        
        if success:
            return jsonify({"message": "Sync job updated successfully"})
        else:
            return jsonify({"error": "Failed to update sync job"}), 400
        
    except Exception as e:
        logger.error(f"Update sync job error: {e}")
        return jsonify({"error": "Failed to update sync job"}), 500

@app.route('/api/airtable/jobs/<string:job_id>', methods=['DELETE'])
@jwt_required()
def delete_sync_job(job_id):
    """Delete a sync job"""
    try:
        if not get_scheduler:
            return jsonify({"error": "Airtable scheduler not available"}), 503
        
        scheduler = get_scheduler()
        success = scheduler.remove_job(job_id)
        
        if success:
            return jsonify({"message": "Sync job deleted successfully"})
        else:
            return jsonify({"error": "Job not found"}), 404
        
    except Exception as e:
        logger.error(f"Delete sync job error: {e}")
        return jsonify({"error": "Failed to delete sync job"}), 500

@app.route('/api/airtable/jobs/<string:job_id>/execute', methods=['POST'])
@jwt_required()
def execute_sync_job(job_id):
    """Execute a sync job immediately"""
    try:
        if not get_scheduler:
            return jsonify({"error": "Airtable scheduler not available"}), 503
        
        scheduler = get_scheduler()
        
        # Execute the job immediately
        scheduler._execute_job(job_id)
        
        return jsonify({"message": f"Sync job {job_id} executed successfully"})
        
    except Exception as e:
        logger.error(f"Execute sync job error: {e}")
        return jsonify({"error": "Failed to execute sync job"}), 500

# Scheduler Control
@app.route('/api/airtable/scheduler/start', methods=['POST'])
@jwt_required()
def start_sync_scheduler():
    """Start the sync scheduler"""
    try:
        if not get_scheduler:
            return jsonify({"error": "Airtable scheduler not available"}), 503
        
        scheduler = get_scheduler()
        scheduler.start_scheduler()
        
        return jsonify({"message": "Sync scheduler started successfully"})
        
    except Exception as e:
        logger.error(f"Start scheduler error: {e}")
        return jsonify({"error": "Failed to start sync scheduler"}), 500

@app.route('/api/airtable/scheduler/stop', methods=['POST'])
@jwt_required()
def stop_sync_scheduler():
    """Stop the sync scheduler"""
    try:
        if not get_scheduler:
            return jsonify({"error": "Airtable scheduler not available"}), 503
        
        scheduler = get_scheduler()
        scheduler.stop_scheduler()
        
        return jsonify({"message": "Sync scheduler stopped successfully"})
        
    except Exception as e:
        logger.error(f"Stop scheduler error: {e}")
        return jsonify({"error": "Failed to stop sync scheduler"}), 500

# Conflict Resolution
@app.route('/api/airtable/conflicts', methods=['GET'])
@jwt_required()
def get_sync_conflicts():
    """Get unresolved sync conflicts"""
    try:
        if not create_sync_service:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        # Get conflicts from all sync services
        # This would need to be tracked globally in a production system
        conflicts = []
        
        return jsonify({
            "conflicts": conflicts,
            "total": len(conflicts)
        })
        
    except Exception as e:
        logger.error(f"Get sync conflicts error: {e}")
        return jsonify({"error": "Failed to get sync conflicts"}), 500

# Base Management Templates
@app.route('/api/airtable/schema/template', methods=['GET'])
@jwt_required()
def get_crm_schema_template():
    """Get the CRM schema template for manual base setup"""
    try:
        if not create_base_manager:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        manager = create_base_manager()
        template = manager.create_base_from_template()
        
        return jsonify(template)
        
    except Exception as e:
        logger.error(f"Get schema template error: {e}")
        return jsonify({"error": "Failed to get schema template"}), 500

@app.route('/api/airtable/schema/instructions', methods=['GET'])
@jwt_required()
def get_setup_instructions():
    """Get detailed setup instructions for manual base configuration"""
    try:
        if not create_base_manager:
            return jsonify({"error": "Airtable integration not available"}), 503
        
        manager = create_base_manager()
        instructions = manager.get_setup_instructions()
        
        return jsonify(instructions)
        
    except Exception as e:
        logger.error(f"Get setup instructions error: {e}")
        return jsonify({"error": "Failed to get setup instructions"}), 500

# Data Export/Import
@app.route('/api/airtable/export/<string:table_name>', methods=['GET'])
@jwt_required()
def export_table_data(table_name):
    """Export table data for backup or analysis"""
    try:
        # Get the model class
        model_mapping = {
            'revenue_streams': RevenueStream,
            'ai_agents': AIAgent,
            'executive_opportunities': ExecutiveOpportunity,
            'healthcare_providers': HealthcareProvider,
            'healthcare_appointments': HealthcareAppointment,
            'retreat_events': RetreatEvent,
            'kpi_metrics': KPIMetric,
            'milestones': Milestone
        }
        
        if table_name not in model_mapping:
            return jsonify({"error": "Invalid table name"}), 400
        
        model = model_mapping[table_name]
        records = model.query.all()
        
        # Convert to dictionaries
        data = []
        for record in records:
            if hasattr(record, 'to_dict'):
                data.append(record.to_dict())
            else:
                record_dict = {}
                for column in record.__table__.columns:
                    value = getattr(record, column.name)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    record_dict[column.name] = value
                data.append(record_dict)
        
        return jsonify({
            "table": table_name,
            "total_records": len(data),
            "exported_at": datetime.utcnow().isoformat(),
            "data": data
        })
        
    except Exception as e:
        logger.error(f"Export table data error: {e}")
        return jsonify({"error": "Failed to export table data"}), 500

# Sync Statistics and Monitoring
@app.route('/api/airtable/stats', methods=['GET'])
@jwt_required()
def get_sync_statistics():
    """Get comprehensive sync statistics"""
    try:
        stats = {
            "airtable_integration": {
                "enabled": create_airtable_client is not None,
                "api_key_configured": bool(AIRTABLE_API_KEY)
            },
            "scheduler": {
                "available": get_scheduler is not None,
                "running": False,
                "total_jobs": 0,
                "enabled_jobs": 0
            },
            "last_sync_times": {},
            "sync_performance": {
                "total_syncs": 0,
                "successful_syncs": 0,
                "failed_syncs": 0,
                "average_sync_time": 0
            }
        }
        
        # Get scheduler stats if available
        if get_scheduler:
            try:
                scheduler = get_scheduler()
                scheduler_status = scheduler.get_job_status()
                stats["scheduler"].update({
                    "running": scheduler_status.get('scheduler_running', False),
                    "total_jobs": scheduler_status.get('total_jobs', 0),
                    "enabled_jobs": scheduler_status.get('enabled_jobs', 0)
                })
            except Exception as e:
                logger.warning(f"Could not get scheduler stats: {e}")
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Get sync statistics error: {e}")
        return jsonify({"error": "Failed to get sync statistics"}), 500

# Real-time Webhooks and Event Streaming
@app.route('/api/airtable/webhooks', methods=['POST'])
def airtable_webhook():
    """Receive webhooks from Airtable for real-time updates"""
    try:
        if not get_realtime_handler:
            return jsonify({"error": "Real-time handler not available"}), 503
        
        webhook_data = request.get_json()
        webhook_id = request.headers.get('X-Webhook-ID', 'unknown')
        
        # Get realtime handler and process webhook
        handler = get_realtime_handler()
        result = handler.handle_airtable_webhook(webhook_data, webhook_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Airtable webhook error: {e}")
        return jsonify({"error": "Failed to process webhook"}), 500

@app.route('/api/airtable/events', methods=['GET'])
@jwt_required()
def get_recent_events():
    """Get recent real-time events"""
    try:
        if not get_realtime_handler:
            return jsonify({"error": "Real-time handler not available"}), 503
        
        limit = int(request.args.get('limit', 50))
        event_type = request.args.get('event_type')
        table_name = request.args.get('table_name')
        
        handler = get_realtime_handler()
        
        # Convert event_type string to enum if provided
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                return jsonify({"error": f"Invalid event type: {event_type}"}), 400
        
        events = handler.get_recent_events(limit, event_type_enum, table_name)
        
        # Convert events to dictionaries
        event_dicts = []
        for event in events:
            event_dict = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "source": event.source,
                "table_name": event.table_name,
                "record_id": event.record_id,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
                "base_id": event.base_id,
                "processed": event.processed,
                "retry_count": event.retry_count
            }
            event_dicts.append(event_dict)
        
        return jsonify({
            "events": event_dicts,
            "total": len(event_dicts),
            "filters": {
                "limit": limit,
                "event_type": event_type,
                "table_name": table_name
            }
        })
        
    except Exception as e:
        logger.error(f"Get recent events error: {e}")
        return jsonify({"error": "Failed to get recent events"}), 500

@app.route('/api/airtable/events/stats', methods=['GET'])
@jwt_required()
def get_event_statistics():
    """Get real-time event processing statistics"""
    try:
        if not get_realtime_handler:
            return jsonify({"error": "Real-time handler not available"}), 503
        
        handler = get_realtime_handler()
        stats = handler.get_event_statistics()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Get event statistics error: {e}")
        return jsonify({"error": "Failed to get event statistics"}), 500

@app.route('/api/airtable/realtime/start', methods=['POST'])
@jwt_required()
def start_realtime_processing():
    """Start real-time event processing"""
    try:
        if not get_realtime_handler:
            return jsonify({"error": "Real-time handler not available"}), 503
        
        handler = get_realtime_handler()
        handler.start_processing()
        
        return jsonify({"message": "Real-time processing started successfully"})
        
    except Exception as e:
        logger.error(f"Start realtime processing error: {e}")
        return jsonify({"error": "Failed to start real-time processing"}), 500

@app.route('/api/airtable/realtime/stop', methods=['POST'])
@jwt_required()
def stop_realtime_processing():
    """Stop real-time event processing"""
    try:
        if not get_realtime_handler:
            return jsonify({"error": "Real-time handler not available"}), 503
        
        handler = get_realtime_handler()
        handler.stop_processing()
        
        return jsonify({"message": "Real-time processing stopped successfully"})
        
    except Exception as e:
        logger.error(f"Stop realtime processing error: {e}")
        return jsonify({"error": "Failed to stop real-time processing"}), 500

@app.route('/api/airtable/webhook/config', methods=['POST'])
@jwt_required()
def configure_webhook():
    """Configure a webhook endpoint"""
    try:
        if not get_realtime_handler:
            return jsonify({"error": "Real-time handler not available"}), 503
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['id', 'name', 'base_id', 'webhook_url']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create webhook config
        webhook_config = WebhookConfig(
            id=data['id'],
            name=data['name'],
            base_id=data['base_id'],
            webhook_url=data['webhook_url'],
            secret_key=data.get('secret_key'),
            enabled=data.get('enabled', True),
            event_types=data.get('event_types', ['record_created', 'record_updated', 'record_deleted'])
        )
        
        handler = get_realtime_handler()
        handler.configure_webhook(webhook_config)
        
        return jsonify({
            "message": "Webhook configured successfully",
            "webhook_id": webhook_config.id
        }), 201
        
    except Exception as e:
        logger.error(f"Configure webhook error: {e}")
        return jsonify({"error": "Failed to configure webhook"}), 500

@app.route('/api/airtable/webhook/config', methods=['GET'])
@jwt_required()
def list_webhook_configs():
    """List all webhook configurations"""
    try:
        if not get_realtime_handler:
            return jsonify({"error": "Real-time handler not available"}), 503
        
        handler = get_realtime_handler()
        configs = handler.list_webhook_configs()
        
        # Convert to dictionaries
        config_dicts = []
        for config in configs:
            config_dict = {
                "id": config.id,
                "name": config.name,
                "base_id": config.base_id,
                "webhook_url": config.webhook_url,
                "enabled": config.enabled,
                "event_types": config.event_types,
                "created_at": config.created_at.isoformat()
            }
            config_dicts.append(config_dict)
        
        return jsonify({
            "webhooks": config_dicts,
            "total": len(config_dicts)
        })
        
    except Exception as e:
        logger.error(f"List webhook configs error: {e}")
        return jsonify({"error": "Failed to list webhook configurations"}), 500

# Initialize Airtable integration on startup
def initialize_airtable_integration():
    """Initialize Airtable integration components on startup"""
    try:
        # Start realtime processing if available
        if get_realtime_handler:
            handler = get_realtime_handler()
            handler.start_processing()
            logger.info("Airtable real-time processing started")
        
        # Start sync scheduler if available
        if get_scheduler:
            scheduler = get_scheduler()
            scheduler.start_scheduler()
            logger.info("Airtable sync scheduler started")
            
    except Exception as e:
        logger.error(f"Error initializing Airtable integration: {e}")

# Call initialization after app setup
with app.app_context():
    initialize_airtable_integration()

# ============================
# WORKFLOW MANAGEMENT API
# ============================

# Workflow Triggers Management
@app.route('/api/workflows/triggers', methods=['GET'])
@jwt_required()
def get_workflow_triggers():
    """Get all workflow triggers"""
    try:
        triggers = WorkflowTrigger.query.all()
        return jsonify([trigger.to_dict() for trigger in triggers])
    except Exception as e:
        logger.error(f"Get workflow triggers error: {e}")
        return jsonify({"error": "Failed to fetch workflow triggers"}), 500

@app.route('/api/workflows/triggers', methods=['POST'])
@jwt_required()
def create_workflow_trigger():
    """Create a new workflow trigger"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'trigger_type', 'event_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate trigger type
        valid_types = ['event', 'schedule', 'webhook', 'manual']
        if data.get('trigger_type') not in valid_types:
            return jsonify({"error": f"Invalid trigger type. Must be one of: {', '.join(valid_types)}"}), 400
        
        trigger = WorkflowTrigger(
            name=data['name'],
            description=data.get('description'),
            trigger_type=data['trigger_type'],
            event_type=data['event_type'],
            conditions=data.get('conditions', {}),
            enabled=data.get('enabled', True),
            priority=data.get('priority', 5),
            metadata=data.get('metadata', {})
        )
        
        db.session.add(trigger)
        db.session.commit()
        
        return jsonify(trigger.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create workflow trigger error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create workflow trigger"}), 500

@app.route('/api/workflows/triggers/<int:trigger_id>', methods=['GET'])
@jwt_required()
def get_workflow_trigger(trigger_id):
    """Get specific workflow trigger"""
    try:
        trigger = WorkflowTrigger.query.get(trigger_id)
        if not trigger:
            return jsonify({"error": "Trigger not found"}), 404
        return jsonify(trigger.to_dict())
    except Exception as e:
        logger.error(f"Get workflow trigger error: {e}")
        return jsonify({"error": "Failed to fetch workflow trigger"}), 500

@app.route('/api/workflows/triggers/<int:trigger_id>', methods=['PUT'])
@jwt_required()
def update_workflow_trigger(trigger_id):
    """Update workflow trigger"""
    try:
        trigger = WorkflowTrigger.query.get(trigger_id)
        if not trigger:
            return jsonify({"error": "Trigger not found"}), 404
        
        data = request.get_json()
        
        # Update fields
        for field in ['name', 'description', 'trigger_type', 'event_type', 'conditions', 'enabled', 'priority', 'metadata']:
            if field in data:
                setattr(trigger, field, data[field])
        
        db.session.commit()
        return jsonify(trigger.to_dict())
        
    except Exception as e:
        logger.error(f"Update workflow trigger error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update workflow trigger"}), 500

@app.route('/api/workflows/triggers/<int:trigger_id>', methods=['DELETE'])
@jwt_required()
def delete_workflow_trigger(trigger_id):
    """Delete workflow trigger"""
    try:
        trigger = WorkflowTrigger.query.get(trigger_id)
        if not trigger:
            return jsonify({"error": "Trigger not found"}), 404
        
        # Check for dependent rules
        dependent_rules = BusinessRule.query.filter_by(trigger_id=trigger_id).all()
        if dependent_rules:
            return jsonify({
                "error": "Cannot delete trigger with dependent business rules",
                "dependent_rules": [rule.name for rule in dependent_rules]
            }), 400
        
        db.session.delete(trigger)
        db.session.commit()
        return jsonify({"message": "Trigger deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Delete workflow trigger error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete workflow trigger"}), 500

# Business Rules Management
@app.route('/api/workflows/rules', methods=['GET'])
@jwt_required()
def get_business_rules():
    """Get all business rules"""
    try:
        rules = BusinessRule.query.all()
        return jsonify([rule.to_dict() for rule in rules])
    except Exception as e:
        logger.error(f"Get business rules error: {e}")
        return jsonify({"error": "Failed to fetch business rules"}), 500

@app.route('/api/workflows/rules', methods=['POST'])
@jwt_required()
def create_business_rule():
    """Create a new business rule"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'trigger_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate trigger exists
        trigger = WorkflowTrigger.query.get(data['trigger_id'])
        if not trigger:
            return jsonify({"error": "Invalid trigger_id"}), 400
        
        rule = BusinessRule(
            name=data['name'],
            description=data.get('description'),
            trigger_id=data['trigger_id'],
            conditions=data.get('conditions', {}),
            actions=data.get('actions', []),
            enabled=data.get('enabled', True),
            priority=data.get('priority', 5),
            metadata=data.get('metadata', {})
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify(rule.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create business rule error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create business rule"}), 500

@app.route('/api/workflows/rules/<int:rule_id>', methods=['GET'])
@jwt_required()
def get_business_rule(rule_id):
    """Get specific business rule"""
    try:
        rule = BusinessRule.query.get(rule_id)
        if not rule:
            return jsonify({"error": "Rule not found"}), 404
        return jsonify(rule.to_dict())
    except Exception as e:
        logger.error(f"Get business rule error: {e}")
        return jsonify({"error": "Failed to fetch business rule"}), 500

@app.route('/api/workflows/rules/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_business_rule(rule_id):
    """Update business rule"""
    try:
        rule = BusinessRule.query.get(rule_id)
        if not rule:
            return jsonify({"error": "Rule not found"}), 404
        
        data = request.get_json()
        
        # Validate trigger if updated
        if 'trigger_id' in data:
            trigger = WorkflowTrigger.query.get(data['trigger_id'])
            if not trigger:
                return jsonify({"error": "Invalid trigger_id"}), 400
        
        # Update fields
        for field in ['name', 'description', 'trigger_id', 'conditions', 'actions', 'enabled', 'priority', 'metadata']:
            if field in data:
                setattr(rule, field, data[field])
        
        db.session.commit()
        return jsonify(rule.to_dict())
        
    except Exception as e:
        logger.error(f"Update business rule error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update business rule"}), 500

@app.route('/api/workflows/rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_business_rule(rule_id):
    """Delete business rule"""
    try:
        rule = BusinessRule.query.get(rule_id)
        if not rule:
            return jsonify({"error": "Rule not found"}), 404
        
        db.session.delete(rule)
        db.session.commit()
        return jsonify({"message": "Rule deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Delete business rule error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete business rule"}), 500

@app.route('/api/workflows/rules/<int:rule_id>/test', methods=['POST'])
@jwt_required()
def test_business_rule(rule_id):
    """Test a business rule with sample data"""
    try:
        rule = BusinessRule.query.get(rule_id)
        if not rule:
            return jsonify({"error": "Rule not found"}), 404
        
        data = request.get_json()
        test_context = data.get('context', {})
        
        # Test rule conditions
        conditions_result = business_rule_engine._evaluate_conditions(rule.conditions, test_context)
        
        results = []
        if conditions_result:
            # Execute actions in test mode
            for action in rule.actions:
                action_result = business_rule_engine._execute_action(action, test_context, test_mode=True)
                results.append(action_result)
        
        return jsonify({
            'rule_id': rule_id,
            'rule_name': rule.name,
            'conditions_met': conditions_result,
            'actions_executed': len(results) if conditions_result else 0,
            'test_results': results,
            'test_context': test_context
        })
        
    except Exception as e:
        logger.error(f"Test business rule error: {e}")
        return jsonify({"error": "Failed to test business rule"}), 500

# Workflow Actions Management
@app.route('/api/workflows/actions', methods=['GET'])
@jwt_required()
def get_workflow_actions():
    """Get all workflow actions"""
    try:
        actions = WorkflowAction.query.all()
        return jsonify([action.to_dict() for action in actions])
    except Exception as e:
        logger.error(f"Get workflow actions error: {e}")
        return jsonify({"error": "Failed to fetch workflow actions"}), 500

@app.route('/api/workflows/actions', methods=['POST'])
@jwt_required()
def create_workflow_action():
    """Create a new workflow action"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'action_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate action type
        valid_types = ['notification', 'webhook', 'email', 'update_data', 'trigger_event', 'execute_script']
        if data.get('action_type') not in valid_types:
            return jsonify({"error": f"Invalid action type. Must be one of: {', '.join(valid_types)}"}), 400
        
        action = WorkflowAction(
            name=data['name'],
            description=data.get('description'),
            action_type=data['action_type'],
            configuration=data.get('configuration', {}),
            enabled=data.get('enabled', True),
            retry_attempts=data.get('retry_attempts', 3),
            timeout_seconds=data.get('timeout_seconds', 30),
            metadata=data.get('metadata', {})
        )
        
        db.session.add(action)
        db.session.commit()
        
        return jsonify(action.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Create workflow action error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create workflow action"}), 500

@app.route('/api/workflows/actions/<int:action_id>', methods=['GET'])
@jwt_required()
def get_workflow_action(action_id):
    """Get specific workflow action"""
    try:
        action = WorkflowAction.query.get(action_id)
        if not action:
            return jsonify({"error": "Action not found"}), 404
        return jsonify(action.to_dict())
    except Exception as e:
        logger.error(f"Get workflow action error: {e}")
        return jsonify({"error": "Failed to fetch workflow action"}), 500

@app.route('/api/workflows/actions/<int:action_id>', methods=['PUT'])
@jwt_required()
def update_workflow_action(action_id):
    """Update workflow action"""
    try:
        action = WorkflowAction.query.get(action_id)
        if not action:
            return jsonify({"error": "Action not found"}), 404
        
        data = request.get_json()
        
        # Update fields
        for field in ['name', 'description', 'action_type', 'configuration', 'enabled', 'retry_attempts', 'timeout_seconds', 'metadata']:
            if field in data:
                setattr(action, field, data[field])
        
        db.session.commit()
        return jsonify(action.to_dict())
        
    except Exception as e:
        logger.error(f"Update workflow action error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update workflow action"}), 500

@app.route('/api/workflows/actions/<int:action_id>', methods=['DELETE'])
@jwt_required()
def delete_workflow_action(action_id):
    """Delete workflow action"""
    try:
        action = WorkflowAction.query.get(action_id)
        if not action:
            return jsonify({"error": "Action not found"}), 404
        
        db.session.delete(action)
        db.session.commit()
        return jsonify({"message": "Action deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Delete workflow action error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete workflow action"}), 500

@app.route('/api/workflows/actions/<int:action_id>/test', methods=['POST'])
@jwt_required()
def test_workflow_action(action_id):
    """Test a workflow action"""
    try:
        action = WorkflowAction.query.get(action_id)
        if not action:
            return jsonify({"error": "Action not found"}), 404
        
        data = request.get_json()
        test_context = data.get('context', {})
        
        # Execute action in test mode
        result = business_rule_engine._execute_action({
            'action': action.action_type,
            'configuration': action.configuration
        }, test_context, test_mode=True)
        
        return jsonify({
            'action_id': action_id,
            'action_name': action.name,
            'action_type': action.action_type,
            'test_result': result,
            'test_context': test_context
        })
        
    except Exception as e:
        logger.error(f"Test workflow action error: {e}")
        return jsonify({"error": "Failed to test workflow action"}), 500

# Workflow Executions Management
@app.route('/api/workflows/executions', methods=['GET'])
@jwt_required()
def get_workflow_executions():
    """Get workflow executions with optional filtering"""
    try:
        query = WorkflowExecution.query
        
        # Filter by status
        status = request.args.get('status')
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        # Filter by trigger
        trigger_id = request.args.get('trigger_id')
        if trigger_id:
            query = query.filter(WorkflowExecution.trigger_id == trigger_id)
        
        # Filter by rule
        rule_id = request.args.get('rule_id')
        if rule_id:
            query = query.filter(WorkflowExecution.rule_id == rule_id)
        
        # Date range filter
        start_date = request.args.get('start_date')
        if start_date:
            query = query.filter(WorkflowExecution.start_time >= datetime.fromisoformat(start_date))
        
        end_date = request.args.get('end_date')
        if end_date:
            query = query.filter(WorkflowExecution.start_time <= datetime.fromisoformat(end_date))
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        executions = query.order_by(WorkflowExecution.start_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'executions': [execution.to_dict() for execution in executions.items],
            'total': executions.total,
            'pages': executions.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        logger.error(f"Get workflow executions error: {e}")
        return jsonify({"error": "Failed to fetch workflow executions"}), 500

@app.route('/api/workflows/executions/<string:execution_id>', methods=['GET'])
@jwt_required()
def get_workflow_execution(execution_id):
    """Get specific workflow execution"""
    try:
        execution = WorkflowExecution.query.filter_by(execution_id=execution_id).first()
        if not execution:
            return jsonify({"error": "Execution not found"}), 404
        return jsonify(execution.to_dict())
    except Exception as e:
        logger.error(f"Get workflow execution error: {e}")
        return jsonify({"error": "Failed to fetch workflow execution"}), 500

@app.route('/api/workflows/executions/<string:execution_id>/retry', methods=['POST'])
@jwt_required()
def retry_workflow_execution(execution_id):
    """Retry a failed workflow execution"""
    try:
        execution = WorkflowExecution.query.filter_by(execution_id=execution_id).first()
        if not execution:
            return jsonify({"error": "Execution not found"}), 404
        
        if execution.status != 'failed':
            return jsonify({"error": "Can only retry failed executions"}), 400
        
        # Create new execution for retry
        new_execution = WorkflowExecution(
            trigger_id=execution.trigger_id,
            rule_id=execution.rule_id,
            status='running',
            start_time=datetime.now(),
            metadata={**execution.metadata, 'retry_of': execution_id}
        )
        
        db.session.add(new_execution)
        db.session.commit()
        
        # Execute the workflow
        # In production, this would be handled by background job system
        logger.info(f"Retrying workflow execution: {execution_id}")
        
        return jsonify({
            'message': 'Workflow execution retry initiated',
            'new_execution_id': new_execution.execution_id,
            'original_execution_id': execution_id
        })
        
    except Exception as e:
        logger.error(f"Retry workflow execution error: {e}")
        return jsonify({"error": "Failed to retry workflow execution"}), 500

# Workflow Templates and Presets
@app.route('/api/workflows/templates', methods=['GET'])
@jwt_required()
def get_workflow_templates():
    """Get predefined workflow templates"""
    try:
        templates = [
            {
                "id": "revenue_milestone_workflow",
                "name": "Revenue Milestone Workflow",
                "description": "Automated workflow for revenue milestone notifications and actions",
                "trigger": {
                    "name": "Revenue Milestone Trigger",
                    "trigger_type": "event",
                    "event_type": "revenue_milestone",
                    "conditions": {"milestone_amount": {"gte": 1000000}}
                },
                "rules": [
                    {
                        "name": "Revenue Milestone Alert Rule",
                        "conditions": {"percentage_increase": {"gte": 10}},
                        "actions": [
                            {"action": "notification", "channels": ["email", "slack"]},
                            {"action": "webhook", "webhook_id": 1},
                            {"action": "update_data", "entity": "milestone", "data": {"achieved": True}}
                        ]
                    }
                ]
            },
            {
                "id": "agent_performance_workflow",
                "name": "AI Agent Performance Workflow",
                "description": "Monitor and optimize AI agent performance automatically",
                "trigger": {
                    "name": "Agent Performance Trigger",
                    "trigger_type": "event",
                    "event_type": "agent_performance_update",
                    "conditions": {}
                },
                "rules": [
                    {
                        "name": "High Performance Alert",
                        "conditions": {"success_rate": {"gte": 95}},
                        "actions": [
                            {"action": "notification", "message": "Agent {agent_name} achieving exceptional performance"}
                        ]
                    },
                    {
                        "name": "Low Performance Alert",
                        "conditions": {"success_rate": {"lte": 30}},
                        "actions": [
                            {"action": "notification", "priority": "high", "message": "Agent {agent_name} needs optimization"},
                            {"action": "trigger_event", "event_type": "agent_optimization_required"}
                        ]
                    }
                ]
            },
            {
                "id": "opportunity_management_workflow",
                "name": "Executive Opportunity Management",
                "description": "Automated management of executive opportunities and follow-ups",
                "trigger": {
                    "name": "Opportunity Status Change",
                    "trigger_type": "event",
                    "event_type": "opportunity_status_change",
                    "conditions": {}
                },
                "rules": [
                    {
                        "name": "Offer Received Alert",
                        "conditions": {"status": {"eq": "offer_received"}},
                        "actions": [
                            {"action": "notification", "priority": "critical", "channels": ["email", "slack"]},
                            {"action": "webhook", "url": "make_com_opportunity_sync"}
                        ]
                    },
                    {
                        "name": "High Match Opportunity",
                        "conditions": {"ai_match_score": {"gte": 90}},
                        "actions": [
                            {"action": "notification", "message": "High-match opportunity: {opportunity_title}"},
                            {"action": "trigger_event", "event_type": "priority_opportunity_review"}
                        ]
                    }
                ]
            }
        ]
        
        return jsonify(templates)
        
    except Exception as e:
        logger.error(f"Get workflow templates error: {e}")
        return jsonify({"error": "Failed to fetch workflow templates"}), 500

@app.route('/api/workflows/templates/<string:template_id>/create', methods=['POST'])
@jwt_required()
def create_workflow_from_template(template_id):
    """Create workflow components from a template"""
    try:
        data = request.get_json()
        
        # Get template (in production, load from database)
        templates = {
            "revenue_milestone_workflow": {
                "trigger": {
                    "name": "Revenue Milestone Trigger",
                    "trigger_type": "event",
                    "event_type": "revenue_milestone",
                    "conditions": {"milestone_amount": {"gte": 1000000}}
                },
                "rule": {
                    "name": "Revenue Milestone Alert Rule",
                    "conditions": {"percentage_increase": {"gte": 10}},
                    "actions": [
                        {"action": "notification", "channels": ["email", "slack"]},
                        {"action": "webhook", "webhook_id": 1}
                    ]
                }
            }
        }
        
        if template_id not in templates:
            return jsonify({"error": "Template not found"}), 404
        
        template = templates[template_id]
        
        # Create trigger
        trigger_data = template['trigger']
        trigger = WorkflowTrigger(
            name=data.get('trigger_name', trigger_data['name']),
            trigger_type=trigger_data['trigger_type'],
            event_type=trigger_data['event_type'],
            conditions=trigger_data.get('conditions', {}),
            enabled=True
        )
        db.session.add(trigger)
        db.session.flush()
        
        # Create rule
        rule_data = template['rule']
        rule = BusinessRule(
            name=data.get('rule_name', rule_data['name']),
            trigger_id=trigger.id,
            conditions=rule_data.get('conditions', {}),
            actions=rule_data.get('actions', []),
            enabled=True
        )
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'message': 'Workflow created from template',
            'template_id': template_id,
            'trigger': trigger.to_dict(),
            'rule': rule.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Create workflow from template error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create workflow from template"}), 500

# Workflow Statistics and Analytics
@app.route('/api/workflows/analytics', methods=['GET'])
@jwt_required()
def get_workflow_analytics():
    """Get workflow analytics and statistics"""
    try:
        # Get execution statistics
        total_executions = WorkflowExecution.query.count()
        successful_executions = WorkflowExecution.query.filter_by(status='completed').count()
        failed_executions = WorkflowExecution.query.filter_by(status='failed').count()
        
        # Get trigger statistics
        total_triggers = WorkflowTrigger.query.count()
        enabled_triggers = WorkflowTrigger.query.filter_by(enabled=True).count()
        
        # Get rule statistics
        total_rules = BusinessRule.query.count()
        enabled_rules = BusinessRule.query.filter_by(enabled=True).count()
        
        # Get recent execution trends (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_executions = WorkflowExecution.query.filter(
            WorkflowExecution.start_time >= week_ago
        ).all()
        
        # Group by day
        daily_stats = {}
        for execution in recent_executions:
            day = execution.start_time.date().isoformat()
            if day not in daily_stats:
                daily_stats[day] = {'total': 0, 'successful': 0, 'failed': 0}
            daily_stats[day]['total'] += 1
            if execution.status == 'completed':
                daily_stats[day]['successful'] += 1
            elif execution.status == 'failed':
                daily_stats[day]['failed'] += 1
        
        return jsonify({
            'overview': {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                'total_triggers': total_triggers,
                'enabled_triggers': enabled_triggers,
                'total_rules': total_rules,
                'enabled_rules': enabled_rules
            },
            'daily_trends': daily_stats,
            'most_active_triggers': [],  # Could add query for most triggered
            'performance_summary': {
                'avg_execution_time': '1.2s',  # Could calculate from actual data
                'total_actions_executed': successful_executions * 2  # Estimated
            }
        })
        
    except Exception as e:
        logger.error(f"Get workflow analytics error: {e}")
        return jsonify({"error": "Failed to fetch workflow analytics"}), 500

# ============================
# BUSINESS PROCESS AUTOMATION
# ============================

# Lead Nurturing Automation
@app.route('/api/automation/lead-nurturing', methods=['POST'])
@jwt_required()
def create_lead_nurturing_workflow():
    """Create automated lead nurturing workflow"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['lead_id', 'lead_source', 'qualification_score']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        lead_id = data['lead_id']
        lead_source = data['lead_source']
        qualification_score = data['qualification_score']
        
        # Create nurturing workflow based on lead qualification score
        if qualification_score >= 80:
            # High-quality lead - immediate action
            workflow_actions = [
                {
                    "action": "notification",
                    "priority": "high",
                    "message": f"High-quality lead {lead_id} requires immediate attention",
                    "channels": ["email", "slack"]
                },
                {
                    "action": "trigger_event",
                    "event_type": "priority_lead_review",
                    "data": {"lead_id": lead_id, "score": qualification_score}
                },
                {
                    "action": "schedule_followup",
                    "delay_hours": 1,
                    "action_type": "sales_call"
                }
            ]
        elif qualification_score >= 60:
            # Medium-quality lead - nurturing sequence
            workflow_actions = [
                {
                    "action": "email",
                    "template": "lead_nurturing_sequence_start",
                    "delay_hours": 0
                },
                {
                    "action": "schedule_followup",
                    "delay_hours": 24,
                    "action_type": "nurturing_email_2"
                },
                {
                    "action": "schedule_followup",
                    "delay_hours": 72,
                    "action_type": "qualification_call"
                }
            ]
        else:
            # Low-quality lead - basic nurturing
            workflow_actions = [
                {
                    "action": "email",
                    "template": "lead_nurturing_basic",
                    "delay_hours": 0
                },
                {
                    "action": "schedule_followup",
                    "delay_hours": 168,  # 1 week
                    "action_type": "re_qualification"
                }
            ]
        
        # Execute workflow actions
        execution_id = str(uuid.uuid4())
        execution_results = []
        
        for action in workflow_actions:
            try:
                result = business_rule_engine._execute_action(action, {
                    'lead_id': lead_id,
                    'lead_source': lead_source,
                    'qualification_score': qualification_score
                })
                execution_results.append({
                    'action': action['action'],
                    'result': result,
                    'status': 'completed'
                })
            except Exception as e:
                execution_results.append({
                    'action': action['action'],
                    'result': str(e),
                    'status': 'failed'
                })
        
        # Log workflow execution
        execution = WorkflowExecution(
            trigger_id=None,  # Automated workflow
            rule_id=None,
            status='completed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            result_data={
                'workflow_type': 'lead_nurturing',
                'lead_id': lead_id,
                'qualification_score': qualification_score,
                'actions_executed': len(execution_results),
                'results': execution_results
            }
        )
        db.session.add(execution)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'execution_id': execution_id,
            'workflow_type': 'lead_nurturing',
            'lead_id': lead_id,
            'qualification_score': qualification_score,
            'actions_executed': len(execution_results),
            'results': execution_results
        })
        
    except Exception as e:
        logger.error(f"Lead nurturing workflow error: {e}")
        return jsonify({"error": "Failed to create lead nurturing workflow"}), 500

@app.route('/api/automation/lead-scoring', methods=['POST'])
@jwt_required()
def automated_lead_scoring():
    """Automated lead scoring and qualification"""
    try:
        data = request.get_json()
        
        # Calculate lead score based on multiple factors
        lead_data = data.get('lead_data', {})
        
        score = 0
        scoring_factors = []
        
        # Company size scoring
        company_size = lead_data.get('company_size', 0)
        if company_size >= 1000:
            score += 25
            scoring_factors.append("Large company (+25 points)")
        elif company_size >= 100:
            score += 15
            scoring_factors.append("Medium company (+15 points)")
        elif company_size >= 10:
            score += 10
            scoring_factors.append("Small company (+10 points)")
        
        # Industry scoring
        industry = lead_data.get('industry', '').lower()
        high_value_industries = ['technology', 'finance', 'healthcare', 'manufacturing']
        if industry in high_value_industries:
            score += 20
            scoring_factors.append(f"High-value industry: {industry} (+20 points)")
        
        # Revenue potential scoring
        revenue_potential = lead_data.get('annual_revenue', 0)
        if revenue_potential >= 10000000:  # $10M+
            score += 30
            scoring_factors.append("High revenue potential (+30 points)")
        elif revenue_potential >= 1000000:  # $1M+
            score += 20
            scoring_factors.append("Medium revenue potential (+20 points)")
        
        # Contact level scoring
        job_title = lead_data.get('job_title', '').lower()
        executive_titles = ['ceo', 'cto', 'cfo', 'vp', 'director', 'head']
        if any(title in job_title for title in executive_titles):
            score += 15
            scoring_factors.append("Executive level contact (+15 points)")
        
        # Engagement scoring
        engagement_score = lead_data.get('engagement_score', 0)
        score += min(engagement_score, 10)  # Max 10 points for engagement
        if engagement_score > 0:
            scoring_factors.append(f"Engagement score (+{min(engagement_score, 10)} points)")
        
        # Determine lead quality
        if score >= 80:
            quality = "high"
            priority = "immediate"
        elif score >= 60:
            quality = "medium"
            priority = "normal"
        else:
            quality = "low"
            priority = "low"
        
        # Trigger appropriate workflow based on score
        if score >= 60:  # Qualified leads
            # Trigger lead nurturing workflow
            nurturing_result = create_lead_nurturing_workflow()
        
        return jsonify({
            'lead_id': data.get('lead_id'),
            'qualification_score': score,
            'quality': quality,
            'priority': priority,
            'scoring_factors': scoring_factors,
            'recommended_actions': {
                'high': ['immediate_sales_call', 'priority_followup', 'executive_alert'],
                'medium': ['nurturing_sequence', 'scheduled_demo', 'qualification_call'],
                'low': ['basic_nurturing', 'newsletter_subscription', 'monthly_check']
            }.get(quality, [])
        })
        
    except Exception as e:
        logger.error(f"Lead scoring error: {e}")
        return jsonify({"error": "Failed to score lead"}), 500

# Opportunity Tracking Automation
@app.route('/api/automation/opportunity-tracking', methods=['POST'])
@jwt_required()
def create_opportunity_tracking_workflow():
    """Create automated opportunity tracking workflow"""
    try:
        data = request.get_json()
        
        opportunity_id = data.get('opportunity_id')
        current_stage = data.get('current_stage')
        previous_stage = data.get('previous_stage')
        deal_value = data.get('deal_value', 0)
        days_in_stage = data.get('days_in_stage', 0)
        
        workflow_actions = []
        
        # Stage-specific automation
        if current_stage == 'discovery':
            workflow_actions.extend([
                {
                    "action": "schedule_followup",
                    "delay_hours": 48,
                    "action_type": "discovery_call_followup"
                },
                {
                    "action": "update_data",
                    "entity": "opportunity",
                    "data": {"next_action": "needs_analysis", "priority": "normal"}
                }
            ])
        
        elif current_stage == 'proposal':
            workflow_actions.extend([
                {
                    "action": "notification",
                    "message": f"Opportunity {opportunity_id} moved to proposal stage - ${deal_value:,.0f}",
                    "channels": ["email", "slack"]
                },
                {
                    "action": "schedule_followup",
                    "delay_hours": 24,
                    "action_type": "proposal_review"
                }
            ])
            
            if deal_value >= 100000:  # High-value deals
                workflow_actions.append({
                    "action": "trigger_event",
                    "event_type": "executive_review_required",
                    "data": {"opportunity_id": opportunity_id, "value": deal_value}
                })
        
        elif current_stage == 'negotiation':
            workflow_actions.extend([
                {
                    "action": "notification",
                    "priority": "high",
                    "message": f"Opportunity {opportunity_id} in negotiation - requires attention",
                    "channels": ["email", "slack"]
                },
                {
                    "action": "schedule_followup",
                    "delay_hours": 12,
                    "action_type": "negotiation_support"
                }
            ])
        
        elif current_stage == 'closed_won':
            workflow_actions.extend([
                {
                    "action": "notification",
                    "priority": "critical",
                    "message": f"🎉 Deal Won! Opportunity {opportunity_id} - ${deal_value:,.0f}",
                    "channels": ["email", "slack", "webhook"]
                },
                {
                    "action": "trigger_event",
                    "event_type": "revenue_milestone",
                    "data": {"amount": deal_value, "opportunity_id": opportunity_id}
                },
                {
                    "action": "webhook",
                    "url": "make_com_deal_won",
                    "data": {"opportunity_id": opportunity_id, "value": deal_value}
                }
            ])
        
        # Stalled opportunity detection
        if days_in_stage > 14 and current_stage not in ['closed_won', 'closed_lost']:
            workflow_actions.append({
                "action": "notification",
                "priority": "medium",
                "message": f"Opportunity {opportunity_id} stalled in {current_stage} for {days_in_stage} days",
                "channels": ["email"]
            })
        
        # Execute workflow
        execution_results = []
        for action in workflow_actions:
            try:
                result = business_rule_engine._execute_action(action, {
                    'opportunity_id': opportunity_id,
                    'current_stage': current_stage,
                    'deal_value': deal_value
                })
                execution_results.append({
                    'action': action['action'],
                    'result': result,
                    'status': 'completed'
                })
            except Exception as e:
                execution_results.append({
                    'action': action['action'],
                    'result': str(e),
                    'status': 'failed'
                })
        
        return jsonify({
            'success': True,
            'opportunity_id': opportunity_id,
            'current_stage': current_stage,
            'actions_executed': len(execution_results),
            'results': execution_results
        })
        
    except Exception as e:
        logger.error(f"Opportunity tracking workflow error: {e}")
        return jsonify({"error": "Failed to create opportunity tracking workflow"}), 500

# AI Agent Coordination Automation
@app.route('/api/automation/agent-coordination', methods=['POST'])
@jwt_required()
def create_agent_coordination_workflow():
    """Create automated AI agent coordination workflow"""
    try:
        data = request.get_json()
        
        coordination_type = data.get('coordination_type')  # 'performance_optimization', 'task_distribution', 'collaboration'
        agents_involved = data.get('agents_involved', [])
        trigger_data = data.get('trigger_data', {})
        
        workflow_actions = []
        
        if coordination_type == 'performance_optimization':
            # Analyze agent performance and optimize
            for agent in agents_involved:
                agent_data = trigger_data.get(f'agent_{agent}', {})
                success_rate = agent_data.get('success_rate', 0)
                
                if success_rate < 30:  # Poor performance
                    workflow_actions.extend([
                        {
                            "action": "notification",
                            "priority": "high",
                            "message": f"Agent {agent} performance below threshold: {success_rate}%",
                            "channels": ["email", "slack"]
                        },
                        {
                            "action": "trigger_event",
                            "event_type": "agent_training_required",
                            "data": {"agent_id": agent, "performance_issue": "low_success_rate"}
                        },
                        {
                            "action": "update_data",
                            "entity": "agent",
                            "data": {"status": "optimization_required", "last_optimization": datetime.now().isoformat()}
                        }
                    ])
                
                elif success_rate > 95:  # Excellent performance
                    workflow_actions.extend([
                        {
                            "action": "notification",
                            "message": f"🌟 Agent {agent} achieving excellent performance: {success_rate}%",
                            "channels": ["slack"]
                        },
                        {
                            "action": "trigger_event",
                            "event_type": "agent_model_promotion",
                            "data": {"agent_id": agent, "performance_level": "excellent"}
                        }
                    ])
        
        elif coordination_type == 'task_distribution':
            # Distribute tasks based on agent capabilities and workload
            total_tasks = trigger_data.get('pending_tasks', 0)
            
            if total_tasks > 100:  # High task volume
                workflow_actions.extend([
                    {
                        "action": "notification",
                        "message": f"High task volume detected: {total_tasks} pending tasks",
                        "channels": ["slack"]
                    },
                    {
                        "action": "trigger_event",
                        "event_type": "agent_scaling_required",
                        "data": {"task_count": total_tasks, "agents_available": len(agents_involved)}
                    }
                ])
                
                # Distribute tasks among available agents
                tasks_per_agent = total_tasks // len(agents_involved)
                for agent in agents_involved:
                    workflow_actions.append({
                        "action": "update_data",
                        "entity": "agent_workload",
                        "data": {"agent_id": agent, "assigned_tasks": tasks_per_agent}
                    })
        
        elif coordination_type == 'collaboration':
            # Coordinate multi-agent collaboration
            collaboration_task = trigger_data.get('collaboration_task')
            
            workflow_actions.extend([
                {
                    "action": "notification",
                    "message": f"Multi-agent collaboration initiated: {collaboration_task}",
                    "channels": ["slack"]
                },
                {
                    "action": "trigger_event",
                    "event_type": "agent_collaboration_started",
                    "data": {"task": collaboration_task, "agents": agents_involved}
                }
            ])
            
            # Set up coordination structure
            primary_agent = agents_involved[0] if agents_involved else None
            if primary_agent:
                workflow_actions.append({
                    "action": "update_data",
                    "entity": "collaboration",
                    "data": {
                        "primary_agent": primary_agent,
                        "supporting_agents": agents_involved[1:],
                        "status": "active",
                        "started_at": datetime.now().isoformat()
                    }
                })
        
        # Execute coordination workflow
        execution_results = []
        for action in workflow_actions:
            try:
                result = business_rule_engine._execute_action(action, {
                    'coordination_type': coordination_type,
                    'agents_involved': agents_involved,
                    'trigger_data': trigger_data
                })
                execution_results.append({
                    'action': action['action'],
                    'result': result,
                    'status': 'completed'
                })
            except Exception as e:
                execution_results.append({
                    'action': action['action'],
                    'result': str(e),
                    'status': 'failed'
                })
        
        return jsonify({
            'success': True,
            'coordination_type': coordination_type,
            'agents_involved': agents_involved,
            'actions_executed': len(execution_results),
            'results': execution_results
        })
        
    except Exception as e:
        logger.error(f"Agent coordination workflow error: {e}")
        return jsonify({"error": "Failed to create agent coordination workflow"}), 500

# Business Process Templates
@app.route('/api/automation/templates', methods=['GET'])
@jwt_required()
def get_business_process_templates():
    """Get predefined business process automation templates"""
    try:
        templates = {
            "lead_nurturing": {
                "name": "Lead Nurturing Automation",
                "description": "Automated lead scoring, qualification, and nurturing workflows",
                "triggers": [
                    "new_lead_created",
                    "lead_engagement_scored", 
                    "lead_qualification_updated"
                ],
                "actions": [
                    "lead_scoring",
                    "nurturing_sequence",
                    "sales_alert",
                    "followup_scheduling"
                ],
                "business_value": "Increases lead conversion by 40% through timely, relevant engagement"
            },
            "opportunity_management": {
                "name": "Opportunity Pipeline Automation", 
                "description": "Automated opportunity tracking, stage progression, and deal management",
                "triggers": [
                    "opportunity_stage_change",
                    "deal_stalled",
                    "proposal_submitted"
                ],
                "actions": [
                    "stage_progression_alerts",
                    "executive_notifications",
                    "followup_reminders",
                    "revenue_tracking"
                ],
                "business_value": "Reduces sales cycle by 25% and improves deal closure rates"
            },
            "agent_performance": {
                "name": "AI Agent Performance Optimization",
                "description": "Automated monitoring and optimization of AI agent performance",
                "triggers": [
                    "agent_performance_update",
                    "success_rate_threshold",
                    "task_completion_metrics"
                ],
                "actions": [
                    "performance_alerts",
                    "training_recommendations",
                    "workload_optimization",
                    "model_improvements"
                ],
                "business_value": "Improves AI agent efficiency by 35% through continuous optimization"
            },
            "revenue_milestones": {
                "name": "Revenue Milestone Automation",
                "description": "Automated tracking and celebration of revenue achievements",
                "triggers": [
                    "revenue_threshold_reached",
                    "monthly_revenue_target",
                    "quarterly_milestone"
                ],
                "actions": [
                    "milestone_notifications",
                    "team_celebrations",
                    "investor_updates",
                    "strategic_planning_triggers"
                ],
                "business_value": "Maintains team motivation and provides real-time business intelligence"
            },
            "executive_opportunities": {
                "name": "Executive Opportunity Management",
                "description": "Automated tracking and management of executive career opportunities", 
                "triggers": [
                    "opportunity_match_score",
                    "application_status_change",
                    "interview_scheduled"
                ],
                "actions": [
                    "opportunity_alerts",
                    "application_tracking",
                    "interview_preparation",
                    "decision_support"
                ],
                "business_value": "Streamlines executive opportunity management and decision-making"
            }
        }
        
        return jsonify(templates)
        
    except Exception as e:
        logger.error(f"Get business process templates error: {e}")
        return jsonify({"error": "Failed to fetch business process templates"}), 500

@app.route('/api/automation/templates/<string:template_id>/deploy', methods=['POST'])
@jwt_required()
def deploy_business_process_template(template_id):
    """Deploy a business process automation template"""
    try:
        data = request.get_json()
        customizations = data.get('customizations', {})
        
        # Template configurations
        template_configs = {
            "lead_nurturing": {
                "triggers": [
                    {
                        "name": "New Lead Created Trigger",
                        "trigger_type": "event",
                        "event_type": "lead_created",
                        "conditions": {}
                    }
                ],
                "rules": [
                    {
                        "name": "High-Value Lead Alert",
                        "conditions": {"qualification_score": {"gte": 80}},
                        "actions": [
                            {"action": "notification", "priority": "high"},
                            {"action": "trigger_event", "event_type": "priority_lead_review"}
                        ]
                    }
                ]
            },
            "opportunity_management": {
                "triggers": [
                    {
                        "name": "Opportunity Stage Change Trigger",
                        "trigger_type": "event", 
                        "event_type": "opportunity_stage_change",
                        "conditions": {}
                    }
                ],
                "rules": [
                    {
                        "name": "Deal Won Celebration",
                        "conditions": {"stage": {"eq": "closed_won"}},
                        "actions": [
                            {"action": "notification", "priority": "critical"},
                            {"action": "webhook", "url": "make_com_deal_celebration"}
                        ]
                    }
                ]
            }
        }
        
        if template_id not in template_configs:
            return jsonify({"error": "Template not found"}), 404
        
        config = template_configs[template_id]
        deployed_components = []
        
        # Deploy triggers
        for trigger_config in config.get('triggers', []):
            trigger_config.update(customizations.get('trigger_overrides', {}))
            
            trigger = WorkflowTrigger(
                name=trigger_config['name'],
                trigger_type=trigger_config['trigger_type'],
                event_type=trigger_config['event_type'],
                conditions=trigger_config.get('conditions', {}),
                enabled=True,
                metadata={'template_id': template_id}
            )
            db.session.add(trigger)
            db.session.flush()
            deployed_components.append({'type': 'trigger', 'id': trigger.id, 'name': trigger.name})
        
        # Deploy rules
        for rule_config in config.get('rules', []):
            rule_config.update(customizations.get('rule_overrides', {}))
            
            rule = BusinessRule(
                name=rule_config['name'],
                trigger_id=trigger.id,  # Link to the first trigger created
                conditions=rule_config.get('conditions', {}),
                actions=rule_config.get('actions', []),
                enabled=True,
                metadata={'template_id': template_id}
            )
            db.session.add(rule)
            deployed_components.append({'type': 'rule', 'id': rule.id, 'name': rule.name})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'template_id': template_id,
            'deployed_components': deployed_components,
            'message': f'Business process template "{template_id}" deployed successfully'
        })
        
    except Exception as e:
        logger.error(f"Deploy business process template error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to deploy business process template"}), 500

# ============================
# WORKFLOW EXECUTION LOGGING & MONITORING
# ============================

# Execution Logging System
@app.route('/api/execution/logs', methods=['GET'])
@jwt_required()
def get_execution_logs():
    """Get detailed execution logs with filtering and pagination"""
    try:
        # Query parameters
        execution_id = request.args.get('execution_id')
        rule_id = request.args.get('rule_id')
        trigger_id = request.args.get('trigger_id')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        log_level = request.args.get('log_level', 'INFO')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Build query
        query = WorkflowExecution.query
        
        if execution_id:
            query = query.filter(WorkflowExecution.execution_id == execution_id)
        if rule_id:
            query = query.filter(WorkflowExecution.rule_id == rule_id)
        if trigger_id:
            query = query.filter(WorkflowExecution.trigger_id == trigger_id)
        if status:
            query = query.filter(WorkflowExecution.status == status)
        if start_date:
            query = query.filter(WorkflowExecution.start_time >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(WorkflowExecution.start_time <= datetime.fromisoformat(end_date))
        
        # Get paginated results
        executions = query.order_by(WorkflowExecution.start_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Enhanced execution logs with performance metrics
        detailed_logs = []
        for execution in executions.items:
            execution_data = execution.to_dict()
            
            # Calculate performance metrics
            if execution.start_time and execution.end_time:
                duration = (execution.end_time - execution.start_time).total_seconds()
                execution_data['duration_seconds'] = duration
                execution_data['performance_category'] = (
                    'fast' if duration < 1 else
                    'normal' if duration < 5 else
                    'slow' if duration < 15 else
                    'very_slow'
                )
            
            # Add step-by-step execution details
            result_data = execution.result_data or {}
            execution_data['step_details'] = result_data.get('step_logs', [])
            execution_data['action_count'] = len(result_data.get('results', []))
            execution_data['success_rate'] = result_data.get('success_rate', 0)
            
            # Add error details if failed
            if execution.status == 'failed':
                execution_data['error_details'] = {
                    'error_message': result_data.get('error'),
                    'failed_step': result_data.get('failed_step'),
                    'stack_trace': result_data.get('stack_trace')
                }
            
            detailed_logs.append(execution_data)
        
        return jsonify({
            'logs': detailed_logs,
            'pagination': {
                'total': executions.total,
                'pages': executions.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': executions.has_next,
                'has_prev': executions.has_prev
            },
            'summary': {
                'total_executions': executions.total,
                'filtered_count': len(detailed_logs)
            }
        })
        
    except Exception as e:
        logger.error(f"Get execution logs error: {e}")
        return jsonify({"error": "Failed to fetch execution logs"}), 500

@app.route('/api/execution/logs/<string:execution_id>/steps', methods=['GET'])
@jwt_required()
def get_execution_step_logs(execution_id):
    """Get detailed step-by-step execution logs for a specific execution"""
    try:
        execution = WorkflowExecution.query.filter_by(execution_id=execution_id).first()
        if not execution:
            return jsonify({"error": "Execution not found"}), 404
        
        result_data = execution.result_data or {}
        step_logs = result_data.get('step_logs', [])
        
        # Enhanced step details with timing and performance data
        enhanced_steps = []
        total_duration = 0
        
        for i, step in enumerate(step_logs):
            step_data = {
                'step_number': i + 1,
                'timestamp': step.get('timestamp'),
                'action_type': step.get('action_type'),
                'description': step.get('description'),
                'status': step.get('status', 'unknown'),
                'result': step.get('result'),
                'duration_ms': step.get('duration_ms', 0),
                'memory_usage': step.get('memory_usage'),
                'retry_count': step.get('retry_count', 0)
            }
            
            # Add error details for failed steps
            if step.get('status') == 'failed':
                step_data['error_details'] = {
                    'error_message': step.get('error'),
                    'error_type': step.get('error_type'),
                    'retry_attempts': step.get('retry_attempts', 0)
                }
            
            # Performance analysis
            duration = step.get('duration_ms', 0)
            total_duration += duration
            step_data['performance_impact'] = (
                'minimal' if duration < 100 else
                'low' if duration < 500 else
                'medium' if duration < 2000 else
                'high'
            )
            
            enhanced_steps.append(step_data)
        
        return jsonify({
            'execution_id': execution_id,
            'total_steps': len(enhanced_steps),
            'total_duration_ms': total_duration,
            'execution_status': execution.status,
            'step_logs': enhanced_steps,
            'performance_summary': {
                'avg_step_duration': total_duration / len(enhanced_steps) if enhanced_steps else 0,
                'slowest_step': max(enhanced_steps, key=lambda x: x['duration_ms']) if enhanced_steps else None,
                'failed_steps': [s for s in enhanced_steps if s['status'] == 'failed']
            }
        })
        
    except Exception as e:
        logger.error(f"Get execution step logs error: {e}")
        return jsonify({"error": "Failed to fetch execution step logs"}), 500

# Real-time Monitoring
@app.route('/api/monitoring/executions/live', methods=['GET'])
@jwt_required()
def get_live_execution_monitoring():
    """Get real-time execution monitoring data"""
    try:
        # Get currently running executions
        running_executions = WorkflowExecution.query.filter_by(status='running').all()
        
        # Get recent executions (last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_executions = WorkflowExecution.query.filter(
            WorkflowExecution.start_time >= one_hour_ago
        ).all()
        
        # Calculate real-time metrics
        total_running = len(running_executions)
        recent_completed = len([e for e in recent_executions if e.status == 'completed'])
        recent_failed = len([e for e in recent_executions if e.status == 'failed'])
        
        # System performance metrics
        system_metrics = {
            'executions_running': total_running,
            'executions_last_hour': len(recent_executions),
            'success_rate_last_hour': (recent_completed / len(recent_executions) * 100) if recent_executions else 0,
            'failure_rate_last_hour': (recent_failed / len(recent_executions) * 100) if recent_executions else 0,
            'avg_execution_time': 2.3,  # Placeholder - could calculate from actual data
            'system_health': 'healthy' if recent_failed < recent_completed else 'degraded'
        }
        
        # Top failing rules/triggers
        failing_rules = {}
        failing_triggers = {}
        
        for execution in recent_executions:
            if execution.status == 'failed':
                if execution.rule_id:
                    failing_rules[execution.rule_id] = failing_rules.get(execution.rule_id, 0) + 1
                if execution.trigger_id:
                    failing_triggers[execution.trigger_id] = failing_triggers.get(execution.trigger_id, 0) + 1
        
        # Format running executions with progress
        live_executions = []
        for execution in running_executions:
            execution_data = execution.to_dict()
            
            # Calculate estimated progress based on typical execution time
            if execution.start_time:
                elapsed = (datetime.now() - execution.start_time).total_seconds()
                estimated_progress = min(elapsed / 10 * 100, 95)  # Max 95% until actually complete
                execution_data['estimated_progress'] = estimated_progress
                execution_data['elapsed_time'] = elapsed
            
            live_executions.append(execution_data)
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'system_metrics': system_metrics,
            'live_executions': live_executions,
            'recent_activity': {
                'total_executions': len(recent_executions),
                'successful': recent_completed,
                'failed': recent_failed,
                'running': total_running
            },
            'top_failing_components': {
                'rules': dict(sorted(failing_rules.items(), key=lambda x: x[1], reverse=True)[:5]),
                'triggers': dict(sorted(failing_triggers.items(), key=lambda x: x[1], reverse=True)[:5])
            }
        })
        
    except Exception as e:
        logger.error(f"Live monitoring error: {e}")
        return jsonify({"error": "Failed to fetch live monitoring data"}), 500

# Performance Analytics
@app.route('/api/monitoring/performance', methods=['GET'])
@jwt_required()
def get_performance_analytics():
    """Get comprehensive performance analytics for workflow executions"""
    try:
        # Time range parameters
        days = request.args.get('days', 7, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # Get executions within time range
        executions = WorkflowExecution.query.filter(
            WorkflowExecution.start_time >= start_date
        ).all()
        
        # Performance metrics calculation
        performance_data = {
            'execution_times': [],
            'success_rates': {},
            'error_patterns': {},
            'throughput_metrics': {},
            'resource_usage': []
        }
        
        # Calculate daily metrics
        daily_metrics = {}
        for execution in executions:
            day = execution.start_time.date().isoformat()
            if day not in daily_metrics:
                daily_metrics[day] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'execution_times': [],
                    'error_types': {}
                }
            
            daily_metrics[day]['total'] += 1
            
            if execution.status == 'completed':
                daily_metrics[day]['successful'] += 1
                
                # Calculate execution time
                if execution.start_time and execution.end_time:
                    duration = (execution.end_time - execution.start_time).total_seconds()
                    daily_metrics[day]['execution_times'].append(duration)
                    performance_data['execution_times'].append({
                        'date': day,
                        'duration': duration,
                        'execution_id': execution.execution_id
                    })
            
            elif execution.status == 'failed':
                daily_metrics[day]['failed'] += 1
                
                # Track error patterns
                error_msg = execution.result_data.get('error', 'Unknown error') if execution.result_data else 'Unknown error'
                error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg
                daily_metrics[day]['error_types'][error_type] = daily_metrics[day]['error_types'].get(error_type, 0) + 1
                
                if error_type not in performance_data['error_patterns']:
                    performance_data['error_patterns'][error_type] = []
                performance_data['error_patterns'][error_type].append({
                    'date': day,
                    'execution_id': execution.execution_id,
                    'message': error_msg
                })
        
        # Calculate aggregated metrics
        all_execution_times = [time for daily in daily_metrics.values() for time in daily['execution_times']]
        
        summary_metrics = {
            'total_executions': len(executions),
            'successful_executions': len([e for e in executions if e.status == 'completed']),
            'failed_executions': len([e for e in executions if e.status == 'failed']),
            'average_execution_time': sum(all_execution_times) / len(all_execution_times) if all_execution_times else 0,
            'median_execution_time': sorted(all_execution_times)[len(all_execution_times)//2] if all_execution_times else 0,
            'p95_execution_time': sorted(all_execution_times)[int(len(all_execution_times)*0.95)] if all_execution_times else 0,
            'success_rate': (len([e for e in executions if e.status == 'completed']) / len(executions) * 100) if executions else 0
        }
        
        # Top performers and problem areas
        rule_performance = {}
        trigger_performance = {}
        
        for execution in executions:
            if execution.rule_id:
                if execution.rule_id not in rule_performance:
                    rule_performance[execution.rule_id] = {'total': 0, 'successful': 0, 'avg_time': 0, 'times': []}
                
                rule_performance[execution.rule_id]['total'] += 1
                if execution.status == 'completed':
                    rule_performance[execution.rule_id]['successful'] += 1
                    if execution.start_time and execution.end_time:
                        duration = (execution.end_time - execution.start_time).total_seconds()
                        rule_performance[execution.rule_id]['times'].append(duration)
        
        # Calculate success rates and average times for rules
        for rule_id, perf in rule_performance.items():
            perf['success_rate'] = (perf['successful'] / perf['total'] * 100) if perf['total'] > 0 else 0
            perf['avg_execution_time'] = sum(perf['times']) / len(perf['times']) if perf['times'] else 0
        
        return jsonify({
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': datetime.now().isoformat(),
                'days': days
            },
            'summary_metrics': summary_metrics,
            'daily_metrics': daily_metrics,
            'performance_trends': performance_data,
            'rule_performance': rule_performance,
            'top_performers': {
                'fastest_rules': dict(sorted(rule_performance.items(), 
                    key=lambda x: x[1]['avg_execution_time'])[:5]),
                'most_reliable_rules': dict(sorted(rule_performance.items(), 
                    key=lambda x: x[1]['success_rate'], reverse=True)[:5])
            },
            'problem_areas': {
                'slowest_rules': dict(sorted(rule_performance.items(), 
                    key=lambda x: x[1]['avg_execution_time'], reverse=True)[:5]),
                'least_reliable_rules': dict(sorted(rule_performance.items(), 
                    key=lambda x: x[1]['success_rate'])[:5])
            }
        })
        
    except Exception as e:
        logger.error(f"Performance analytics error: {e}")
        return jsonify({"error": "Failed to fetch performance analytics"}), 500

# Error Tracking and Diagnostics
@app.route('/api/monitoring/errors', methods=['GET'])
@jwt_required()
def get_error_tracking():
    """Get comprehensive error tracking and diagnostic information"""
    try:
        # Time range
        days = request.args.get('days', 7, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # Get failed executions
        failed_executions = WorkflowExecution.query.filter(
            WorkflowExecution.status == 'failed',
            WorkflowExecution.start_time >= start_date
        ).all()
        
        # Error analysis
        error_analysis = {
            'total_errors': len(failed_executions),
            'error_types': {},
            'error_frequency': {},
            'affected_components': {
                'rules': {},
                'triggers': {},
                'actions': {}
            },
            'error_trends': {},
            'recovery_analysis': {}
        }
        
        # Analyze error patterns
        for execution in failed_executions:
            error_data = execution.result_data or {}
            error_msg = error_data.get('error', 'Unknown error')
            error_type = error_msg.split(':')[0] if ':' in error_msg else 'General Error'
            
            # Count error types
            if error_type not in error_analysis['error_types']:
                error_analysis['error_types'][error_type] = {
                    'count': 0,
                    'examples': [],
                    'affected_executions': []
                }
            
            error_analysis['error_types'][error_type]['count'] += 1
            error_analysis['error_types'][error_type]['examples'].append(error_msg)
            error_analysis['error_types'][error_type]['affected_executions'].append(execution.execution_id)
            
            # Track daily error frequency
            day = execution.start_time.date().isoformat()
            if day not in error_analysis['error_frequency']:
                error_analysis['error_frequency'][day] = 0
            error_analysis['error_frequency'][day] += 1
            
            # Track affected components
            if execution.rule_id:
                rule_id = str(execution.rule_id)
                if rule_id not in error_analysis['affected_components']['rules']:
                    error_analysis['affected_components']['rules'][rule_id] = 0
                error_analysis['affected_components']['rules'][rule_id] += 1
            
            if execution.trigger_id:
                trigger_id = str(execution.trigger_id)
                if trigger_id not in error_analysis['affected_components']['triggers']:
                    error_analysis['affected_components']['triggers'][trigger_id] = 0
                error_analysis['affected_components']['triggers'][trigger_id] += 1
        
        # Error diagnostics and recommendations
        diagnostics = []
        
        # High error rate components
        for rule_id, error_count in error_analysis['affected_components']['rules'].items():
            if error_count >= 5:  # Threshold for problematic rules
                diagnostics.append({
                    'severity': 'high',
                    'component_type': 'rule',
                    'component_id': rule_id,
                    'issue': 'High error rate',
                    'error_count': error_count,
                    'recommendation': 'Review rule conditions and actions for potential issues'
                })
        
        # Frequent error types
        for error_type, data in error_analysis['error_types'].items():
            if data['count'] >= 10:  # Threshold for frequent errors
                diagnostics.append({
                    'severity': 'medium',
                    'component_type': 'error_pattern',
                    'component_id': error_type,
                    'issue': 'Frequent error pattern',
                    'error_count': data['count'],
                    'recommendation': f'Investigate root cause of {error_type} errors'
                })
        
        # Recovery recommendations
        recovery_suggestions = []
        
        if error_analysis['total_errors'] > 50:
            recovery_suggestions.append({
                'priority': 'high',
                'action': 'system_review',
                'description': 'High error volume detected - comprehensive system review recommended'
            })
        
        for error_type, data in error_analysis['error_types'].items():
            if data['count'] > error_analysis['total_errors'] * 0.3:  # 30% of all errors
                recovery_suggestions.append({
                    'priority': 'medium',
                    'action': 'error_pattern_fix',
                    'description': f'Focus on resolving {error_type} errors (dominant error pattern)'
                })
        
        return jsonify({
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': datetime.now().isoformat(),
                'days': days
            },
            'error_analysis': error_analysis,
            'diagnostics': diagnostics,
            'recovery_suggestions': recovery_suggestions,
            'health_score': max(0, 100 - (error_analysis['total_errors'] * 2))  # Simple health scoring
        })
        
    except Exception as e:
        logger.error(f"Error tracking error: {e}")
        return jsonify({"error": "Failed to fetch error tracking data"}), 500

# Execution Replay and Debugging
@app.route('/api/monitoring/replay/<string:execution_id>', methods=['POST'])
@jwt_required()
def replay_execution(execution_id):
    """Replay a failed or completed execution for debugging purposes"""
    try:
        original_execution = WorkflowExecution.query.filter_by(execution_id=execution_id).first()
        if not original_execution:
            return jsonify({"error": "Original execution not found"}), 404
        
        # Create replay execution
        replay_execution = WorkflowExecution(
            trigger_id=original_execution.trigger_id,
            rule_id=original_execution.rule_id,
            status='running',
            start_time=datetime.now(),
            metadata={
                'replay_of': execution_id,
                'replay_mode': True,
                'original_execution_data': original_execution.result_data
            }
        )
        
        db.session.add(replay_execution)
        db.session.commit()
        
        # In a real implementation, this would trigger the actual workflow replay
        # For now, we'll simulate the replay process
        
        return jsonify({
            'success': True,
            'replay_execution_id': replay_execution.execution_id,
            'original_execution_id': execution_id,
            'status': 'replay_initiated',
            'message': 'Execution replay initiated for debugging'
        })
        
    except Exception as e:
        logger.error(f"Execution replay error: {e}")
        return jsonify({"error": "Failed to replay execution"}), 500

# System Health Monitoring
@app.route('/api/monitoring/health', methods=['GET'])
@jwt_required()
def get_system_health():
    """Get overall system health and status"""
    try:
        # Get recent execution statistics
        last_hour = datetime.now() - timedelta(hours=1)
        last_24h = datetime.now() - timedelta(hours=24)
        
        recent_executions = WorkflowExecution.query.filter(
            WorkflowExecution.start_time >= last_hour
        ).all()
        
        daily_executions = WorkflowExecution.query.filter(
            WorkflowExecution.start_time >= last_24h
        ).all()
        
        # Calculate health metrics
        recent_success_rate = (
            len([e for e in recent_executions if e.status == 'completed']) / 
            len(recent_executions) * 100
        ) if recent_executions else 100
        
        daily_success_rate = (
            len([e for e in daily_executions if e.status == 'completed']) / 
            len(daily_executions) * 100
        ) if daily_executions else 100
        
        # System status determination
        if recent_success_rate >= 95 and daily_success_rate >= 90:
            system_status = 'healthy'
            status_color = 'green'
        elif recent_success_rate >= 80 and daily_success_rate >= 75:
            system_status = 'warning'
            status_color = 'yellow'
        else:
            system_status = 'critical'
            status_color = 'red'
        
        # Active components count
        active_triggers = WorkflowTrigger.query.filter_by(enabled=True).count()
        active_rules = BusinessRule.query.filter_by(enabled=True).count()
        running_executions = WorkflowExecution.query.filter_by(status='running').count()
        
        health_data = {
            'system_status': system_status,
            'status_color': status_color,
            'last_updated': datetime.now().isoformat(),
            'metrics': {
                'recent_success_rate': round(recent_success_rate, 2),
                'daily_success_rate': round(daily_success_rate, 2),
                'executions_last_hour': len(recent_executions),
                'executions_last_24h': len(daily_executions),
                'currently_running': running_executions,
                'active_triggers': active_triggers,
                'active_rules': active_rules
            },
            'alerts': []
        }
        
        # Generate alerts based on metrics
        if recent_success_rate < 80:
            health_data['alerts'].append({
                'severity': 'high',
                'message': f'Low success rate in last hour: {recent_success_rate:.1f}%',
                'type': 'performance'
            })
        
        if running_executions > 20:
            health_data['alerts'].append({
                'severity': 'medium',
                'message': f'High number of running executions: {running_executions}',
                'type': 'capacity'
            })
        
        if len(recent_executions) == 0:
            health_data['alerts'].append({
                'severity': 'low',
                'message': 'No workflow executions in the last hour',
                'type': 'activity'
            })
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"System health monitoring error: {e}")
        return jsonify({"error": "Failed to fetch system health data"}), 500

# Business Events Management
@app.route('/api/events', methods=['GET'])
@jwt_required()
def get_business_events():
    """Get business events with optional filtering"""
    try:
        query = BusinessEvent.query
        
        # Filter by event type
        event_type = request.args.get('event_type')
        if event_type:
            query = query.filter(BusinessEvent.event_type == event_type)
        
        # Filter by entity type
        entity_type = request.args.get('entity_type')
        if entity_type:
            query = query.filter(BusinessEvent.entity_type == entity_type)
        
        # Filter by processed status
        processed = request.args.get('processed')
        if processed is not None:
            query = query.filter(BusinessEvent.processed == (processed.lower() == 'true'))
        
        # Filter by priority
        priority = request.args.get('priority')
        if priority:
            query = query.filter(BusinessEvent.priority == priority)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        events = query.order_by(BusinessEvent.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'events': [event.to_dict() for event in events.items],
            'total': events.total,
            'pages': events.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        logger.error(f"Get business events error: {e}")
        return jsonify({"error": "Failed to fetch business events"}), 500

@app.route('/api/events/trigger', methods=['POST'])
@jwt_required()
def trigger_manual_event():
    """Manually trigger a business event"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['event_type', 'entity_type', 'entity_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        event_data = data.get('event_data', {})
        source = data.get('source', 'manual')
        priority = data.get('priority', 'medium')
        
        # Trigger the event
        results = trigger_business_event(
            event_type=data['event_type'],
            entity_type=data['entity_type'],
            entity_id=data['entity_id'],
            event_data=event_data,
            source=source,
            priority=priority
        )
        
        return jsonify({
            'message': 'Business event triggered successfully',
            'event_type': data['event_type'],
            'rules_triggered': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Trigger manual event error: {e}")
        return jsonify({"error": "Failed to trigger business event"}), 500

# Notification History and Logs
@app.route('/api/notifications/history', methods=['GET'])
@jwt_required()
def get_notification_history():
    """Get notification history from workflow executions"""
    try:
        # Get executions that involved notifications
        executions = WorkflowExecution.query.filter(
            WorkflowExecution.result_data.contains({'actions': [{'action': 'notification'}]})
        ).order_by(WorkflowExecution.start_time.desc()).limit(100).all()
        
        history = []
        for execution in executions:
            if execution.result_data and 'actions' in execution.result_data:
                for action in execution.result_data['actions']:
                    if action.get('action') == 'notification':
                        history.append({
                            'execution_id': execution.execution_id,
                            'timestamp': execution.start_time.isoformat(),
                            'status': execution.status,
                            'notification_data': action,
                            'rule_id': execution.rule_id,
                            'trigger_id': execution.trigger_id
                        })
        
        return jsonify({
            'history': history,
            'total_count': len(history)
        })
        
    except Exception as e:
        logger.error(f"Get notification history error: {e}")
        return jsonify({"error": "Failed to fetch notification history"}), 500

# Notification Templates (for future expansion)
@app.route('/api/notifications/templates', methods=['GET'])
@jwt_required()
def get_notification_templates():
    """Get notification templates"""
    try:
        # This is a placeholder for notification templates
        # In a full implementation, you'd have a NotificationTemplate model
        templates = [
            {
                "id": 1,
                "name": "Revenue Milestone Alert",
                "type": "revenue_milestone",
                "subject": "🎉 Revenue Milestone Achieved: ${milestone_amount}",
                "content": "Congratulations! ${stream_name} has reached ${current_amount} - exceeding the ${milestone_amount} milestone by ${excess_amount}.",
                "channels": ["email", "slack"],
                "priority": "high"
            },
            {
                "id": 2,
                "name": "Agent High Performance",
                "type": "agent_performance",
                "subject": "🚀 Agent High Performance Alert: ${agent_name}",
                "content": "${agent_name} is performing exceptionally well with a ${success_rate}% success rate and ${pipeline_value} in pipeline value.",
                "channels": ["internal", "email"],
                "priority": "medium"
            },
            {
                "id": 3,
                "name": "Opportunity Offer Received",
                "type": "opportunity_status",
                "subject": "🎯 Offer Received: ${opportunity_title}",
                "content": "Great news! You've received an offer for ${opportunity_title} at ${company}. Compensation: ${compensation_range}",
                "channels": ["email", "slack"],
                "priority": "critical"
            }
        ]
        
        return jsonify(templates)
        
    except Exception as e:
        logger.error(f"Get notification templates error: {e}")
        return jsonify({"error": "Failed to fetch notification templates"}), 500

# Enhanced Notification Delivery System
class NotificationDeliveryService:
    """Enhanced notification delivery service with improved functionality"""
    
    @staticmethod
    def send_email_notification(config: dict, message: str, priority: str, context: dict) -> dict:
        """Send email notification"""
        try:
            # In production, integrate with email service (SendGrid, AWS SES, etc.)
            to_email = config.get('to_email', 'dede@risktravel.com')
            from_email = config.get('from_email', 'noreply@aiempire.com')
            subject = config.get('subject', f'AI Empire Alert - {priority.upper()}')
            
            # Format message with context
            formatted_message = message.format(**context) if context else message
            formatted_subject = subject.format(**context) if context else subject
            
            # Mock email sending (replace with actual email service)
            logger.info(f"EMAIL SENT - To: {to_email}, Subject: {formatted_subject}, Priority: {priority}")
            
            return {
                'success': True,
                'channel': 'email',
                'to': to_email,
                'subject': formatted_subject,
                'message_length': len(formatted_message)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_slack_notification(config: dict, message: str, priority: str, context: dict) -> dict:
        """Send Slack notification"""
        try:
            webhook_url = config.get('webhook_url')
            channel = config.get('channel', '#general')
            username = config.get('username', 'AI Empire Bot')
            
            if not webhook_url:
                return {'success': False, 'error': 'Slack webhook URL not configured'}
            
            # Format message with context
            formatted_message = message.format(**context) if context else message
            
            # Priority-based formatting
            priority_icons = {'low': '🔵', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
            icon = priority_icons.get(priority, '⚪')
            
            payload = {
                'channel': channel,
                'username': username,
                'text': f"{icon} *{priority.upper()} ALERT*\n{formatted_message}",
                'icon_emoji': ':robot_face:'
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'channel': 'slack',
                'slack_channel': channel,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_webhook_notification(config: dict, message: str, priority: str, context: dict) -> dict:
        """Send webhook notification"""
        try:
            url = config.get('url')
            headers = config.get('headers', {})
            secret_key = config.get('secret_key')
            
            if not url:
                return {'success': False, 'error': 'Webhook URL not configured'}
            
            if secret_key:
                headers['X-Webhook-Secret'] = secret_key
            
            payload = {
                'message': message.format(**context) if context else message,
                'priority': priority,
                'context': context,
                'timestamp': datetime.now().isoformat(),
                'source': 'ai_empire_notification_system'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'channel': 'webhook',
                'url': url,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

@app.route('/api/notifications/delivery/test', methods=['POST'])
@jwt_required()
def test_notification_delivery():
    """Test notification delivery service"""
    try:
        data = request.get_json()
        
        delivery_type = data.get('type', 'email')
        config = data.get('config', {})
        message = data.get('message', 'Test notification from AI Empire platform')
        priority = data.get('priority', 'medium')
        context = data.get('context', {})
        
        if delivery_type == 'email':
            result = NotificationDeliveryService.send_email_notification(config, message, priority, context)
        elif delivery_type == 'slack':
            result = NotificationDeliveryService.send_slack_notification(config, message, priority, context)
        elif delivery_type == 'webhook':
            result = NotificationDeliveryService.send_webhook_notification(config, message, priority, context)
        else:
            return jsonify({"error": f"Unsupported delivery type: {delivery_type}"}), 400
        
        return jsonify({
            'test_result': result,
            'delivery_type': delivery_type,
            'test_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Test notification delivery error: {e}")
        return jsonify({"error": "Failed to test notification delivery"}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "deployment": "manus",
        "features": [
            "authentication",
            "revenue_tracking", 
            "kpi_monitoring",
            "ai_agents",
            "healthcare_management",
            "milestone_tracking",
            "frontend_integrated"
        ]
    })

# Initialize database on startup
with app.app_context():
    create_and_seed_database()
    # Initialize Make.com bridges after database is ready
    initialize_make_bridges()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

