# Dr. Dédé's RiskTravel Intelligence Platform

## Project Overview

This is a Flask web application that serves as Dr. Dédé's RiskTravel Intelligence Platform - a comprehensive business and healthcare management dashboard. The application combines business intelligence features with healthcare management tools, providing a unified platform for tracking revenue, managing AI agents, monitoring KPIs, and handling healthcare providers and appointments.

## Recent Changes (September 16, 2025)

- **Project Import**: Successfully imported and configured the project for Replit environment
- **Dependencies**: Installed Python 3.11 and all required Flask dependencies
- **Workflow**: Configured Flask server to run on port 5000 with webview output
- **Deployment**: Set up autoscale deployment configuration using Gunicorn
- **Testing**: Verified all API endpoints and authentication functionality

## User Preferences

- No specific coding style preferences documented yet
- Standard Flask application structure maintained
- Production-ready configuration with proper security practices

## Project Architecture

### Technology Stack
- **Backend**: Flask 2.3.3 with JWT authentication
- **Frontend**: Integrated HTML/CSS/JavaScript using TailwindCSS
- **Dependencies**: 
  - Flask-CORS for cross-origin requests
  - Flask-JWT-Extended for authentication
  - Gunicorn for production deployment
  - python-dotenv for environment configuration

### Application Structure
- **Single File Architecture**: Both frontend and backend are contained in `main.py`
- **Data Storage**: In-memory data structures (suitable for demo/development)
- **Authentication**: JWT-based with demo credentials (dede@risktravel.com / password123)

### Key Features
1. **Revenue Tracking**: 4 revenue streams with targets and growth rates
2. **Healthcare Management**: Provider directory, appointment scheduling, health metrics
3. **AI Agent Monitoring**: Status tracking for LinkedIn, Content, and Email agents
4. **KPI Dashboard**: MRR, CAC, LTV, Conversion rate monitoring
5. **Responsive Design**: Mobile and desktop compatible interface

### API Endpoints
- **Authentication**: `/api/auth/login`, `/api/auth/register`
- **Dashboard**: `/api/dashboard/overview`, `/health`
- **Revenue**: `/api/revenue`, `/api/kpi`, `/api/milestones`
- **AI Agents**: `/api/agents`
- **Healthcare**: `/api/healthcare/providers`, `/api/healthcare/appointments`, `/api/healthcare/metrics`

### Configuration
- **Development**: Flask development server on 0.0.0.0:5000
- **Production**: Gunicorn WSGI server with autoscale deployment
- **Security**: JWT tokens, CORS enabled, input validation

### Current Status
✅ **Fully Operational**: All components working correctly
✅ **Replit Ready**: Configured for Replit environment
✅ **Production Ready**: Deployment configuration complete
✅ **Tested**: API endpoints and authentication verified

### Next Steps
- Consider implementing persistent data storage (database)
- Add environment-specific configuration
- Implement real integration with external services
- Add comprehensive error handling and logging