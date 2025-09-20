#!/usr/bin/env python3
"""
Quick script to check the actual total records in WealthX
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.wealthx_client import WealthXClient

load_dotenv()


def main():
    """Get the actual total records from WealthX"""
    client = WealthXClient()

    try:
        print("Checking WealthX API for total records...")
        total_records = client.get_total_records()
        print(f"Total records available in WealthX: {total_records:,}")
        return total_records
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    main()
