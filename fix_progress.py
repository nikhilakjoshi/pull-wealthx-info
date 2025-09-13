#!/usr/bin/env python3
"""
Fix Progress Script

This script fixes the progress tracking when totalDossiers is incorrectly reported as 1.
"""

import json
import os
import sys

def fix_progress():
    """Fix the progress tracking issue"""
    
    progress_file = "progress.json"
    
    print("="*50)
    print("     WealthX Progress Fix Tool")
    print("="*50)
    
    # Read current progress
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        print(f"Current total_records: {progress.get('total_records', 0)}")
        print(f"Current last_processed_index: {progress.get('last_processed_index', 0)}")
    else:
        progress = {
            "last_processed_index": 0,
            "total_records": 0,
            "records_processed": 0,
            "last_batch_time": None,
            "session_id": None,
            "session_start": None,
            "batches_completed": 0,
            "errors": [],
        }
        print("No existing progress file found")
    
    # Fix the progress
    print("\nFixing progress...")
    print("Setting total_records to estimated 420,000 (based on your app description)")
    print("Resetting last_processed_index to 0 to start fresh")
    
    progress.update({
        "last_processed_index": 0,
        "total_records": 420000,  # Based on your app description
        "records_processed": 0,
        "last_batch_time": None,
        "session_id": None,
        "session_start": None,
        "batches_completed": 0,
        "errors": [],
    })
    
    # Save fixed progress
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)
    
    print(f"✅ Progress fixed!")
    print(f"New total_records: {progress['total_records']:,}")
    print(f"New last_processed_index: {progress['last_processed_index']}")
    print("\nYou can now run manual_batch_trigger.py again")
    print("="*50)

if __name__ == "__main__":
    fix_progress()