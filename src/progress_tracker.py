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
            "last_offset": 0,
            "last_wealthx_id": None,
            "total_processed": 0,
            "last_batch_time": None,
            "session_id": None,
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

    def get_resume_offset(self) -> int:
        """Get the offset to resume from"""
        return self.progress_data.get("last_offset", 0)

    def update_progress(
        self, offset: int, batch_size: int, wealthx_id: Optional[str] = None
    ):
        """Update progress after successful batch"""
        self.progress_data.update(
            {
                "last_offset": offset + batch_size,
                "last_wealthx_id": wealthx_id,
                "total_processed": self.progress_data["total_processed"] + batch_size,
                "last_batch_time": datetime.utcnow().isoformat(),
                "batches_completed": self.progress_data["batches_completed"] + 1,
            }
        )
        self._save_progress()

        self.logger.info(
            f"Progress updated: {self.progress_data['batches_completed']} batches, "
            f"{self.progress_data['total_processed']} records processed"
        )

    def log_error(self, error: str, offset: int):
        """Log an error during processing"""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(error),
            "offset": offset,
        }

        if "errors" not in self.progress_data:
            self.progress_data["errors"] = []

        self.progress_data["errors"].append(error_entry)
        self._save_progress()

    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        return {
            "batches_completed": self.progress_data.get("batches_completed", 0),
            "total_processed": self.progress_data.get("total_processed", 0),
            "last_offset": self.progress_data.get("last_offset", 0),
            "session_id": self.progress_data.get("session_id"),
            "session_start": self.progress_data.get("session_start"),
            "last_batch_time": self.progress_data.get("last_batch_time"),
            "error_count": len(self.progress_data.get("errors", [])),
        }

    def reset_progress(self):
        """Reset progress tracking"""
        self.progress_data = {
            "last_offset": 0,
            "last_wealthx_id": None,
            "total_processed": 0,
            "last_batch_time": None,
            "session_id": None,
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

            processed = self.progress_data["total_processed"]
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
