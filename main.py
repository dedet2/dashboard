"""
Dr. Dédé's RiskTravel Intelligence Platform - Manus Deployment
Optimized for deployment at https://hfqukiyd.manus.space/dashboard
"""

from flask import Flask, jsonify, request, render_template_string, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
import logging
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
APOLLO_API_KEY = os.getenv('APOLLO_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY') 
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# API Base URLs
APOLLO_BASE_URL = "https://api.apollo.io/v1"
AIRTABLE_BASE_URL = "https://api.airtable.com/v0"
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

app = Flask(__name__, static_folder='static', static_url_path='/static')

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
        "speakers": ["Dr. Dédé", "Mindfulness expert", "Executive chef"],
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
        "speakers": ["Dr. Dédé", "Accessibility advocates", "Tech innovators"],
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
        "speakers": ["Dr. Dédé", "Board governance experts", "AI ethics specialists"],
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
    <title>Dr. Dédé's RiskTravel Intelligence Platform</title>
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
            <h1 class="text-2xl font-bold">🏥 Dr. Dédé's RiskTravel Intelligence</h1>
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
                    <h3 class="text-lg font-semibold mb-4">Revenue Streams</h3>
                    <div id="revenueStreams" class="grid grid-cols-1 md:grid-cols-2 gap-4">
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

    <!-- Welcome Screen -->
    <div id="welcomeScreen" class="container mx-auto p-6">
        <div class="text-center py-20">
            <h2 class="text-4xl font-bold text-gray-800 mb-4">Welcome to Dr. Dédé's RiskTravel Intelligence Platform</h2>
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
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900">${stream.name}</h4>
                    <div class="mt-2">
                        <div class="flex justify-between text-sm">
                            <span>Current: $${stream.current_month.toLocaleString()}</span>
                            <span>Target: $${stream.target_month.toLocaleString()}</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                            <div class="bg-blue-600 h-2 rounded-full" style="width: ${(stream.current_month / stream.target_month) * 100}%"></div>
                        </div>
                        <div class="text-xs text-gray-600 mt-1">Growth: ${stream.growth_rate}%</div>
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
                "name": "Dr. Dédé",
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
                "name": "Dr. Dédé",
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

@app.route('/')
def index():
    return DASHBOARD_HTML

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
    return jsonify(REVENUE_STREAMS)

@app.route('/api/revenue/<int:stream_id>', methods=['GET'])
@jwt_required()
def get_revenue_stream(stream_id):
    stream = next((s for s in REVENUE_STREAMS if s['id'] == stream_id), None)
    if not stream:
        return jsonify({"error": "Revenue stream not found"}), 404
    return jsonify(stream)

@app.route('/api/revenue', methods=['POST'])
@jwt_required()
def create_revenue_entry():
    try:
        data = request.get_json()
        new_entry = {
            "id": len(REVENUE_STREAMS) + 1,
            "name": data.get('name'),
            "current_month": data.get('current_month', 0),
            "target_month": data.get('target_month', 0),
            "ytd": data.get('ytd', 0),
            "target_ytd": data.get('target_ytd', 0),
            "growth_rate": data.get('growth_rate', 0),
            "last_updated": datetime.now().isoformat()
        }
        REVENUE_STREAMS.append(new_entry)
        return jsonify(new_entry), 201
    except Exception as e:
        logger.error(f"Create revenue entry error: {e}")
        return jsonify({"error": "Failed to create revenue entry"}), 500

# KPI routes
@app.route('/api/kpi', methods=['GET'])
@jwt_required()
def get_kpis():
    return jsonify(KPI_METRICS)

@app.route('/api/kpi/<int:kpi_id>', methods=['GET'])
@jwt_required()
def get_kpi(kpi_id):
    kpi = next((k for k in KPI_METRICS if k['id'] == kpi_id), None)
    if not kpi:
        return jsonify({"error": "KPI not found"}), 404
    return jsonify(kpi)

# AI Agent routes
@app.route('/api/agents', methods=['GET'])
@jwt_required()
def get_agents():
    return jsonify(AI_AGENTS)

