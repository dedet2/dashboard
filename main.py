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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Sample data for the platform
REVENUE_STREAMS = [
    {
        "id": 1,
        "name": "Consulting Services",
        "current_month": 45000,
        "target_month": 50000,
        "ytd": 480000,
        "target_ytd": 600000,
        "growth_rate": 12.5,
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": 2,
        "name": "Digital Products",
        "current_month": 28000,
        "target_month": 35000,
        "ytd": 320000,
        "target_ytd": 420000,
        "growth_rate": 8.3,
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": 3,
        "name": "Training Programs",
        "current_month": 15000,
        "target_month": 20000,
        "ytd": 180000,
        "target_ytd": 240000,
        "growth_rate": 15.2,
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": 4,
        "name": "Partnerships",
        "current_month": 12000,
        "target_month": 15000,
        "ytd": 144000,
        "target_ytd": 180000,
        "growth_rate": 6.7,
        "last_updated": datetime.now().isoformat()
    }
]

KPI_METRICS = [
    {
        "id": 1,
        "name": "Monthly Recurring Revenue",
        "value": 100000,
        "target": 120000,
        "unit": "USD",
        "trend": "up",
        "change_percent": 8.5,
        "category": "revenue"
    },
    {
        "id": 2,
        "name": "Customer Acquisition Cost",
        "value": 250,
        "target": 200,
        "unit": "USD",
        "trend": "down",
        "change_percent": -5.2,
        "category": "marketing"
    },
    {
        "id": 3,
        "name": "Customer Lifetime Value",
        "value": 5200,
        "target": 5000,
        "unit": "USD",
        "trend": "up",
        "change_percent": 4.0,
        "category": "revenue"
    },
    {
        "id": 4,
        "name": "Conversion Rate",
        "value": 3.2,
        "target": 3.5,
        "unit": "%",
        "trend": "up",
        "change_percent": 0.8,
        "category": "marketing"
    }
]

AI_AGENTS = [
    {
        "id": 1,
        "name": "LinkedIn Outreach Agent",
        "status": "active",
        "last_activity": datetime.now().isoformat(),
        "tasks_completed": 45,
        "success_rate": 78.5,
        "next_scheduled": (datetime.now() + timedelta(hours=2)).isoformat()
    },
    {
        "id": 2,
        "name": "Content Creation Agent",
        "status": "active",
        "last_activity": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "tasks_completed": 23,
        "success_rate": 92.1,
        "next_scheduled": (datetime.now() + timedelta(hours=4)).isoformat()
    },
    {
        "id": 3,
        "name": "Email Marketing Agent",
        "status": "paused",
        "last_activity": (datetime.now() - timedelta(hours=2)).isoformat(),
        "tasks_completed": 67,
        "success_rate": 85.3,
        "next_scheduled": (datetime.now() + timedelta(hours=6)).isoformat()
    }
]

MILESTONES = [
    {
        "id": 1,
        "title": "Q1 Revenue Target",
        "target_date": "2025-03-31",
        "progress": 85,
        "status": "on_track",
        "description": "Achieve $300K in Q1 revenue"
    },
    {
        "id": 2,
        "title": "Platform Launch",
        "target_date": "2025-06-15",
        "progress": 45,
        "status": "in_progress",
        "description": "Launch new RiskTravel intelligence platform"
    },
    {
        "id": 3,
        "title": "Team Expansion",
        "target_date": "2025-09-30",
        "progress": 20,
        "status": "planning",
        "description": "Hire 5 additional team members"
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
                const headers = { Authorization: `Bearer ${authToken}` };
                
                // Load overview
                const overview = await axios.get(`${API_BASE}/api/dashboard/overview`, { headers });
                updateOverview(overview.data);
                
                // Load revenue streams
                const revenue = await axios.get(`${API_BASE}/api/revenue`, { headers });
                updateRevenueStreams(revenue.data);
                
                // Load AI agents
                const agents = await axios.get(`${API_BASE}/api/agents`, { headers });
                updateAIAgents(agents.data);
                
                // Load healthcare data
                const providers = await axios.get(`${API_BASE}/api/healthcare/providers`, { headers });
                const appointments = await axios.get(`${API_BASE}/api/healthcare/appointments`, { headers });
                updateHealthcareData(providers.data, appointments.data);
                
                // Load KPIs
                const kpis = await axios.get(`${API_BASE}/api/kpi`, { headers });
                updateKPIs(kpis.data);
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
                if (error.response?.status === 401) {
                    handleLogout();
                }
            }
        }
        
        function updateOverview(data) {
            document.getElementById('totalRevenue').textContent = `$${data.total_revenue.toLocaleString()}`;
            document.getElementById('activeAgents').textContent = data.active_agents;
            document.getElementById('appointments').textContent = data.upcoming_appointments;
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

