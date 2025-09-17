#!/usr/bin/env python3
"""
Test the fixed database schema for ExecutiveOpportunity
"""

import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    from database import db, ExecutiveOpportunity
    from main import app
    print("✅ Database modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import database modules: {e}")
    sys.exit(1)

def test_database_operations():
    """Test all database operations with the fixed schema"""
    print("🔍 Testing Fixed Database Schema Operations...")
    
    try:
        with app.app_context():
            # Test creating opportunities of different types
            test_opportunities = [
                {
                    "type": "board_director",
                    "title": "Independent Board Director",
                    "company": "Tech Corp Inc.",
                    "compensation_range": "$120,000 - $180,000",
                    "location": "San Francisco, CA",
                    "status": "prospect",
                    "ai_match_score": 0.85,
                    "requirements": ["Board experience", "Tech industry knowledge", "Financial expertise"],
                    "source": "apollo_test",
                    "governance_focus": ["Audit", "Risk", "Technology"],
                    "board_size": 9,
                    "notes": "Excellent board opportunity at fast-growing tech company"
                },
                {
                    "type": "executive_position",
                    "title": "Chief Risk Officer",
                    "company": "Financial Services LLC",
                    "compensation_range": "$300,000 - $400,000",
                    "location": "New York, NY",
                    "status": "prospect",
                    "ai_match_score": 0.92,
                    "requirements": ["CRO experience", "Financial services", "Regulatory knowledge"],
                    "source": "apollo_search",
                    "notes": "Senior executive role with significant growth potential"
                },
                {
                    "type": "consulting_project",
                    "title": "GRC Advisory Engagement",
                    "company": "Manufacturing Giant Corp",
                    "compensation_range": "$2,500/day",
                    "location": "Chicago, IL",
                    "status": "prospect",
                    "ai_match_score": 0.78,
                    "requirements": ["GRC expertise", "Manufacturing industry", "Project management"],
                    "source": "apollo_consulting",
                    "notes": "6-month consulting engagement for risk framework implementation"
                }
            ]
            
            created_opportunities = []
            
            # Create test opportunities
            print(f"\n📝 Creating {len(test_opportunities)} test opportunities...")
            for opp_data in test_opportunities:
                opportunity = ExecutiveOpportunity(**opp_data)
                db.session.add(opportunity)
                db.session.flush()  # Get the ID without committing
                created_opportunities.append(opportunity)
                print(f"   ✅ Created: {opportunity.title} at {opportunity.company} (ID: {opportunity.id})")
            
            db.session.commit()
            print("✅ All opportunities committed to database")
            
            # Test querying
            print("\n🔍 Testing Database Queries...")
            
            # Query by type
            board_directors = ExecutiveOpportunity.query.filter_by(type='board_director').all()
            print(f"   Board Director opportunities: {len(board_directors)}")
            
            executives = ExecutiveOpportunity.query.filter_by(type='executive_position').all()
            print(f"   Executive Position opportunities: {len(executives)}")
            
            consulting = ExecutiveOpportunity.query.filter_by(type='consulting_project').all()
            print(f"   Consulting Project opportunities: {len(consulting)}")
            
            # Query by status
            prospects = ExecutiveOpportunity.query.filter_by(status='prospect').all()
            print(f"   Prospect status opportunities: {len(prospects)}")
            
            # Test updates
            print("\n📝 Testing Updates...")
            if board_directors:
                bd = board_directors[0]
                original_status = bd.status
                bd.status = 'applied'
                bd.notes = f"{bd.notes} - Updated during testing"
                db.session.commit()
                print(f"   ✅ Updated board director status from {original_status} to {bd.status}")
            
            # Test Apollo.io fields
            print("\n🔍 Testing Apollo.io Integration Fields...")
            if created_opportunities:
                opp = created_opportunities[0]
                opp.apollo_prospect_id = "test_apollo_123"
                opp.apollo_email = "director@techcorp.com"
                opp.apollo_email_status = "verified"
                opp.apollo_phone_number = "+1-555-0123"
                opp.apollo_linkedin_url = "https://linkedin.com/in/director123"
                opp.apollo_seniority = "c_suite"
                opp.apollo_last_enriched = datetime.utcnow()
                opp.apollo_company_data = {
                    "name": "Tech Corp Inc.",
                    "industry": "Technology",
                    "employee_count": 1500,
                    "revenue": 250000000
                }
                db.session.commit()
                print("   ✅ Updated Apollo.io integration fields successfully")
            
            # Test serialization
            print("\n📊 Testing Serialization...")
            for opp in created_opportunities:
                opp_dict = opp.to_dict()
                print(f"   ✅ Serialized: {opp.title} - {len(opp_dict)} fields")
                
                # Verify key fields are present
                required_fields = ['id', 'type', 'title', 'company', 'ai_match_score', 'created_at']
                for field in required_fields:
                    if field not in opp_dict:
                        print(f"   ❌ Missing field in serialization: {field}")
                    
            # Clean up test data
            print("\n🧹 Cleaning up test data...")
            for opp in created_opportunities:
                db.session.delete(opp)
            db.session.commit()
            print("   ✅ Test data cleaned up")
            
            print("\n🎉 All database operations completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        # Try to clean up on error
        try:
            db.session.rollback()
        except:
            pass
        return False

def main():
    """Run database tests"""
    print("🚀 Testing Fixed Database Schema")
    print("=" * 50)
    
    if test_database_operations():
        print("\n✅ Database schema is working correctly!")
        print("💡 The ExecutiveOpportunity model can handle:")
        print("   • Board director positions")
        print("   • Executive positions") 
        print("   • Consulting projects")
        print("   • Apollo.io integration fields")
        print("   • Complete CRUD operations")
    else:
        print("\n❌ Database tests failed")

if __name__ == "__main__":
    main()