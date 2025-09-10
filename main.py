#!/usr/bin/env python3
"""
WealthX Data Puller - Main Entry Point

This script pulls WealthX data in batches and stores it in MongoDB.
Supports resume capability and configurable batch sizes.
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


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the application"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "wealthx_pull.log")

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="WealthX Data Puller - Pull WealthX data in batches to MongoDB"
    )

    parser.add_argument(
        "--processing-batch-size",
        type=int,
        help="Number of records to process per session (default: from .env or 14000)",
    )

    parser.add_argument(
        "--max-batches",
        type=int,
        help="Maximum number of batches to process (useful for testing)",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from last successful batch (default: True)",
    )

    parser.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        help="Start from the beginning, ignore previous progress",
    )

    parser.add_argument(
        "--status", action="store_true", help="Show current status and exit"
    )

    parser.add_argument(
        "--cleanup", action="store_true", help="Run cleanup and optimization tasks"
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset progress tracking (use with caution)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Set logging level",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Create batch processor
    processor = BatchProcessor()

    try:
        # Override batch size if provided
        if args.processing_batch_size:
            processor.processing_batch_size = args.processing_batch_size
            logger.info(
                f"Using custom processing batch size: {args.processing_batch_size}"
            )

        # Handle different operations
        if args.status:
            status = processor.get_status()
            print("\n=== WealthX Data Puller Status ===")
            print(f"Database Records: {status['database_records']:,}")
            print(f"Session ID: {status['session_stats'].get('session_id', 'None')}")
            print(f"Batches Completed: {status['session_stats']['batches_completed']}")
            print(
                f"Records Processed: {status['session_stats']['records_processed']:,}"
            )
            print(
                f"Last Processed Index: {status['session_stats']['last_processed_index']:,}"
            )
            print(f"Total Records: {status['session_stats']['total_records']:,}")
            print(f"Errors: {status['session_stats']['error_count']}")
            print(
                f"WealthX API: {'✓' if status['connections']['wealthx_api'] else '✗'}"
            )
            print(f"MongoDB: {'✓' if status['connections']['mongodb'] else '✗'}")
            return

        if args.reset:
            processor.progress_tracker.reset_progress()
            logger.info("Progress tracking has been reset")
            return

        if args.cleanup:
            processor.cleanup_and_optimize()
            return

        # Run main sync process
        logger.info("Starting WealthX data synchronization...")
        logger.info(f"API batch size: {processor.api_batch_size:,}")
        logger.info(f"Processing batch size: {processor.processing_batch_size:,}")
        logger.info(f"Resume mode: {args.resume}")

        if args.max_batches:
            logger.info(f"Max batches: {args.max_batches}")

        result = processor.run_full_sync(
            resume=args.resume, max_batches=args.max_batches
        )

        if result["success"]:
            print("\n=== Synchronization Completed Successfully ===")
            print(f"Session ID: {result['session_id']}")
            print(f"API Calls Made: {result['api_calls_made']}")
            print(f"Session Records: {result['session_records_processed']:,}")
            print(f"Total Records Processed: {result['total_records_processed']:,}")
            print(f"Total in Database: {result['total_in_database']:,}")
            print(f"Completion: {result['completion_percentage']:.2f}%")
            print(f"Est. Remaining Days: {result['estimated_remaining_days']:.1f}")
        else:
            print(f"\n=== Synchronization Failed ===")
            print(f"Error: {result.get('error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\nProcess interrupted. Progress has been saved.")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

    finally:
        # Clean up connections
        processor.close_connections()


if __name__ == "__main__":
    main()
