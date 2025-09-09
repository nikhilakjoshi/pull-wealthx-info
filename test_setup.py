#!/usr/bin/env python3
"""
Test script for WealthX Data Puller

This script tests various components of the system to ensure everything is working correctly.
"""

import os
import sys
import logging
from typing import Dict, Any

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.config import validate_environment, get_batch_schedule
from src.wealthx_client import WealthXClient
from src.mongo_client import MongoDBClient
from src.progress_tracker import ProgressTracker
from src.batch_processor import BatchProcessor


def test_environment() -> Dict[str, Any]:
    """Test environment configuration"""
    print("Testing environment configuration...")

    validation = validate_environment()

    if validation["valid"]:
        print("✓ Environment configuration is valid")
        if validation["using_defaults"]:
            print("  Using default values for:")
            for default in validation["using_defaults"]:
                print(f"    - {default}")
    else:
        print("✗ Environment configuration is invalid")
        print("  Missing required variables:")
        for var in validation["missing_required"]:
            print(f"    - {var}")

    return validation


def test_wealthx_connection() -> bool:
    """Test WealthX API connection"""
    print("\nTesting WealthX API connection...")

    try:
        client = WealthXClient()
        if client.test_connection():
            print("✓ WealthX API connection successful")

            # Try to get record count
            try:
                count = client.get_total_records()
                print(f"  Total records available: {count:,}")
                return True
            except Exception as e:
                print(f"  Warning: Could not get record count: {e}")
                return True  # Connection works, but API might have issues
        else:
            print("✗ WealthX API connection failed")
            return False

    except Exception as e:
        print(f"✗ WealthX API connection error: {e}")
        return False


def test_mongodb_connection() -> bool:
    """Test MongoDB connection"""
    print("\nTesting MongoDB connection...")

    try:
        client = MongoDBClient()
        if client.test_connection():
            print("✓ MongoDB connection successful")

            # Get current document count
            count = client.get_total_documents()
            print(f"  Current documents in database: {count:,}")
            return True
        else:
            print("✗ MongoDB connection failed")
            return False

    except Exception as e:
        print(f"✗ MongoDB connection error: {e}")
        return False


def test_progress_tracker() -> bool:
    """Test progress tracking functionality"""
    print("\nTesting progress tracker...")

    try:
        tracker = ProgressTracker("test_progress.json")

        # Test basic functionality
        session_id = tracker.start_session()
        print(f"✓ Progress tracker initialized (Session: {session_id})")

        # Test progress update
        tracker.update_progress(0, 100, "test_id")
        stats = tracker.get_statistics()
        print(f"✓ Progress tracking working (Processed: {stats['total_processed']})")

        # Clean up test file
        if os.path.exists("test_progress.json"):
            os.remove("test_progress.json")

        return True

    except Exception as e:
        print(f"✗ Progress tracker error: {e}")
        return False


def test_batch_calculation() -> bool:
    """Test batch size calculations"""
    print("\nTesting batch calculations...")

    try:
        # Test with sample data
        schedule = get_batch_schedule(
            420000, 10, 3
        )  # 420k records, 10 days, 3 runs/day

        print(f"✓ Batch calculation successful:")
        print(f"  Total records: {schedule['total_records']:,}")
        print(f"  Total batches: {schedule['total_batches']:,}")
        print(f"  Batch size: {schedule['batch_size']:,}")
        print(f"  Batches per run: {schedule['batches_per_run']}")
        print(
            f"  Estimated completion: {schedule['estimated_completion_days']:.1f} days"
        )

        return True

    except Exception as e:
        print(f"✗ Batch calculation error: {e}")
        return False


def test_batch_processor() -> bool:
    """Test batch processor initialization"""
    print("\nTesting batch processor...")

    try:
        processor = BatchProcessor()
        print("✓ Batch processor initialized successfully")

        # Test connection validation
        connections_valid = processor.validate_connections()
        if connections_valid:
            print("✓ All service connections validated")
        else:
            print("✗ Some service connections failed")

        processor.close_connections()
        return connections_valid

    except Exception as e:
        print(f"✗ Batch processor error: {e}")
        return False


def run_comprehensive_test() -> None:
    """Run all tests and provide summary"""
    print("=" * 60)
    print("WealthX Data Puller - Comprehensive Test Suite")
    print("=" * 60)

    # Configure minimal logging for tests
    logging.basicConfig(level=logging.ERROR)

    # Run all tests
    tests = [
        ("Environment Configuration", test_environment),
        ("WealthX API Connection", test_wealthx_connection),
        ("MongoDB Connection", test_mongodb_connection),
        ("Progress Tracker", test_progress_tracker),
        ("Batch Calculations", test_batch_calculation),
        ("Batch Processor", test_batch_processor),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            if test_name == "Environment Configuration":
                result = test_func()
                results[test_name] = result["valid"]
            else:
                results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<30} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Run: python main.py --status")
        print("2. Test with: python main.py --max-batches 1")
        print("3. Start scheduler: python scheduler.py")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and connections.")

        if not results.get("Environment Configuration", False):
            print("\n💡 Make sure to:")
            print("1. Copy .env.example to .env")
            print("2. Add your WealthX API credentials to .env")

        if not results.get("MongoDB Connection", False):
            print("3. Ensure MongoDB is running and accessible")


if __name__ == "__main__":
    run_comprehensive_test()
