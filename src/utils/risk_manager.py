import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.utils.risk_manager import RiskManager


class MarketAnalyzer:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        self.indicators = {}
        self.min_data_points = self.config.get("min_data_points", 20)
        self.rsi_period = self.config.get("rsi_period", 14)
        self.short_ma_period = self.config.get("short_ma_period", 9)
        self.long_ma_period = self.config.get("long_ma_period", 21)
        self.risk_manager = RiskManager(self.config)

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("market_analyzer")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(
            f'logs/market_analyzer_{datetime.now().strftime("%Y%m%d")}.log'
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def analyze_market(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive market analysis"""
        required_columns = ["close", "volume"]
        for col in required_columns:
            if col not in price_data.columns:
                self.logger.error(f"Missing required column: {col}")
                return {
                    "signal": "ERROR",
                    "confidence": 0,
                    "reason": f"Missing required column: {col}",
                }

        if len(price_data) < self.min_data_points:
            self.logger.warning("Insufficient data points for analysis")
            return {"signal": "NEUTRAL", "confidence": 0, "reason": "Insufficient data"}

        try:
            analysis = {
                "trend": self.analyze_trend(price_data),
                "momentum": self.calculate_momentum(price_data),
                "volatility": self.calculate_volatility(price_data),
                "volume_analysis": self.analyze_volume(price_data),
                "timestamp": datetime.now().isoformat(),
            }

            # Generate final signal
            signal = self.generate_signal(analysis)
            analysis.update(signal)

            # Assess risk using RiskManager
            risk_assessment = self.risk_manager.validate_trade(
                {
                    "account_balance": self.risk_manager.current_balance,
                    "entry_price": price_data["close"].iloc[-1],
                    "stop_loss": price_data["close"].iloc[-1]
                    * 0.95,  # Example stop loss
                }
            )
            analysis.update(risk_assessment)

            return analysis

        except Exception as e:
            self.logger.error(f"Error in market analysis: {str(e)}")
            return {
                "signal": "ERROR",
                "confidence": 0,
                "reason": f"Analysis error: {str(e)}",
            }

    def analyze_trend(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trend using moving averages"""
        prices = data["close"].values

        # Calculate moving averages
        short_ma = self._calculate_sma(prices, self.short_ma_period)
        long_ma = self._calculate_sma(prices, self.long_ma_period)

        # Determine trend direction and strength
        if len(short_ma) > 0 and len(long_ma) > 0:
            trend_strength = (short_ma[-1] - long_ma[-1]) / long_ma[-1] * 100

            if trend_strength > 1:
                trend = "STRONG_UPTREND"
            elif trend_strength > 0:
                trend = "WEAK_UPTREND"
            elif trend_strength > -1:
                trend = "WEAK_DOWNTREND"
            else:
                trend = "STRONG_DOWNTREND"

            return {
                "direction": trend,
                "strength": abs(trend_strength),
                "short_ma": float(short_ma[-1]),
                "long_ma": float(long_ma[-1]),
            }

        return {
            "direction": "NEUTRAL",
            "strength": 0,
            "short_ma": None,
            "long_ma": None,
        }

    def calculate_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate momentum indicators"""
        prices = data["close"].values
        momentum = {}

        # Calculate RSI
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-self.rsi_period :])
        avg_loss = np.mean(losses[-self.rsi_period :])

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        momentum["rsi"] = rsi

        # Calculate rate of change
        roc = ((prices[-1] / prices[-20]) - 1) * 100
        momentum["roc"] = roc

        return momentum

    def calculate_volatility(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volatility metrics"""
        prices = data["close"].values
        returns = np.diff(np.log(prices))

        volatility = {
            "daily_volatility": np.std(returns) * np.sqrt(252),
            "atr": self._calculate_atr(data),
            "bollinger_bands": self._calculate_bollinger_bands(data),
        }

        return volatility

    def _calculate_sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        if len(data) < period:
            return np.array([])
        return np.convolve(data, np.ones(period) / period, mode="valid")

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = data["high"].values
        low = data["low"].values
        close = data["close"].values

        tr1 = np.abs(high[1:] - close[:-1])
        tr2 = np.abs(low[1:] - close[:-1])
        tr3 = high[1:] - low[1:]

        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        atr = np.mean(tr[-period:])

        return atr

    def _calculate_bollinger_bands(
        self, data: pd.DataFrame, period: int = 20
    ) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        prices = data["close"].values
        sma = self._calculate_sma(prices, period)

        if len(sma) > 0:
            std = np.std(prices[-period:])
            upper = sma[-1] + (2 * std)
            lower = sma[-1] - (2 * std)

            return {
                "upper": float(upper),
                "middle": float(sma[-1]),
                "lower": float(lower),
            }

        return {"upper": None, "middle": None, "lower": None}

    def analyze_volume(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns"""
        volume = data["volume"].values

        avg_volume = np.mean(volume[-20:])
        current_volume = volume[-1]

        volume_ratio = current_volume / avg_volume

        return {
            "volume_ratio": volume_ratio,
            "volume_trend": (
                "HIGH"
                if volume_ratio > 1.5
                else "LOW"
                if volume_ratio < 0.5
                else "NORMAL"
            ),
        }

    def generate_signal(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on analysis"""
        trend = analysis["trend"]["direction"]
        momentum_rsi = analysis["momentum"]["rsi"]
        volume_ratio = analysis["volume_analysis"]["volume_ratio"]

        signal = "NEUTRAL"
        confidence = 0.0

        if trend.endswith("UPTREND") and momentum_rsi < 70:
            signal = "BUY"
            confidence = analysis["trend"]["strength"] * 0.01
        elif trend.endswith("DOWNTREND") and momentum_rsi > 30:
            signal = "SELL"
            confidence = analysis["trend"]["strength"] * 0.01

        # Adjust confidence based on volume
        confidence *= min(volume_ratio, 2.0)

        return {"signal": signal, "confidence": min(confidence, 1.0)}
