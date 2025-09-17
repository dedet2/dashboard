"""
LinkedIn Lead Qualification Engine
Advanced AI-powered lead qualification system that integrates Apollo.io data, 
LinkedIn profiles, and Perplexity research for enhanced targeting and scoring
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import re
from enum import Enum

from database import db, ExecutiveOpportunity
from linkedin_models import LinkedInLead, LinkedInCampaign
from apollo_integration import ApolloAPIWrapper, ApolloProspect
from perplexity_service import PerplexityResearchService, PerplexityAPI
from ai_scoring_service import AIOpportunityScorer, create_ai_scorer

logger = logging.getLogger(__name__)

class QualificationLevel(Enum):
    """Lead qualification levels"""
    UNQUALIFIED = "unqualified"
    DEVELOPING = "developing" 
    POTENTIAL = "potential"
    QUALIFIED = "qualified"
    HOT_LEAD = "hot_lead"

class OpportunityType(Enum):
    """Executive opportunity types for matching"""
    BOARD_DIRECTOR = "board_director"
    BOARD_ADVISOR = "board_advisor"
    CONSULTANT = "consultant"
    SPEAKER = "speaker"
    INTERIM_EXECUTIVE = "interim_executive"
    STRATEGIC_ADVISOR = "strategic_advisor"
    INVESTOR = "investor"
    PARTNERSHIP = "partnership"

@dataclass
class QualificationCriteria:
    """Criteria for lead qualification"""
    min_lead_score: float = 60.0
    min_engagement_score: float = 40.0
    required_titles: Optional[List[str]] = None
    required_industries: Optional[List[str]] = None
    min_company_size: Optional[str] = None
    min_seniority_level: int = 3  # 1=Entry, 5=C-Suite
    email_verified: bool = True
    linkedin_premium: bool = False
    recent_activity_days: int = 90

@dataclass 
class QualificationResult:
    """Result of lead qualification process"""
    lead_id: str
    qualification_level: QualificationLevel
    overall_score: float
    component_scores: Dict[str, float]
    opportunity_matches: List[Dict[str, Any]]
    qualification_reasons: List[str]
    disqualification_reasons: List[str]
    recommended_actions: List[str]
    confidence_score: float
    next_review_date: datetime

class LinkedInQualificationEngine:
    """
    Advanced lead qualification engine using AI scoring and multi-source data integration
    """
    
    def __init__(self, apollo_api: Optional[ApolloAPIWrapper] = None,
                 perplexity_api: Optional[PerplexityAPI] = None,
                 ai_scorer: Optional[AIOpportunityScorer] = None):
        self.apollo_api = apollo_api
        self.perplexity_api = perplexity_api
        self.perplexity_research = PerplexityResearchService(perplexity_api) if perplexity_api else None
        self.ai_scorer = ai_scorer or create_ai_scorer()
        
        # Qualification model weights and thresholds
        self.qualification_weights = {
            'profile_completeness': 0.15,
            'apollo_enrichment': 0.20,
            'title_relevance': 0.25,
            'company_quality': 0.20,
            'engagement_potential': 0.10,
            'research_insights': 0.10
        }
        
        # Executive opportunity matching weights
        self.opportunity_matching_weights = {
            'title_match': 0.30,
            'industry_experience': 0.25,
            'company_stage': 0.20,
            'network_potential': 0.15,
            'availability_signals': 0.10
        }
        
        # Initialize qualification thresholds
        self.qualification_thresholds = {
            QualificationLevel.HOT_LEAD: 90.0,
            QualificationLevel.QUALIFIED: 75.0,
            QualificationLevel.POTENTIAL: 60.0,
            QualificationLevel.DEVELOPING: 40.0,
            QualificationLevel.UNQUALIFIED: 0.0
        }
        
        # Industry relevance mapping for different opportunity types
        self.industry_relevance = {
            OpportunityType.BOARD_DIRECTOR: {
                'financial_services': 1.0,
                'healthcare': 0.9,
                'technology': 0.9,
                'manufacturing': 0.8,
                'retail': 0.7,
                'consulting': 0.6
            },
            OpportunityType.CONSULTANT: {
                'consulting': 1.0,
                'financial_services': 0.9,
                'technology': 0.8,
                'healthcare': 0.8,
                'manufacturing': 0.7
            },
            OpportunityType.SPEAKER: {
                'technology': 1.0,
                'financial_services': 0.9,
                'consulting': 0.9,
                'healthcare': 0.8,
                'education': 0.8
            }
        }
    
    def qualify_lead(self, lead_id: str, qualification_criteria: Optional[QualificationCriteria] = None) -> QualificationResult:
        """
        Perform comprehensive lead qualification
        
        Args:
            lead_id: LinkedIn lead ID to qualify
            qualification_criteria: Optional custom qualification criteria
            
        Returns:
            QualificationResult with detailed scoring and recommendations
        """
        try:
            # Get lead data
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Use default criteria if none provided
            criteria = qualification_criteria or QualificationCriteria()
            
            # Calculate component scores
            component_scores = {}
            
            # 1. Profile completeness score
            component_scores['profile_completeness'] = self._score_profile_completeness(lead)
            
            # 2. Apollo enrichment score
            component_scores['apollo_enrichment'] = self._score_apollo_enrichment(lead)
            
            # 3. Title relevance score
            component_scores['title_relevance'] = self._score_title_relevance(lead)
            
            # 4. Company quality score
            component_scores['company_quality'] = self._score_company_quality(lead)
            
            # 5. Engagement potential score
            component_scores['engagement_potential'] = self._score_engagement_potential(lead)
            
            # 6. Research insights score
            component_scores['research_insights'] = self._score_research_insights(lead)
            
            # Calculate overall score
            overall_score = sum(
                score * self.qualification_weights[component]
                for component, score in component_scores.items()
            )
            
            # Determine qualification level
            qualification_level = self._determine_qualification_level(overall_score)
            
            # Find opportunity matches
            opportunity_matches = self._find_opportunity_matches(lead)
            
            # Generate qualification reasons
            qualification_reasons = self._generate_qualification_reasons(lead, component_scores)
            disqualification_reasons = self._generate_disqualification_reasons(lead, component_scores, criteria)
            
            # Generate recommended actions
            recommended_actions = self._generate_recommended_actions(lead, qualification_level, component_scores)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(component_scores, lead)
            
            # Determine next review date
            next_review_date = self._calculate_next_review_date(qualification_level)
            
            # Create qualification result
            result = QualificationResult(
                lead_id=lead_id,
                qualification_level=qualification_level,
                overall_score=overall_score,
                component_scores=component_scores,
                opportunity_matches=opportunity_matches,
                qualification_reasons=qualification_reasons,
                disqualification_reasons=disqualification_reasons,
                recommended_actions=recommended_actions,
                confidence_score=confidence_score,
                next_review_date=next_review_date
            )
            
            # Update lead with qualification results
            self._update_lead_qualification(lead, result)
            
            logger.info(f"Qualified lead {lead_id}: {qualification_level.value} (score: {overall_score:.1f})")
            return result
            
        except Exception as e:
            logger.error(f"Error qualifying lead {lead_id}: {e}")
            raise
    
    def batch_qualify_leads(self, campaign_id: str, limit: Optional[int] = None) -> List[QualificationResult]:
        """
        Qualify multiple leads in a campaign
        
        Args:
            campaign_id: Campaign ID to qualify leads for
            limit: Optional limit on number of leads to process
            
        Returns:
            List of QualificationResult objects
        """
        try:
            # Get unqualified leads from campaign
            query = LinkedInLead.query.filter_by(campaign_id=campaign_id)
            
            # Filter for leads that need qualification
            query = query.filter(
                (LinkedInLead.qualification_status.is_(None)) |
                (LinkedInLead.last_updated < datetime.utcnow() - timedelta(days=7))
            )
            
            if limit:
                query = query.limit(limit)
            
            leads = query.all()
            
            results = []
            for lead in leads:
                try:
                    result = self.qualify_lead(lead.lead_id)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error qualifying lead {lead.lead_id}: {e}")
                    continue
            
            logger.info(f"Batch qualified {len(results)} leads for campaign {campaign_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch qualification: {e}")
            return []
    
    def enrich_and_qualify(self, lead_id: str) -> QualificationResult:
        """
        Enrich lead with Apollo data and then qualify
        
        Args:
            lead_id: LinkedIn lead ID to enrich and qualify
            
        Returns:
            QualificationResult after enrichment
        """
        try:
            # First enrich with Apollo data
            if self.apollo_api:
                self._enrich_lead_with_apollo(lead_id)
            
            # Then enrich with Perplexity research
            if self.perplexity_research:
                self._research_lead_with_perplexity(lead_id)
            
            # Finally qualify the enriched lead
            return self.qualify_lead(lead_id)
            
        except Exception as e:
            logger.error(f"Error in enrich and qualify for lead {lead_id}: {e}")
            raise
    
    def find_best_opportunity_match(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Find the best executive opportunity match for a qualified lead
        
        Args:
            lead_id: LinkedIn lead ID
            
        Returns:
            Dictionary with best opportunity match details or None
        """
        try:
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                return None
            
            # Find all potential opportunity matches
            opportunity_matches = self._find_opportunity_matches(lead)
            
            if not opportunity_matches:
                return None
            
            # Return the highest scoring match
            best_match = max(opportunity_matches, key=lambda x: x['match_score'])
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding opportunity match for lead {lead_id}: {e}")
            return None
    
    def requalify_lead(self, lead_id: str, force_research: bool = False) -> QualificationResult:
        """
        Re-qualify an existing lead with updated data
        
        Args:
            lead_id: LinkedIn lead ID to re-qualify
            force_research: Whether to force new Perplexity research
            
        Returns:
            Updated QualificationResult
        """
        try:
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Update research if requested or if old
            if force_research or self._needs_research_update(lead):
                if self.perplexity_research:
                    self._research_lead_with_perplexity(lead_id)
            
            # Re-qualify with updated data
            result = self.qualify_lead(lead_id)
            
            logger.info(f"Re-qualified lead {lead_id}: {result.qualification_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error re-qualifying lead {lead_id}: {e}")
            raise
    
    # === PRIVATE SCORING METHODS ===
    
    def _score_profile_completeness(self, lead: LinkedInLead) -> float:
        """Score based on LinkedIn profile completeness"""
        try:
            score = 0.0
            max_score = 100.0
            
            # Basic profile fields (60% of score)
            basic_fields = {
                'full_name': 10.0,
                'current_title': 15.0,
                'current_company': 15.0,
                'location': 10.0,
                'industry': 10.0
            }
            
            for field, weight in basic_fields.items():
                if getattr(lead, field):
                    score += weight
            
            # Contact information (30% of score)
            if lead.email:
                score += 20.0
            if lead.phone:
                score += 10.0
            
            # Additional profile data (10% of score)
            if lead.headline:
                score += 5.0
            if lead.profile_image_url:
                score += 5.0
            
            return min(score, max_score)
            
        except Exception as e:
            logger.error(f"Error scoring profile completeness: {e}")
            return 0.0
    
    def _score_apollo_enrichment(self, lead: LinkedInLead) -> float:
        """Score based on Apollo.io enrichment data quality"""
        try:
            if not lead.apollo_data:
                return 0.0
            
            apollo_data = lead.apollo_data
            score = 0.0
            
            # Email verification (40% of score)
            if apollo_data.get('email_status') == 'verified':
                score += 40.0
            elif apollo_data.get('email_status') == 'likely_to_engage':
                score += 30.0
            elif apollo_data.get('email'):
                score += 20.0
            
            # Phone number (20% of score)
            if apollo_data.get('phone_numbers'):
                score += 20.0
            
            # Company data enrichment (25% of score)
            organization = apollo_data.get('organization', {})
            if organization.get('name'):
                score += 10.0
            if organization.get('website_url'):
                score += 5.0
            if organization.get('industry'):
                score += 5.0
            if organization.get('estimated_num_employees'):
                score += 5.0
            
            # Social links (15% of score)
            if apollo_data.get('linkedin_url'):
                score += 10.0
            if apollo_data.get('twitter_url'):
                score += 5.0
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error scoring Apollo enrichment: {e}")
            return 0.0
    
    def _score_title_relevance(self, lead: LinkedInLead) -> float:
        """Score based on job title relevance for executive opportunities"""
        try:
            if not lead.current_title:
                return 0.0
            
            title_lower = lead.current_title.lower()
            score = 0.0
            
            # C-Suite executives (highest score)
            c_suite_titles = ['ceo', 'cfo', 'cto', 'coo', 'chief executive', 'chief financial', 
                             'chief technology', 'chief operating', 'chief risk', 'chief compliance']
            for c_title in c_suite_titles:
                if c_title in title_lower:
                    score = max(score, 95.0)
                    break
            
            # Senior executive titles
            if score < 90:
                senior_titles = ['president', 'executive vice president', 'senior vice president']
                for title in senior_titles:
                    if title in title_lower:
                        score = max(score, 85.0)
                        break
            
            # Vice president level
            if score < 80 and ('vice president' in title_lower or 'vp ' in title_lower):
                score = max(score, 75.0)
            
            # Director level
            if score < 70:
                director_titles = ['director', 'head of', 'managing director']
                for title in director_titles:
                    if title in title_lower:
                        score = max(score, 65.0)
                        break
            
            # Board positions (special scoring)
            board_titles = ['board member', 'board director', 'independent director', 'non-executive director']
            for title in board_titles:
                if title in title_lower:
                    score = max(score, 90.0)
                    break
            
            # Risk/Governance/Compliance specialization bonus
            specialization_keywords = ['risk', 'governance', 'compliance', 'audit', 'regulatory']
            specialization_bonus = sum(5.0 for keyword in specialization_keywords if keyword in title_lower)
            score = min(score + specialization_bonus, 100.0)
            
            return score
            
        except Exception as e:
            logger.error(f"Error scoring title relevance: {e}")
            return 0.0
    
    def _score_company_quality(self, lead: LinkedInLead) -> float:
        """Score based on company quality and relevance"""
        try:
            score = 0.0
            
            # Company size scoring (40% of total)
            company_size_score = self._score_company_size(lead.company_size)
            score += company_size_score * 0.4
            
            # Industry relevance (30% of total)
            industry_score = self._score_industry_relevance(lead.industry)
            score += industry_score * 0.3
            
            # Company reputation (30% of total)
            reputation_score = self._score_company_reputation(lead.current_company)
            score += reputation_score * 0.3
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error scoring company quality: {e}")
            return 0.0
    
    def _score_company_size(self, company_size: Optional[str]) -> float:
        """Score based on company size preference"""
        if not company_size:
            return 50.0  # Neutral score if unknown
        
        size_lower = str(company_size).lower()
        
        # Map company size to score (preferring larger companies for executive opportunities)
        if any(indicator in size_lower for indicator in ['10000+', '10,000+', 'enterprise', 'fortune']):
            return 100.0
        elif any(indicator in size_lower for indicator in ['5000', '5,000', 'large']):
            return 90.0
        elif any(indicator in size_lower for indicator in ['1000', '1,000', 'medium']):
            return 75.0
        elif any(indicator in size_lower for indicator in ['500', 'small']):
            return 60.0
        elif any(indicator in size_lower for indicator in ['100', 'startup']):
            return 40.0
        else:
            return 50.0
    
    def _score_industry_relevance(self, industry: Optional[str]) -> float:
        """Score industry relevance for executive opportunities"""
        if not industry:
            return 50.0
        
        industry_lower = industry.lower()
        
        # High-value industries for executive opportunities
        high_value_industries = {
            'financial services': 100.0,
            'banking': 95.0,
            'insurance': 90.0,
            'healthcare': 90.0,
            'pharmaceuticals': 85.0,
            'technology': 85.0,
            'consulting': 80.0,
            'manufacturing': 75.0,
            'energy': 75.0,
            'telecommunications': 70.0
        }
        
        # Check for exact or partial matches
        for industry_key, score in high_value_industries.items():
            if industry_key in industry_lower:
                return score
        
        # Default score for other industries
        return 60.0
    
    def _score_company_reputation(self, company_name: Optional[str]) -> float:
        """Score based on company reputation (simplified)"""
        if not company_name:
            return 50.0
        
        company_lower = company_name.lower()
        
        # Fortune 500 / well-known companies (simplified check)
        well_known_companies = ['google', 'microsoft', 'apple', 'amazon', 'meta', 'tesla', 
                               'jpmorgan', 'bank of america', 'wells fargo', 'goldman sachs',
                               'johnson & johnson', 'pfizer', 'merck', 'abbott']
        
        if any(company in company_lower for company in well_known_companies):
            return 95.0
        
        # Look for indicators of established companies
        established_indicators = ['inc', 'corp', 'corporation', 'llc', 'ltd', 'limited']
        if any(indicator in company_lower for indicator in established_indicators):
            return 70.0
        
        return 60.0  # Default score
    
    def _score_engagement_potential(self, lead: LinkedInLead) -> float:
        """Score potential for engagement based on LinkedIn activity"""
        try:
            score = 50.0  # Base score
            
            # Recent activity bonus
            if lead.last_activity_at:
                days_since_activity = (datetime.utcnow() - lead.last_activity_at).days
                if days_since_activity <= 7:
                    score += 30.0
                elif days_since_activity <= 30:
                    score += 20.0
                elif days_since_activity <= 90:
                    score += 10.0
            
            # Connection status bonus
            if lead.status == 'connection_accepted':
                score += 20.0
            elif lead.status == 'connection_sent':
                score += 10.0
            
            # Response history bonus
            if lead.last_response_at:
                score += 25.0
                
                # Recent response bonus
                days_since_response = (datetime.utcnow() - lead.last_response_at).days
                if days_since_response <= 7:
                    score += 15.0
                elif days_since_response <= 30:
                    score += 10.0
            
            # Social signals bonus (if available)
            if lead.social_signals:
                social_score = self._analyze_social_signals(lead.social_signals)
                score += social_score * 0.2
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error scoring engagement potential: {e}")
            return 50.0
    
    def _score_research_insights(self, lead: LinkedInLead) -> float:
        """Score based on Perplexity research insights"""
        try:
            if not lead.perplexity_research:
                return 30.0  # Lower score if no research available
            
            research_data = lead.perplexity_research
            score = 50.0  # Base score for having research
            
            # Analyze research quality
            if 'analysis' in research_data:
                analysis = research_data['analysis']
                
                # Look for positive indicators
                positive_indicators = ['leadership', 'achievement', 'award', 'recognition', 
                                     'growth', 'success', 'innovation', 'strategic']
                positive_count = sum(1 for indicator in positive_indicators 
                                   if indicator.lower() in analysis.lower())
                score += min(positive_count * 5, 30)
                
                # Look for governance/risk experience
                governance_indicators = ['governance', 'risk management', 'compliance', 
                                       'board', 'audit', 'regulatory']
                governance_count = sum(1 for indicator in governance_indicators 
                                     if indicator.lower() in analysis.lower())
                score += min(governance_count * 8, 40)
            
            # Research recency bonus
            if 'timestamp' in research_data:
                try:
                    research_date = datetime.fromisoformat(research_data['timestamp'])
                    days_since_research = (datetime.utcnow() - research_date).days
                    if days_since_research <= 7:
                        score += 15.0
                    elif days_since_research <= 30:
                        score += 10.0
                except:
                    pass
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error scoring research insights: {e}")
            return 30.0
    
    def _analyze_social_signals(self, social_signals: Dict[str, Any]) -> float:
        """Analyze social signals for engagement scoring"""
        try:
            score = 0.0
            
            # Recent posts
            if social_signals.get('recent_posts_count', 0) > 0:
                score += 20.0
            
            # Professional content
            if social_signals.get('professional_content', False):
                score += 30.0
            
            # Engagement with others
            if social_signals.get('engagement_rate', 0) > 0.05:  # 5% engagement rate
                score += 25.0
            
            # Thought leadership indicators
            if social_signals.get('thought_leadership', False):
                score += 25.0
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error analyzing social signals: {e}")
            return 0.0
    
    def _determine_qualification_level(self, overall_score: float) -> QualificationLevel:
        """Determine qualification level based on overall score"""
        for level, threshold in sorted(self.qualification_thresholds.items(), 
                                     key=lambda x: x[1], reverse=True):
            if overall_score >= threshold:
                return level
        return QualificationLevel.UNQUALIFIED
    
    def _find_opportunity_matches(self, lead: LinkedInLead) -> List[Dict[str, Any]]:
        """Find matching executive opportunities for the lead"""
        try:
            matches = []
            
            # Check each opportunity type
            for opp_type in OpportunityType:
                match_score = self._calculate_opportunity_match_score(lead, opp_type)
                
                if match_score >= 60.0:  # Minimum threshold for consideration
                    match = {
                        'opportunity_type': opp_type.value,
                        'match_score': match_score,
                        'match_reasons': self._get_opportunity_match_reasons(lead, opp_type),
                        'requirements_met': self._check_opportunity_requirements(lead, opp_type)
                    }
                    matches.append(match)
            
            # Sort by match score (highest first)
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding opportunity matches: {e}")
            return []
    
    def _calculate_opportunity_match_score(self, lead: LinkedInLead, 
                                         opportunity_type: OpportunityType) -> float:
        """Calculate match score for a specific opportunity type"""
        try:
            score = 0.0
            
            # Title match scoring
            title_score = self._score_title_for_opportunity(lead.current_title, opportunity_type)
            score += title_score * self.opportunity_matching_weights['title_match']
            
            # Industry experience scoring
            industry_score = self._score_industry_for_opportunity(lead.industry, opportunity_type)
            score += industry_score * self.opportunity_matching_weights['industry_experience']
            
            # Company stage scoring
            company_score = self._score_company_for_opportunity(lead, opportunity_type)
            score += company_score * self.opportunity_matching_weights['company_stage']
            
            # Network potential scoring
            network_score = self._score_network_potential(lead, opportunity_type)
            score += network_score * self.opportunity_matching_weights['network_potential']
            
            # Availability signals scoring
            availability_score = self._score_availability_signals(lead, opportunity_type)
            score += availability_score * self.opportunity_matching_weights['availability_signals']
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating opportunity match score: {e}")
            return 0.0
    
    def _score_title_for_opportunity(self, title: Optional[str], 
                                   opportunity_type: OpportunityType) -> float:
        """Score title relevance for specific opportunity type"""
        if not title:
            return 0.0
        
        title_lower = title.lower()
        
        # Define title patterns for each opportunity type
        title_patterns = {
            OpportunityType.BOARD_DIRECTOR: {
                'patterns': ['ceo', 'cfo', 'cto', 'president', 'board', 'director', 'chief'],
                'boost_keywords': ['governance', 'risk', 'strategy']
            },
            OpportunityType.CONSULTANT: {
                'patterns': ['consultant', 'advisor', 'partner', 'principal', 'director'],
                'boost_keywords': ['consulting', 'advisory', 'strategy', 'transformation']
            },
            OpportunityType.SPEAKER: {
                'patterns': ['chief', 'head', 'director', 'vp', 'president'],
                'boost_keywords': ['thought', 'leadership', 'innovation', 'strategy']
            }
        }
        
        if opportunity_type not in title_patterns:
            return 50.0
        
        patterns = title_patterns[opportunity_type]
        score = 0.0
        
        # Check for pattern matches
        for pattern in patterns['patterns']:
            if pattern in title_lower:
                score = max(score, 70.0)
                break
        
        # Boost for relevant keywords
        for keyword in patterns['boost_keywords']:
            if keyword in title_lower:
                score += 15.0
        
        return min(score, 100.0)
    
    def _score_industry_for_opportunity(self, industry: Optional[str], 
                                      opportunity_type: OpportunityType) -> float:
        """Score industry relevance for specific opportunity type"""
        if not industry or opportunity_type not in self.industry_relevance:
            return 50.0
        
        industry_lower = industry.lower()
        relevance_map = self.industry_relevance[opportunity_type]
        
        # Find best industry match
        best_score = 50.0
        for industry_key, score in relevance_map.items():
            if industry_key in industry_lower:
                best_score = max(best_score, score * 100)
        
        return best_score
    
    def _score_company_for_opportunity(self, lead: LinkedInLead, 
                                     opportunity_type: OpportunityType) -> float:
        """Score company characteristics for opportunity type"""
        score = 50.0  # Base score
        
        # Company size preferences vary by opportunity type
        if opportunity_type == OpportunityType.BOARD_DIRECTOR:
            # Prefer larger companies for board positions
            if lead.company_size and '1000' in str(lead.company_size):
                score += 30.0
        elif opportunity_type == OpportunityType.CONSULTANT:
            # Consultants from various company sizes are valuable
            score += 20.0
        
        return min(score, 100.0)
    
    def _score_network_potential(self, lead: LinkedInLead, 
                               opportunity_type: OpportunityType) -> float:
        """Score network potential for opportunity type"""
        # This would analyze the lead's network connections and influence
        # For now, return a simulated score based on title and company
        
        score = 50.0
        
        if lead.current_title and any(title in lead.current_title.lower() 
                                    for title in ['ceo', 'president', 'chief']):
            score += 30.0
        
        if lead.industry in ['financial services', 'technology', 'consulting']:
            score += 20.0
        
        return min(score, 100.0)
    
    def _score_availability_signals(self, lead: LinkedInLead, 
                                  opportunity_type: OpportunityType) -> float:
        """Score availability signals for opportunity engagement"""
        # This would analyze signals that indicate availability for opportunities
        # For now, return a baseline score
        
        score = 60.0  # Assume moderate availability
        
        # Recent LinkedIn activity suggests engagement
        if lead.last_activity_at:
            days_since_activity = (datetime.utcnow() - lead.last_activity_at).days
            if days_since_activity <= 30:
                score += 20.0
        
        # Response to outreach indicates interest
        if lead.last_response_at:
            score += 20.0
        
        return min(score, 100.0)
    
    def _get_opportunity_match_reasons(self, lead: LinkedInLead, 
                                     opportunity_type: OpportunityType) -> List[str]:
        """Get reasons why lead matches opportunity type"""
        reasons = []
        
        if lead.current_title:
            title_lower = lead.current_title.lower()
            if any(keyword in title_lower for keyword in ['ceo', 'president', 'chief']):
                reasons.append(f"Senior executive title: {lead.current_title}")
        
        if lead.industry:
            reasons.append(f"Relevant industry experience: {lead.industry}")
        
        if lead.apollo_data and lead.apollo_data.get('email_status') == 'verified':
            reasons.append("Verified contact information available")
        
        return reasons
    
    def _check_opportunity_requirements(self, lead: LinkedInLead, 
                                      opportunity_type: OpportunityType) -> Dict[str, bool]:
        """Check if lead meets opportunity requirements"""
        requirements = {
            'senior_title': False,
            'verified_contact': False,
            'relevant_industry': False,
            'linkedin_profile': False
        }
        
        # Check senior title
        if lead.current_title:
            title_lower = lead.current_title.lower()
            if any(keyword in title_lower for keyword in ['ceo', 'cfo', 'cto', 'president', 'vp', 'director']):
                requirements['senior_title'] = True
        
        # Check verified contact
        if lead.email or (lead.apollo_data and lead.apollo_data.get('email')):
            requirements['verified_contact'] = True
        
        # Check relevant industry
        if lead.industry:
            requirements['relevant_industry'] = True
        
        # Check LinkedIn profile
        if lead.linkedin_url:
            requirements['linkedin_profile'] = True
        
        return requirements
    
    def _generate_qualification_reasons(self, lead: LinkedInLead, 
                                      component_scores: Dict[str, float]) -> List[str]:
        """Generate reasons for lead qualification"""
        reasons = []
        
        # High-scoring components
        for component, score in component_scores.items():
            if score >= 80.0:
                if component == 'title_relevance':
                    reasons.append(f"Excellent title match: {lead.current_title}")
                elif component == 'apollo_enrichment':
                    reasons.append("High-quality contact data available")
                elif component == 'company_quality':
                    reasons.append(f"Strong company profile: {lead.current_company}")
                elif component == 'research_insights':
                    reasons.append("Positive research insights available")
        
        # Specific qualifications
        if lead.current_title and any(title in lead.current_title.lower() 
                                    for title in ['ceo', 'cfo', 'cto']):
            reasons.append("C-suite executive level")
        
        if lead.apollo_data and lead.apollo_data.get('email_status') == 'verified':
            reasons.append("Verified email address")
        
        return reasons
    
    def _generate_disqualification_reasons(self, lead: LinkedInLead, 
                                         component_scores: Dict[str, float],
                                         criteria: QualificationCriteria) -> List[str]:
        """Generate reasons for lead disqualification"""
        reasons = []
        
        # Low-scoring components
        for component, score in component_scores.items():
            if score < 40.0:
                if component == 'profile_completeness':
                    reasons.append("Incomplete LinkedIn profile")
                elif component == 'apollo_enrichment':
                    reasons.append("Limited contact information available")
                elif component == 'title_relevance':
                    reasons.append("Title not aligned with target opportunities")
        
        # Specific disqualifiers
        if criteria.email_verified and not lead.email:
            reasons.append("No verified email address")
        
        if criteria.required_titles:
            if not lead.current_title or not any(title.lower() in lead.current_title.lower() 
                                               for title in criteria.required_titles):
                reasons.append("Title does not match required criteria")
        
        return reasons
    
    def _generate_recommended_actions(self, lead: LinkedInLead, 
                                    qualification_level: QualificationLevel,
                                    component_scores: Dict[str, float]) -> List[str]:
        """Generate recommended actions based on qualification"""
        actions = []
        
        if qualification_level == QualificationLevel.HOT_LEAD:
            actions.append("Prioritize immediate outreach")
            actions.append("Schedule executive conversation")
            actions.append("Prepare customized opportunity presentation")
        
        elif qualification_level == QualificationLevel.QUALIFIED:
            actions.append("Initiate personalized outreach sequence")
            actions.append("Share relevant thought leadership content")
            actions.append("Research specific opportunity alignment")
        
        elif qualification_level == QualificationLevel.POTENTIAL:
            actions.append("Continue nurturing with valuable content")
            actions.append("Monitor for engagement signals")
            actions.append("Gather additional qualification data")
        
        # Component-specific recommendations
        if component_scores.get('apollo_enrichment', 0) < 50:
            actions.append("Enrich contact data via Apollo.io")
        
        if component_scores.get('research_insights', 0) < 50:
            actions.append("Conduct Perplexity research for personalization")
        
        return actions
    
    def _calculate_confidence_score(self, component_scores: Dict[str, float], 
                                  lead: LinkedInLead) -> float:
        """Calculate confidence in qualification accuracy"""
        try:
            # Base confidence on data completeness
            data_completeness = 0.0
            
            # Profile data completeness
            profile_fields = ['full_name', 'current_title', 'current_company', 'industry']
            completed_fields = sum(1 for field in profile_fields if getattr(lead, field))
            data_completeness += (completed_fields / len(profile_fields)) * 30
            
            # Contact data completeness
            if lead.email:
                data_completeness += 25
            if lead.phone:
                data_completeness += 15
            
            # Enrichment data completeness
            if lead.apollo_data:
                data_completeness += 20
            
            # Research data completeness
            if lead.perplexity_research:
                data_completeness += 10
            
            # Adjust based on score consistency
            score_variance = np.var(list(component_scores.values())) if component_scores else 0
            consistency_bonus = max(0, 20 - (score_variance / 10))
            
            confidence = min(data_completeness + consistency_bonus, 100.0)
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 70.0  # Default confidence
    
    def _calculate_next_review_date(self, qualification_level: QualificationLevel) -> datetime:
        """Calculate when lead should be reviewed again"""
        days_to_add = {
            QualificationLevel.HOT_LEAD: 3,
            QualificationLevel.QUALIFIED: 7,
            QualificationLevel.POTENTIAL: 14,
            QualificationLevel.DEVELOPING: 30,
            QualificationLevel.UNQUALIFIED: 90
        }
        
        days = days_to_add.get(qualification_level, 30)
        return datetime.utcnow() + timedelta(days=days)
    
    def _update_lead_qualification(self, lead: LinkedInLead, result: QualificationResult):
        """Update lead record with qualification results"""
        try:
            lead.qualification_status = result.qualification_level.value
            lead.lead_score = result.overall_score
            lead.opportunity_match_score = max([m['match_score'] for m in result.opportunity_matches], default=0)
            
            # Set opportunity type to best match
            if result.opportunity_matches:
                best_match = result.opportunity_matches[0]
                lead.opportunity_type = best_match['opportunity_type']
            
            lead.last_updated = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating lead qualification: {e}")
            db.session.rollback()
    
    def _enrich_lead_with_apollo(self, lead_id: str) -> bool:
        """Enrich lead using Apollo.io API"""
        try:
            if not self.apollo_api:
                return False
            
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                return False
            
            # Enrich using Apollo
            enrichment_data = self.apollo_api.enrich_person(
                first_name=lead.first_name,
                last_name=lead.last_name,
                organization_name=lead.current_company,
                domain=lead.company_domain
            )
            
            if enrichment_data and 'person' in enrichment_data:
                person_data = enrichment_data['person']
                
                # Update lead with enriched data
                lead.email = person_data.get('email') or lead.email
                phone_numbers = person_data.get('phone_numbers', [])
                if phone_numbers:
                    lead.phone = phone_numbers[0].get('raw_number') or lead.phone
                
                lead.apollo_data = enrichment_data
                lead.last_updated = datetime.utcnow()
                db.session.commit()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enriching lead with Apollo: {e}")
            return False
    
    def _research_lead_with_perplexity(self, lead_id: str) -> bool:
        """Research lead using Perplexity AI"""
        try:
            if not self.perplexity_research:
                return False
            
            lead = LinkedInLead.query.filter_by(lead_id=lead_id).first()
            if not lead:
                return False
            
            # Research executive for potential opportunities
            research_result = self.perplexity_research.research_executive_opportunity(
                executive_name=lead.full_name,
                company_name=lead.current_company,
                opportunity_type="executive_engagement"
            )
            
            if research_result:
                lead.perplexity_research = research_result
                lead.last_updated = datetime.utcnow()
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error researching lead with Perplexity: {e}")
            return False
    
    def _needs_research_update(self, lead: LinkedInLead) -> bool:
        """Check if lead needs research update"""
        if not lead.perplexity_research:
            return True
        
        try:
            research_data = lead.perplexity_research
            if 'timestamp' in research_data:
                research_date = datetime.fromisoformat(research_data['timestamp'])
                days_since_research = (datetime.utcnow() - research_date).days
                return days_since_research > 30
        except:
            pass
        
        return True


# Factory function
def create_linkedin_qualification_engine(apollo_api: Optional[ApolloAPIWrapper] = None,
                                        perplexity_api: Optional[PerplexityAPI] = None,
                                        ai_scorer: Optional[AIOpportunityScorer] = None) -> LinkedInQualificationEngine:
    """Factory function to create LinkedIn qualification engine"""
    return LinkedInQualificationEngine(apollo_api, perplexity_api, ai_scorer)