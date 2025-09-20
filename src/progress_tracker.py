import os
import json
from typing import Dict, Optional
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()


class ProgressTracker:
    """Tracks progress and enables resume capability"""

    def __init__(self, progress_file: str = "progress.json"):
        self.progress_file = progress_file
        self.logger = logging.getLogger(__name__)
        self.progress_data = self._load_progress()

    def _load_progress(self) -> Dict:
        """Load progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.warning(f"Could not load progress file: {e}")

        return {
            "last_processed_index": 0,  # WealthX uses 1-based indexing
            "total_records": 0,  # Deprecated: ID range estimate
            "target_db_records": 2500000,  # Target: actual DB record count
            "records_processed": 0,
            "last_batch_time": None,
            "session_id": None,
            "session_start": None,
            "batches_completed": 0,
            "errors": [],
        }

    def _save_progress(self):
        """Save progress to file"""
        try:
            with open(self.progress_file, "w") as f:
                json.dump(self.progress_data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Could not save progress: {e}")

    def start_session(self) -> str:
        """Start a new tracking session"""
        session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.progress_data["session_id"] = session_id
        self.progress_data["session_start"] = datetime.utcnow().isoformat()
        self._save_progress()
        return session_id

    def get_progress(self) -> Dict:
        """Get current progress data"""
        # Ensure target_db_records exists for backward compatibility
        if "target_db_records" not in self.progress_data:
            self.progress_data["target_db_records"] = 2500000
            self._save_progress()
        return self.progress_data

    def update_target_db_records(self, target_db_records: int):
        """Update the target database records count"""
        self.progress_data["target_db_records"] = target_db_records
        self._save_progress()

    def update_total_records(self, total_records: int):
        """Update the total records count (deprecated, kept for compatibility)"""
        self.progress_data["total_records"] = total_records
        self._save_progress()

    def get_resume_index(self) -> int:
        """Get the index to resume from (1-based)"""
        return self.progress_data.get("last_processed_index", 0) + 1

    def update_progress(
        self,
        last_processed_index: int,
        records_processed: int,
        session_start: Optional[str] = None,
    ):
        """Update progress after successful batch session"""
        self.progress_data.update(
            {
                "last_processed_index": last_processed_index,
                "records_processed": records_processed,
                "last_batch_time": datetime.utcnow().isoformat(),
                "batches_completed": self.progress_data.get("batches_completed", 0) + 1,
            }
        )

        if session_start:
            self.progress_data["session_start"] = session_start

        self._save_progress()

        self.logger.info(
            f"Progress updated: {records_processed:,} total records processed, "
            f"last index: {last_processed_index:,}"
        )

    def log_error(self, error: str, index: int):
        """Log an error during processing"""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(error),
            "index": index,
        }

        if "errors" not in self.progress_data:
            self.progress_data["errors"] = []

        self.progress_data["errors"].append(error_entry)
        self._save_progress()

    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        return {
            "batches_completed": self.progress_data.get("batches_completed", 0),
            "records_processed": self.progress_data.get("records_processed", 0),
            "last_processed_index": self.progress_data.get("last_processed_index", 0),
            "total_records": self.progress_data.get("total_records", 0),  # Deprecated
            "target_db_records": self.progress_data.get("target_db_records", 2500000),
            "session_id": self.progress_data.get("session_id"),
            "session_start": self.progress_data.get("session_start"),
            "last_batch_time": self.progress_data.get("last_batch_time"),
            "error_count": len(self.progress_data.get("errors", [])),
        }

    def reset_progress(self):
        """Reset progress tracking"""
        self.progress_data = {
            "last_processed_index": 0,
            "total_records": 0,  # Deprecated
            "target_db_records": 2500000,  # Target DB record count
            "records_processed": 0,
            "last_batch_time": None,
            "session_id": None,
            "session_start": None,
            "batches_completed": 0,
            "errors": [],
        }
        self._save_progress()
        self.logger.info("Progress tracking reset")

    def calculate_eta(self, total_records: int, batch_size: int) -> Optional[str]:
        """Calculate estimated time to completion"""
        if not self.progress_data.get("session_start") or not self.progress_data.get(
            "last_batch_time"
        ):
            return None

        try:
            start_time = datetime.fromisoformat(self.progress_data["session_start"])
            current_time = datetime.utcnow()
            elapsed = (current_time - start_time).total_seconds()

            processed = self.progress_data["records_processed"]
            remaining = total_records - processed

            if processed == 0 or elapsed == 0:
                return None

            rate = processed / elapsed  # records per second
            eta_seconds = remaining / rate

            hours = int(eta_seconds // 3600)
            minutes = int((eta_seconds % 3600) // 60)

            return f"{hours}h {minutes}m"

        except (ValueError, ZeroDivisionError):
            return None
