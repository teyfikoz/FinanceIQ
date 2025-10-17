from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import requests
from datetime import datetime, timedelta
import pandas as pd

from app.utils.logger import get_logger
from app.core.config import settings


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"collector.{name}")
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # Default 1 second between requests

    def _rate_limit(self) -> None:
        """Enforce rate limiting between API calls."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> requests.Response:
        """Make a rate-limited HTTP request."""
        self._rate_limit()

        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}", error=str(e))
            raise

    @abstractmethod
    def collect_data(self, **kwargs) -> Dict[str, Any]:
        """
        Collect data from the external source.
        Must be implemented by each collector.
        """
        pass

    @abstractmethod
    def get_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> pd.DataFrame:
        """
        Get historical data for a date range.
        Must be implemented by each collector.
        """
        pass

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate collected data."""
        if not data:
            self.logger.warning("Empty data received")
            return False

        if 'error' in data:
            self.logger.error(f"API error: {data['error']}")
            return False

        return True

    def clean_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize raw data."""
        # Default implementation - can be overridden
        return raw_data

    def transform_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Transform API response to pandas DataFrame."""
        # Default implementation - should be overridden
        return pd.DataFrame(data)

    def get_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate data quality score (0-1)."""
        if df.empty:
            return 0.0

        # Basic quality checks
        total_points = 0
        max_points = 0

        # Check for missing values
        max_points += 1
        missing_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        if missing_ratio < 0.05:  # Less than 5% missing
            total_points += 1
        elif missing_ratio < 0.10:  # Less than 10% missing
            total_points += 0.5

        # Check for duplicate rows
        max_points += 1
        if not df.duplicated().any():
            total_points += 1

        # Check for reasonable data ranges (if numeric)
        max_points += 1
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            # Check for infinite or extremely large values
            if not df[numeric_cols].isin([float('inf'), float('-inf')]).any().any():
                total_points += 1

        return total_points / max_points if max_points > 0 else 0.0

    def log_collection_result(
        self,
        success: bool,
        records_count: int = 0,
        error_message: str = None
    ) -> None:
        """Log the result of data collection."""
        if success:
            self.logger.info(
                f"Data collection successful",
                collector=self.name,
                records_collected=records_count
            )
        else:
            self.logger.error(
                f"Data collection failed",
                collector=self.name,
                error=error_message
            )