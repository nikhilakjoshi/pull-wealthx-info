import os
import time
import logging
from typing import Optional, Dict
from tqdm import tqdm
from dotenv import load_dotenv

from .wealthx_client import WealthXClient
from .mongo_client import MongoDBClient
from .progress_tracker import ProgressTracker

load_dotenv()


class BatchProcessor:
    """Handles batch processing of WealthX data with API call limits"""

    def __init__(self):
        self.api_batch_size = int(os.getenv("API_BATCH_SIZE", 500))  # Per API call
        self.processing_batch_size = int(
            os.getenv("PROCESSING_BATCH_SIZE", 14000)
        )  # Per session
        self.retry_delay = int(os.getenv("RETRY_DELAY", 60))

        self.wealthx_client = WealthXClient()
        self.mongo_client = MongoDBClient()
        self.progress_tracker = ProgressTracker()

        self.logger = logging.getLogger(__name__)

    def validate_connections(self) -> bool:
        """Validate all service connections"""
        self.logger.info("Validating service connections...")

        # Test WealthX API connection
        if not self.wealthx_client.test_connection():
            self.logger.error("Failed to connect to WealthX API")
            return False

        # Test MongoDB connection
        if not self.mongo_client.test_connection():
            self.logger.error("Failed to connect to MongoDB")
            return False

        self.logger.info("All service connections validated")
        return True

    def process_batch_session(self, max_batches: Optional[int] = None) -> Dict:
        """
        Process one batch session (multiple API calls up to processing_batch_size)
        This is the main method for scheduled runs
        """
        from datetime import datetime

        session_start_time = datetime.now()
        progress = self.progress_tracker.get_progress()

        # Determine starting index (WealthX uses 1-based indexing)
        current_index = progress.get("last_processed_index", 0) + 1
        total_records = progress.get("total_records", 0)

        # Get total records if not known
        if total_records == 0:
            try:
                total_records = self.wealthx_client.get_total_records()
                self.progress_tracker.update_total_records(total_records)
            except Exception as e:
                self.logger.error(f"Failed to get total records: {e}")
                return {"success": False, "error": str(e)}

        session_records_processed = 0
        session_records_target = self.processing_batch_size

        # Limit by max_batches if specified (for testing)
        if max_batches:
            session_records_target = min(
                session_records_target, max_batches * self.api_batch_size
            )

        self.logger.info(f"Starting batch session from index {current_index}")
        self.logger.info(f"Target records for this session: {session_records_target}")

        api_calls_made = 0

        with tqdm(desc=f"Session Progress", total=session_records_target) as pbar:
            while (
                session_records_processed < session_records_target
                and current_index <= total_records
            ):

                # Calculate end index for this API call
                to_index = min(
                    current_index + self.api_batch_size - 1,
                    current_index
                    + (session_records_target - session_records_processed)
                    - 1,
                    total_records,
                )

                if current_index > to_index:
                    break

                try:
                    # Make API call
                    self.logger.info(
                        f"API call {api_calls_made + 1}: Fetching records {current_index} to {to_index}"
                    )
                    dossiers = self.wealthx_client.get_profiles_batch(
                        current_index, to_index
                    )

                    if not dossiers:
                        self.logger.warning(
                            f"No records returned for range {current_index}-{to_index}"
                        )
                        break

                    # Store in MongoDB
                    result = self.mongo_client.bulk_upsert_profiles(dossiers)
                    records_in_batch = len(dossiers)

                    self.logger.info(
                        f"Stored {records_in_batch} dossiers (Inserted: {result['inserted']}, Updated: {result['updated']})"
                    )

                    # Update progress
                    session_records_processed += records_in_batch
                    current_index = to_index + 1
                    api_calls_made += 1

                    # Update progress tracker
                    self.progress_tracker.update_progress(
                        last_processed_index=to_index,
                        records_processed=progress.get("records_processed", 0)
                        + records_in_batch,
                        session_start=session_start_time.isoformat(),
                    )

                    # Update progress bar
                    pbar.update(records_in_batch)
                    pbar.set_postfix(
                        {
                            "API Calls": api_calls_made,
                            "Records": session_records_processed,
                            "Last Index": to_index,
                        }
                    )

                    # Small delay between API calls to be respectful
                    time.sleep(1)

                except Exception as e:
                    self.logger.error(
                        f"Error processing batch {current_index}-{to_index}: {e}"
                    )
                    # Move to next batch instead of failing entire session
                    current_index += self.api_batch_size
                    continue

        session_end_time = datetime.now()
        session_duration = (session_end_time - session_start_time).total_seconds()

        # Calculate progress statistics
        final_progress = self.progress_tracker.get_progress()
        total_processed = final_progress.get("records_processed", 0)
        completion_percentage = (
            (total_processed / total_records * 100) if total_records > 0 else 0
        )

        result = {
            "success": True,
            "session_records_processed": session_records_processed,
            "api_calls_made": api_calls_made,
            "total_records_processed": total_processed,
            "total_records": total_records,
            "completion_percentage": round(completion_percentage, 2),
            "session_duration_seconds": round(session_duration, 2),
            "last_processed_index": current_index - 1,
            "estimated_remaining_days": self._estimate_remaining_time(
                total_processed, total_records
            ),
        }

        self.logger.info(f"Batch session completed: {result}")
        return result

    def _estimate_remaining_time(self, processed: int, total: int) -> float:
        """Estimate remaining days based on current progress"""
        if processed <= 0:
            return 10.0

        runs_per_day = int(os.getenv("RUNS_PER_DAY", 3))
        avg_per_run = self.processing_batch_size  # Expected records per run
        remaining_records = total - processed
        remaining_runs = remaining_records / max(1, avg_per_run)
        return remaining_runs / runs_per_day

    def run_full_sync(
        self, resume: bool = True, max_batches: Optional[int] = None
    ) -> Dict:
        """Run full synchronization of WealthX data using batch sessions"""
        if not self.validate_connections():
            return {"success": False, "error": "Connection validation failed"}

        session_id = self.progress_tracker.start_session()
        self.logger.info(f"Starting WealthX data sync (Session: {session_id})")

        try:
            # Use the new batch session processor
            result = self.process_batch_session(max_batches)

            if result["success"]:
                # Get final statistics
                stats = self.progress_tracker.get_statistics()
                final_count = self.mongo_client.get_total_documents()

                self.logger.info(
                    f"Sync session completed - API calls: {result['api_calls_made']}, "
                    f"Records processed: {result['session_records_processed']:,}, "
                    f"Total in DB: {final_count:,}, "
                    f"Progress: {result['completion_percentage']:.2f}%"
                )

                return {
                    "success": True,
                    "session_id": session_id,
                    "api_calls_made": result["api_calls_made"],
                    "session_records_processed": result["session_records_processed"],
                    "total_records_processed": result["total_records_processed"],
                    "total_in_database": final_count,
                    "completion_percentage": result["completion_percentage"],
                    "estimated_remaining_days": result["estimated_remaining_days"],
                    "session_duration_seconds": result["session_duration_seconds"],
                }
            else:
                return result

        except Exception as e:
            self.logger.error(f"Fatal error during sync: {str(e)}")
            return {"success": False, "error": str(e)}

    def cleanup_and_optimize(self):
        """Run cleanup and optimization tasks"""
        self.logger.info("Running cleanup and optimization...")

        # Remove duplicates
        duplicates_removed = self.mongo_client.cleanup_duplicates()

        self.logger.info(
            f"Cleanup completed - Duplicates removed: {duplicates_removed}"
        )

    def get_status(self) -> Dict:
        """Get current status and statistics"""
        stats = self.progress_tracker.get_statistics()
        db_count = self.mongo_client.get_total_documents()

        return {
            "database_records": db_count,
            "session_stats": stats,
            "connections": {
                "wealthx_api": self.wealthx_client.test_connection(),
                "mongodb": self.mongo_client.test_connection(),
            },
        }

    def close_connections(self):
        """Close all service connections"""
        self.mongo_client.close()
        self.logger.info("All connections closed")
