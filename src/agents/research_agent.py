import logging
from datetime import datetime
from typing import Dict, Any
import requests


class ResearchAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.base_url = config.get("base_url", "https : //api.coingecko.com/api/v3")

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("research_agent")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(
            f'logs/research_agent_{datetime.now().strftime("%Y%m%d")}.log'
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _get_price_data(self, symbol: str) -> Dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}/simple/price",
                params={"ids": symbol.lower(), "vs_currencies": "usd"},
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "symbol": symbol,
                    "price": data.get(symbol.lower(), {}).get("usd", 0),
                }
            return None
        except Exception as e:
            self.logger.error(f"Error getting price data: {str(e)}")
            return None

    def _get_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        return {"social_score": 0.5, "news_sentiment": 0.5, "market_momentum": 0.5}

    def _generate_signal(
        self, price_data: Dict[str, Any], sentiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        avg_sentiment = sum(sentiment_data.values()) / len(sentiment_data)
        signal = "NEUTRAL"
        confidence = avg_sentiment

        if avg_sentiment > 0.7:
            signal = "BUY"
        elif avg_sentiment < 0.3:
            signal = "SELL"

        return {
            "signal": signal,
            "confidence": confidence,
            "price": price_data.get("price", 0),
            "timestamp": datetime.now().isoformat(),
            "sentiment_data": sentiment_data,
        }

    def analyze_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        self.logger.info(f"Analyzing market sentiment for: {symbol}")
        try:
            price_data = self._get_price_data(symbol)
            if not price_data:
                return {
                    "signal": "ERROR",
                    "confidence": 0,
                    "reason": "Failed to fetch price data",
                }
            sentiment_data = self._get_sentiment_data(symbol)
            return self._generate_signal(price_data, sentiment_data)
        except Exception as e:
            self.logger.error(f"Error in analysis: {str(e)}")
            return {
                "signal": "ERROR",
                "confidence": 0,
                "reason": f"Analysis error: {str(e)}",
            }
