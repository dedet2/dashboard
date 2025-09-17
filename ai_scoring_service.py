"""
AI Scoring Service
Enhanced opportunity scoring using Perplexity AI for company research and prospect analysis
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import os

from apollo_integration import ApolloProspect, ApolloCompany

# Import enhanced Perplexity services
try:
    from perplexity_service import (
        create_research_service, create_content_service, create_opportunity_analyzer,
        SearchRecency
    )
    PERPLEXITY_SERVICES_AVAILABLE = True
except ImportError:
    PERPLEXITY_SERVICES_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIOpportunityScorer:
    """
    Enhanced AI-powered opportunity scoring service using comprehensive Perplexity AI integration
    """
    
    def __init__(self, perplexity_api_key: str = None):
        self.perplexity_api_key = perplexity_api_key or os.getenv('PERPLEXITY_API_KEY')
        if not self.perplexity_api_key:
            logger.warning("Perplexity API key not configured. AI scoring will use fallback methods.")
        
        # Initialize enhanced Perplexity services
        self.research_service = None
        self.content_service = None
        self.opportunity_analyzer = None
        
        if PERPLEXITY_SERVICES_AVAILABLE and self.perplexity_api_key:
            try:
                self.research_service = create_research_service(self.perplexity_api_key)
                self.content_service = create_content_service(self.perplexity_api_key)
                self.opportunity_analyzer = create_opportunity_analyzer(self.perplexity_api_key)
                logger.info("Enhanced Perplexity services initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize enhanced Perplexity services: {e}")
        
        # Enhanced scoring weights for different factors
        self.scoring_weights = {
            'apollo_base_score': 0.15,          # Base Apollo match score (reduced)
            'company_research': 0.25,           # Comprehensive company research
            'role_relevance': 0.20,             # How relevant the role is to our services
            'market_intelligence': 0.20,        # Market size and growth potential
            'opportunity_analysis': 0.20        # AI-powered opportunity analysis
        }
        
        # Industry relevance mapping (expanded)
        self.high_relevance_industries = [
            'financial services', 'banking', 'insurance', 'healthcare', 'pharmaceuticals',
            'technology', 'software', 'artificial intelligence', 'cybersecurity',
            'energy', 'utilities', 'telecommunications', 'aerospace', 'defense',
            'manufacturing', 'automotive', 'government', 'consulting', 'fintech',
            'biotech', 'renewable energy', 'logistics', 'real estate', 'media',
            'entertainment', 'education', 'retail', 'ecommerce'
        ]
        
        # High-value role keywords (expanded)
        self.high_value_roles = [
            'chief risk officer', 'cro', 'board director', 'independent director',
            'chief compliance officer', 'chief audit executive', 'chairman',
            'chief ai officer', 'head of risk', 'governance director',
            'chief data officer', 'chief security officer', 'chief sustainability officer',
            'lead director', 'audit committee chair', 'risk committee chair'
        ]
    
    def score_apollo_prospect(self, prospect: ApolloProspect, opportunity_type: str) -> Dict[str, Any]:
        """
        Generate comprehensive AI-powered scoring for an Apollo prospect using enhanced Perplexity services
        
        Args:
            prospect: ApolloProspect object with enriched data
            opportunity_type: Type of opportunity (board_director, executive_position, speaking, etc.)
            
        Returns:
            Dict with enhanced scoring details and final score
        """
        try:
            scoring_result = {
                'final_score': 0.0,
                'component_scores': {},
                'analysis_summary': '',
                'recommendations': [],
                'risk_factors': [],
                'research_insights': {},
                'content_briefs': {},
                'scoring_timestamp': datetime.utcnow().isoformat(),
                'enhanced_analysis': True
            }
            
            # Component 1: Base Apollo Score
            apollo_score = prospect.match_score
            scoring_result['component_scores']['apollo_base'] = apollo_score
            
            # Component 2: Enhanced Company Research (using comprehensive Perplexity services)
            company_score, company_research = self._enhanced_company_research(prospect)
            scoring_result['component_scores']['company_research'] = company_score
            scoring_result['research_insights']['company'] = company_research
            
            # Component 3: Role Relevance Analysis (enhanced)
            role_score, role_analysis = self._enhanced_role_analysis(prospect, opportunity_type)
            scoring_result['component_scores']['role_relevance'] = role_score
            scoring_result['research_insights']['role'] = role_analysis
            
            # Component 4: Market Intelligence Analysis
            market_score, market_intelligence = self._enhanced_market_intelligence(prospect, opportunity_type)
            scoring_result['component_scores']['market_intelligence'] = market_score
            scoring_result['research_insights']['market'] = market_intelligence
            
            # Component 5: AI-Powered Opportunity Analysis
            opportunity_score, opportunity_analysis = self._enhanced_opportunity_analysis(prospect, opportunity_type)
            scoring_result['component_scores']['opportunity_analysis'] = opportunity_score
            scoring_result['research_insights']['opportunity'] = opportunity_analysis
            
            # Calculate enhanced weighted final score
            final_score = (
                apollo_score * self.scoring_weights['apollo_base_score'] +
                company_score * self.scoring_weights['company_research'] +
                role_score * self.scoring_weights['role_relevance'] +
                market_score * self.scoring_weights['market_intelligence'] +
                opportunity_score * self.scoring_weights['opportunity_analysis']
            )
            
            scoring_result['final_score'] = min(final_score, 1.0)  # Cap at 1.0
            
            # Generate enhanced content briefs
            scoring_result['content_briefs'] = self._generate_enhanced_content_briefs(
                prospect, opportunity_type, scoring_result
            )
            
            # Generate enhanced analysis summary and recommendations
            scoring_result['analysis_summary'] = self._generate_enhanced_analysis_summary(
                prospect, opportunity_type, scoring_result
            )
            
            scoring_result['recommendations'] = self._generate_enhanced_recommendations(
                prospect, opportunity_type, scoring_result
            )
            
            scoring_result['risk_factors'] = self._identify_enhanced_risk_factors(
                prospect, scoring_result
            )
            
            logger.info(f"Enhanced AI scoring completed for prospect {prospect.id}: {final_score:.3f}")
            return scoring_result
            
        except Exception as e:
            logger.error(f"Error in enhanced AI prospect scoring: {e}")
            # Fallback to basic scoring if enhanced fails
            try:
                return self._basic_prospect_scoring(prospect, opportunity_type)
            except:
                # Ultimate fallback
                return {
                    'final_score': prospect.match_score,
                    'component_scores': {'apollo_base': prospect.match_score},
                    'analysis_summary': 'Fallback scoring used due to AI analysis error',
                    'recommendations': ['Manual review recommended'],
                    'risk_factors': ['AI analysis unavailable'],
                    'scoring_timestamp': datetime.utcnow().isoformat(),
                    'enhanced_analysis': False,
                    'error': str(e)
                }
    
    # ========================================
    # Enhanced Analysis Methods using Comprehensive Perplexity Services
    # ========================================
    
    def _enhanced_company_research(self, prospect: ApolloProspect) -> Tuple[float, Dict[str, Any]]:
        """
        Enhanced company research using comprehensive Perplexity services
        """
        try:
            if not self.research_service:
                return self._fallback_company_analysis(prospect)
            
            company_name = prospect.company_name
            company_domain = prospect.company_domain
            
            # Conduct comprehensive company research
            research_result = self.research_service.research_company(
                company_name=company_name,
                company_domain=company_domain,
                recency=SearchRecency.WEEK
            )
            
            if research_result:
                # Extract insights and calculate score
                analysis_content = research_result.get('analysis', '')
                score = self._extract_score_from_research(analysis_content)
                
                return score, {
                    'method': 'enhanced_perplexity_research',
                    'research_data': research_result,
                    'governance_indicators': self._extract_governance_indicators(analysis_content),
                    'risk_signals': self._extract_risk_signals(analysis_content),
                    'growth_potential': self._extract_growth_indicators(analysis_content),
                    'score': score
                }
            else:
                return self._fallback_company_analysis(prospect)
                
        except Exception as e:
            logger.error(f"Enhanced company research error: {e}")
            return self._fallback_company_analysis(prospect)
    
    def _enhanced_role_analysis(self, prospect: ApolloProspect, opportunity_type: str) -> Tuple[float, Dict[str, Any]]:
        """
        Enhanced role relevance analysis with executive research
        """
        try:
            base_score, base_analysis = self._analyze_role_relevance(prospect, opportunity_type)
            
            if not self.research_service:
                return base_score, base_analysis
            
            # Conduct executive research for deeper insights
            executive_research = self.research_service.research_executive_opportunity(
                executive_name=prospect.name,
                company_name=prospect.company_name,
                opportunity_type=opportunity_type,
                recency=SearchRecency.WEEK
            )
            
            if executive_research:
                research_content = executive_research.get('analysis', '')
                executive_score = self._extract_score_from_research(research_content)
                
                # Weighted combination of base analysis and executive research
                combined_score = (base_score * 0.6) + (executive_score * 0.4)
                
                return combined_score, {
                    'method': 'enhanced_executive_research',
                    'base_analysis': base_analysis,
                    'executive_research': executive_research,
                    'leadership_experience': self._extract_leadership_indicators(research_content),
                    'governance_expertise': self._extract_governance_expertise(research_content),
                    'industry_reputation': self._extract_reputation_indicators(research_content),
                    'combined_score': combined_score
                }
            else:
                return base_score, base_analysis
                
        except Exception as e:
            logger.error(f"Enhanced role analysis error: {e}")
            return self._analyze_role_relevance(prospect, opportunity_type)
    
    def _enhanced_market_intelligence(self, prospect: ApolloProspect, opportunity_type: str) -> Tuple[float, Dict[str, Any]]:
        """
        Enhanced market intelligence using industry analysis
        """
        try:
            base_score, base_analysis = self._analyze_market_opportunity(prospect, opportunity_type)
            
            if not self.research_service:
                return base_score, base_analysis
            
            industry = self._extract_industry_from_prospect(prospect)
            if not industry:
                return base_score, base_analysis
            
            # Conduct industry analysis
            industry_research = self.research_service.analyze_industry(
                industry=industry,
                focus_areas=['governance', 'risk management', 'board composition', 'regulatory trends'],
                recency=SearchRecency.MONTH
            )
            
            if industry_research:
                research_content = industry_research.get('analysis', '')
                industry_score = self._extract_score_from_research(research_content)
                
                # Weighted combination
                combined_score = (base_score * 0.7) + (industry_score * 0.3)
                
                return combined_score, {
                    'method': 'enhanced_industry_intelligence',
                    'base_analysis': base_analysis,
                    'industry_research': industry_research,
                    'market_trends': self._extract_market_trends(research_content),
                    'regulatory_environment': self._extract_regulatory_factors(research_content),
                    'competitive_landscape': self._extract_competitive_factors(research_content),
                    'combined_score': combined_score
                }
            else:
                return base_score, base_analysis
                
        except Exception as e:
            logger.error(f"Enhanced market intelligence error: {e}")
            return self._analyze_market_opportunity(prospect, opportunity_type)
    
    def _enhanced_opportunity_analysis(self, prospect: ApolloProspect, opportunity_type: str) -> Tuple[float, Dict[str, Any]]:
        """
        AI-powered opportunity analysis using specialized analyzers
        """
        try:
            if not self.opportunity_analyzer:
                return 0.5, {'method': 'fallback', 'note': 'Opportunity analyzer not available'}
            
            company_name = prospect.company_name
            company_domain = prospect.company_domain
            
            analysis_result = None
            
            # Route to appropriate analyzer based on opportunity type
            if opportunity_type in ['board_director', 'governance', 'executive_position']:
                analysis_result = self.opportunity_analyzer.analyze_governance_opportunity(
                    company_name=company_name,
                    company_domain=company_domain
                )
            elif opportunity_type in ['speaking', 'conference', 'webinar']:
                event_context = f"{opportunity_type} opportunity at {company_name}"
                analysis_result = self.opportunity_analyzer.analyze_speaking_opportunity(
                    event_context=event_context,
                    target_audience=self._infer_target_audience(prospect, opportunity_type)
                )
            else:
                # General market entry analysis
                market_segment = f"{self._extract_industry_from_prospect(prospect)} governance consulting"
                analysis_result = self.opportunity_analyzer.analyze_market_entry_opportunity(
                    market_segment=market_segment,
                    focus_areas=['risk management', 'compliance', 'board advisory']
                )
            
            if analysis_result:
                score_key = self._get_score_key_for_opportunity_type(opportunity_type)
                opportunity_score = analysis_result.get(score_key, 0.5)
                
                return opportunity_score, {
                    'method': 'ai_opportunity_analysis',
                    'opportunity_type': opportunity_type,
                    'analysis_result': analysis_result,
                    'strategic_fit': self._assess_strategic_fit(analysis_result),
                    'value_potential': self._assess_value_potential(analysis_result),
                    'execution_feasibility': self._assess_execution_feasibility(analysis_result),
                    'opportunity_score': opportunity_score
                }
            else:
                return 0.5, {'method': 'analyzer_failed', 'opportunity_type': opportunity_type}
                
        except Exception as e:
            logger.error(f"Enhanced opportunity analysis error: {e}")
            return 0.5, {'method': 'error_fallback', 'error': str(e)}
    
    def _generate_enhanced_content_briefs(self, prospect: ApolloProspect, opportunity_type: str, 
                                         scoring_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enhanced content briefs using content generation service
        """
        try:
            if not self.content_service:
                return {'note': 'Content service not available'}
            
            content_briefs = {}
            
            # Generate executive summary
            if scoring_result.get('research_insights'):
                executive_summary = self.content_service.generate_executive_summary(
                    scoring_result['research_insights']
                )
                if executive_summary:
                    content_briefs['executive_summary'] = executive_summary
            
            # Generate opportunity brief
            prospect_data = {
                'name': prospect.name,
                'title': prospect.title,
                'company': prospect.company_name,
                'opportunity_type': opportunity_type,
                'scoring_result': scoring_result
            }
            
            opportunity_brief = self.content_service.generate_opportunity_brief(prospect_data)
            if opportunity_brief:
                content_briefs['opportunity_brief'] = opportunity_brief
            
            # Generate industry insight if we have market research
            if scoring_result.get('research_insights', {}).get('market'):
                market_data = scoring_result['research_insights']['market']
                industry_insight = self.content_service.generate_industry_insight(market_data)
                if industry_insight:
                    content_briefs['industry_insight'] = industry_insight
            
            return content_briefs
            
        except Exception as e:
            logger.error(f"Enhanced content brief generation error: {e}")
            return {'error': str(e)}
    
    def _generate_enhanced_analysis_summary(self, prospect: ApolloProspect, opportunity_type: str,
                                           scoring_result: Dict[str, Any]) -> str:
        """
        Generate enhanced analysis summary with rich insights
        """
        try:
            final_score = scoring_result['final_score']
            company_name = prospect.company_name
            title = prospect.title
            
            # Determine priority level
            if final_score >= 0.8:
                priority = "EXCEPTIONAL OPPORTUNITY"
                recommendation = "Immediate high-priority outreach recommended"
            elif final_score >= 0.7:
                priority = "HIGH PRIORITY OPPORTUNITY"
                recommendation = "Priority outreach within 48 hours"
            elif final_score >= 0.6:
                priority = "STRONG OPPORTUNITY"
                recommendation = "Outreach recommended within 1 week"
            elif final_score >= 0.4:
                priority = "MODERATE OPPORTUNITY"
                recommendation = "Consider for targeted campaign"
            else:
                priority = "LOW PRIORITY"
                recommendation = "Monitor for future developments"
            
            # Extract key insights from research
            research_insights = scoring_result.get('research_insights', {})
            key_insights = []
            
            if research_insights.get('company', {}).get('governance_indicators'):
                key_insights.append("Strong governance profile identified")
            
            if research_insights.get('role', {}).get('leadership_experience'):
                key_insights.append("Proven leadership experience confirmed")
            
            if research_insights.get('market', {}).get('market_trends'):
                key_insights.append("Favorable market conditions detected")
            
            if research_insights.get('opportunity', {}).get('strategic_fit'):
                key_insights.append("High strategic fit assessment")
            
            # Build comprehensive summary
            summary_parts = [
                f"{priority} - AI Score: {final_score:.3f}",
                "",
                f"Prospect: {prospect.name} ({title}) at {company_name}",
                f"Opportunity Type: {opportunity_type.replace('_', ' ').title()}",
                "",
                f"✓ Recommendation: {recommendation}",
                "",
                "🎯 Component Scores:",
                f"• Apollo Base Score: {scoring_result['component_scores'].get('apollo_base', 0):.3f}",
                f"• Company Research: {scoring_result['component_scores'].get('company_research', 0):.3f}",
                f"• Role Relevance: {scoring_result['component_scores'].get('role_relevance', 0):.3f}",
                f"• Market Intelligence: {scoring_result['component_scores'].get('market_intelligence', 0):.3f}",
                f"• Opportunity Analysis: {scoring_result['component_scores'].get('opportunity_analysis', 0):.3f}"
            ]
            
            if key_insights:
                summary_parts.extend([
                    "",
                    "🔍 Key AI Insights:",
                    *[f"• {insight}" for insight in key_insights]
                ])
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Enhanced analysis summary error: {e}")
            return f"Enhanced AI Analysis completed with score: {scoring_result.get('final_score', 0):.3f}"
    
    def _generate_enhanced_recommendations(self, prospect: ApolloProspect, opportunity_type: str,
                                          scoring_result: Dict[str, Any]) -> List[str]:
        """
        Generate enhanced recommendations based on comprehensive analysis
        """
        try:
            recommendations = []
            final_score = scoring_result['final_score']
            research_insights = scoring_result.get('research_insights', {})
            
            # Score-based strategic recommendations
            if final_score >= 0.8:
                recommendations.extend([
                    "🚀 PRIORITY: Schedule C-level meeting within 48 hours",
                    "📊 Prepare comprehensive governance assessment presentation",
                    "🎯 Customize value proposition based on AI research insights",
                    "📞 Consider direct phone outreach for immediate engagement"
                ])
            elif final_score >= 0.6:
                recommendations.extend([
                    "⚡ High-priority outreach within 1 week",
                    "🔍 Conduct deeper company research before approach",
                    "💼 Prepare industry-specific talking points",
                    "📧 Craft personalized email sequence based on research"
                ])
            else:
                recommendations.extend([
                    "📈 Add to nurture campaign for long-term engagement",
                    "👀 Monitor for trigger events and company changes",
                    "🔄 Re-evaluate quarterly with fresh market intelligence"
                ])
            
            # Research-driven recommendations
            if research_insights.get('company', {}).get('governance_indicators'):
                recommendations.append("🏛️ Highlight board governance expertise in approach")
            
            if research_insights.get('company', {}).get('risk_signals'):
                recommendations.append("⚠️ Address potential risk factors proactively")
            
            if research_insights.get('role', {}).get('governance_expertise'):
                recommendations.append("🎓 Emphasize governance credentials alignment")
            
            if research_insights.get('market', {}).get('regulatory_environment'):
                recommendations.append("📋 Focus on regulatory compliance value proposition")
            
            # Opportunity-specific recommendations
            if opportunity_type == 'board_director':
                recommendations.extend([
                    "📋 Prepare board readiness assessment",
                    "🏆 Reference relevant board experience and credentials",
                    "📈 Highlight ESG and governance expertise"
                ])
            elif opportunity_type in ['speaking', 'conference']:
                recommendations.extend([
                    "🎤 Propose specific speaking topics aligned with company challenges",
                    "📊 Offer to share relevant case studies and insights",
                    "🤝 Suggest workshop or extended engagement opportunities"
                ])
            
            # Contact method recommendations
            if prospect.email:
                recommendations.append("📧 Email contact available - primary engagement channel")
            if prospect.linkedin_url:
                recommendations.append("💼 LinkedIn profile available - social engagement opportunity")
            if prospect.phone:
                recommendations.append("📱 Phone contact available - consider direct outreach")
            
            return recommendations[:12]  # Limit to top 12 recommendations
            
        except Exception as e:
            logger.error(f"Enhanced recommendations error: {e}")
            return ["Manual review recommended due to analysis error"]
    
    def _identify_enhanced_risk_factors(self, prospect: ApolloProspect, scoring_result: Dict[str, Any]) -> List[str]:
        """
        Identify enhanced risk factors using comprehensive analysis
        """
        try:
            risk_factors = []
            research_insights = scoring_result.get('research_insights', {})
            
            # Contact-related risks
            if not prospect.email:
                risk_factors.append("❌ No email address available - limited outreach options")
            
            if not prospect.phone and not prospect.linkedin_url:
                risk_factors.append("📞 Limited contact methods available")
            
            # Research-based risk factors
            if research_insights.get('company', {}).get('risk_signals'):
                risk_factors.append("⚠️ Company risk signals identified in research")
            
            if research_insights.get('market', {}).get('competitive_landscape', {}).get('high_competition'):
                risk_factors.append("🏁 High competition in target market segment")
            
            if research_insights.get('opportunity', {}).get('execution_feasibility', 0) < 0.5:
                risk_factors.append("🚧 Low execution feasibility assessment")
            
            # Score-based risk assessment
            component_scores = scoring_result.get('component_scores', {})
            if component_scores.get('company_research', 0) < 0.4:
                risk_factors.append("🔍 Limited company intelligence available")
            
            if component_scores.get('market_intelligence', 0) < 0.4:
                risk_factors.append("📊 Uncertain market conditions")
            
            # Industry-specific risks
            industry = self._extract_industry_from_prospect(prospect)
            if industry and 'cryptocurrency' in industry.lower():
                risk_factors.append("💰 High-risk cryptocurrency industry exposure")
            
            if industry and any(term in industry.lower() for term in ['startup', 'early-stage']):
                risk_factors.append("🚀 Early-stage company stability concerns")
            
            return risk_factors[:8]  # Limit to top 8 risk factors
            
        except Exception as e:
            logger.error(f"Enhanced risk factors identification error: {e}")
            return ["Risk assessment unavailable due to analysis error"]
    
    def _basic_prospect_scoring(self, prospect: ApolloProspect, opportunity_type: str) -> Dict[str, Any]:
        """
        Fallback to basic prospect scoring when enhanced services are unavailable
        """
        try:
            # Use original scoring logic as fallback
            scoring_result = {
                'final_score': 0.0,
                'component_scores': {},
                'analysis_summary': '',
                'recommendations': [],
                'risk_factors': [],
                'scoring_timestamp': datetime.utcnow().isoformat(),
                'enhanced_analysis': False
            }
            
            # Basic scoring components
            apollo_score = prospect.match_score
            scoring_result['component_scores']['apollo_base'] = apollo_score
            
            company_score, company_analysis = self._fallback_company_analysis(prospect)
            scoring_result['component_scores']['company_analysis'] = company_score
            
            role_score, role_analysis = self._analyze_role_relevance(prospect, opportunity_type)
            scoring_result['component_scores']['role_relevance'] = role_score
            
            market_score, market_analysis = self._analyze_market_opportunity(prospect, opportunity_type)
            scoring_result['component_scores']['market_opportunity'] = market_score
            
            # Calculate basic weighted score
            final_score = (
                apollo_score * 0.25 +
                company_score * 0.30 +
                role_score * 0.25 +
                market_score * 0.20
            )
            
            scoring_result['final_score'] = min(final_score, 1.0)
            
            # Basic summaries
            scoring_result['analysis_summary'] = self._generate_analysis_summary(
                prospect, opportunity_type, scoring_result
            )
            scoring_result['recommendations'] = self._generate_recommendations(
                prospect, opportunity_type, scoring_result
            )
            scoring_result['risk_factors'] = self._identify_risk_factors(
                prospect, scoring_result
            )
            
            return scoring_result
            
        except Exception as e:
            logger.error(f"Basic prospect scoring error: {e}")
            return {
                'final_score': prospect.match_score,
                'component_scores': {'apollo_base': prospect.match_score},
                'analysis_summary': 'Basic fallback scoring used',
                'recommendations': ['Manual review recommended'],
                'risk_factors': ['Limited analysis available'],
                'scoring_timestamp': datetime.utcnow().isoformat(),
                'enhanced_analysis': False,
                'error': str(e)
            }
    
    # ========================================
    # Helper Methods for Enhanced Analysis
    # ========================================
    
    def _extract_score_from_research(self, research_content: str) -> float:
        """Extract numerical score from research content"""
        try:
            import re
            
            # Look for various score patterns
            patterns = [
                r'score[:\s]*([0-1]\.?\d*)',
                r'([0-1]\.\d+)',
                r'(\d+)/10',
                r'(\d+)%',
                r'rating[:\s]*([0-1]\.?\d*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, research_content.lower())
                if matches:
                    score_str = matches[0]
                    if '/' in score_str:
                        score = float(score_str.split('/')[0]) / 10
                    elif '%' in score_str:
                        score = float(score_str.replace('%', '')) / 100
                    else:
                        score = float(score_str)
                    return min(max(score, 0.0), 1.0)
            
            # Sentiment-based scoring fallback
            return self._sentiment_score(research_content)
            
        except Exception as e:
            logger.error(f"Score extraction error: {e}")
            return 0.5
    
    def _sentiment_score(self, text: str) -> float:
        """Calculate sentiment-based score from text"""
        positive_indicators = [
            'strong', 'excellent', 'outstanding', 'robust', 'solid', 'impressive',
            'growing', 'expanding', 'successful', 'leading', 'profitable', 'stable'
        ]
        
        negative_indicators = [
            'weak', 'poor', 'declining', 'struggling', 'challenging', 'risky',
            'unstable', 'concerning', 'problematic', 'limited', 'difficult'
        ]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_indicators if word in text_lower)
        negative_count = sum(1 for word in negative_indicators if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.5
        
        sentiment_ratio = positive_count / (positive_count + negative_count)
        return min(max(sentiment_ratio, 0.0), 1.0)
    
    def _extract_governance_indicators(self, content: str) -> List[str]:
        """Extract governance-related indicators from research content"""
        indicators = []
        content_lower = content.lower()
        
        governance_terms = [
            'board', 'governance', 'compliance', 'audit', 'risk management',
            'regulatory', 'ethics', 'oversight', 'transparency', 'accountability'
        ]
        
        for term in governance_terms:
            if term in content_lower:
                indicators.append(term.title())
        
        return indicators[:5]  # Top 5 indicators
    
    def _extract_risk_signals(self, content: str) -> List[str]:
        """Extract risk signals from research content"""
        signals = []
        content_lower = content.lower()
        
        risk_terms = [
            'lawsuit', 'investigation', 'fine', 'penalty', 'violation',
            'scandal', 'controversy', 'bankruptcy', 'layoffs', 'restructuring'
        ]
        
        for term in risk_terms:
            if term in content_lower:
                signals.append(term.title())
        
        return signals[:3]  # Top 3 signals
    
    def _extract_growth_indicators(self, content: str) -> List[str]:
        """Extract growth indicators from research content"""
        indicators = []
        content_lower = content.lower()
        
        growth_terms = [
            'expansion', 'growth', 'acquisition', 'merger', 'funding',
            'investment', 'new market', 'innovation', 'digital transformation'
        ]
        
        for term in growth_terms:
            if term in content_lower:
                indicators.append(term.title())
        
        return indicators[:5]  # Top 5 indicators
    
    def _extract_leadership_indicators(self, content: str) -> List[str]:
        """Extract leadership experience indicators"""
        indicators = []
        content_lower = content.lower()
        
        leadership_terms = [
            'ceo', 'president', 'founder', 'director', 'board',
            'chairman', 'leadership', 'executive', 'management'
        ]
        
        for term in leadership_terms:
            if term in content_lower:
                indicators.append(term.upper() if term in ['ceo'] else term.title())
        
        return list(set(indicators))[:5]  # Unique top 5 indicators
    
    def _extract_governance_expertise(self, content: str) -> List[str]:
        """Extract governance expertise indicators"""
        expertise = []
        content_lower = content.lower()
        
        expertise_terms = [
            'governance', 'compliance', 'audit', 'risk', 'regulatory',
            'ethics', 'esg', 'sustainability', 'cybersecurity'
        ]
        
        for term in expertise_terms:
            if term in content_lower:
                expertise.append(term.title())
        
        return list(set(expertise))[:5]  # Unique top 5 expertise areas
    
    def _extract_reputation_indicators(self, content: str) -> List[str]:
        """Extract reputation indicators"""
        indicators = []
        content_lower = content.lower()
        
        reputation_terms = [
            'award', 'recognition', 'speaker', 'author', 'expert',
            'thought leader', 'industry leader', 'respected'
        ]
        
        for term in reputation_terms:
            if term in content_lower:
                indicators.append(term.title())
        
        return list(set(indicators))[:5]
    
    def _extract_market_trends(self, content: str) -> List[str]:
        """Extract market trend indicators"""
        trends = []
        content_lower = content.lower()
        
        trend_terms = [
            'digital transformation', 'ai', 'automation', 'sustainability',
            'esg', 'remote work', 'cybersecurity', 'data privacy'
        ]
        
        for term in trend_terms:
            if term in content_lower:
                trends.append(term.title())
        
        return list(set(trends))[:5]
    
    def _extract_regulatory_factors(self, content: str) -> List[str]:
        """Extract regulatory environment factors"""
        factors = []
        content_lower = content.lower()
        
        regulatory_terms = [
            'regulation', 'compliance', 'gdpr', 'sox', 'sec',
            'regulatory change', 'policy', 'legislation'
        ]
        
        for term in regulatory_terms:
            if term in content_lower:
                factors.append(term.upper() if term in ['gdpr', 'sox', 'sec'] else term.title())
        
        return list(set(factors))[:5]
    
    def _extract_competitive_factors(self, content: str) -> List[str]:
        """Extract competitive landscape factors"""
        factors = []
        content_lower = content.lower()
        
        competitive_terms = [
            'competition', 'market leader', 'competitive advantage',
            'differentiation', 'market share', 'consolidation'
        ]
        
        for term in competitive_terms:
            if term in content_lower:
                factors.append(term.title())
        
        return list(set(factors))[:5]
    
    def _infer_target_audience(self, prospect: ApolloProspect, opportunity_type: str) -> str:
        """Infer target audience for speaking opportunities"""
        industry = self._extract_industry_from_prospect(prospect)
        if industry:
            return f"{industry} executives and board members"
        return "Senior executives and governance professionals"
    
    def _get_score_key_for_opportunity_type(self, opportunity_type: str) -> str:
        """Get the appropriate score key based on opportunity type"""
        score_key_map = {
            'board_director': 'governance_score',
            'governance': 'governance_score',
            'executive_position': 'governance_score',
            'speaking': 'opportunity_score',
            'conference': 'opportunity_score',
            'webinar': 'opportunity_score'
        }
        return score_key_map.get(opportunity_type, 'entry_score')
    
    def _assess_strategic_fit(self, analysis_result: Dict[str, Any]) -> float:
        """Assess strategic fit from analysis result"""
        try:
            # Look for strategic fit indicators in the analysis
            analysis_content = str(analysis_result.get('analysis', ''))
            return self._sentiment_score(analysis_content)
        except:
            return 0.5
    
    def _assess_value_potential(self, analysis_result: Dict[str, Any]) -> float:
        """Assess value potential from analysis result"""
        try:
            analysis_content = str(analysis_result.get('analysis', ''))
            value_indicators = ['high value', 'significant', 'substantial', 'profitable', 'revenue']
            content_lower = analysis_content.lower()
            
            value_score = sum(0.2 for indicator in value_indicators if indicator in content_lower)
            return min(value_score, 1.0)
        except:
            return 0.5
    
    def _assess_execution_feasibility(self, analysis_result: Dict[str, Any]) -> float:
        """Assess execution feasibility from analysis result"""
        try:
            analysis_content = str(analysis_result.get('analysis', ''))
            feasibility_indicators = ['feasible', 'achievable', 'realistic', 'practical']
            barrier_indicators = ['difficult', 'challenging', 'barriers', 'obstacles']
            
            content_lower = analysis_content.lower()
            
            positive_score = sum(0.25 for indicator in feasibility_indicators if indicator in content_lower)
            negative_score = sum(0.25 for indicator in barrier_indicators if indicator in content_lower)
            
            return min(max(0.5 + positive_score - negative_score, 0.0), 1.0)
        except:
            return 0.5
    
    def _analyze_company_with_ai(self, prospect: ApolloProspect) -> Tuple[float, Dict[str, Any]]:
        """
        Use AI to analyze the prospect's company for governance and risk management needs
        """
        try:
            if not self.perplexity_api_key:
                return self._fallback_company_analysis(prospect)
            
            # Prepare company analysis prompt
            company_name = prospect.company_name
            domain = prospect.company_domain or ""
            industry = self._extract_industry_from_prospect(prospect)
            
            prompt = f"""
            Analyze the company "{company_name}" (domain: {domain}) for governance, risk management, and AI governance opportunities.
            
            Please evaluate:
            1. Company size and market position
            2. Industry risk profile and regulatory requirements
            3. Potential need for governance, risk, and compliance (GRC) services
            4. AI/technology adoption and governance needs
            5. Board composition and governance maturity
            6. Recent regulatory challenges or opportunities
            
            Provide a score from 0-1 indicating the likelihood this company would benefit from:
            - Board director expertise
            - Risk management consulting
            - AI governance advisory services
            - Speaking engagements on governance topics
            
            Focus on factual information about the company's business model, industry, and known governance needs.
            """
            
            # Call Perplexity API
            ai_response = self._call_perplexity_api(prompt)
            
            if ai_response:
                # Parse the AI response and extract score
                analysis_score = self._parse_company_analysis_score(ai_response)
                
                return analysis_score, {
                    'ai_analysis': ai_response,
                    'industry_classification': industry,
                    'governance_needs_identified': True,
                    'analysis_method': 'perplexity_ai'
                }
            else:
                return self._fallback_company_analysis(prospect)
                
        except Exception as e:
            logger.error(f"Error in AI company analysis: {e}")
            return self._fallback_company_analysis(prospect)
    
    def _analyze_role_relevance(self, prospect: ApolloProspect, opportunity_type: str) -> Tuple[float, Dict[str, Any]]:
        """
        Analyze how relevant the prospect's role is to our target opportunity type
        """
        try:
            title = prospect.title.lower()
            seniority = prospect.seniority or ""
            
            relevance_score = 0.0
            analysis = {
                'title_match': False,
                'seniority_match': False,
                'experience_indicators': [],
                'role_alignment': 'low'
            }
            
            # Check title relevance
            if opportunity_type == 'board_director':
                if any(keyword in title for keyword in ['board', 'director', 'chairman', 'trustee']):
                    relevance_score += 0.4
                    analysis['title_match'] = True
                elif any(keyword in title for keyword in ['ceo', 'president', 'founder']):
                    relevance_score += 0.3
                    analysis['experience_indicators'].append('C-suite experience')
            
            elif opportunity_type == 'executive_position':
                if any(keyword in title for keyword in ['chief', 'head of', 'vp', 'vice president']):
                    relevance_score += 0.4
                    analysis['title_match'] = True
                if any(keyword in title for keyword in ['risk', 'compliance', 'audit', 'governance']):
                    relevance_score += 0.3
                    analysis['experience_indicators'].append('GRC expertise')
            
            # Check seniority alignment
            if seniority.lower() in ['c_suite', 'owner', 'founder', 'partner']:
                relevance_score += 0.2
                analysis['seniority_match'] = True
            elif seniority.lower() in ['vp', 'head', 'director']:
                relevance_score += 0.15
                analysis['seniority_match'] = True
            
            # Industry-specific role bonuses
            if any(keyword in title for keyword in ['ai', 'artificial intelligence', 'machine learning']):
                relevance_score += 0.2
                analysis['experience_indicators'].append('AI/ML experience')
            
            if any(keyword in title for keyword in ['cyber', 'security', 'privacy']):
                relevance_score += 0.15
                analysis['experience_indicators'].append('Cybersecurity experience')
            
            # Determine role alignment level
            if relevance_score >= 0.7:
                analysis['role_alignment'] = 'high'
            elif relevance_score >= 0.4:
                analysis['role_alignment'] = 'medium'
            else:
                analysis['role_alignment'] = 'low'
            
            return min(relevance_score, 1.0), analysis
            
        except Exception as e:
            logger.error(f"Error in role relevance analysis: {e}")
            return 0.5, {'error': str(e), 'role_alignment': 'unknown'}
    
    def _analyze_market_opportunity(self, prospect: ApolloProspect, opportunity_type: str) -> Tuple[float, Dict[str, Any]]:
        """
        Analyze the market opportunity size and potential for this prospect
        """
        try:
            # Extract company size indicators
            company_size = self._estimate_company_size_from_prospect(prospect)
            industry = self._extract_industry_from_prospect(prospect)
            
            market_score = 0.0
            analysis = {
                'company_size_category': company_size,
                'industry': industry,
                'revenue_potential': 'unknown',
                'market_factors': []
            }
            
            # Company size scoring
            size_scores = {
                'enterprise': 0.4,      # 10,000+ employees
                'large': 0.3,           # 1,000-10,000 employees
                'medium': 0.2,          # 100-1,000 employees
                'small': 0.1            # <100 employees
            }
            market_score += size_scores.get(company_size, 0.1)
            
            # Industry relevance scoring
            if industry and any(ind in industry.lower() for ind in self.high_relevance_industries):
                market_score += 0.3
                analysis['market_factors'].append('High-relevance industry')
            
            # Opportunity type specific scoring
            if opportunity_type == 'board_director':
                if company_size in ['enterprise', 'large']:
                    market_score += 0.2
                    analysis['revenue_potential'] = 'high'
                    analysis['market_factors'].append('Large company board opportunity')
            
            elif opportunity_type == 'executive_position':
                if company_size in ['enterprise', 'large', 'medium']:
                    market_score += 0.15
                    analysis['revenue_potential'] = 'medium-high'
                    analysis['market_factors'].append('Substantial executive opportunity')
            
            # Technology/AI companies get bonus for AI governance opportunities
            if industry and any(tech in industry.lower() for tech in ['technology', 'software', 'ai', 'artificial intelligence']):
                market_score += 0.15
                analysis['market_factors'].append('Technology sector AI governance needs')
            
            return min(market_score, 1.0), analysis
            
        except Exception as e:
            logger.error(f"Error in market opportunity analysis: {e}")
            return 0.5, {'error': str(e)}
    
    def _call_perplexity_api(self, prompt: str) -> Optional[str]:
        """
        Call Perplexity API for AI analysis
        """
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            
            return None
            
        except Exception as e:
            logger.error(f"Error calling Perplexity API: {e}")
            return None
    
    def _parse_company_analysis_score(self, ai_response: str) -> float:
        """
        Parse AI response to extract company analysis score
        """
        try:
            # Look for numerical scores in the response
            import re
            
            # Look for patterns like "0.8", "Score: 0.7", etc.
            score_patterns = [
                r'score[:\s]*([0-1]\.?\d*)',
                r'([0-1]\.\d+)',
                r'(\d+)/10',
                r'(\d+)%'
            ]
            
            for pattern in score_patterns:
                matches = re.findall(pattern, ai_response.lower())
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
            
            # Fallback: analyze sentiment and keywords
            response_lower = ai_response.lower()
            sentiment_score = 0.5  # Default
            
            positive_indicators = ['high potential', 'strong candidate', 'excellent fit', 'significant opportunity']
            negative_indicators = ['low potential', 'poor fit', 'limited opportunity', 'not suitable']
            
            for indicator in positive_indicators:
                if indicator in response_lower:
                    sentiment_score += 0.1
            
            for indicator in negative_indicators:
                if indicator in response_lower:
                    sentiment_score -= 0.1
            
            return min(max(sentiment_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error parsing AI analysis score: {e}")
            return 0.5
    
    def _fallback_company_analysis(self, prospect: ApolloProspect) -> Tuple[float, Dict[str, Any]]:
        """
        Fallback company analysis when AI is not available
        """
        score = 0.5  # Default neutral score
        analysis = {
            'analysis_method': 'rule_based_fallback',
            'company_size_factor': 0.0,
            'industry_factor': 0.0
        }
        
        # Estimate based on available data
        company_size = self._estimate_company_size_from_prospect(prospect)
        if company_size in ['enterprise', 'large']:
            score += 0.2
            analysis['company_size_factor'] = 0.2
        
        industry = self._extract_industry_from_prospect(prospect)
        if industry and any(ind in industry.lower() for ind in self.high_relevance_industries):
            score += 0.2
            analysis['industry_factor'] = 0.2
        
        return min(score, 1.0), analysis
    
    def _extract_industry_from_prospect(self, prospect: ApolloProspect) -> Optional[str]:
        """
        Extract industry information from prospect data
        """
        if prospect.raw_data and 'organization' in prospect.raw_data:
            org_data = prospect.raw_data['organization']
            return org_data.get('industry') or org_data.get('primary_industry')
        return None
    
    def _estimate_company_size_from_prospect(self, prospect: ApolloProspect) -> str:
        """
        Estimate company size category from prospect data
        """
        if prospect.raw_data and 'organization' in prospect.raw_data:
            org_data = prospect.raw_data['organization']
            employee_count = org_data.get('estimated_num_employees', 0)
            
            if employee_count >= 10000:
                return 'enterprise'
            elif employee_count >= 1000:
                return 'large'
            elif employee_count >= 100:
                return 'medium'
            else:
                return 'small'
        
        return 'unknown'
    
    def _generate_analysis_summary(self, prospect: ApolloProspect, opportunity_type: str, scoring_result: Dict) -> str:
        """
        Generate a human-readable analysis summary
        """
        try:
            final_score = scoring_result['final_score']
            company_name = prospect.company_name
            title = prospect.title
            
            if final_score >= 0.8:
                priority = "HIGH PRIORITY"
                recommendation = "Immediate outreach recommended"
            elif final_score >= 0.6:
                priority = "MEDIUM-HIGH PRIORITY"  
                recommendation = "Strong candidate for outreach"
            elif final_score >= 0.4:
                priority = "MEDIUM PRIORITY"
                recommendation = "Consider for targeted campaign"
            else:
                priority = "LOW PRIORITY"
                recommendation = "Monitor for future opportunities"
            
            summary = f"""
            {priority} OPPORTUNITY - Score: {final_score:.2f}
            
            Prospect: {prospect.name} ({title}) at {company_name}
            Opportunity Type: {opportunity_type.replace('_', ' ').title()}
            
            {recommendation}
            
            Key Insights:
            - Apollo Match Score: {scoring_result['component_scores'].get('apollo_base', 0):.2f}
            - Company Analysis: {scoring_result['component_scores'].get('company_analysis', 0):.2f}
            - Role Relevance: {scoring_result['component_scores'].get('role_relevance', 0):.2f}
            - Market Opportunity: {scoring_result['component_scores'].get('market_opportunity', 0):.2f}
            """
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
            return f"Analysis completed with score: {scoring_result.get('final_score', 0):.2f}"
    
    def _generate_recommendations(self, prospect: ApolloProspect, opportunity_type: str, scoring_result: Dict) -> List[str]:
        """
        Generate actionable recommendations based on scoring
        """
        recommendations = []
        final_score = scoring_result['final_score']
        
        # Score-based recommendations
        if final_score >= 0.8:
            recommendations.extend([
                "Priority outreach within 24-48 hours",
                "Research recent company developments",
                "Prepare personalized value proposition"
            ])
        elif final_score >= 0.6:
            recommendations.extend([
                "Schedule outreach within 1 week",
                "Review LinkedIn activity and connections",
                "Craft targeted messaging based on role"
            ])
        
        # Contact-specific recommendations
        if prospect.email:
            recommendations.append("Email contact available - primary outreach channel")
        if prospect.linkedin_url:
            recommendations.append("LinkedIn profile available - social engagement opportunity")
        if prospect.phone:
            recommendations.append("Phone contact available - consider direct outreach")
        
        # Opportunity-specific recommendations
        if opportunity_type == 'board_director':
            recommendations.extend([
                "Highlight board governance expertise",
                "Reference AI governance and risk management experience",
                "Prepare board readiness assessment"
            ])
        elif opportunity_type == 'executive_position':
            recommendations.extend([
                "Focus on GRC consulting capabilities",
                "Prepare industry-specific risk assessment",
                "Highlight regulatory compliance expertise"
            ])
        
        return recommendations[:8]  # Limit to top 8 recommendations
    
    def _identify_risk_factors(self, prospect: ApolloProspect, scoring_result: Dict) -> List[str]:
        """
        Identify potential risk factors in the opportunity
        """
        risk_factors = []
        
        # Email-related risks
        email_status = None
        if prospect.raw_data:
            email_status = prospect.raw_data.get('email_status')
        
        if not prospect.email:
            risk_factors.append("No email address available")
        elif email_status == 'unverified':
            risk_factors.append("Email address not verified")
        elif email_status == 'unavailable':
            risk_factors.append("Email marked as unavailable")
        
        # Company-related risks
        company_size = self._estimate_company_size_from_prospect(prospect)
        if company_size == 'small':
            risk_factors.append("Small company - limited budget potential")
        
        # Score-related risks
        apollo_score = scoring_result['component_scores'].get('apollo_base', 0)
        if apollo_score < 0.3:
            risk_factors.append("Low initial Apollo match score")
        
        role_score = scoring_result['component_scores'].get('role_relevance', 0)
        if role_score < 0.4:
            risk_factors.append("Role may not align well with services")
        
        # Generic risks
        if not prospect.linkedin_url:
            risk_factors.append("No LinkedIn profile for social proof")
        
        return risk_factors[:5]  # Limit to top 5 risk factors


# Convenience function for creating scorer
def create_ai_scorer() -> AIOpportunityScorer:
    """
    Create AI opportunity scorer instance
    
    Returns:
        AIOpportunityScorer instance
    """
    return AIOpportunityScorer()