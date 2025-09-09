"""
Configuration module for WealthX Data Puller

This module contains configuration constants and helper functions.
"""

import os
from typing import Dict, Any

# Default configuration values
DEFAULT_CONFIG = {
    "batch_size": 12000,
    "max_retries": 3,
    "retry_delay": 60,
    "request_timeout": 30,
    "daily_runs": 3,
    "max_runtime_hours": 2,
    "log_level": "INFO",
}

# MongoDB configuration
MONGODB_INDEXES = [
    {"keys": [("wealthx_id", 1)], "unique": True, "sparse": True},
    {"keys": [("created_at", 1)]},
    {
        "keys": [("updated_at", 1)],
    },
]

# API endpoints (these would be actual WealthX endpoints)
WEALTHX_ENDPOINTS = {
    "profiles": "profiles",
    "profile_count": "profiles/count",
    "health": "health",
}


def get_batch_schedule(
    total_records: int, days: int = 10, daily_runs: int = 3
) -> Dict[str, Any]:
    """Calculate optimal batch scheduling"""
    batch_size = int(os.getenv("BATCH_SIZE", DEFAULT_CONFIG["batch_size"]))

    total_batches = (total_records + batch_size - 1) // batch_size
    total_runs = days * daily_runs
    batches_per_run = (total_batches + total_runs - 1) // total_runs

    return {
        "total_records": total_records,
        "total_batches": total_batches,
        "batch_size": batch_size,
        "days": days,
        "daily_runs": daily_runs,
        "total_runs": total_runs,
        "batches_per_run": batches_per_run,
        "estimated_completion_days": (total_batches / batches_per_run) / daily_runs,
    }


def validate_environment() -> Dict[str, Any]:
    """Validate environment configuration"""
    required_vars = ["WEALTHX_USERNAME", "WEALTHX_PASSWORD"]
    optional_vars = {
        "WEALTHX_API_URL": "https://connect.wealthx.com/rest/v1/",
        "MONGO_URI": "mongodb://localhost:27017/",
        "MONGO_DATABASE": "wealthx_data",
        "MONGO_COLLECTION": "dossiers",
        "BATCH_SIZE": str(DEFAULT_CONFIG["batch_size"]),
        "MAX_RETRIES": str(DEFAULT_CONFIG["max_retries"]),
        "RETRY_DELAY": str(DEFAULT_CONFIG["retry_delay"]),
        "LOG_LEVEL": DEFAULT_CONFIG["log_level"],
    }

    validation_result = {"valid": True, "missing_required": [], "using_defaults": []}

    # Check required variables
    for var in required_vars:
        if not os.getenv(var):
            validation_result["missing_required"].append(var)
            validation_result["valid"] = False

    # Check optional variables and set defaults
    for var, default in optional_vars.items():
        if not os.getenv(var):
            validation_result["using_defaults"].append(f"{var}={default}")
            os.environ[var] = default

    return validation_result
