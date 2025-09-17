"""
Apollo.io Integration Module
Comprehensive API wrapper for Apollo.io with prospect search, enrichment, and sequence management
"""

import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class ApolloProspect:
    """Data class for standardized prospect information from Apollo"""
    id: str
    first_name: str
    last_name: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    title: str
    linkedin_url: Optional[str]
    company_name: str
    company_domain: Optional[str]
    company_id: Optional[str]
    location: Optional[str]
    seniority: Optional[str]
    match_score: float
    source: str = "apollo"
    raw_data: Dict = None
    
@dataclass
class ApolloCompany:
    """Data class for standardized company information from Apollo"""
    id: str
    name: str
    domain: Optional[str]
    website_url: Optional[str]
    industry: Optional[str]
    employee_count: Optional[int]
    revenue: Optional[int]
    location: Optional[str]
    description: Optional[str]
    technologies: List[str] = None
    raw_data: Dict = None

class ApolloAPIError(Exception):
    """Custom exception for Apollo API errors"""
    def __init__(self, message: str, status_code: int = None, response: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)

class ApolloAPIWrapper:
    """
    Comprehensive Apollo.io API wrapper for prospect search, enrichment, and automation
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Key': api_key
        })
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        
        # GRC and AI Governance specific search terms
        self.grc_keywords = [
            "chief risk officer", "cro", "risk management", "governance", 
            "compliance", "audit", "regulatory", "enterprise risk"
        ]
        
        self.board_keywords = [
            "board director", "board member", "independent director", 
            "chairman", "board chair", "non-executive director"
        ]
        
        self.ai_governance_keywords = [
            "ai governance", "artificial intelligence", "ai ethics", 
            "ai risk", "chief ai officer", "cai", "ai compliance"
        ]
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None, params: Dict = None) -> Dict:
        """
        Make authenticated request to Apollo API with rate limiting and error handling
        """
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            else:
                raise ApolloAPIError(f"Unsupported HTTP method: {method}")
            
            self.last_request_time = time.time()
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Apollo API rate limit hit. Waiting {retry_after} seconds.")
                time.sleep(retry_after)
                # Retry the request
                return self._make_request(endpoint, method, data, params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Apollo API HTTP error: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg += f" - {error_data}"
                except:
                    error_msg += f" - {e.response.text}"
            logger.error(error_msg)
            raise ApolloAPIError(error_msg, e.response.status_code if e.response else None)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Apollo API request error: {e}"
            logger.error(error_msg)
            raise ApolloAPIError(error_msg)
    
    # === PEOPLE SEARCH AND ENRICHMENT ===
    
    def search_people(self, 
                     person_titles: List[str] = None,
                     person_seniorities: List[str] = None,
                     person_locations: List[str] = None,
                     organization_locations: List[str] = None,
                     keywords: str = None,
                     organization_domains: List[str] = None,
                     email_status: List[str] = None,
                     revenue_range: Dict[str, int] = None,
                     employee_count_ranges: List[str] = None,
                     technologies: List[str] = None,
                     page: int = 1,
                     per_page: int = 25,
                     include_similar_titles: bool = True) -> Dict:
        """
        Search for people using Apollo's People Search API
        
        Args:
            person_titles: List of job titles to search for
            person_seniorities: List of seniority levels (owner, founder, c_suite, partner, vp, head, director, manager, senior, entry, intern)
            person_locations: List of personal locations
            organization_locations: List of company headquarters locations
            keywords: General keywords to search for
            organization_domains: List of company domains
            email_status: List of email statuses (verified, unverified, likely_to_engage, unavailable)
            revenue_range: Dict with 'min' and 'max' revenue values
            employee_count_ranges: List of employee count ranges (e.g., ["1,10", "250,500"])
            technologies: List of technologies used by companies
            page: Page number
            per_page: Results per page (max 100)
            include_similar_titles: Whether to include similar job titles
            
        Returns:
            Dict containing search results with contacts and pagination info
        """
        data = {
            "page": page,
            "per_page": min(per_page, 100)  # Apollo max is 100
        }
        
        if person_titles:
            data["person_titles"] = person_titles
            data["include_similar_titles"] = include_similar_titles
            
        if person_seniorities:
            data["person_seniorities"] = person_seniorities
            
        if person_locations:
            data["person_locations"] = person_locations
            
        if organization_locations:
            data["organization_locations"] = organization_locations
            
        if keywords:
            data["q_keywords"] = keywords
            
        if organization_domains:
            data["q_organization_domains_list"] = organization_domains
            
        if email_status:
            data["contact_email_status"] = email_status
            
        if revenue_range:
            if 'min' in revenue_range:
                data["revenue_range"] = {"min": revenue_range['min']}
            if 'max' in revenue_range:
                data["revenue_range"] = data.get("revenue_range", {})
                data["revenue_range"]["max"] = revenue_range['max']
                
        if employee_count_ranges:
            data["organization_num_employees_ranges"] = employee_count_ranges
            
        if technologies:
            data["currently_using_any_of_technology_uids"] = technologies
        
        return self._make_request("mixed_people/search", "POST", data)
    
    def enrich_person(self, 
                     email: str = None,
                     first_name: str = None, 
                     last_name: str = None,
                     organization_name: str = None,
                     domain: str = None,
                     reveal_personal_emails: bool = False,
                     reveal_phone_number: bool = False) -> Dict:
        """
        Enrich a single person's data using Apollo's People Match API
        
        Args:
            email: Person's email address
            first_name: Person's first name
            last_name: Person's last name
            organization_name: Person's company name
            domain: Company domain
            reveal_personal_emails: Whether to reveal personal email addresses
            reveal_phone_number: Whether to reveal phone numbers
            
        Returns:
            Dict containing enriched person data
        """
        params = {}
        
        if email:
            params["email"] = email
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if organization_name:
            params["organization_name"] = organization_name
        if domain:
            params["domain"] = domain
            
        params["reveal_personal_emails"] = reveal_personal_emails
        params["reveal_phone_number"] = reveal_phone_number
        
        return self._make_request("people/match", "POST", params=params)
    
    def bulk_enrich_people(self, people_data: List[Dict], 
                          reveal_personal_emails: bool = False,
                          reveal_phone_number: bool = False) -> Dict:
        """
        Enrich multiple people (up to 10) using Apollo's Bulk People Match API
        
        Args:
            people_data: List of dicts with person data (email, first_name, last_name, etc.)
            reveal_personal_emails: Whether to reveal personal email addresses
            reveal_phone_number: Whether to reveal phone numbers
            
        Returns:
            Dict containing bulk enrichment results
        """
        if len(people_data) > 10:
            raise ApolloAPIError("Bulk enrichment supports maximum 10 people per request")
        
        data = {
            "details": people_data,
            "reveal_personal_emails": reveal_personal_emails,
            "reveal_phone_number": reveal_phone_number
        }
        
        return self._make_request("people/bulk_match", "POST", data)
    
    # === ORGANIZATION SEARCH AND ENRICHMENT ===
    
    def search_organizations(self,
                           organization_locations: List[str] = None,
                           q_keywords: str = None,
                           organization_names: List[str] = None,
                           organization_domains: List[str] = None,
                           employee_count_ranges: List[str] = None,
                           revenue_range: Dict[str, int] = None,
                           industries: List[str] = None,
                           technologies: List[str] = None,
                           page: int = 1,
                           per_page: int = 25) -> Dict:
        """
        Search for organizations using Apollo's Organization Search API
        
        Args:
            organization_locations: List of company locations
            q_keywords: Keywords to search for
            organization_names: List of company names
            organization_domains: List of company domains
            employee_count_ranges: List of employee count ranges
            revenue_range: Dict with 'min' and 'max' revenue values
            industries: List of industries
            technologies: List of technologies used
            page: Page number
            per_page: Results per page
            
        Returns:
            Dict containing search results with organizations and pagination info
        """
        data = {
            "page": page,
            "per_page": min(per_page, 100)
        }
        
        if organization_locations:
            data["organization_locations"] = organization_locations
        if q_keywords:
            data["q_keywords"] = q_keywords
        if organization_names:
            data["q_organization_name_list"] = organization_names
        if organization_domains:
            data["q_organization_domains_list"] = organization_domains
        if employee_count_ranges:
            data["organization_num_employees_ranges"] = employee_count_ranges
        if revenue_range:
            if 'min' in revenue_range:
                data["revenue_range"] = {"min": revenue_range['min']}
            if 'max' in revenue_range:
                data["revenue_range"] = data.get("revenue_range", {})
                data["revenue_range"]["max"] = revenue_range['max']
        if industries:
            data["q_organization_keyword_list"] = industries
        if technologies:
            data["currently_using_any_of_technology_uids"] = technologies
            
        return self._make_request("organizations/search", "POST", data)
    
    def enrich_organization(self, domain: str) -> Dict:
        """
        Enrich organization data using Apollo's Organization Match API
        
        Args:
            domain: Company domain to enrich
            
        Returns:
            Dict containing enriched organization data
        """
        params = {"domain": domain}
        return self._make_request("organizations/match", "POST", params=params)
    
    # === SPECIALIZED SEARCH METHODS FOR GRC AND AI GOVERNANCE ===
    
    def search_grc_executives(self, 
                            organization_locations: List[str] = None,
                            employee_count_ranges: List[str] = ["1000,5000", "5000,10000", "10000,50000", "50000,100000", "100000,"],
                            revenue_range: Dict[str, int] = {"min": 100000000},  # $100M+
                            page: int = 1,
                            per_page: int = 25) -> Dict:
        """
        Search for GRC (Governance, Risk, Compliance) executives
        
        Returns:
            Dict containing GRC executive prospects
        """
        grc_titles = [
            "chief risk officer", "cro", "head of risk", "risk management director",
            "compliance officer", "chief compliance officer", "governance director",
            "enterprise risk manager", "risk and compliance", "audit director",
            "chief audit executive", "regulatory affairs", "internal audit"
        ]
        
        grc_seniorities = ["c_suite", "vp", "head", "director"]
        
        return self.search_people(
            person_titles=grc_titles,
            person_seniorities=grc_seniorities,
            organization_locations=organization_locations,
            employee_count_ranges=employee_count_ranges,
            revenue_range=revenue_range,
            keywords="risk governance compliance audit regulatory",
            email_status=["verified", "likely_to_engage"],
            page=page,
            per_page=per_page
        )
    
    def search_board_directors(self,
                             organization_locations: List[str] = None,
                             employee_count_ranges: List[str] = ["1000,5000", "5000,10000", "10000,50000", "50000,100000", "100000,"],
                             revenue_range: Dict[str, int] = {"min": 500000000},  # $500M+
                             page: int = 1,
                             per_page: int = 25) -> Dict:
        """
        Search for board directors and independent directors
        
        Returns:
            Dict containing board director prospects
        """
        board_titles = [
            "board director", "independent director", "board member", "non-executive director",
            "chairman", "board chair", "lead director", "presiding director", "board advisor"
        ]
        
        board_seniorities = ["owner", "founder", "c_suite", "partner"]
        
        return self.search_people(
            person_titles=board_titles,
            person_seniorities=board_seniorities,
            organization_locations=organization_locations,
            employee_count_ranges=employee_count_ranges,
            revenue_range=revenue_range,
            keywords="board governance director independent",
            email_status=["verified", "likely_to_engage"],
            page=page,
            per_page=per_page
        )
    
    def search_ai_governance_leaders(self,
                                   organization_locations: List[str] = None,
                                   employee_count_ranges: List[str] = ["500,1000", "1000,5000", "5000,10000", "10000,50000", "50000,100000", "100000,"],
                                   revenue_range: Dict[str, int] = {"min": 50000000},  # $50M+
                                   page: int = 1,
                                   per_page: int = 25) -> Dict:
        """
        Search for AI governance and AI ethics leaders
        
        Returns:
            Dict containing AI governance leader prospects
        """
        ai_titles = [
            "chief ai officer", "chief artificial intelligence officer", "ai ethics",
            "ai governance", "head of ai", "ai compliance", "ai risk", "ai strategy",
            "machine learning ethics", "algorithmic governance", "responsible ai"
        ]
        
        ai_seniorities = ["c_suite", "vp", "head", "director", "senior"]
        
        ai_technologies = [
            "tensorflow", "pytorch", "machine_learning", "artificial_intelligence",
            "deep_learning", "neural_networks"
        ]
        
        return self.search_people(
            person_titles=ai_titles,
            person_seniorities=ai_seniorities,
            organization_locations=organization_locations,
            employee_count_ranges=employee_count_ranges,
            revenue_range=revenue_range,
            technologies=ai_technologies,
            keywords="artificial intelligence ai ethics governance machine learning",
            email_status=["verified", "likely_to_engage"],
            page=page,
            per_page=per_page
        )
    
    def search_consulting_executives(self,
                                    organization_locations: List[str] = None,
                                    employee_count_ranges: List[str] = ["50,100", "100,250", "250,500", "500,1000"],
                                    revenue_range: Dict[str, int] = {"min": 5000000},  # $5M+
                                    page: int = 1,
                                    per_page: int = 25) -> Dict:
        """
        Search for consulting executives and independent consultants
        
        Args:
            organization_locations: List of company locations to search
            employee_count_ranges: List of employee count ranges
            revenue_range: Dict with 'min' and 'max' revenue values
            page: Page number
            per_page: Results per page
            
        Returns:
            Dict containing consulting executive prospects
        """
        consulting_titles = [
            "consultant", "senior consultant", "principal consultant",
            "managing consultant", "independent consultant", "strategy consultant",
            "management consultant", "business consultant", "advisory",
            "advisor", "senior advisor", "strategic advisor",
            "fractional executive", "interim executive", "risk consultant",
            "compliance consultant", "governance consultant"
        ]
        
        consulting_seniorities = ["senior", "director", "vp", "partner", "owner", "c_suite"]
        
        return self.search_people(
            person_titles=consulting_titles,
            person_seniorities=consulting_seniorities,
            organization_locations=organization_locations,
            employee_count_ranges=employee_count_ranges,
            revenue_range=revenue_range,
            keywords="consulting advisory strategy management independent fractional",
            email_status=["verified", "likely_to_engage", "unverified"],
            page=page,
            per_page=per_page,
            include_similar_titles=True
        )

    def search_optimized_board_directors(self,
                                       organization_locations: List[str] = None,
                                       page: int = 1,
                                       per_page: int = 25) -> Dict:
        """
        Optimized search for board directors with more practical criteria
        
        Returns:
            Dict containing board director prospects with broader criteria
        """
        board_titles = [
            "board director", "independent director", "board member", 
            "non-executive director", "chairman", "board chair", "director",
            "lead director", "presiding director", "board advisor",
            "trustee", "board trustee"
        ]
        
        board_seniorities = ["c_suite", "founder", "owner", "partner", "vp"]
        
        # More practical company sizes and revenue
        employee_ranges = ["250,500", "500,1000", "1000,5000", "5000,10000", "10000,50000"]
        revenue_range = {"min": 25000000}  # $25M+ instead of $500M+
        
        return self.search_people(
            person_titles=board_titles,
            person_seniorities=board_seniorities,
            organization_locations=organization_locations,
            employee_count_ranges=employee_ranges,
            revenue_range=revenue_range,
            keywords="board governance director independent corporate governance",
            email_status=["verified", "likely_to_engage", "unverified"],
            page=page,
            per_page=per_page,
            include_similar_titles=True
        )

    def search_optimized_grc_executives(self,
                                      organization_locations: List[str] = None,
                                      page: int = 1,
                                      per_page: int = 25) -> Dict:
        """
        Optimized search for GRC executives with more practical criteria
        
        Returns:
            Dict containing GRC executive prospects with broader criteria
        """
        grc_titles = [
            "chief risk officer", "cro", "head of risk", "risk director",
            "compliance officer", "chief compliance officer", "compliance director",
            "governance director", "enterprise risk", "risk management",
            "audit director", "chief audit", "regulatory affairs",
            "risk consultant", "compliance consultant", "governance consultant"
        ]
        
        grc_seniorities = ["c_suite", "vp", "head", "director", "senior", "manager"]
        
        # Broader company sizes and lower revenue requirement
        employee_ranges = ["100,250", "250,500", "500,1000", "1000,5000", "5000,10000"]
        revenue_range = {"min": 10000000}  # $10M+ instead of $100M+
        
        return self.search_people(
            person_titles=grc_titles,
            person_seniorities=grc_seniorities,
            organization_locations=organization_locations,
            employee_count_ranges=employee_ranges,
            revenue_range=revenue_range,
            keywords="risk governance compliance audit regulatory consulting advisory",
            email_status=["verified", "likely_to_engage", "unverified"],
            page=page,
            per_page=per_page,
            include_similar_titles=True
        )
    
    # === DATA CONVERSION METHODS ===
    
    def convert_to_prospect(self, apollo_contact: Dict) -> ApolloProspect:
        """
        Convert Apollo contact data to standardized ApolloProspect object
        
        Args:
            apollo_contact: Raw contact data from Apollo API
            
        Returns:
            ApolloProspect object with standardized fields
        """
        # Calculate match score based on various factors
        match_score = self._calculate_match_score(apollo_contact)
        
        return ApolloProspect(
            id=apollo_contact.get('id', ''),
            first_name=apollo_contact.get('first_name', ''),
            last_name=apollo_contact.get('last_name', ''),
            name=apollo_contact.get('name', ''),
            email=apollo_contact.get('email'),
            phone=apollo_contact.get('sanitized_phone'),
            title=apollo_contact.get('title', ''),
            linkedin_url=apollo_contact.get('linkedin_url'),
            company_name=apollo_contact.get('organization_name', ''),
            company_domain=apollo_contact.get('organization', {}).get('primary_domain') if apollo_contact.get('organization') else None,
            company_id=apollo_contact.get('organization_id'),
            location=apollo_contact.get('present_raw_address'),
            seniority=apollo_contact.get('seniority'),
            match_score=match_score,
            raw_data=apollo_contact
        )
    
    def convert_to_company(self, apollo_org: Dict) -> ApolloCompany:
        """
        Convert Apollo organization data to standardized ApolloCompany object
        
        Args:
            apollo_org: Raw organization data from Apollo API
            
        Returns:
            ApolloCompany object with standardized fields
        """
        return ApolloCompany(
            id=apollo_org.get('id', ''),
            name=apollo_org.get('name', ''),
            domain=apollo_org.get('primary_domain'),
            website_url=apollo_org.get('website_url'),
            industry=apollo_org.get('industry'),
            employee_count=apollo_org.get('estimated_num_employees'),
            revenue=apollo_org.get('annual_revenue'),
            location=apollo_org.get('organization_raw_address'),
            description=apollo_org.get('short_description'),
            technologies=apollo_org.get('technology_names', []),
            raw_data=apollo_org
        )
    
    def _calculate_match_score(self, contact: Dict) -> float:
        """
        Calculate a match score for a contact based on various criteria
        This is the base Apollo scoring that can be enhanced with AI scoring
        
        Args:
            contact: Apollo contact data
            
        Returns:
            Float score between 0.0 and 1.0
        """
        score = 0.0
        
        # Email verification status (30% weight)
        email_status = contact.get('email_status', '')
        if email_status == 'verified':
            score += 0.3
        elif email_status == 'likely_to_engage':
            score += 0.2
        elif email_status == 'unverified':
            score += 0.1
        
        # LinkedIn profile (20% weight)
        if contact.get('linkedin_url'):
            score += 0.2
        
        # Phone number (15% weight)
        if contact.get('sanitized_phone'):
            score += 0.15
        
        # Title relevance (20% weight)
        title = contact.get('title', '').lower()
        for keyword_list in [self.grc_keywords, self.board_keywords, self.ai_governance_keywords]:
            for keyword in keyword_list:
                if keyword.lower() in title:
                    score += 0.2
                    break
        
        # Company size (15% weight)
        org = contact.get('organization', {})
        employee_count = org.get('estimated_num_employees', 0)
        if employee_count >= 1000:
            score += 0.15
        elif employee_count >= 500:
            score += 0.1
        elif employee_count >= 100:
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def enhance_prospect_with_ai_scoring(self, prospect: ApolloProspect, opportunity_type: str) -> ApolloProspect:
        """
        Enhance a prospect with AI-powered scoring
        
        Args:
            prospect: ApolloProspect object
            opportunity_type: Type of opportunity for scoring context
            
        Returns:
            Enhanced ApolloProspect with updated match score
        """
        try:
            from ai_scoring_service import create_ai_scorer
            
            ai_scorer = create_ai_scorer()
            ai_scoring_result = ai_scorer.score_apollo_prospect(prospect, opportunity_type)
            
            # Update the prospect's match score with AI-enhanced score
            enhanced_score = ai_scoring_result['final_score']
            
            # Create enhanced prospect with new score and AI analysis
            enhanced_prospect = ApolloProspect(
                id=prospect.id,
                first_name=prospect.first_name,
                last_name=prospect.last_name,
                name=prospect.name,
                email=prospect.email,
                phone=prospect.phone,
                title=prospect.title,
                linkedin_url=prospect.linkedin_url,
                company_name=prospect.company_name,
                company_domain=prospect.company_domain,
                company_id=prospect.company_id,
                location=prospect.location,
                seniority=prospect.seniority,
                match_score=enhanced_score,  # Updated with AI score
                source=prospect.source,
                raw_data={
                    **prospect.raw_data,
                    'ai_scoring_result': ai_scoring_result  # Add AI analysis to raw data
                }
            )
            
            logger.info(f"Enhanced prospect {prospect.id} score from {prospect.match_score:.3f} to {enhanced_score:.3f}")
            return enhanced_prospect
            
        except Exception as e:
            logger.error(f"Error enhancing prospect with AI scoring: {e}")
            # Return original prospect if AI enhancement fails
            return prospect
    
    # === UTILITY METHODS ===
    
    def get_supported_technologies(self) -> List[str]:
        """
        Get list of supported technology filters from Apollo
        
        Returns:
            List of supported technology UIDs
        """
        try:
            # Apollo provides a CSV endpoint for supported technologies
            response = requests.get("https://api.apollo.io/v1/auth/supported_technologies_csv")
            if response.status_code == 200:
                # Parse CSV and return technology names
                lines = response.text.strip().split('\n')
                technologies = []
                for line in lines[1:]:  # Skip header
                    if line:
                        tech_uid = line.split(',')[0]  # First column is UID
                        technologies.append(tech_uid)
                return technologies
            else:
                logger.warning("Could not fetch supported technologies from Apollo")
                return []
        except Exception as e:
            logger.error(f"Error fetching supported technologies: {e}")
            return []
    
    def validate_api_key(self) -> bool:
        """
        Validate that the API key is working
        
        Returns:
            Boolean indicating if API key is valid
        """
        try:
            # Try a simple request to validate the API key
            self.search_people(per_page=1, page=1)
            return True
        except ApolloAPIError:
            return False
        except Exception:
            return False


# Convenience function for creating Apollo wrapper with environment variable
def create_apollo_client() -> Optional[ApolloAPIWrapper]:
    """
    Create Apollo client using environment variable
    
    Returns:
        ApolloAPIWrapper instance or None if API key not found
    """
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        logger.error("APOLLO_API_KEY environment variable not found")
        return None
    
    return ApolloAPIWrapper(api_key)

# Alias for compatibility with LinkedIn automation system
def create_apollo_wrapper() -> Optional[ApolloAPIWrapper]:
    """
    Create Apollo wrapper using environment variable (alias for create_apollo_client)
    
    Returns:
        ApolloAPIWrapper instance or None if API key not found
    """
    return create_apollo_client()