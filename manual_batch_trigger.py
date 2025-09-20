#!/usr/bin/env python3
"""
Manual Batch Trigger Script for WealthX Data Puller

This script allows you to manually trigger batch processing sessions
with various options for testing and manual control.
"""

import os
import sys
import logging
import argparse
from typing import Optional
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.batch_processor import BatchProcessor

# Load environment variables
load_dotenv()


def setup_logging(log_level: str = "INFO", quiet: bool = False) -> None:
    """Configure logging for the script"""
    if quiet:
        log_level = "ERROR"

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "manual_batch.log")

    handlers = [logging.FileHandler(log_file)]
    if not quiet:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)


def print_status(processor: BatchProcessor) -> None:
    """Print current status in a formatted way"""
    status = processor.get_status()

    print("\n" + "=" * 50)
    print("     WealthX Data Puller - Current Status")
    print("=" * 50)
    print(f"Database Records:     {status['database_records']:,}")
    print(f"Session ID:           {status['session_stats'].get('session_id', 'None')}")
    print(f"Batches Completed:    {status['session_stats']['batches_completed']}")
    print(f"Records Processed:    {status['session_stats']['records_processed']:,}")
    print(f"Last Index:           {status['session_stats']['last_processed_index']:,}")
    print(f"Target DB Records:    {status['session_stats']['target_db_records']:,}")
    print(f"Errors:               {status['session_stats']['error_count']}")
    print(
        f"WealthX API:          {'✓ Connected' if status['connections']['wealthx_api'] else '✗ Failed'}"
    )
    print(
        f"MongoDB:              {'✓ Connected' if status['connections']['mongodb'] else '✗ Failed'}"
    )

    target_db_records = status["session_stats"]["target_db_records"]
    if target_db_records > 0:
        completion = (
            status["session_stats"]["records_processed"] / target_db_records
        ) * 100
        print(f"Completion:           {completion:.2f}%")

    print("=" * 50)


