#!/usr/bin/env python3
"""
WealthX Data Puller - Project Overview and Status

This script provides a comprehensive overview of the project structure,
configuration, and current status.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def show_project_structure():
    """Display the project structure"""
    print("📁 PROJECT STRUCTURE")
    print("=" * 50)

    structure = """
pull-wealthx/
├── src/                        # Core application modules
│   ├── __init__.py
│   ├── wealthx_client.py      # WealthX API client
│   ├── mongo_client.py        # MongoDB operations
│   ├── progress_tracker.py    # Resume capability
│   ├── batch_processor.py     # Main processing logic
│   └── config.py              # Configuration management
├── prompts/                   # Project requirements
│   └── pull-wealthx-in-batches.prompt.md
├── logs/                      # Application logs
├── main.py                    # Main CLI application
├── scheduler.py               # Automated scheduling
├── test_setup.py             # System testing
├── setup.sh                  # Setup script
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── .env                     # Environment variables (create from template)
├── progress.json            # Progress tracking (auto-generated)
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
└── README.md               # Documentation
    """

    print(structure)


def show_configuration_guide():
    """Show configuration information"""
    print("\n⚙️  CONFIGURATION")
    print("=" * 50)

    print("Required Environment Variables:")
    print("  WEALTHX_API_KEY     - Your WealthX API key")
    print("  WEALTHX_API_SECRET  - Your WealthX API secret")
    print()
    print("Optional Environment Variables:")
    print("  WEALTHX_API_URL     - API base URL (default: https://api.wealthx.com/v1/)")
    print(
        "  MONGO_URI           - MongoDB connection (default: mongodb://localhost:27017/)"
    )
    print("  MONGO_DATABASE      - Database name (default: wealthx_data)")
    print("  MONGO_COLLECTION    - Collection name (default: profiles)")
    print("  BATCH_SIZE          - Records per batch (default: 12,000)")
    print("  DAILY_RUNS          - Scheduled runs per day (default: 3)")
    print("  MAX_RETRIES         - API retry attempts (default: 3)")
    print("  LOG_LEVEL           - Logging level (default: INFO)")


def show_batch_strategy():
    """Show the batching strategy"""
    print("\n📊 BATCHING STRATEGY")
    print("=" * 50)

    print("Objective: Process ~420,000 WealthX records in 10 days")
    print()
    print("Strategy:")
    print("  • Batch Size: 12,000 records per batch")
    print("  • Total Batches: ~35 batches needed")
    print("  • Schedule: 3-4 runs per day")
    print("  • Batches per Run: ~1-2 batches")
    print("  • Resume Capability: Yes, from last successful batch")
    print()
    print("Timeline:")
    print("  • Day 1-5: ~18 batches (216k records)")
    print("  • Day 6-10: ~17 batches (204k records)")
    print("  • Buffer: Built-in for retries and system maintenance")


def show_usage_examples():
    """Show usage examples"""
    print("\n🚀 USAGE EXAMPLES")
    print("=" * 50)

    examples = [
        ("Check system status", "python main.py --status"),
        ("Test with 1 batch", "python main.py --max-batches 1"),
        ("Run full sync (resume)", "python main.py --resume"),
        ("Run from beginning", "python main.py --no-resume"),
        ("Custom batch size", "python main.py --batch-size 5000"),
        ("Start scheduler", "python scheduler.py"),
        ("Run immediate pull", "python scheduler.py --run-now"),
        ("Test setup", "python test_setup.py"),
        ("Reset progress", "python main.py --reset"),
        ("Cleanup duplicates", "python main.py --cleanup"),
    ]

    for description, command in examples:
        print(f"  {description:<25} {command}")


def show_current_status():
    """Show current project status"""
    print("\n📈 CURRENT STATUS")
    print("=" * 50)

    # Check if .env exists
    env_exists = os.path.exists(".env")
    print(
        f"Configuration file (.env): {'✓ Exists' if env_exists else '✗ Missing (copy from .env.example)'}"
    )

    # Check progress file
    progress_exists = os.path.exists("progress.json")
    if progress_exists:
        try:
            with open("progress.json", "r") as f:
                progress = json.load(f)

            print(f"Progress tracking: ✓ Active")
            print(f"  Last session: {progress.get('session_id', 'N/A')}")
            print(f"  Batches completed: {progress.get('batches_completed', 0)}")
            print(f"  Records processed: {progress.get('total_processed', 0):,}")
            print(f"  Last offset: {progress.get('last_offset', 0):,}")
            print(f"  Errors: {len(progress.get('errors', []))}")
        except Exception:
            print(f"Progress tracking: ⚠️  File exists but unreadable")
    else:
        print(f"Progress tracking: ○ No previous runs")

    # Check logs directory
    logs_exist = os.path.exists("logs") and os.path.isdir("logs")
    if logs_exist:
        log_files = [f for f in os.listdir("logs") if f.endswith(".log")]
        print(f"Logs: ✓ Directory exists ({len(log_files)} log files)")
    else:
        print(f"Logs: ○ No logs directory")


def show_docker_info():
    """Show Docker deployment information"""
    print("\n🐳 DOCKER DEPLOYMENT")
    print("=" * 50)

    print("Quick start with Docker:")
    print("  1. Copy .env.example to .env and configure")
    print("  2. docker-compose up -d mongodb      # Start MongoDB")
    print("  3. docker-compose run wealthx-puller python test_setup.py")
    print("  4. docker-compose run wealthx-puller python main.py --max-batches 1")
    print("  5. docker-compose up scheduler      # Start scheduled pulls")
    print()
    print("Services:")
    print("  • wealthx-puller: Main application")
    print("  • scheduler: Automated scheduling service")
    print("  • mongodb: MongoDB database")


def main():
    """Main function"""
    print("🌟 WealthX Data Puller - Project Overview")
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    show_project_structure()
    show_configuration_guide()
    show_batch_strategy()
    show_usage_examples()
    show_current_status()
    show_docker_info()

    print("\n" + "=" * 70)
    print("📚 For detailed information, see README.md")
    print("🔧 For setup help, run: ./setup.sh")
    print("🧪 For system testing, run: python test_setup.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
