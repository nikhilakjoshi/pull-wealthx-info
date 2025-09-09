#!/usr/bin/env python3
"""
WealthX Data Puller Scheduler

Schedules the WealthX data pull to run 3-4 times per day automatically.
Designed to complete 420k records in 10 days with resume capability.
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.batch_processor import BatchProcessor

# Load environment variables
load_dotenv()


class WealthXScheduler:
    """Scheduler for automated WealthX data pulls"""

    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.processor = BatchProcessor()

        # Schedule configuration
        self.daily_runs = int(os.getenv("DAILY_RUNS", 3))  # 3-4 runs per day
        self.max_runtime_hours = int(
            os.getenv("MAX_RUNTIME_HOURS", 2)
        )  # Max 2 hours per run

        self.logger.info(
            f"Scheduler initialized: {self.daily_runs} runs per day, "
            f"max {self.max_runtime_hours}h per run"
        )

    def setup_logging(self):
        """Setup logging for scheduler"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "scheduler.log")),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def calculate_batch_limit(self) -> int:
        """Calculate how many batches to run per session to finish in 10 days"""
        try:
            total_records = self.processor.wealthx_client.get_total_records()
            batch_size = self.processor.batch_size
            total_batches_needed = (total_records + batch_size - 1) // batch_size

            # 10 days * daily_runs = total sessions
            total_sessions = 10 * self.daily_runs
            batches_per_session = (
                total_batches_needed + total_sessions - 1
            ) // total_sessions

            self.logger.info(
                f"Calculated {batches_per_session} batches per session "
                f"(Total: {total_batches_needed}, Sessions: {total_sessions})"
            )

            return batches_per_session

        except Exception as e:
            self.logger.error(f"Error calculating batch limit: {e}")
            # Fallback to a reasonable default
            return 5  # Conservative fallback

    def run_scheduled_pull(self):
        """Execute a scheduled data pull"""
        start_time = datetime.now()
        self.logger.info(f"Starting scheduled WealthX pull at {start_time}")

        try:
            # Calculate batch limit for this session
            batch_limit = self.calculate_batch_limit()

            # Run the sync with batch limit
            result = self.processor.run_full_sync(resume=True, max_batches=batch_limit)

            duration = datetime.now() - start_time

            if result["success"]:
                self.logger.info(f"Scheduled pull completed successfully in {duration}")
                self.logger.info(
                    f"Processed {result['records_processed']:,} records "
                    f"in {result['batches_processed']} batches"
                )
            else:
                self.logger.error(f"Scheduled pull failed: {result.get('error')}")

        except Exception as e:
            self.logger.error(f"Error during scheduled pull: {str(e)}")

        finally:
            # Always close connections after each run
            self.processor.close_connections()

    def setup_schedule(self):
        """Setup the pull schedule"""
        if self.daily_runs == 3:
            # 3 times per day: 8 AM, 2 PM, 8 PM
            schedule.every().day.at("08:00").do(self.run_scheduled_pull)
            schedule.every().day.at("14:00").do(self.run_scheduled_pull)
            schedule.every().day.at("20:00").do(self.run_scheduled_pull)
            self.logger.info("Schedule: 3 times daily (8:00, 14:00, 20:00)")

        elif self.daily_runs == 4:
            # 4 times per day: 6 AM, 12 PM, 6 PM, 12 AM
            schedule.every().day.at("06:00").do(self.run_scheduled_pull)
            schedule.every().day.at("12:00").do(self.run_scheduled_pull)
            schedule.every().day.at("18:00").do(self.run_scheduled_pull)
            schedule.every().day.at("00:00").do(self.run_scheduled_pull)
            self.logger.info("Schedule: 4 times daily (6:00, 12:00, 18:00, 00:00)")

        else:
            # Custom schedule - distribute evenly throughout the day
            hours_between = 24 // self.daily_runs
            for i in range(self.daily_runs):
                hour = (i * hours_between) % 24
                time_str = f"{hour:02d}:00"
                schedule.every().day.at(time_str).do(self.run_scheduled_pull)

            self.logger.info(
                f"Schedule: {self.daily_runs} times daily, "
                f"every {hours_between} hours"
            )

    def run_scheduler(self):
        """Run the scheduler"""
        self.logger.info("WealthX Scheduler started")

        # Validate connections before starting
        if not self.processor.validate_connections():
            self.logger.error("Connection validation failed. Cannot start scheduler.")
            return

        # Setup schedule
        self.setup_schedule()

        # Show next scheduled runs
        self.show_next_runs()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")

        except Exception as e:
            self.logger.error(f"Scheduler error: {str(e)}")

    def show_next_runs(self):
        """Show information about next scheduled runs"""
        jobs = schedule.get_jobs()
        if jobs:
            self.logger.info("Scheduled runs:")
            for job in jobs[:5]:  # Show next 5 runs
                next_run = job.next_run
                if next_run:
                    self.logger.info(f"  - {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    def run_once_now(self):
        """Run a single pull immediately (for testing)"""
        self.logger.info("Running immediate pull...")
        batch_limit = self.calculate_batch_limit()

        result = self.processor.run_full_sync(resume=True, max_batches=batch_limit)

        if result["success"]:
            print(f"Pull completed: {result['records_processed']:,} records processed")
        else:
            print(f"Pull failed: {result.get('error')}")


def main():
    """Main entry point for scheduler"""
    import argparse

    parser = argparse.ArgumentParser(description="WealthX Data Pull Scheduler")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run a single pull immediately instead of starting scheduler",
    )
    parser.add_argument(
        "--daily-runs", type=int, choices=[3, 4], help="Number of runs per day (3 or 4)"
    )

    args = parser.parse_args()

    # Override daily runs if provided
    if args.daily_runs:
        os.environ["DAILY_RUNS"] = str(args.daily_runs)

    scheduler = WealthXScheduler()

    if args.run_now:
        scheduler.run_once_now()
    else:
        scheduler.run_scheduler()


if __name__ == "__main__":
    main()
