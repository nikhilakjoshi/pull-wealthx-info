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
        self.base_url = os.getenv(
            "WEALTHX_API_URL", "https://connect.wealthx.com/rest/v1/"
        )
        self.username = os.getenv("WEALTHX_USERNAME")
        self.password = os.getenv("WEALTHX_PASSWORD")
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", 30))
        self.max_retries = int(os.getenv("MAX_RETRIES", 3))

        if not self.username or not self.password:
            raise ValueError(
                "WealthX API credentials (username/password) not found in environment variables"
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "username": self.username,
                "password": self.password,
                "Accept": "application/json",
            }
        )

        self.logger = logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_total_records(self) -> int:
        """Get total number of records available from a sample API call"""
        try:
            # Make a small sample request to get totalDossiers count
            response = self.session.get(
                f"{self.base_url}alldossiers",
                params={"dossierType": "both", "fromIndex": 1, "toIndex": 1},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            total_count = data.get("totalDossiers", 0)
            self.logger.info(f"Total dossiers available: {total_count}")
            return total_count
        except requests.RequestException as e:
            self.logger.error(f"Error getting total records: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_profiles_batch(self, from_index: int, to_index: int) -> List[Dict]:
        """Get a batch of profiles from WealthX API using fromIndex and toIndex"""
        try:
            params = {
                "dossierType": "both",  # Get both UHNW and VHNW
                "fromIndex": from_index,
                "toIndex": to_index,
            }

            response = self.session.get(
                f"{self.base_url}alldossiers", params=params, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            dossiers = data.get("dossiers", [])
            last_index = data.get("lastIndexId", to_index)

            self.logger.info(
                f"Retrieved {len(dossiers)} dossiers (from {from_index} to {to_index}, lastIndex: {last_index})"
            )
            return dossiers

        except requests.RequestException as e:
            self.logger.error(
                f"Error fetching batch from {from_index} to {to_index}: {e}"
            )
            raise

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self.session.get(
                f"{self.base_url}alldossiers",
                params={"dossierType": "both", "fromIndex": 1, "toIndex": 1},
                timeout=10,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
