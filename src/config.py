"""
Configuration module for WealthX Data Puller

This module contains configuration constants and helper functions.
"""

import os
from typing import Dict, Any

# Default configuration values
DEFAULT_CONFIG = {
    "api_batch_size": 500,
    "processing_batch_size": 14000,
    "max_retries": 3,
    "retry_delay": 60,
    "request_timeout": 30,
    "runs_per_day": 3,
    "target_days": 10,
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
    total_records: int, days: int = 10, runs_per_day: int = 3
) -> Dict[str, Any]:
    """Calculate optimal batch scheduling with dual-batch configuration"""
    api_batch_size = int(os.getenv("API_BATCH_SIZE", DEFAULT_CONFIG["api_batch_size"]))
    processing_batch_size = int(
        os.getenv("PROCESSING_BATCH_SIZE", DEFAULT_CONFIG["processing_batch_size"])
    )

    # Calculate API calls per processing session
    api_calls_per_session = processing_batch_size // api_batch_size

    # Calculate sessions needed to complete all records
    total_sessions = (
        total_records + processing_batch_size - 1
    ) // processing_batch_size
    total_runs_available = days * runs_per_day

    # Calculate records per day
    records_per_day = runs_per_day * processing_batch_size

    return {
        "total_records": total_records,
        "api_batch_size": api_batch_size,
        "processing_batch_size": processing_batch_size,
        "api_calls_per_session": api_calls_per_session,
        "total_sessions_needed": total_sessions,
        "days": days,
        "runs_per_day": runs_per_day,
        "total_runs_available": total_runs_available,
        "records_per_day": records_per_day,
        "estimated_completion_days": total_sessions / runs_per_day,
        "total_capacity": records_per_day * days,
    }


def validate_environment() -> Dict[str, Any]:
    """Validate environment configuration"""
    required_vars = ["WEALTHX_USERNAME", "WEALTHX_PASSWORD"]
    optional_vars = {
        "WEALTHX_API_URL": "https://connect.wealthx.com/rest/v1/",
        "MONGO_URI": "mongodb://localhost:27017/",
        "MONGO_DATABASE": "wealthx_data",
        "MONGO_COLLECTION": "dossiers",
        "API_BATCH_SIZE": str(DEFAULT_CONFIG["api_batch_size"]),
        "PROCESSING_BATCH_SIZE": str(DEFAULT_CONFIG["processing_batch_size"]),
        "MAX_RETRIES": str(DEFAULT_CONFIG["max_retries"]),
        "RETRY_DELAY": str(DEFAULT_CONFIG["retry_delay"]),
        "RUNS_PER_DAY": str(DEFAULT_CONFIG["runs_per_day"]),
        "TARGET_DAYS": str(DEFAULT_CONFIG["target_days"]),
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
