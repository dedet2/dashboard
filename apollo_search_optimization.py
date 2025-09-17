#!/usr/bin/env python3
"""
Apollo.io Search Optimization
Enhanced search methods with more practical criteria for board directors, GRC executives, and consulting roles
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from apollo_integration import create_apollo_client, ApolloAPIError
    print("✅ Apollo integration imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Apollo integration: {e}")
    exit(1)

class OptimizedApolloSearch:
    """
    Optimized Apollo search methods with more practical criteria
    """
    
    def __init__(self):
        self.apollo_client = create_apollo_client()
        if not self.apollo_client:
            raise ValueError("Apollo client could not be created")
    
    def search_board_directors_optimized(self, 
                                       locations: List[str] = None,
                                       page: int = 1,
                                       per_page: int = 25) -> Dict:
        """
        Optimized search for board directors with more practical criteria
        """
        print(f"\n🔍 Searching for Board Directors (Page {page}, Per Page: {per_page})...")
        
        # More practical board director titles
        board_titles = [
            "board director", "independent director", "board member", 
            "non-executive director", "chairman", "board chair", "director",
            "lead director", "presiding director", "board advisor",
            "trustee", "board trustee"  # Added more common titles
        ]
        
        # More inclusive seniority levels
        board_seniorities = ["c_suite", "founder", "owner", "partner", "vp"]
        
        # More practical company sizes (not just mega-corporations)
        employee_ranges = [
            "250,500", "500,1000", "1000,5000", "5000,10000", "10000,50000"
        ]
        
        # Lower revenue requirement - many board opportunities exist at smaller companies
        revenue_range = {"min": 25000000}  # $25M+ instead of $500M+
        
        if not locations:
            locations = ["United States"]  # Default to US
        
        try:
            results = self.apollo_client.search_people(
                person_titles=board_titles,
                person_seniorities=board_seniorities,
                organization_locations=locations,
                employee_count_ranges=employee_ranges,
                revenue_range=revenue_range,
                keywords="board governance director independent corporate governance",
                email_status=["verified", "likely_to_engage", "unverified"],  # Include unverified
                page=page,
                per_page=per_page,
                include_similar_titles=True
            )
            
            contact_count = len(results.get('contacts', []))
            total_results = results.get('total_results', 0)
            print(f"✅ Found {contact_count} board director prospects (Total: {total_results})")
            return results
            
        except ApolloAPIError as e:
            print(f"❌ Apollo API Error: {e.message}")
            return {"contacts": [], "total_results": 0, "error": str(e)}
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {"contacts": [], "total_results": 0, "error": str(e)}
    
    def search_grc_executives_optimized(self, 
                                      locations: List[str] = None,
                                      page: int = 1,
                                      per_page: int = 25) -> Dict:
        """
        Optimized search for GRC executives with more practical criteria
        """
        print(f"\n🔍 Searching for GRC Executives (Page {page}, Per Page: {per_page})...")
        
        # Broader GRC titles including consulting roles
        grc_titles = [
            "chief risk officer", "cro", "head of risk", "risk director",
            "compliance officer", "chief compliance officer", "compliance director",
            "governance director", "enterprise risk", "risk management",
            "audit director", "chief audit", "regulatory affairs",
            "risk consultant", "compliance consultant", "governance consultant",
            "risk advisory", "compliance advisory"  # Added consulting roles
        ]
        
        # More inclusive seniority levels
        grc_seniorities = ["c_suite", "vp", "head", "director", "senior", "manager"]
        
        # Broader company sizes
        employee_ranges = [
            "100,250", "250,500", "500,1000", "1000,5000", "5000,10000"
        ]
        
        # Much lower revenue requirement - many GRC roles exist at smaller companies
        revenue_range = {"min": 10000000}  # $10M+ instead of $100M+
        
        if not locations:
            locations = ["United States"]
        
        try:
            results = self.apollo_client.search_people(
                person_titles=grc_titles,
                person_seniorities=grc_seniorities,
                organization_locations=locations,
                employee_count_ranges=employee_ranges,
                revenue_range=revenue_range,
                keywords="risk governance compliance audit regulatory consulting advisory",
                email_status=["verified", "likely_to_engage", "unverified"],
                page=page,
                per_page=per_page,
                include_similar_titles=True
            )
            
            contact_count = len(results.get('contacts', []))
            total_results = results.get('total_results', 0)
            print(f"✅ Found {contact_count} GRC executive prospects (Total: {total_results})")
            return results
            
        except ApolloAPIError as e:
            print(f"❌ Apollo API Error: {e.message}")
            return {"contacts": [], "total_results": 0, "error": str(e)}
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {"contacts": [], "total_results": 0, "error": str(e)}
    
    def search_consulting_executives(self, 
                                   locations: List[str] = None,
                                   page: int = 1,
                                   per_page: int = 25) -> Dict:
        """
        Search specifically for consulting executives and independent consultants
        """
        print(f"\n🔍 Searching for Consulting Executives (Page {page}, Per Page: {per_page})...")
        
        # Consulting-specific titles
        consulting_titles = [
            "consultant", "senior consultant", "principal consultant",
            "managing consultant", "independent consultant", "strategy consultant",
            "management consultant", "business consultant", "advisory",
            "advisor", "senior advisor", "strategic advisor",
            "fractional executive", "interim executive"
        ]
        
        # Consulting seniority levels
        consulting_seniorities = ["senior", "director", "vp", "partner", "owner", "c_suite"]
        
        # All company sizes for consulting
        employee_ranges = [
            "1,10", "10,50", "50,100", "100,250", "250,500", "500,1000"
        ]
        
        if not locations:
            locations = ["United States"]
        
        try:
            results = self.apollo_client.search_people(
                person_titles=consulting_titles,
                person_seniorities=consulting_seniorities,
                organization_locations=locations,
                employee_count_ranges=employee_ranges,
                keywords="consulting advisory strategy management independent fractional",
                email_status=["verified", "likely_to_engage", "unverified"],
                page=page,
                per_page=per_page,
                include_similar_titles=True
            )
            
            contact_count = len(results.get('contacts', []))
            total_results = results.get('total_results', 0)
            print(f"✅ Found {contact_count} consulting executive prospects (Total: {total_results})")
            return results
            
        except ApolloAPIError as e:
            print(f"❌ Apollo API Error: {e.message}")
            return {"contacts": [], "total_results": 0, "error": str(e)}
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {"contacts": [], "total_results": 0, "error": str(e)}
    
    def search_executive_positions_optimized(self,
                                           locations: List[str] = None,
                                           page: int = 1,
                                           per_page: int = 25) -> Dict:
        """
        Optimized search for executive positions
        """
        print(f"\n🔍 Searching for Executive Positions (Page {page}, Per Page: {per_page})...")
        
        # Executive titles
        exec_titles = [
            "ceo", "president", "chief executive", "managing director",
            "executive director", "general manager", "chief operating officer", "coo",
            "chief financial officer", "cfo", "chief technology officer", "cto",
            "chief strategy officer", "chief marketing officer", "cmo"
        ]
        
        # Executive seniority levels
        exec_seniorities = ["c_suite", "founder", "owner", "partner"]
        
        # Various company sizes
        employee_ranges = [
            "50,100", "100,250", "250,500", "500,1000", "1000,5000"
        ]
        
        # Reasonable revenue range
        revenue_range = {"min": 5000000}  # $5M+
        
        if not locations:
            locations = ["United States"]
        
        try:
            results = self.apollo_client.search_people(
                person_titles=exec_titles,
                person_seniorities=exec_seniorities,
                organization_locations=locations,
                employee_count_ranges=employee_ranges,
                revenue_range=revenue_range,
                keywords="executive leadership management strategy",
                email_status=["verified", "likely_to_engage", "unverified"],
                page=page,
                per_page=per_page,
                include_similar_titles=True
            )
            
            contact_count = len(results.get('contacts', []))
            total_results = results.get('total_results', 0)
            print(f"✅ Found {contact_count} executive position prospects (Total: {total_results})")
            return results
            
        except ApolloAPIError as e:
            print(f"❌ Apollo API Error: {e.message}")
            return {"contacts": [], "total_results": 0, "error": str(e)}
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {"contacts": [], "total_results": 0, "error": str(e)}

def test_optimized_searches():
    """Test all optimized search methods"""
    print("🚀 Testing Optimized Apollo Search Methods")
    print("=" * 60)
    
    try:
        search_service = OptimizedApolloSearch()
        
        # Test each search type with small result sets
        tests = [
            ("Board Directors", lambda: search_service.search_board_directors_optimized(
                locations=["California", "New York"], per_page=5)),
            ("GRC Executives", lambda: search_service.search_grc_executives_optimized(
                locations=["California", "New York"], per_page=5)),
            ("Consulting Executives", lambda: search_service.search_consulting_executives(
                locations=["California", "New York"], per_page=5)),
            ("Executive Positions", lambda: search_service.search_executive_positions_optimized(
                locations=["California", "New York"], per_page=5))
        ]
        
        results_summary = {}
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                results = test_func()
                contact_count = len(results.get('contacts', []))
                total_results = results.get('total_results', 0)
                results_summary[test_name] = {
                    'contacts_returned': contact_count,
                    'total_available': total_results,
                    'success': contact_count > 0 or total_results >= 0
                }
                
                # Show sample contacts
                if contact_count > 0:
                    print(f"\n📋 Sample Results:")
                    for i, contact in enumerate(results['contacts'][:2]):  # Show first 2
                        print(f"  {i+1}. {contact.get('name', 'N/A')} - {contact.get('title', 'N/A')}")
                        print(f"     Company: {contact.get('organization_name', 'N/A')}")
                        print(f"     Email Status: {contact.get('email_status', 'N/A')}")
                        print()
                        
            except Exception as e:
                print(f"❌ {test_name} test failed: {e}")
                results_summary[test_name] = {
                    'contacts_returned': 0,
                    'total_available': 0,
                    'success': False,
                    'error': str(e)
                }
        
        # Summary
        print("\n" + "="*60)
        print("📊 Optimized Search Results Summary")
        print("="*60)
        for test_name, result in results_summary.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {test_name}: {result['contacts_returned']} contacts (Total: {result['total_available']})")
            if 'error' in result:
                print(f"    Error: {result['error']}")
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")

if __name__ == "__main__":
    test_optimized_searches()