#!/usr/bin/env python3
"""
Configuration Summary for WealthX 10-Day Data Pull

Displays the optimized batch configuration and performance projections.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def show_configuration():
    """Display the current configuration for the 10-day WealthX pull"""

    api_batch_size = int(os.getenv("API_BATCH_SIZE", 500))
    processing_batch_size = int(os.getenv("PROCESSING_BATCH_SIZE", 14000))
    runs_per_day = int(os.getenv("RUNS_PER_DAY", 3))
    target_days = int(os.getenv("TARGET_DAYS", 10))

    # Calculate performance metrics
    records_per_day = runs_per_day * processing_batch_size
    total_capacity = records_per_day * target_days
    api_calls_per_session = processing_batch_size // api_batch_size
    api_calls_per_day = api_calls_per_session * runs_per_day

    print("=" * 60)
    print("🎯 WEALTHX 10-DAY PULL CONFIGURATION")
    print("=" * 60)
    print()
    print("📊 BATCH SETTINGS:")
    print(f"   • API Batch Size (per call):     {api_batch_size:,} records")
    print(f"   • Processing Batch (per session): {processing_batch_size:,} records")
    print(f"   • API calls per session:         {api_calls_per_session}")
    print()
    print("⏰ SCHEDULE SETTINGS:")
    print(f"   • Runs per day:                  {runs_per_day}")
    print(f"   • Target completion:             {target_days} days")
    print()
    print("📈 PERFORMANCE PROJECTION:")
    print(f"   • Records per day:               {records_per_day:,}")
    print(f"   • API calls per day:             {api_calls_per_day}")
    print(
        f"   • Total capacity ({target_days} days):         {total_capacity:,} records"
    )
    print()
    print("🎯 420,000 RECORD TARGET:")
    days_needed = 420000 / records_per_day
    print(f"   • Estimated completion time:     {days_needed:.1f} days")
    print(f"   • Safety margin:                 {target_days - days_needed:.1f} days")
    print()

    # API call analysis
    total_api_calls_needed = (420000 + api_batch_size - 1) // api_batch_size
    total_api_calls_capacity = api_calls_per_day * target_days

    print("🔌 API CALL ANALYSIS:")
    print(f"   • Total API calls needed:        {total_api_calls_needed:,}")
    print(f"   • Total API calls capacity:      {total_api_calls_capacity:,}")
    print(f"   • API calls per session:         {api_calls_per_session}")
    print()

    # Schedule breakdown
    print("📅 DAILY SCHEDULE BREAKDOWN:")
    schedule_times = ["8:00 AM", "2:00 PM", "8:00 PM"]
    for i, time in enumerate(schedule_times[:runs_per_day]):
        print(
            f"   • Run {i+1} at {time:<8}: {processing_batch_size:,} records ({api_calls_per_session} API calls)"
        )
    print()

    if days_needed <= target_days:
        print("✅ Configuration will complete 420k records within 10 days!")
        print(f"   Buffer time: {(target_days - days_needed) * 24:.1f} hours")
    else:
        print("⚠️  Configuration may not complete 420k records in 10 days")
        needed_runs = int(420000 / (processing_batch_size * target_days)) + 1
        print(f"   Consider increasing runs per day to {needed_runs}")

    print()
    print("🛠️  HOW IT WORKS:")
    print(f"   1. Each session makes {api_calls_per_session} API calls")
    print(f"   2. Each API call fetches {api_batch_size} records (WealthX limit)")
    print(f"   3. Total per session: {processing_batch_size:,} records")
    print(f"   4. Runs {runs_per_day} times daily = {records_per_day:,} records/day")
    print("   5. Automatic resume on interruption")
    print("   6. Progress tracking and monitoring")
    print("=" * 60)


def show_current_progress():
    """Show current progress if progress.json exists"""
    try:
        import json

        with open("progress.json", "r") as f:
            progress = json.load(f)

        print("\n📊 CURRENT PROGRESS:")
        print(f"   • Records processed: {progress.get('records_processed', 0):,}")
        print(f"   • Last processed index: {progress.get('last_processed_index', 0):,}")
        if progress.get("total_records"):
            completion = (
                progress.get("records_processed", 0) / progress.get("total_records", 1)
            ) * 100
            print(f"   • Completion: {completion:.2f}%")

        if progress.get("session_start"):
            print(f"   • Session started: {progress.get('session_start')}")

    except FileNotFoundError:
        print("\n📊 No progress file found - ready to start!")
    except Exception as e:
        print(f"\n⚠️  Error reading progress: {e}")


if __name__ == "__main__":
    show_configuration()
    show_current_progress()
