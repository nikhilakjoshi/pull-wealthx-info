#!/usr/bin/env python3
"""
Debug WealthX API Script

This script helps diagnose issues with the WealthX API connection
and shows the actual API responses.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.wealthx_client import WealthXClient

# Load environment variables
load_dotenv()

def setup_logging():
    """Setup detailed logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

def test_api_connection():
    """Test the WealthX API connection with detailed output"""
    
    print("="*60)
    print("           WealthX API Debug Tool")
    print("="*60)
    
    # Check environment variables
    print("\n1. Environment Variables:")
    print(f"   WEALTHX_API_URL: {os.getenv('WEALTHX_API_URL', 'Not set')}")
    print(f"   WEALTHX_USERNAME: {'Set' if os.getenv('WEALTHX_USERNAME') else 'Not set'}")
    print(f"   WEALTHX_PASSWORD: {'Set' if os.getenv('WEALTHX_PASSWORD') else 'Not set'}")
    
    try:
        # Create client
        print("\n2. Creating WealthX Client...")
        client = WealthXClient()
        print("   ✓ Client created successfully")
        
        # Test basic connection
        print("\n3. Testing Basic Connection...")
        if client.test_connection():
            print("   ✓ Basic connection test passed")
        else:
            print("   ✗ Basic connection test failed")
            return
        
        # Test get total records with detailed response
        print("\n4. Testing Get Total Records...")
        print("   Making API call to get total records...")
        
        # Make the API call manually to see the raw response
        response = client.session.get(
            f"{client.base_url}alldossiers",
            params={"dossierType": "both", "fromIndex": 1, "toIndex": 1},
            timeout=client.timeout,
        )
        
        print(f"   Response Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Data:")
            print(json.dumps(data, indent=4))
            
            total_count = data.get("totalDossiers", 0)
            print(f"\n   Total Dossiers Found: {total_count}")
            
            if total_count == 1:
                print("   ⚠️  WARNING: Only 1 record found - this seems incorrect!")
                print("   This could indicate:")
                print("     - API credentials have limited access")
                print("     - API endpoint or parameters have changed") 
                print("     - Data filtering is applied to your account")
            elif total_count > 100000:
                print(f"   ✓ Found {total_count:,} records - this looks correct!")
            else:
                print(f"   ⚠️  Found {total_count:,} records - lower than expected")
                
        else:
            print(f"   ✗ API call failed with status {response.status_code}")
            print(f"   Response text: {response.text}")
            
        # Test fetching a small batch
        print("\n5. Testing Small Batch Fetch...")
        try:
            dossiers = client.get_profiles_batch(1, 5)
            print(f"   ✓ Successfully fetched {len(dossiers)} dossiers")
            
            if dossiers:
                print("   Sample dossier keys:", list(dossiers[0].keys()) if dossiers else "None")
                
        except Exception as e:
            print(f"   ✗ Batch fetch failed: {e}")
            
    except Exception as e:
        print(f"\n✗ Error creating client or testing API: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "="*60)

def main():
    """Main entry point"""
    setup_logging()
    test_api_connection()

if __name__ == "__main__":
    main()