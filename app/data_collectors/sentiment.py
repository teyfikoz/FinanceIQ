from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import requests

from .base import BaseCollector


class SentimentCollector(BaseCollector):
    """Collector for market sentiment indicators."""

    def __init__(self):
        super().__init__("sentiment")
        self.rate_limit_delay = 1.0

    def collect_data(self) -> Dict[str, Any]:
        """Collect various sentiment indicators."""
        try:
            sentiment_data = {}

            # Fear & Greed Index
            fng_data = self.get_fear_greed_index()
            if fng_data:
                sentiment_data["fear_greed"] = fng_data

            # VIX data would come from Yahoo Finance collector
            # Placeholder for additional sentiment sources

            result = {
                "sentiment_data": sentiment_data,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "sentiment"
            }

            if self.validate_data(result):
                self.log_collection_result(True, len(sentiment_data))
                return result
            else:
                self.log_collection_result(False, error_message="Data validation failed")
                return {}

        except Exception as e:
            self.log_collection_result(False, error_message=str(e))
            return {}

    def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get Fear & Greed Index from Alternative.me."""
        try:
            url = "https://api.alternative.me/fng/"
            response = self._make_request(url)
            data = response.json()

            if "data" in data and len(data["data"]) > 0:
                fng_data = data["data"][0]

                return {
                    "value": int(fng_data["value"]),
                    "value_classification": fng_data["value_classification"],
                    "timestamp": fng_data["timestamp"],
                    "time_until_update": fng_data.get("time_until_update"),
                    "source": "alternative.me"
                }

            return {}

        except Exception as e:
            self.logger.error("Failed to get Fear & Greed Index", error=str(e))
            return {}

    def get_historical_fear_greed(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Get historical Fear & Greed Index data."""
        try:
            # Calculate days between dates
            days = (end_date - start_date).days
            if days > 365:  # API limit
                days = 365

            url = f"https://api.alternative.me/fng/?limit={days}"
            response = self._make_request(url)
            data = response.json()

            if "data" not in data:
                return pd.DataFrame()

            records = []
            for item in data["data"]:
                records.append({
                    "timestamp": pd.to_datetime(int(item["timestamp"]), unit="s"),
                    "value": int(item["value"]),
                    "value_classification": item["value_classification"]
                })

            df = pd.DataFrame(records)

            # Filter by date range
            df = df[
                (df["timestamp"] >= start_date) &
                (df["timestamp"] <= end_date)
            ]

            df = df.sort_values("timestamp").reset_index(drop=True)

            self.logger.info(f"Collected {len(df)} historical Fear & Greed records")
            return df

        except Exception as e:
            self.logger.error("Failed to get historical Fear & Greed data", error=str(e))
            return pd.DataFrame()

    def get_crypto_social_sentiment(self) -> Dict[str, Any]:
        """Get crypto social sentiment (placeholder for future implementation)."""
        # This would integrate with social media APIs like Twitter, Reddit, etc.
        # For now, return placeholder data

        return {
            "twitter_sentiment": {
                "bitcoin_mentions": 1250,
                "bitcoin_sentiment_score": 0.65,
                "ethereum_mentions": 890,
                "ethereum_sentiment_score": 0.72
            },
            "reddit_sentiment": {
                "r_cryptocurrency_posts": 45,
                "r_bitcoin_posts": 23,
                "average_sentiment": 0.58
            },
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Placeholder data - real implementation would require social media API access"
        }

    def get_google_trends_data(self, keywords: List[str] = None) -> Dict[str, Any]:
        """Get Google Trends data for crypto keywords (placeholder)."""
        if keywords is None:
            keywords = ["bitcoin", "ethereum", "cryptocurrency", "DeFi"]

        # This would require pytrends or similar library
        # Placeholder implementation

        trends_data = {}
        for keyword in keywords:
            trends_data[keyword] = {
                "interest_score": 75,  # Placeholder score
                "change_week": 5.2,
                "related_queries": ["bitcoin price", "bitcoin news", "bitcoin chart"]
            }

        return {
            "google_trends": trends_data,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Placeholder data - real implementation would require Google Trends API"
        }

    def calculate_composite_sentiment(self, sentiment_data: Dict[str, Any]) -> float:
        """Calculate a composite sentiment score from multiple indicators."""
        try:
            scores = []
            weights = []

            # Fear & Greed Index (0-100 scale)
            if "fear_greed" in sentiment_data:
                fng_value = sentiment_data["fear_greed"].get("value", 50)
                scores.append(fng_value / 100.0)  # Normalize to 0-1
                weights.append(0.4)  # 40% weight

            # VIX (inverse relationship - high VIX = low sentiment)
            # This would come from the Yahoo Finance collector
            # Placeholder implementation
            vix_value = 20  # Placeholder
            vix_normalized = max(0, min(1, (50 - vix_value) / 50))  # Inverse and normalize
            scores.append(vix_normalized)
            weights.append(0.3)  # 30% weight

            # Social sentiment (if available)
            if "twitter_sentiment" in sentiment_data:
                social_score = sentiment_data["twitter_sentiment"].get("bitcoin_sentiment_score", 0.5)
                scores.append(social_score)
                weights.append(0.3)  # 30% weight

            # Calculate weighted average
            if scores and weights:
                weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
                total_weight = sum(weights)
                composite_score = weighted_sum / total_weight
                return round(composite_score, 3)

            return 0.5  # Neutral if no data

        except Exception as e:
            self.logger.error("Failed to calculate composite sentiment", error=str(e))
            return 0.5

    def get_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator: str = "fear_greed"
    ) -> pd.DataFrame:
        """Get historical sentiment data."""
        if indicator == "fear_greed":
            return self.get_historical_fear_greed(start_date, end_date)
        else:
            self.logger.warning(f"Unknown sentiment indicator: {indicator}")
            return pd.DataFrame()

    def transform_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Transform sentiment data to standardized DataFrame."""
        if "sentiment_data" not in data:
            return pd.DataFrame()

        sentiment_data = data["sentiment_data"]
        records = []

        # Process Fear & Greed Index
        if "fear_greed" in sentiment_data:
            fng = sentiment_data["fear_greed"]
            records.append({
                "indicator_name": "Fear & Greed Index",
                "value": fng.get("value"),
                "classification": fng.get("value_classification"),
                "timestamp": pd.to_datetime(int(fng["timestamp"]), unit="s") if "timestamp" in fng else datetime.utcnow(),
                "source": "alternative.me"
            })

        # Add other sentiment indicators as they become available

        df = pd.DataFrame(records)
        return df

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate sentiment data."""
        if not super().validate_data(data):
            return False

        # Check if sentiment_data exists
        if "sentiment_data" not in data:
            self.logger.warning("No sentiment data in response")
            return False

        # At least one sentiment indicator should be present
        sentiment_data = data["sentiment_data"]
        if not sentiment_data:
            self.logger.warning("Empty sentiment data")
            return False

        return True

    def get_market_regime_indicators(self) -> Dict[str, Any]:
        """Get indicators that help identify market regimes."""
        try:
            # This would combine various sentiment and volatility indicators
            # to classify market regime (bull, bear, uncertainty, etc.)

            regime_data = {
                "current_regime": "risk_on",  # risk_on, risk_off, uncertainty
                "regime_confidence": 0.75,
                "indicators": {
                    "fear_greed_contribution": 0.3,
                    "volatility_contribution": 0.4,
                    "correlation_contribution": 0.3
                },
                "regime_duration_days": 15,
                "previous_regime": "uncertainty",
                "regime_change_probability": 0.25
            }

            return regime_data

        except Exception as e:
            self.logger.error("Failed to get market regime indicators", error=str(e))
            return {}