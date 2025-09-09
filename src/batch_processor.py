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
    """Handles batch processing of WealthX data"""

    def __init__(self):
        self.batch_size = int(os.getenv("BATCH_SIZE", 12000))
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

    def process_batch(self, offset: int, batch_size: Optional[int] = None) -> Dict:
        """Process a single batch of records"""
        batch_size = batch_size or self.batch_size

        try:
            # Fetch data from WealthX API
            profiles = self.wealthx_client.get_profiles_batch(offset, batch_size)

            if not profiles:
                self.logger.warning(f"No profiles returned for offset {offset}")
                return {"success": False, "records": 0, "error": "No data returned"}

            # Store in MongoDB
            result = self.mongo_client.bulk_upsert_profiles(profiles)

            # Update progress
            last_id = profiles[-1].get("id") if profiles else None
            self.progress_tracker.update_progress(offset, len(profiles), last_id)

            return {
                "success": True,
                "records": len(profiles),
                "inserted": result["inserted"],
                "updated": result["updated"],
                "errors": result["errors"],
            }

        except Exception as e:
            error_msg = f"Error processing batch at offset {offset}: {str(e)}"
            self.logger.error(error_msg)
            self.progress_tracker.log_error(error_msg, offset)
            return {"success": False, "records": 0, "error": str(e)}

    def run_full_sync(
        self, resume: bool = True, max_batches: Optional[int] = None
    ) -> Dict:
        """Run full synchronization of WealthX data"""
        if not self.validate_connections():
            return {"success": False, "error": "Connection validation failed"}

        session_id = self.progress_tracker.start_session()
        self.logger.info(f"Starting WealthX data sync (Session: {session_id})")

        try:
            # Get total records available
            total_records = self.wealthx_client.get_total_records()
            self.logger.info(f"Total records available: {total_records:,}")

            # Determine starting offset
            start_offset = self.progress_tracker.get_resume_offset() if resume else 0
            if start_offset > 0:
                self.logger.info(f"Resuming from offset: {start_offset:,}")

            # Calculate batches needed
            remaining_records = total_records - start_offset
            estimated_batches = (
                remaining_records + self.batch_size - 1
            ) // self.batch_size

            if max_batches:
                estimated_batches = min(estimated_batches, max_batches)
                self.logger.info(f"Limited to {max_batches} batches")

            self.logger.info(f"Estimated batches to process: {estimated_batches}")

            # Process batches with progress bar
            total_processed = 0
            total_errors = 0

            with tqdm(total=estimated_batches, desc="Processing batches") as pbar:
                current_offset = start_offset
                batch_count = 0

                while current_offset < total_records and (
                    not max_batches or batch_count < max_batches
                ):
                    # Calculate batch size (may be smaller for last batch)
                    current_batch_size = min(
                        self.batch_size, total_records - current_offset
                    )

                    # Process batch
                    result = self.process_batch(current_offset, current_batch_size)

                    if result["success"]:
                        total_processed += result["records"]
                        pbar.set_postfix(
                            {
                                "Processed": f"{total_processed:,}",
                                "Errors": total_errors,
                                "ETA": self.progress_tracker.calculate_eta(
                                    total_records, self.batch_size
                                )
                                or "N/A",
                            }
                        )
                    else:
                        total_errors += 1
                        self.logger.error(f"Batch failed: {result.get('error')}")

                        # Wait before retrying or continuing
                        time.sleep(self.retry_delay)

                    current_offset += current_batch_size
                    batch_count += 1
                    pbar.update(1)

                    # Small delay to avoid overwhelming the API
                    time.sleep(1)

            # Final statistics
            stats = self.progress_tracker.get_statistics()
            final_count = self.mongo_client.get_total_documents()

            self.logger.info(
                f"Sync completed - Batches: {stats['batches_completed']}, "
                f"Records processed: {stats['total_processed']:,}, "
                f"Total in DB: {final_count:,}, "
                f"Errors: {stats['error_count']}"
            )

            return {
                "success": True,
                "session_id": session_id,
                "batches_processed": stats["batches_completed"],
                "records_processed": stats["total_processed"],
                "total_in_database": final_count,
                "errors": stats["error_count"],
            }

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
