"""
Comprehensive Perplexity AI Service
Advanced AI-powered research, content generation, and intelligent analysis service
"""

import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import os
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class PerplexityModel(Enum):
    """Available Perplexity models"""
    SMALL = "llama-3.1-sonar-small-128k-online"
    LARGE = "llama-3.1-sonar-large-128k-online"
    HUGE = "llama-3.1-sonar-huge-128k-online"


class SearchRecency(Enum):
    """Search recency filter options"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


@dataclass
class PerplexityRequest:
    """Request configuration for Perplexity API"""
    prompt: str
    system_message: Optional[str] = None
    model: PerplexityModel = PerplexityModel.SMALL
    max_tokens: Optional[int] = None
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 0
    search_domain_filter: Optional[List[str]] = None
    search_recency_filter: Optional[SearchRecency] = None
    return_images: bool = False
    return_related_questions: bool = False
    stream: bool = False
    presence_penalty: float = 0.0
    frequency_penalty: float = 1.0


@dataclass
class PerplexityResponse:
    """Structured response from Perplexity API"""
    content: str
    citations: List[str] = None
    id: Optional[str] = None
    model: Optional[str] = None
    created: Optional[int] = None
    usage: Optional[Dict[str, int]] = None
    related_questions: Optional[List[str]] = None
    images: Optional[List[Dict[str, Any]]] = None
    raw_response: Optional[Dict[str, Any]] = None


class PerplexityAPI:
    """
    Comprehensive Perplexity AI API wrapper following blueprint specifications
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Perplexity API client
        
        Args:
            api_key: Perplexity API key. If None, uses PERPLEXITY_API_KEY environment variable
        """
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            logger.warning("Perplexity API key not configured. Set PERPLEXITY_API_KEY environment variable.")
            raise ValueError("PERPLEXITY_API_KEY is required")
        
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def chat_completion(self, request: PerplexityRequest) -> Optional[PerplexityResponse]:
        """
        Send chat completion request to Perplexity API
        
        Args:
            request: PerplexityRequest object with all parameters
            
        Returns:
            PerplexityResponse object or None if error
        """
        try:
            # Build messages array
            messages = []
            
            # Add system message if provided
            if request.system_message:
                messages.append({
                    "role": "system",
                    "content": request.system_message
                })
            
            # Add user message
            messages.append({
                "role": "user",
                "content": request.prompt
            })
            
            # Build request payload
            payload = {
                "model": request.model.value,
                "messages": messages,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "top_k": request.top_k,
                "stream": request.stream,
                "presence_penalty": request.presence_penalty,
                "frequency_penalty": request.frequency_penalty,
                "return_images": request.return_images,
                "return_related_questions": request.return_related_questions
            }
            
            # Add optional parameters
            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens
            
            if request.search_domain_filter:
                payload["search_domain_filter"] = request.search_domain_filter
            
            if request.search_recency_filter:
                payload["search_recency_filter"] = request.search_recency_filter.value
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse response
            return self._parse_response(result)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Perplexity API request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Perplexity API call: {e}")
            return None
    
    def _parse_response(self, response_data: Dict[str, Any]) -> PerplexityResponse:
        """Parse raw API response into PerplexityResponse object"""
        try:
            content = ""
            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0]['message']['content']
            
            return PerplexityResponse(
                content=content,
                citations=response_data.get('citations', []),
                id=response_data.get('id'),
                model=response_data.get('model'),
                created=response_data.get('created'),
                usage=response_data.get('usage'),
                related_questions=response_data.get('related_questions'),
                images=response_data.get('images'),
                raw_response=response_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing Perplexity response: {e}")
            return PerplexityResponse(content="", raw_response=response_data)
    
    def simple_query(self, prompt: str, model: PerplexityModel = PerplexityModel.SMALL, 
                     temperature: float = 0.2, max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Simple query method for quick requests
        
        Args:
            prompt: User query
            model: Model to use
            temperature: Response creativity (0.0-1.0)
            max_tokens: Maximum response tokens
            
        Returns:
            Response content as string or None if error
        """
        request = PerplexityRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        response = self.chat_completion(request)
        return response.content if response else None


