#!/usr/bin/env python3
"""
Test script for Apollo.io integration
Tests the search functionality for board directors, GRC executives, and AI governance leaders
"""

import os
import json
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our Apollo integration
try:
    from apollo_integration import create_apollo_client, ApolloAPIError
    from prospect_import_service import create_prospect_import_service
    print("✅ Apollo integration modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Apollo integration modules: {e}")
    sys.exit(1)

def test_apollo_connection():
    """Test basic Apollo API connection"""
    print("\n🔍 Testing Apollo API connection...")
    
    try:
        apollo_client = create_apollo_client()
        if not apollo_client:
            print("❌ Apollo client creation failed - API key not configured")
            return False
        print("✅ Apollo client created successfully")
        return True
    except Exception as e:
        print(f"❌ Apollo connection test failed: {e}")
        return False

def test_grc_executive_search():
    """Test GRC executive search functionality"""
    print("\n🔍 Testing GRC Executive Search...")
    
    try:
        apollo_client = create_apollo_client()
        if not apollo_client:
            print("❌ Apollo client not available")
            return False
        
        # Test GRC executive search with limited results
        results = apollo_client.search_grc_executives(
            organization_locations=["United States"],
            page=1,
            per_page=5
        )
        
        if results and 'contacts' in results:
            contact_count = len(results['contacts'])
            print(f"✅ GRC Executive search successful - Found {contact_count} prospects")
            
            # Show sample result
            if contact_count > 0:
                sample_contact = results['contacts'][0]
                print(f"   Sample: {sample_contact.get('name', 'N/A')} at {sample_contact.get('organization_name', 'N/A')}")
                print(f"   Title: {sample_contact.get('title', 'N/A')}")
            return True
        else:
            print("❌ GRC Executive search returned no results")
            return False
            
    except ApolloAPIError as e:
        print(f"❌ Apollo API Error in GRC search: {e.message}")
        if hasattr(e, 'status_code'):
            print(f"   Status Code: {e.status_code}")
        return False
    except Exception as e:
        print(f"❌ GRC Executive search failed: {e}")
        return False

def test_board_director_search():
    """Test board director search functionality"""
    print("\n🔍 Testing Board Director Search...")
    
    try:
        apollo_client = create_apollo_client()
        if not apollo_client:
            print("❌ Apollo client not available")
            return False
        
        # Test board director search with limited results
        results = apollo_client.search_board_directors(
            organization_locations=["United States"],
            page=1,
            per_page=5
        )
        
        if results and 'contacts' in results:
            contact_count = len(results['contacts'])
            print(f"✅ Board Director search successful - Found {contact_count} prospects")
            
            # Show sample result
            if contact_count > 0:
                sample_contact = results['contacts'][0]
                print(f"   Sample: {sample_contact.get('name', 'N/A')} at {sample_contact.get('organization_name', 'N/A')}")
                print(f"   Title: {sample_contact.get('title', 'N/A')}")
            return True
        else:
            print("❌ Board Director search returned no results")
            return False
            
    except ApolloAPIError as e:
        print(f"❌ Apollo API Error in Board Director search: {e.message}")
        if hasattr(e, 'status_code'):
            print(f"   Status Code: {e.status_code}")
        return False
    except Exception as e:
        print(f"❌ Board Director search failed: {e}")
        return False

def test_ai_governance_search():
    """Test AI governance leader search functionality"""
    print("\n🔍 Testing AI Governance Leader Search...")
    
    try:
        apollo_client = create_apollo_client()
        if not apollo_client:
            print("❌ Apollo client not available")
            return False
        
        # Test AI governance leader search with limited results
        results = apollo_client.search_ai_governance_leaders(
            organization_locations=["United States"],
            page=1,
            per_page=5
        )
        
        if results and 'contacts' in results:
            contact_count = len(results['contacts'])
            print(f"✅ AI Governance Leader search successful - Found {contact_count} prospects")
            
            # Show sample result
            if contact_count > 0:
                sample_contact = results['contacts'][0]
                print(f"   Sample: {sample_contact.get('name', 'N/A')} at {sample_contact.get('organization_name', 'N/A')}")
                print(f"   Title: {sample_contact.get('title', 'N/A')}")
            return True
        else:
            print("❌ AI Governance Leader search returned no results")
            return False
            
    except ApolloAPIError as e:
        print(f"❌ Apollo API Error in AI Governance search: {e.message}")
        if hasattr(e, 'status_code'):
            print(f"   Status Code: {e.status_code}")
        return False
    except Exception as e:
        print(f"❌ AI Governance Leader search failed: {e}")
        return False

def test_import_service():
    """Test prospect import service"""
    print("\n🔍 Testing Prospect Import Service...")
    
    try:
        import_service = create_prospect_import_service()
        if not import_service:
            print("❌ Import service creation failed")
            return False
        
        print("✅ Import service created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import service test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Apollo.io Integration Tests")
    print("=" * 50)
    
    # Check API key
    apollo_api_key = os.getenv('APOLLO_API_KEY')
    if apollo_api_key:
        print(f"✅ Apollo API Key configured (ends with: {apollo_api_key[-8:]})")
    else:
        print("❌ Apollo API Key not found in environment")
        return
    
    tests = [
        test_apollo_connection,
        test_grc_executive_search,
        test_board_director_search,
        test_ai_governance_search,
        test_import_service
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All tests passed! Apollo.io integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()