def run_batch_session(
    processor: BatchProcessor,
    max_batches: Optional[int] = None,
    processing_batch_size: Optional[int] = None,
) -> dict:
    """Run a single batch session"""

    if processing_batch_size:
        processor.processing_batch_size = processing_batch_size
        print(f"Using custom processing batch size: {processing_batch_size:,}")

    print(f"\nStarting batch session...")
    print(f"API batch size: {processor.api_batch_size}")
    print(f"Processing batch size: {processor.processing_batch_size:,}")

    if max_batches:
        print(f"Limited to {max_batches} API batches")

    result = processor.process_batch_session(max_batches=max_batches)
    return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manual WealthX Batch Trigger - Run WealthX data pulls manually",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a single batch session with default settings
  python manual_batch_trigger.py
  
  # Run with custom processing batch size
  python manual_batch_trigger.py --processing-batch-size 5000
  
  # Run limited number of API batches (for testing)
  python manual_batch_trigger.py --max-api-batches 5
  
  # Just check status
  python manual_batch_trigger.py --status-only
  
  # Run full sync (multiple sessions until complete)
  python manual_batch_trigger.py --full-sync
  
  # Set target database records count
  python manual_batch_trigger.py --set-target-records 2500000
  
  # Refresh total records count from API
  python manual_batch_trigger.py --refresh-total
  
  # Reset progress (use with caution)
  python manual_batch_trigger.py --reset-progress
        """,
    )

    parser.add_argument(
        "--processing-batch-size",
        type=int,
        help="Number of records to process in this session (default: from .env or 14000)",
    )

    parser.add_argument(
        "--max-api-batches",
        type=int,
        help="Maximum number of API batches to process (useful for testing)",
    )

    parser.add_argument(
        "--status-only",
        action="store_true",
        help="Only show current status and exit",
    )

    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="Run full synchronization (multiple sessions until complete)",
    )

    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start from the beginning, ignore previous progress",
    )

    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Reset progress tracking (use with caution)",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Run cleanup and optimization tasks",
    )

    parser.add_argument(
        "--set-target-records",
        type=int,
        help="Set the target database records count (e.g., 2500000)",
    )

    parser.add_argument(
        "--refresh-total",
        action="store_true",
        help="Refresh the total records count from WealthX API",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Set logging level",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output (logs still written to file)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level, args.quiet)
    logger = logging.getLogger(__name__)

    # Create batch processor
    processor = BatchProcessor()

    try:
        # Handle set target records
        if args.set_target_records:
            print(f"🎯 Setting target database records to: {args.set_target_records:,}")
            processor.progress_tracker.update_target_db_records(args.set_target_records)
            print("✅ Target database records updated")
            return

        # Handle refresh total records
        if args.refresh_total:
            print("🔄 Refreshing total records count from WealthX API...")
            try:
                total_records = processor.refresh_total_records()
                print(f"✅ Total records updated to: {total_records:,}")
            except Exception as e:
                print(f"❌ Failed to refresh total records: {e}")
            return

        # Handle reset progress
        if args.reset_progress:
            print("⚠️  WARNING: This will reset all progress tracking!")
            confirmation = input("Type 'YES' to confirm: ")
            if confirmation == "YES":
                processor.progress_tracker.reset_progress()
                logger.info("Progress tracking has been reset")
                print("✅ Progress tracking has been reset")
            else:
                print("❌ Reset cancelled")
            return

        # Handle cleanup
        if args.cleanup:
            print("🧹 Running cleanup and optimization...")
            processor.cleanup_and_optimize()
            print("✅ Cleanup completed")
            return

        # Always show status first
        if not args.quiet:
            print_status(processor)

        # Handle status-only request
        if args.status_only:
            return

        # Validate connections
        print("\n🔍 Validating connections...")
        if not processor.validate_connections():
            print("❌ Connection validation failed")
            return

        print("✅ All connections validated")

        # Handle full sync
        if args.full_sync:
            print("\n🚀 Starting FULL synchronization...")
            print("This will run multiple sessions until all data is processed.")

            result = processor.run_full_sync(
                resume=not args.no_resume, max_batches=args.max_api_batches
            )

            if result["success"]:
                print("\n" + "=" * 50)
                print("     FULL SYNCHRONIZATION COMPLETED")
                print("=" * 50)
                print(f"Session ID:           {result['session_id']}")
                print(f"API Calls Made:       {result['api_calls_made']}")
                print(f"Session Records:      {result['session_records_processed']:,}")
                print(f"Total Processed:      {result['total_records_processed']:,}")
                print(f"Total in Database:    {result['total_in_database']:,}")
                print(f"Completion:           {result['completion_percentage']:.2f}%")
                print(f"Est. Remaining Days:  {result['estimated_remaining_days']:.1f}")
                if result.get("consecutive_empty_batches", 0) > 0:
                    print(
                        f"Empty Batches Skipped: {result['consecutive_empty_batches']}"
                    )
                print("=" * 50)
            else:
                print(f"\n❌ Full synchronization failed: {result.get('error')}")
                sys.exit(1)

        else:
            # Run single batch session
            print("\n🚀 Starting batch session...")

            result = run_batch_session(
                processor,
                max_batches=args.max_api_batches,
                processing_batch_size=args.processing_batch_size,
            )

            if result["success"]:
                print("\n" + "=" * 50)
                print("     BATCH SESSION COMPLETED")
                print("=" * 50)
                print(f"Session Records:      {result['session_records_processed']:,}")
                print(f"API Calls Made:       {result['api_calls_made']}")
                print(f"Total Processed:      {result['total_records_processed']:,}")
                print(f"Completion:           {result['completion_percentage']:.2f}%")
                print(f"Est. Remaining Days:  {result['estimated_remaining_days']:.1f}")
                print(
                    f"Session Duration:     {result['session_duration_seconds']:.1f}s"
                )
                if result.get("consecutive_empty_batches", 0) > 0:
                    print(
                        f"Empty Batches Skipped: {result['consecutive_empty_batches']}"
                    )
                    print(
                        f"End Reason:           {result.get('end_reason', 'unknown')}"
                    )
                print("=" * 50)
            else:
                print(f"\n❌ Batch session failed: {result.get('error')}")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\n⏹️  Process interrupted. Progress has been saved.")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

    finally:
        # Clean up connections
        processor.close_connections()


if __name__ == "__main__":
    main()