class PerplexityResearchService:
    """
    Advanced research service using Perplexity AI for market intelligence and analysis
    """
    
    def __init__(self, perplexity_api: PerplexityAPI):
        self.api = perplexity_api
        self.research_templates = {
            'market_analysis': """
Analyze the market for {topic}. Provide comprehensive insights including:
1. Market size and growth projections
2. Key players and competitive landscape
3. Current trends and emerging opportunities
4. Regulatory environment and challenges
5. Future outlook and predictions

Focus on recent data and credible sources.
""",
            'company_research': """
Research {company_name} and provide a comprehensive analysis including:
1. Business model and revenue streams
2. Recent financial performance and key metrics
3. Leadership team and board composition
4. Strategic initiatives and recent developments
5. Industry position and competitive advantages
6. Governance structure and risk factors
7. Recent news and market developments

Provide factual, up-to-date information from reliable sources.
""",
            'industry_intelligence': """
Provide intelligence analysis on the {industry} industry including:
1. Industry overview and market dynamics
2. Key trends and disruptions
3. Regulatory landscape and compliance requirements
4. Technology adoption and innovation
5. Risk factors and challenges
6. Growth opportunities and investment trends
7. Notable companies and market leaders

Focus on current and forward-looking insights.
""",
            'competitive_analysis': """
Conduct a competitive analysis comparing {primary_company} with {competitors}. Include:
1. Market positioning and differentiation
2. Product/service offerings comparison
3. Pricing strategies and business models
4. Market share and financial performance
5. Strengths and weaknesses analysis
6. Strategic initiatives and future plans
7. Competitive advantages and threats

Provide objective, data-driven analysis.
""",
            'executive_research': """
Research {executive_name} at {company_name} for potential {opportunity_type} opportunity. Analyze:
1. Professional background and experience
2. Leadership style and achievements
3. Industry expertise and specializations
4. Board positions and affiliations
5. Speaking engagements and thought leadership
6. Educational background and credentials
7. Recent activities and public statements
8. Governance and risk management experience

Focus on professional qualifications and public information.
"""
        }
    
    def conduct_market_analysis(self, topic: str, recency: SearchRecency = SearchRecency.MONTH) -> Optional[Dict[str, Any]]:
        """
        Conduct comprehensive market analysis on a given topic
        
        Args:
            topic: Market/industry topic to analyze
            recency: How recent the information should be
            
        Returns:
            Dictionary with analysis results and metadata
        """
        try:
            prompt = self.research_templates['market_analysis'].format(topic=topic)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a market research analyst. Provide detailed, factual analysis with specific data points and citations.",
                model=PerplexityModel.LARGE,
                temperature=0.1,
                max_tokens=1500,
                search_recency_filter=recency,
                return_related_questions=True
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                return {
                    'analysis': response.content,
                    'citations': response.citations,
                    'related_questions': response.related_questions,
                    'topic': topic,
                    'research_type': 'market_analysis',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return None
    
    def research_company(self, company_name: str, company_domain: Optional[str] = None,
                        recency: SearchRecency = SearchRecency.WEEK) -> Optional[Dict[str, Any]]:
        """
        Conduct comprehensive company research
        
        Args:
            company_name: Name of company to research
            company_domain: Optional company domain for more targeted search
            recency: How recent the information should be
            
        Returns:
            Dictionary with research results and metadata
        """
        try:
            search_filters = []
            if company_domain:
                search_filters.append(company_domain)
            
            prompt = self.research_templates['company_research'].format(company_name=company_name)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a business analyst researching companies. Focus on factual information, recent developments, and verifiable data.",
                model=PerplexityModel.LARGE,
                temperature=0.1,
                max_tokens=1800,
                search_recency_filter=recency,
                search_domain_filter=search_filters if search_filters else None,
                return_related_questions=True
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                return {
                    'analysis': response.content,
                    'citations': response.citations,
                    'related_questions': response.related_questions,
                    'company_name': company_name,
                    'company_domain': company_domain,
                    'research_type': 'company_research',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in company research: {e}")
            return None
    
    def analyze_industry(self, industry: str, focus_areas: Optional[List[str]] = None,
                        recency: SearchRecency = SearchRecency.MONTH) -> Optional[Dict[str, Any]]:
        """
        Conduct industry intelligence analysis
        
        Args:
            industry: Industry to analyze
            focus_areas: Optional specific areas to focus on
            recency: How recent the information should be
            
        Returns:
            Dictionary with analysis results and metadata
        """
        try:
            prompt = self.research_templates['industry_intelligence'].format(industry=industry)
            
            if focus_areas:
                prompt += f"\n\nPay special attention to: {', '.join(focus_areas)}"
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are an industry analyst providing strategic intelligence. Focus on data-driven insights and trends.",
                model=PerplexityModel.LARGE,
                temperature=0.1,
                max_tokens=1600,
                search_recency_filter=recency,
                return_related_questions=True
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                return {
                    'analysis': response.content,
                    'citations': response.citations,
                    'related_questions': response.related_questions,
                    'industry': industry,
                    'focus_areas': focus_areas,
                    'research_type': 'industry_intelligence',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in industry analysis: {e}")
            return None
    
    def competitive_analysis(self, primary_company: str, competitors: List[str],
                           recency: SearchRecency = SearchRecency.MONTH) -> Optional[Dict[str, Any]]:
        """
        Conduct competitive analysis between companies
        
        Args:
            primary_company: Main company to analyze
            competitors: List of competing companies
            recency: How recent the information should be
            
        Returns:
            Dictionary with analysis results and metadata
        """
        try:
            competitors_str = ', '.join(competitors)
            prompt = self.research_templates['competitive_analysis'].format(
                primary_company=primary_company,
                competitors=competitors_str
            )
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a competitive analyst. Provide objective, data-driven comparisons with specific metrics and examples.",
                model=PerplexityModel.LARGE,
                temperature=0.1,
                max_tokens=2000,
                search_recency_filter=recency,
                return_related_questions=True
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                return {
                    'analysis': response.content,
                    'citations': response.citations,
                    'related_questions': response.related_questions,
                    'primary_company': primary_company,
                    'competitors': competitors,
                    'research_type': 'competitive_analysis',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in competitive analysis: {e}")
            return None
    
    def research_executive_opportunity(self, executive_name: str, company_name: str,
                                     opportunity_type: str, recency: SearchRecency = SearchRecency.WEEK) -> Optional[Dict[str, Any]]:
        """
        Research executive for potential opportunity (board position, speaking engagement, etc.)
        
        Args:
            executive_name: Name of executive to research
            company_name: Company where executive works
            opportunity_type: Type of opportunity (board_director, speaker, consultant)
            recency: How recent the information should be
            
        Returns:
            Dictionary with research results and metadata
        """
        try:
            prompt = self.research_templates['executive_research'].format(
                executive_name=executive_name,
                company_name=company_name,
                opportunity_type=opportunity_type
            )
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are researching executives for business opportunities. Focus on professional qualifications, public information, and relevant experience.",
                model=PerplexityModel.LARGE,
                temperature=0.1,
                max_tokens=1400,
                search_recency_filter=recency,
                return_related_questions=True
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                return {
                    'analysis': response.content,
                    'citations': response.citations,
                    'related_questions': response.related_questions,
                    'executive_name': executive_name,
                    'company_name': company_name,
                    'opportunity_type': opportunity_type,
                    'research_type': 'executive_research',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in executive research: {e}")
            return None


class PerplexityContentService:
    """
    AI-powered content generation service using Perplexity for insights and reports
    """
    
    def __init__(self, perplexity_api: PerplexityAPI):
        self.api = perplexity_api
        self.content_templates = {
            'executive_summary': """
Create a comprehensive executive summary based on the following research data:

{research_data}

The summary should include:
1. Key findings and insights
2. Strategic implications
3. Recommended actions
4. Risk factors and considerations
5. Timeline and priorities

Format as a professional executive briefing document.
""",
            'market_report': """
Generate a professional market report based on this analysis:

{market_data}

Structure the report with:
1. Executive Summary
2. Market Overview
3. Key Trends and Drivers
4. Competitive Landscape
5. Opportunities and Challenges
6. Strategic Recommendations
7. Conclusion

Use professional business language and include specific data points.
""",
            'opportunity_brief': """
Create a business opportunity brief for the following prospect:

{prospect_data}

Include:
1. Opportunity Overview
2. Prospect Profile and Qualifications
3. Value Proposition Alignment
4. Engagement Strategy
5. Success Probability Assessment
6. Next Steps and Timeline
7. Risk Mitigation Factors

Focus on actionable business intelligence.
""",
            'industry_insight': """
Generate an industry insight article based on this research:

{industry_data}

Create content suitable for thought leadership with:
1. Current State Analysis
2. Emerging Trends and Disruptions
3. Strategic Implications
4. Future Predictions
5. Key Takeaways for Leaders

Write in an authoritative, analytical tone.
"""
        }
    
    def generate_executive_summary(self, research_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate executive summary from research data
        
        Args:
            research_data: Research findings to summarize
            
        Returns:
            Dictionary with generated summary and metadata
        """
        try:
            # Format research data for prompt
            data_str = json.dumps(research_data, indent=2)
            prompt = self.content_templates['executive_summary'].format(research_data=data_str)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are an executive communications specialist creating professional business summaries. Write clearly and concisely for C-level audience.",
                model=PerplexityModel.LARGE,
                temperature=0.3,
                max_tokens=1200,
                return_related_questions=False
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                return {
                    'summary': response.content,
                    'source_data': research_data,
                    'content_type': 'executive_summary',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return None
    
    def generate_market_report(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate comprehensive market report from analysis data
        
        Args:
            market_data: Market analysis data
            
        Returns:
            Dictionary with generated report and metadata
        """
        try:
            data_str = json.dumps(market_data, indent=2)
            prompt = self.content_templates['market_report'].format(market_data=data_str)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a market research report writer creating professional business reports. Use data-driven insights and professional formatting.",
                model=PerplexityModel.LARGE,
                temperature=0.2,
                max_tokens=2000,
                return_related_questions=True
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                return {
                    'report': response.content,
                    'related_questions': response.related_questions,
                    'source_data': market_data,
                    'content_type': 'market_report',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating market report: {e}")
            return None
    
    def generate_opportunity_brief(self, prospect_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate business opportunity brief from prospect research
        
        Args:
            prospect_data: Prospect research and analysis data
            
        Returns:
            Dictionary with generated brief and metadata
        """
        try:
            data_str = json.dumps(prospect_data, indent=2)
            prompt = self.content_templates['opportunity_brief'].format(prospect_data=data_str)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a business development analyst creating opportunity assessments. Focus on actionable insights and strategic recommendations.",
                model=PerplexityModel.LARGE,
                temperature=0.2,
                max_tokens=1400,
                return_related_questions=True
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                return {
                    'brief': response.content,
                    'related_questions': response.related_questions,
                    'source_data': prospect_data,
                    'content_type': 'opportunity_brief',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating opportunity brief: {e}")
            return None
    
    def generate_industry_insight(self, industry_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate thought leadership content from industry analysis
        
        Args:
            industry_data: Industry research and analysis data
            
        Returns:
            Dictionary with generated insight article and metadata
        """
        try:
            data_str = json.dumps(industry_data, indent=2)
            prompt = self.content_templates['industry_insight'].format(industry_data=data_str)
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a thought leader creating industry insights. Write with authority and provide strategic perspectives for business leaders.",
                model=PerplexityModel.LARGE,
                temperature=0.3,
                max_tokens=1800,
                return_related_questions=True
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                return {
                    'insight': response.content,
                    'related_questions': response.related_questions,
                    'source_data': industry_data,
                    'content_type': 'industry_insight',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating industry insight: {e}")
            return None


class PerplexityOpportunityAnalyzer:
    """
    Advanced opportunity analysis service integrating with executive opportunity scoring
    """
    
    def __init__(self, perplexity_api: PerplexityAPI, research_service: PerplexityResearchService):
        self.api = perplexity_api
        self.research = research_service
        self.analysis_templates = {
            'governance_fit': """
Analyze {company_name}'s governance structure and assess fit for board director opportunity:

Company Research: {company_data}

Evaluate:
1. Current board composition and diversity
2. Governance maturity and practices
3. Committee structure and expertise gaps
4. Recent governance challenges or changes
5. Regulatory compliance requirements
6. Risk management framework
7. Stakeholder engagement practices
8. ESG and sustainability initiatives

Provide governance fit score (0-1) and specific recommendations.
""",
            'speaking_opportunity': """
Assess speaking opportunity potential for {event_context}:

Research Data: {research_data}

Analyze:
1. Audience alignment with expertise
2. Topic relevance and thought leadership potential
3. Platform prestige and reach
4. Network expansion opportunities
5. Revenue potential and value proposition
6. Brand building and authority establishment
7. Follow-up business opportunities
8. Scheduling and logistics feasibility

Provide opportunity score (0-1) and strategic assessment.
""",
            'market_entry': """
Evaluate market entry opportunity for {market_segment}:

Market Analysis: {market_data}

Assessment areas:
1. Market size and growth potential
2. Competitive intensity and barriers
3. Regulatory environment and requirements
4. Technology and innovation trends
5. Customer needs and pain points
6. Resource requirements and investment
7. Time to market and scaling potential
8. Risk factors and mitigation strategies

Provide market entry score (0-1) and strategic roadmap.
"""
        }
    
    def analyze_governance_opportunity(self, company_name: str, company_domain: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze company for board director/governance opportunity fit
        
        Args:
            company_name: Name of target company
            company_domain: Optional company domain for focused research
            
        Returns:
            Dictionary with governance analysis and scoring
        """
        try:
            # First, conduct company research
            company_research = self.research.research_company(
                company_name=company_name,
                company_domain=company_domain,
                recency=SearchRecency.WEEK
            )
            
            if not company_research:
                logger.error("Failed to conduct company research for governance analysis")
                return None
            
            # Analyze governance fit
            prompt = self.analysis_templates['governance_fit'].format(
                company_name=company_name,
                company_data=json.dumps(company_research, indent=2)
            )
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a corporate governance expert analyzing board opportunities. Focus on governance gaps, compliance needs, and strategic fit.",
                model=PerplexityModel.LARGE,
                temperature=0.1,
                max_tokens=1500,
                search_recency_filter=SearchRecency.WEEK
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                # Extract governance fit score from response
                governance_score = self._extract_score_from_response(response.content)
                
                return {
                    'governance_analysis': response.content,
                    'governance_score': governance_score,
                    'company_research': company_research,
                    'citations': response.citations,
                    'company_name': company_name,
                    'analysis_type': 'governance_opportunity',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in governance opportunity analysis: {e}")
            return None
    
    def analyze_speaking_opportunity(self, event_context: str, target_audience: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze speaking opportunity potential and strategic value
        
        Args:
            event_context: Context about the speaking event/opportunity
            target_audience: Optional description of target audience
            
        Returns:
            Dictionary with speaking opportunity analysis and scoring
        """
        try:
            # Enhance context with audience information
            full_context = event_context
            if target_audience:
                full_context += f" Target Audience: {target_audience}"
            
            # Research the speaking opportunity context
            market_research = self.research.conduct_market_analysis(
                topic=f"speaking opportunities {event_context}",
                recency=SearchRecency.MONTH
            )
            
            prompt = self.analysis_templates['speaking_opportunity'].format(
                event_context=full_context,
                research_data=json.dumps(market_research, indent=2) if market_research else "No specific research available"
            )
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a professional speaking consultant analyzing opportunity value. Focus on strategic benefits, audience fit, and business development potential.",
                model=PerplexityModel.LARGE,
                temperature=0.2,
                max_tokens=1300,
                search_recency_filter=SearchRecency.MONTH
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                # Extract opportunity score from response
                opportunity_score = self._extract_score_from_response(response.content)
                
                return {
                    'speaking_analysis': response.content,
                    'opportunity_score': opportunity_score,
                    'market_research': market_research,
                    'citations': response.citations,
                    'event_context': event_context,
                    'target_audience': target_audience,
                    'analysis_type': 'speaking_opportunity',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in speaking opportunity analysis: {e}")
            return None
    
    def analyze_market_entry_opportunity(self, market_segment: str, focus_areas: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze market entry opportunity and strategic potential
        
        Args:
            market_segment: Target market segment to analyze
            focus_areas: Optional specific focus areas for analysis
            
        Returns:
            Dictionary with market entry analysis and scoring
        """
        try:
            # Research the market segment
            market_analysis = self.research.analyze_industry(
                industry=market_segment,
                focus_areas=focus_areas,
                recency=SearchRecency.MONTH
            )
            
            if not market_analysis:
                logger.error("Failed to conduct market analysis for entry opportunity")
                return None
            
            prompt = self.analysis_templates['market_entry'].format(
                market_segment=market_segment,
                market_data=json.dumps(market_analysis, indent=2)
            )
            
            request = PerplexityRequest(
                prompt=prompt,
                system_message="You are a market entry strategist analyzing business opportunities. Focus on feasibility, competitive dynamics, and strategic potential.",
                model=PerplexityModel.LARGE,
                temperature=0.1,
                max_tokens=1600,
                search_recency_filter=SearchRecency.MONTH
            )
            
            response = self.api.chat_completion(request)
            
            if response:
                # Extract market entry score from response
                entry_score = self._extract_score_from_response(response.content)
                
                return {
                    'market_entry_analysis': response.content,
                    'entry_score': entry_score,
                    'market_analysis': market_analysis,
                    'citations': response.citations,
                    'market_segment': market_segment,
                    'focus_areas': focus_areas,
                    'analysis_type': 'market_entry_opportunity',
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_used': response.model,
                    'usage': response.usage
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in market entry opportunity analysis: {e}")
            return None
    
    def _extract_score_from_response(self, response_content: str) -> float:
        """
        Extract numerical score from AI response text
        
        Args:
            response_content: AI response containing score
            
        Returns:
            Extracted score as float between 0.0 and 1.0
        """
        try:
            # Look for numerical scores in various formats
            score_patterns = [
                r'score[:\s]*([0-1]\.?\d*)',
                r'([0-1]\.\d+)',
                r'(\d+)/10',
                r'(\d+)%',
                r'rating[:\s]*([0-1]\.?\d*)',
                r'assessment[:\s]*([0-1]\.?\d*)'
            ]
            
            for pattern in score_patterns:
                matches = re.findall(pattern, response_content.lower())
                if matches:
                    score_str = matches[0]
                    if '/' in score_str:
                        # Handle X/10 format
                        score = float(score_str.split('/')[0]) / 10
                    elif '%' in score_str:
                        # Handle percentage
                        score = float(score_str.replace('%', '')) / 100
                    else:
                        score = float(score_str)
                    
                    return min(max(score, 0.0), 1.0)
            
            # Fallback: sentiment analysis
            return self._sentiment_based_score(response_content)
            
        except Exception as e:
            logger.error(f"Error extracting score from response: {e}")
            return 0.5
    
    def _sentiment_based_score(self, text: str) -> float:
        """
        Generate score based on sentiment analysis of response text
        
        Args:
            text: Text to analyze
            
        Returns:
            Score between 0.0 and 1.0 based on sentiment
        """
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = [
            'excellent', 'outstanding', 'exceptional', 'strong', 'high potential',
            'significant opportunity', 'well-positioned', 'strategic fit', 'ideal',
            'compelling', 'attractive', 'promising', 'favorable', 'advantageous'
        ]
        
        # Negative indicators
        negative_words = [
            'poor', 'weak', 'limited', 'challenging', 'difficult', 'unfavorable',
            'low potential', 'risky', 'problematic', 'concerning', 'inadequate',
            'insufficient', 'barriers', 'obstacles', 'threats'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate sentiment-based score
        if positive_count + negative_count == 0:
            return 0.5  # Neutral
        
        sentiment_ratio = positive_count / (positive_count + negative_count)
        return min(max(sentiment_ratio, 0.0), 1.0)


# Factory functions for easy initialization
def create_perplexity_api(api_key: Optional[str] = None) -> PerplexityAPI:
    """Create Perplexity API client"""
    return PerplexityAPI(api_key)

def create_research_service(api_key: Optional[str] = None) -> PerplexityResearchService:
    """Create Perplexity research service"""
    api = create_perplexity_api(api_key)
    return PerplexityResearchService(api)

def create_content_service(api_key: Optional[str] = None) -> PerplexityContentService:
    """Create Perplexity content service"""
    api = create_perplexity_api(api_key)
    return PerplexityContentService(api)

def create_opportunity_analyzer(api_key: Optional[str] = None) -> PerplexityOpportunityAnalyzer:
    """Create Perplexity opportunity analyzer"""
    api = create_perplexity_api(api_key)
    research = PerplexityResearchService(api)
    return PerplexityOpportunityAnalyzer(api, research)