import logging
from datetime import datetime
from typing import Any, Dict

from src.utils.risk_manager import RiskManager


class TradingAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        self.risk_manager = RiskManager(config)

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("trading_agent")
        logger.setLevel(logging.INFO)
        return logger

    def analyze_trade_opportunity(
        self, symbol: str, price_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze if there's a trading opportunity"""
        self.logger.info(f"Analyzing trading opportunity for {symbol}")

        current_price = price_data.get("price", 0)
        if current_price <= 0:
            return {
                "action": "hold",
                "reason": "Invalid price data",
                "confidence": 0.0,  # Added confidence
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
            }

        # Simple moving average strategy (example)
        prices = price_data.get("history", [current_price])
        if len(prices) < 2:
            return {
                "action": "hold",
                "reason": "Insufficient price history",
                "confidence": 0.0,  # Added confidence
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
            }

        short_ma = sum(prices[-5:]) / min(5, len(prices))
        long_ma = sum(prices[-20:]) / min(20, len(prices))

        action = "hold"
        confidence = 0.0

        if short_ma > long_ma * 1.02:  # 2% above long MA
            action = "buy"
            confidence = min((short_ma / long_ma - 1) * 5, 1.0)
        elif short_ma < long_ma * 0.98:  # 2% below long MA
            action = "sell"
            confidence = min((1 - short_ma / long_ma) * 5, 1.0)

        return {
            "symbol": symbol,
            "action": action,
            "confidence": confidence,
            "current_price": current_price,
            "short_ma": short_ma,
            "long_ma": long_ma,
            "timestamp": datetime.now().isoformat(),
        }
