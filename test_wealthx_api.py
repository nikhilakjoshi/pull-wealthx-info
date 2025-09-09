#!/usr/bin/env python3
"""
Test script to verify WealthX API integration

This script tests the actual WealthX API endpoint format based on the provided curl example.
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()


def test_wealthx_api():
    """Test the WealthX API with the correct format"""

    # Get credentials
    username = os.getenv("WEALTHX_USERNAME")
    password = os.getenv("WEALTHX_PASSWORD")
    base_url = os.getenv("WEALTHX_API_URL", "https://connect.wealthx.com/rest/v1/")

    if not username or not password:
        print("❌ Error: WEALTHX_USERNAME and WEALTHX_PASSWORD must be set in .env")
        return False

    if username == "your_username_here" or password == "your_password_here":
        print("⚠️  Please update .env with your actual WealthX credentials")
        return False

    print("🔄 Testing WealthX API connection...")
    print(f"   API URL: {base_url}")
    print(f"   Username: {username}")

    try:
        # Test the exact format from the provided curl example
        headers = {
            "username": username,
            "password": password,
            "Accept": "application/json",
        }

        params = {
            "dossierType": "both",
            "fromIndex": 1,
            "toIndex": 5,  # Just get 5 records for testing
        }

        url = f"{base_url}alldossiers"
        print(f"   Testing: {url}")
        print(f"   Params: {params}")

        response = requests.get(url, headers=headers, params=params, timeout=30)

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            dossiers = data.get("dossiers", [])
            total_dossiers = data.get("totalDossiers", 0)
            last_index_id = data.get("lastIndexId", 0)

            print("✅ API connection successful!")
            print(f"   Retrieved {len(dossiers)} dossiers")
            print(f"   Total dossiers available: {total_dossiers:,}")
            print(f"   Last index ID: {last_index_id}")

            if dossiers:
                first_dossier = dossiers[0]
                print(f"   Sample record ID: {first_dossier.get('ID', 'N/A')}")
                print(
                    f"   Sample name: {first_dossier.get('firstName', '')} {first_dossier.get('lastName', '')}"
                )
                print(
                    f"   Sample category: {first_dossier.get('dossierCategory', 'N/A')}"
                )

            return True

        elif response.status_code == 401:
            print("❌ Authentication failed - check your username and password")
            return False
        elif response.status_code == 403:
            print("❌ Access forbidden - check your account permissions")
            return False
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out - check your internet connection")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check the API URL and internet connection")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def test_batch_sizes():
    """Test different batch sizes to find optimal setting"""
    username = os.getenv("WEALTHX_USERNAME")
    password = os.getenv("WEALTHX_PASSWORD")
    base_url = os.getenv("WEALTHX_API_URL", "https://connect.wealthx.com/rest/v1/")

    if not username or not password or username == "your_username_here":
        print("⚠️  Skipping batch size test - credentials not configured")
        return

    print("\n🧪 Testing different batch sizes...")

    headers = {"username": username, "password": password, "Accept": "application/json"}

    batch_sizes = [10, 50, 100, 500, 1000]

    for batch_size in batch_sizes:
        try:
            params = {"dossierType": "both", "fromIndex": 1, "toIndex": batch_size}

            response = requests.get(
                f"{base_url}alldossiers", headers=headers, params=params, timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                actual_records = len(data.get("dossiers", []))
                print(
                    f"   ✅ Batch size {batch_size:4d}: Got {actual_records:3d} records"
                )
            else:
                print(
                    f"   ❌ Batch size {batch_size:4d}: Failed ({response.status_code})"
                )

        except Exception as e:
            print(f"   ❌ Batch size {batch_size:4d}: Error - {str(e)}")


def main():
    print("🌟 WealthX API Integration Test")
    print("=" * 50)

    success = test_wealthx_api()

    if success:
        test_batch_sizes()

        print("\n🎉 API integration test completed successfully!")
        print("\nNext steps:")
        print("1. Run: python main.py --max-batches 1")
        print("2. Run: python scheduler.py --run-now")
    else:
        print("\n❌ API integration test failed")
        print("\nTroubleshooting:")
        print("1. Verify your WealthX credentials in .env")
        print("2. Check your internet connection")
        print("3. Contact WealthX support if needed")


if __name__ == "__main__":
    main()