@app.route('/api/agents/<int:agent_id>', methods=['GET'])
@jwt_required()
def get_agent(agent_id):
    agent = next((a for a in AI_AGENTS if a['id'] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    return jsonify(agent)

@app.route('/api/agents/<int:agent_id>/status', methods=['PUT'])
@jwt_required()
def update_agent_status(agent_id):
    try:
        agent = next((a for a in AI_AGENTS if a['id'] == agent_id), None)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['active', 'paused', 'stopped']:
            return jsonify({"error": "Invalid status"}), 400
        
        agent['status'] = new_status
        agent['last_activity'] = datetime.now().isoformat()
        
        return jsonify(agent)
    except Exception as e:
        logger.error(f"Update agent status error: {e}")
        return jsonify({"error": "Failed to update agent status"}), 500

# Milestone routes
@app.route('/api/milestones', methods=['GET'])
@jwt_required()
def get_milestones():
    return jsonify(MILESTONES)

@app.route('/api/milestones/<int:milestone_id>', methods=['GET'])
@jwt_required()
def get_milestone(milestone_id):
    milestone = next((m for m in MILESTONES if m['id'] == milestone_id), None)
    if not milestone:
        return jsonify({"error": "Milestone not found"}), 404
    return jsonify(milestone)

# Healthcare Provider routes
@app.route('/api/healthcare/providers', methods=['GET'])
@jwt_required()
def get_healthcare_providers():
    return jsonify(HEALTHCARE_PROVIDERS)

@app.route('/api/healthcare/providers/<int:provider_id>', methods=['GET'])
@jwt_required()
def get_healthcare_provider(provider_id):
    provider = next((p for p in HEALTHCARE_PROVIDERS if p['id'] == provider_id), None)
    if not provider:
        return jsonify({"error": "Provider not found"}), 404
    return jsonify(provider)

@app.route('/api/healthcare/providers', methods=['POST'])
@jwt_required()
def create_healthcare_provider():
    try:
        data = request.get_json()
        new_provider = {
            "id": len(HEALTHCARE_PROVIDERS) + 1,
            "name": data.get('name'),
            "specialty": data.get('specialty'),
            "phone": data.get('phone'),
            "rating": data.get('rating', 0),
            "insurance_accepted": data.get('insurance_accepted', []),
            "next_available": data.get('next_available'),
            "address": data.get('address'),
            "notes": data.get('notes', '')
        }
        HEALTHCARE_PROVIDERS.append(new_provider)
        return jsonify(new_provider), 201
    except Exception as e:
        logger.error(f"Create healthcare provider error: {e}")
        return jsonify({"error": "Failed to create healthcare provider"}), 500

# Healthcare Appointment routes
@app.route('/api/healthcare/appointments', methods=['GET'])
@jwt_required()
def get_healthcare_appointments():
    return jsonify(HEALTHCARE_APPOINTMENTS)

@app.route('/api/healthcare/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_healthcare_appointment(appointment_id):
    appointment = next((a for a in HEALTHCARE_APPOINTMENTS if a['id'] == appointment_id), None)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    return jsonify(appointment)

@app.route('/api/healthcare/appointments', methods=['POST'])
@jwt_required()
def create_healthcare_appointment():
    try:
        data = request.get_json()
        new_appointment = {
            "id": len(HEALTHCARE_APPOINTMENTS) + 1,
            "provider": data.get('provider'),
            "date": data.get('date'),
            "time": data.get('time'),
            "purpose": data.get('purpose'),
            "status": data.get('status', 'scheduled'),
            "notes": data.get('notes', '')
        }
        HEALTHCARE_APPOINTMENTS.append(new_appointment)
        return jsonify(new_appointment), 201
    except Exception as e:
        logger.error(f"Create healthcare appointment error: {e}")
        return jsonify({"error": "Failed to create healthcare appointment"}), 500

@app.route('/api/healthcare/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_healthcare_appointment(appointment_id):
    try:
        appointment = next((a for a in HEALTHCARE_APPOINTMENTS if a['id'] == appointment_id), None)
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
        
        data = request.get_json()
        appointment.update({
            "provider": data.get('provider', appointment['provider']),
            "date": data.get('date', appointment['date']),
            "time": data.get('time', appointment['time']),
            "purpose": data.get('purpose', appointment['purpose']),
            "status": data.get('status', appointment['status']),
            "notes": data.get('notes', appointment['notes'])
        })
        
        return jsonify(appointment)
    except Exception as e:
        logger.error(f"Update healthcare appointment error: {e}")
        return jsonify({"error": "Failed to update healthcare appointment"}), 500

# Health Metrics routes
@app.route('/api/healthcare/metrics', methods=['GET'])
@jwt_required()
def get_health_metrics():
    return jsonify(HEALTH_METRICS)

@app.route('/api/healthcare/metrics', methods=['POST'])
@jwt_required()
def create_health_metric():
    try:
        data = request.get_json()
        new_metric = {
            "id": len(HEALTH_METRICS) + 1,
            "metric": data.get('metric'),
            "value": data.get('value'),
            "unit": data.get('unit'),
            "date": data.get('date', datetime.now().isoformat()),
            "status": data.get('status', 'normal'),
            "target": data.get('target', '')
        }
        HEALTH_METRICS.append(new_metric)
        return jsonify(new_metric), 201
    except Exception as e:
        logger.error(f"Create health metric error: {e}")
        return jsonify({"error": "Failed to create health metric"}), 500

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
    return jsonify(HEALTH_WELLNESS['energy_tracking'])

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
    return jsonify(HEALTH_WELLNESS['wellness_goals'])

@app.route('/api/wellness/alerts', methods=['GET'])
@jwt_required()
def get_wellness_alerts():
    return jsonify(HEALTH_WELLNESS['alerts'])

@app.route('/api/wellness/overview', methods=['GET'])
@jwt_required()
def get_wellness_overview():
    return jsonify(HEALTH_WELLNESS)

# Executive Opportunities Management routes
@app.route('/api/executive/opportunities', methods=['GET'])
@jwt_required()
def get_executive_opportunities():
    return jsonify(EXECUTIVE_OPPORTUNITIES)

@app.route('/api/executive/opportunities/<int:opp_id>', methods=['GET'])
@jwt_required()
def get_executive_opportunity(opp_id):
    opp = next((o for o in EXECUTIVE_OPPORTUNITIES if o['id'] == opp_id), None)
    if not opp:
        return jsonify({"error": "Opportunity not found"}), 404
    return jsonify(opp)

@app.route('/api/executive/opportunities', methods=['POST'])
@jwt_required()
def create_executive_opportunity():
    try:
        data = request.get_json()
        new_opp = {
            "id": len(EXECUTIVE_OPPORTUNITIES) + 1,
            "type": data.get('type'),
            "title": data.get('title'),
            "company": data.get('company'),
            "compensation": data.get('compensation'),
            "location": data.get('location'),
            "status": data.get('status', 'applied'),
            "match_score": data.get('match_score', 0),
            "requirements": data.get('requirements', []),
            "application_date": data.get('application_date', datetime.now().date().isoformat()),
            "next_step": data.get('next_step', ''),
            "notes": data.get('notes', '')
        }
        EXECUTIVE_OPPORTUNITIES.append(new_opp)
        return jsonify(new_opp), 201
    except Exception as e:
        logger.error(f"Create executive opportunity error: {e}")
        return jsonify({"error": "Failed to create executive opportunity"}), 500

@app.route('/api/executive/opportunities/<int:opp_id>/status', methods=['PUT'])
@jwt_required()
def update_opportunity_status(opp_id):
    try:
        opp = next((o for o in EXECUTIVE_OPPORTUNITIES if o['id'] == opp_id), None)
        if not opp:
            return jsonify({"error": "Opportunity not found"}), 404
        
        data = request.get_json()
        opp.update({
            "status": data.get('status', opp['status']),
            "next_step": data.get('next_step', opp['next_step']),
            "notes": data.get('notes', opp['notes'])
        })
        
        return jsonify(opp)
    except Exception as e:
        logger.error(f"Update opportunity status error: {e}")
        return jsonify({"error": "Failed to update opportunity status"}), 500

@app.route('/api/executive/opportunities/type/<string:opportunity_type>', methods=['GET'])
@jwt_required()
def get_opportunities_by_type(opportunity_type):
    opportunities = [o for o in EXECUTIVE_OPPORTUNITIES if o['type'] == opportunity_type]
    return jsonify(opportunities)

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

