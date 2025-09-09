import os
from typing import Dict, List, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from dotenv import load_dotenv

load_dotenv()


class WealthXClient:
    """Client for interacting with WealthX API"""

    def __init__(self):
        self.base_url = os.getenv("WEALTHX_API_URL", "https://api.wealthx.com/v1/")
        self.api_key = os.getenv("WEALTHX_API_KEY")
        self.api_secret = os.getenv("WEALTHX_API_SECRET")
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", 30))
        self.max_retries = int(os.getenv("MAX_RETRIES", 3))

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "WealthX API credentials not found in environment variables"
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-API-Secret": self.api_secret,
            }
        )

        self.logger = logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_total_records(self) -> int:
        """Get total number of records available"""
        try:
            response = self.session.get(
                f"{self.base_url}profiles/count", timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("count", 0)
        except requests.RequestException as e:
            self.logger.error(f"Error getting total records: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_profiles_batch(self, offset: int, limit: int) -> List[Dict]:
        """Get a batch of profiles from WealthX API"""
        try:
            params = {
                "offset": offset,
                "limit": limit,
                "sort": "id",  # Ensure consistent ordering
                "order": "asc",
            }

            response = self.session.get(
                f"{self.base_url}profiles", params=params, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            profiles = data.get("data", [])

            self.logger.info(f"Retrieved {len(profiles)} profiles (offset: {offset})")
            return profiles

        except requests.RequestException as e:
            self.logger.error(f"Error fetching batch at offset {offset}: {e}")
            raise

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self.session.get(f"{self.base_url}health", timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
