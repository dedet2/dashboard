"""
Prospect Import Service
Handles data mapping and automated import of Apollo prospects into ExecutiveOpportunity pipeline
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
from dataclasses import asdict

# Import Apollo integration and database models
from apollo_integration import ApolloAPIWrapper, ApolloProspect, ApolloCompany, create_apollo_client
from database import db, ExecutiveOpportunity

logger = logging.getLogger(__name__)

class ProspectImportService:
    """
    Service for importing and managing Apollo prospects in the ExecutiveOpportunity pipeline
    """
    
    def __init__(self, apollo_client: ApolloAPIWrapper = None):
        self.apollo_client = apollo_client or create_apollo_client()
        if not self.apollo_client:
            raise ValueError("Apollo API client could not be initialized. Check APOLLO_API_KEY.")
        
        # Define opportunity type mapping based on titles and seniorities
        self.opportunity_type_mapping = {
            'board_director': [
                'board director', 'independent director', 'board member', 'non-executive director',
                'chairman', 'board chair', 'lead director', 'presiding director', 'board advisor'
            ],
            'executive_position': [
                'chief risk officer', 'cro', 'chief compliance officer', 'chief audit executive',
                'head of risk', 'risk management director', 'compliance officer', 'governance director'
            ],
            'advisor': [
                'advisor', 'strategic advisor', 'board advisor', 'governance advisor', 'risk advisor'
            ],
            'speaking': [
                'speaker', 'keynote speaker', 'thought leader', 'industry expert'
            ]
        }
        
        # Compensation estimation based on role and company size
        self.compensation_estimates = {
            'board_director': {
                'small': '$50K-150K annually',
                'medium': '$150K-300K annually', 
                'large': '$300K-500K annually',
                'enterprise': '$500K-1M annually'
            },
            'executive_position': {
                'small': '$200K-500K annually',
                'medium': '$500K-1M annually',
                'large': '$1M-3M annually', 
                'enterprise': '$3M-10M annually'
            },
            'advisor': {
                'small': '$25K-75K annually',
                'medium': '$75K-200K annually',
                'large': '$200K-500K annually',
                'enterprise': '$500K-1M annually'
            },
            'speaking': {
                'small': '$10K-50K per event',
                'medium': '$50K-150K per event',
                'large': '$150K-300K per event',
                'enterprise': '$300K-500K per event'
            }
        }
    
    def search_and_import_grc_executives(self, 
                                       locations: List[str] = None,
                                       max_results: int = 50,
                                       auto_import: bool = True,
                                       min_match_score: float = 0.6) -> Dict[str, Any]:
        """
        Search for GRC executives using Apollo and optionally auto-import them
        
        Args:
            locations: Geographic locations to search
            max_results: Maximum number of results to process
            auto_import: Whether to automatically import high-scoring prospects
            min_match_score: Minimum match score for auto-import
            
        Returns:
            Dict with search results and import statistics
        """
        logger.info(f"Starting GRC executive search with auto_import={auto_import}")
        
        try:
            # Search for GRC executives using Apollo
            search_results = self.apollo_client.search_grc_executives(
                organization_locations=locations,
                per_page=min(max_results, 25)  # Apollo max per page
            )
            
            if not search_results or 'contacts' not in search_results:
                return {
                    'success': False,
                    'error': 'No search results returned from Apollo',
                    'imported_count': 0,
                    'total_found': 0
                }
            
            # Convert to standardized prospect format
            prospects = []
            for contact in search_results['contacts']:
                prospect = self.apollo_client.convert_to_prospect(contact)
                prospects.append(prospect)
            
            # Import qualified prospects
            import_results = []
            imported_count = 0
            
            if auto_import:
                for prospect in prospects:
                    if prospect.match_score >= min_match_score:
                        try:
                            opportunity = self._create_executive_opportunity_from_prospect(
                                prospect, 'executive_position', 'apollo_grc_search'
                            )
                            if opportunity:
                                import_results.append({
                                    'prospect_id': prospect.id,
                                    'opportunity_id': opportunity.id,
                                    'match_score': prospect.match_score,
                                    'status': 'imported'
                                })
                                imported_count += 1
                            else:
                                import_results.append({
                                    'prospect_id': prospect.id,
                                    'status': 'skipped_existing'
                                })
                        except Exception as e:
                            logger.error(f"Error importing prospect {prospect.id}: {e}")
                            import_results.append({
                                'prospect_id': prospect.id,
                                'status': 'import_error',
                                'error': str(e)
                            })
            
            return {
                'success': True,
                'total_found': len(prospects),
                'imported_count': imported_count,
                'min_match_score': min_match_score,
                'prospects': [asdict(p) for p in prospects] if not auto_import else [],
                'import_results': import_results,
                'search_criteria': 'grc_executives',
                'locations': locations
            }
            
        except Exception as e:
            logger.error(f"Error in GRC executive search: {e}")
            return {
                'success': False,
                'error': str(e),
                'imported_count': 0,
                'total_found': 0
            }
    
    def search_and_import_board_directors(self,
                                        locations: List[str] = None,
                                        max_results: int = 50,
                                        auto_import: bool = True,
                                        min_match_score: float = 0.7) -> Dict[str, Any]:
        """
        Search for board directors using Apollo and optionally auto-import them
        """
        logger.info(f"Starting board director search with auto_import={auto_import}")
        
        try:
            search_results = self.apollo_client.search_board_directors(
                organization_locations=locations,
                per_page=min(max_results, 25)
            )
            
            if not search_results or 'contacts' not in search_results:
                return {
                    'success': False,
                    'error': 'No search results returned from Apollo',
                    'imported_count': 0,
                    'total_found': 0
                }
            
            prospects = []
            for contact in search_results['contacts']:
                prospect = self.apollo_client.convert_to_prospect(contact)
                prospects.append(prospect)
            
            import_results = []
            imported_count = 0
            
            if auto_import:
                for prospect in prospects:
                    if prospect.match_score >= min_match_score:
                        try:
                            opportunity = self._create_executive_opportunity_from_prospect(
                                prospect, 'board_director', 'apollo_board_search'
                            )
                            if opportunity:
                                import_results.append({
                                    'prospect_id': prospect.id,
                                    'opportunity_id': opportunity.id,
                                    'match_score': prospect.match_score,
                                    'status': 'imported'
                                })
                                imported_count += 1
                            else:
                                import_results.append({
                                    'prospect_id': prospect.id,
                                    'status': 'skipped_existing'
                                })
                        except Exception as e:
                            logger.error(f"Error importing board director prospect {prospect.id}: {e}")
                            import_results.append({
                                'prospect_id': prospect.id,
                                'status': 'import_error',
                                'error': str(e)
                            })
            
            return {
                'success': True,
                'total_found': len(prospects),
                'imported_count': imported_count,
                'min_match_score': min_match_score,
                'prospects': [asdict(p) for p in prospects] if not auto_import else [],
                'import_results': import_results,
                'search_criteria': 'board_directors',
                'locations': locations
            }
            
        except Exception as e:
            logger.error(f"Error in board director search: {e}")
            return {
                'success': False,
                'error': str(e),
                'imported_count': 0,
                'total_found': 0
            }
    
    def search_and_import_ai_governance_leaders(self,
                                              locations: List[str] = None,
                                              max_results: int = 50,
                                              auto_import: bool = True,
                                              min_match_score: float = 0.6) -> Dict[str, Any]:
        """
        Search for AI governance leaders using Apollo and optionally auto-import them
        """
        logger.info(f"Starting AI governance leader search with auto_import={auto_import}")
        
        try:
            search_results = self.apollo_client.search_ai_governance_leaders(
                organization_locations=locations,
                per_page=min(max_results, 25)
            )
            
            if not search_results or 'contacts' not in search_results:
                return {
                    'success': False,
                    'error': 'No search results returned from Apollo',
                    'imported_count': 0,
                    'total_found': 0
                }
            
            prospects = []
            for contact in search_results['contacts']:
                prospect = self.apollo_client.convert_to_prospect(contact)
                prospects.append(prospect)
            
            import_results = []
            imported_count = 0
            
            if auto_import:
                for prospect in prospects:
                    if prospect.match_score >= min_match_score:
                        try:
                            opportunity = self._create_executive_opportunity_from_prospect(
                                prospect, 'executive_position', 'apollo_ai_governance_search'
                            )
                            if opportunity:
                                import_results.append({
                                    'prospect_id': prospect.id,
                                    'opportunity_id': opportunity.id,
                                    'match_score': prospect.match_score,
                                    'status': 'imported'
                                })
                                imported_count += 1
                            else:
                                import_results.append({
                                    'prospect_id': prospect.id,
                                    'status': 'skipped_existing'
                                })
                        except Exception as e:
                            logger.error(f"Error importing AI governance prospect {prospect.id}: {e}")
                            import_results.append({
                                'prospect_id': prospect.id,
                                'status': 'import_error',
                                'error': str(e)
                            })
            
            return {
                'success': True,
                'total_found': len(prospects),
                'imported_count': imported_count,
                'min_match_score': min_match_score,
                'prospects': [asdict(p) for p in prospects] if not auto_import else [],
                'import_results': import_results,
                'search_criteria': 'ai_governance_leaders',
                'locations': locations
            }
            
        except Exception as e:
            logger.error(f"Error in AI governance leader search: {e}")
            return {
                'success': False,
                'error': str(e),
                'imported_count': 0,
                'total_found': 0
            }
    
    def enrich_existing_opportunity(self, opportunity_id: int) -> Dict[str, Any]:
        """
        Enrich an existing ExecutiveOpportunity with Apollo data
        
        Args:
            opportunity_id: ID of the existing opportunity
            
        Returns:
            Dict with enrichment results
        """
        try:
            opportunity = ExecutiveOpportunity.query.get(opportunity_id)
            if not opportunity:
                return {
                    'success': False,
                    'error': f'Opportunity {opportunity_id} not found'
                }
            
            # Try to enrich using available information
            enrichment_data = None
            
            # Try to match using Apollo prospect ID if available
            if opportunity.apollo_prospect_id:
                # Apollo doesn't provide a direct "get prospect by ID" endpoint
                # We'll search by the company and try to match
                pass
            
            # Try to enrich using company name or domain
            company_name = opportunity.company
            if company_name:
                try:
                    # Search for people at this company
                    search_results = self.apollo_client.search_people(
                        organization_domains=[company_name.lower().replace(' ', '') + '.com'],
                        person_titles=[opportunity.title] if opportunity.title else None,
                        per_page=5
                    )
                    
                    if search_results and 'contacts' in search_results and search_results['contacts']:
                        # Find the best match
                        best_match = None
                        best_score = 0.0
                        
                        for contact in search_results['contacts']:
                            prospect = self.apollo_client.convert_to_prospect(contact)
                            if prospect.match_score > best_score:
                                best_match = prospect
                                best_score = prospect.match_score
                        
                        if best_match and best_score > 0.6:
                            # Update opportunity with Apollo data
                            self._update_opportunity_with_apollo_data(opportunity, best_match)
                            
                            return {
                                'success': True,
                                'opportunity_id': opportunity_id,
                                'enriched': True,
                                'match_score': best_score,
                                'apollo_prospect_id': best_match.id,
                                'updated_fields': self._get_updated_fields_list()
                            }
                    
                except Exception as e:
                    logger.warning(f"Company-based enrichment failed: {e}")
            
            return {
                'success': True,
                'opportunity_id': opportunity_id,
                'enriched': False,
                'reason': 'No matching Apollo data found'
            }
            
        except Exception as e:
            logger.error(f"Error enriching opportunity {opportunity_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_executive_opportunity_from_prospect(self, 
                                                  prospect: ApolloProspect, 
                                                  opportunity_type: str,
                                                  source: str) -> Optional[ExecutiveOpportunity]:
        """
        Create an ExecutiveOpportunity record from an Apollo prospect
        
        Args:
            prospect: ApolloProspect object
            opportunity_type: Type of opportunity (board_director, executive_position, etc.)
            source: Source identifier for tracking
            
        Returns:
            ExecutiveOpportunity object or None if skipped/error
        """
        try:
            # Check if this prospect already exists
            existing = ExecutiveOpportunity.query.filter_by(
                apollo_prospect_id=prospect.id
            ).first()
            
            if existing:
                logger.info(f"Prospect {prospect.id} already exists as opportunity {existing.id}")
                return None
            
            # Determine company size category for compensation estimation
            company_size_category = self._determine_company_size_category(prospect)
            
            # Estimate compensation based on role and company size
            compensation_range = self.compensation_estimates.get(
                opportunity_type, {}
            ).get(company_size_category, 'TBD')
            
            # Create the opportunity record
            opportunity = ExecutiveOpportunity(
                type=opportunity_type,
                title=prospect.title,
                company=prospect.company_name,
                compensation_range=compensation_range,
                location=prospect.location,
                status='prospect',
                ai_match_score=prospect.match_score,
                requirements=self._extract_requirements_from_prospect(prospect),
                notes=f"Auto-imported from Apollo.io via {source}",
                source='apollo',
                
                # Apollo-specific fields
                apollo_prospect_id=prospect.id,
                apollo_organization_id=prospect.company_id,
                apollo_email=prospect.email,
                apollo_email_status=self._extract_email_status(prospect),
                apollo_phone_number=prospect.phone,
                apollo_linkedin_url=prospect.linkedin_url,
                apollo_seniority=prospect.seniority,
                apollo_last_enriched=datetime.utcnow(),
                apollo_match_criteria=self._create_match_criteria_dict(opportunity_type, source),
                apollo_company_data=self._extract_company_data(prospect),
                apollo_raw_data=prospect.raw_data,
                
                # Set initial pipeline fields
                priority_level=self._determine_priority_level(prospect),
                conversion_probability=min(prospect.match_score + 0.2, 1.0),  # Boost conversion prob slightly
                estimated_close_date=self._estimate_close_date(opportunity_type),
                next_step='Research and initial outreach'
            )
            
            db.session.add(opportunity)
            db.session.commit()
            
            logger.info(f"Created opportunity {opportunity.id} from Apollo prospect {prospect.id}")
            return opportunity
            
        except Exception as e:
            logger.error(f"Error creating opportunity from prospect {prospect.id}: {e}")
            db.session.rollback()
            return None
    
    def _update_opportunity_with_apollo_data(self, 
                                           opportunity: ExecutiveOpportunity, 
                                           prospect: ApolloProspect) -> None:
        """
        Update an existing opportunity with Apollo data
        """
        try:
            opportunity.apollo_prospect_id = prospect.id
            opportunity.apollo_organization_id = prospect.company_id
            opportunity.apollo_email = prospect.email
            opportunity.apollo_email_status = self._extract_email_status(prospect)
            opportunity.apollo_phone_number = prospect.phone
            opportunity.apollo_linkedin_url = prospect.linkedin_url
            opportunity.apollo_seniority = prospect.seniority
            opportunity.apollo_last_enriched = datetime.utcnow()
            opportunity.apollo_company_data = self._extract_company_data(prospect)
            opportunity.apollo_raw_data = prospect.raw_data
            
            # Update match score if Apollo score is higher
            if prospect.match_score > opportunity.ai_match_score:
                opportunity.ai_match_score = prospect.match_score
            
            # Update source if it wasn't from Apollo
            if opportunity.source != 'apollo':
                opportunity.source = f"{opportunity.source}, apollo_enriched"
            
            db.session.commit()
            logger.info(f"Updated opportunity {opportunity.id} with Apollo data")
            
        except Exception as e:
            logger.error(f"Error updating opportunity with Apollo data: {e}")
            db.session.rollback()
    
    def _determine_company_size_category(self, prospect: ApolloProspect) -> str:
        """
        Determine company size category based on prospect data
        """
        if not prospect.raw_data:
            return 'medium'
        
        org_data = prospect.raw_data.get('organization', {})
        employee_count = org_data.get('estimated_num_employees', 0)
        
        if employee_count >= 10000:
            return 'enterprise'
        elif employee_count >= 1000:
            return 'large'
        elif employee_count >= 100:
            return 'medium'
        else:
            return 'small'
    
    def _extract_requirements_from_prospect(self, prospect: ApolloProspect) -> List[str]:
        """
        Extract requirements based on prospect data
        """
        requirements = []
        
        # Add requirements based on title
        title_lower = prospect.title.lower()
        if any(keyword in title_lower for keyword in ['chief', 'ceo', 'president']):
            requirements.extend(['C-suite experience', 'Strategic leadership'])
        
        if any(keyword in title_lower for keyword in ['risk', 'compliance', 'audit']):
            requirements.extend(['GRC expertise', 'Regulatory knowledge'])
        
        if any(keyword in title_lower for keyword in ['board', 'director']):
            requirements.extend(['Board experience', 'Fiduciary responsibility'])
        
        if any(keyword in title_lower for keyword in ['ai', 'artificial intelligence', 'machine learning']):
            requirements.extend(['AI/ML expertise', 'Technology governance'])
        
        return list(set(requirements))  # Remove duplicates
    
    def _extract_email_status(self, prospect: ApolloProspect) -> Optional[str]:
        """
        Extract email status from prospect raw data
        """
        if prospect.raw_data:
            return prospect.raw_data.get('email_status')
        return None
    
    def _extract_company_data(self, prospect: ApolloProspect) -> Dict[str, Any]:
        """
        Extract and structure company data from prospect
        """
        if not prospect.raw_data:
            return {}
        
        org_data = prospect.raw_data.get('organization', {})
        
        return {
            'name': org_data.get('name', prospect.company_name),
            'domain': org_data.get('primary_domain', prospect.company_domain),
            'industry': org_data.get('industry'),
            'employee_count': org_data.get('estimated_num_employees'),
            'revenue': org_data.get('annual_revenue'),
            'description': org_data.get('short_description'),
            'website': org_data.get('website_url'),
            'technologies': org_data.get('technology_names', [])
        }
    
    def _create_match_criteria_dict(self, opportunity_type: str, source: str) -> Dict[str, Any]:
        """
        Create match criteria dictionary for tracking
        """
        return {
            'search_type': opportunity_type,
            'source': source,
            'timestamp': datetime.utcnow().isoformat(),
            'criteria_used': self._get_search_criteria_for_type(opportunity_type)
        }
    
    def _get_search_criteria_for_type(self, opportunity_type: str) -> Dict[str, Any]:
        """
        Get the search criteria used for each opportunity type
        """
        if opportunity_type == 'board_director':
            return {
                'titles': self.opportunity_type_mapping['board_director'],
                'seniorities': ['owner', 'founder', 'c_suite', 'partner'],
                'min_revenue': 500000000
            }
        elif opportunity_type == 'executive_position':
            return {
                'titles': self.opportunity_type_mapping['executive_position'],
                'seniorities': ['c_suite', 'vp', 'head', 'director'],
                'min_revenue': 100000000
            }
        else:
            return {}
    
    def _determine_priority_level(self, prospect: ApolloProspect) -> str:
        """
        Determine priority level based on prospect data
        """
        if prospect.match_score >= 0.9:
            return 'critical'
        elif prospect.match_score >= 0.7:
            return 'high'
        elif prospect.match_score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_close_date(self, opportunity_type: str) -> str:
        """
        Estimate close date based on opportunity type
        """
        if opportunity_type == 'board_director':
            # Board positions typically have longer cycles
            close_date = datetime.now() + timedelta(days=180)
        elif opportunity_type == 'speaking':
            # Speaking opportunities are usually shorter cycle
            close_date = datetime.now() + timedelta(days=60)
        else:
            # Executive positions - medium cycle
            close_date = datetime.now() + timedelta(days=120)
        
        return close_date.strftime('%Y-%m-%d')
    
    def _get_updated_fields_list(self) -> List[str]:
        """
        Get list of fields that were updated during enrichment
        """
        return [
            'apollo_prospect_id', 'apollo_organization_id', 'apollo_email',
            'apollo_email_status', 'apollo_phone_number', 'apollo_linkedin_url',
            'apollo_seniority', 'apollo_company_data', 'apollo_raw_data',
            'ai_match_score'
        ]
    
    def get_import_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get statistics for Apollo imports over the specified period
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with import statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            apollo_opportunities = ExecutiveOpportunity.query.filter(
                ExecutiveOpportunity.source == 'apollo',
                ExecutiveOpportunity.created_at >= cutoff_date
            ).all()
            
            stats = {
                'total_imported': len(apollo_opportunities),
                'by_type': {},
                'by_status': {},
                'average_match_score': 0.0,
                'with_email': 0,
                'with_phone': 0,
                'with_linkedin': 0,
                'period_days': days
            }
            
            if apollo_opportunities:
                # Calculate statistics
                total_match_score = 0.0
                
                for opp in apollo_opportunities:
                    # By type
                    opp_type = opp.type
                    stats['by_type'][opp_type] = stats['by_type'].get(opp_type, 0) + 1
                    
                    # By status
                    status = opp.status
                    stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                    
                    # Match scores
                    total_match_score += opp.ai_match_score
                    
                    # Contact info
                    if opp.apollo_email:
                        stats['with_email'] += 1
                    if opp.apollo_phone_number:
                        stats['with_phone'] += 1
                    if opp.apollo_linkedin_url:
                        stats['with_linkedin'] += 1
                
                stats['average_match_score'] = total_match_score / len(apollo_opportunities)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting import statistics: {e}")
            return {'error': str(e)}


# Convenience function for creating the import service
def create_prospect_import_service() -> Optional[ProspectImportService]:
    """
    Create ProspectImportService instance
    
    Returns:
        ProspectImportService instance or None if Apollo API key not found
    """
    try:
        return ProspectImportService()
    except ValueError as e:
        logger.error(f"Could not create ProspectImportService: {e}")
        return None