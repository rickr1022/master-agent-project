import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class MarketAnalyzer:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        self.indicators = {}
        self.min_data_points = self.config.get("min_data_points", 20)
        self.rsi_period = self.config.get("rsi_period", 14)
        self.short_ma_period = self.config.get("short_ma_period", 9)
        self.long_ma_period = self.config.get("long_ma_period", 21)

    def _setup_logging(self) -> logging.Logger:
        if not os.path.exists("logs"):
            os.makedirs("logs")
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

        # Handle edge case where moving averages cannot be calculated
        if len(short_ma) == 0 or len(long_ma) == 0:
            return {
                "direction": "NEUTRAL",
                "strength": 0,
                "short_ma": np.nan,
                "long_ma": np.nan,
            }

        # Determine trend direction
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
            "short_ma": short_ma[-1],
            "long_ma": long_ma[-1],
        }

    def calculate_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate momentum indicators including RSI"""
        prices = data["close"].values
        rsi = self._calculate_rsi(prices)

        momentum = {
            "rsi": rsi[-1],
            "overbought": rsi[-1] > 70,
            "oversold": rsi[-1] < 30,
        }

        # Add rate of change
        if len(prices) >= 5:
            roc = (prices[-1] - prices[-5]) / prices[-5] * 100
        else:
            roc = np.nan
        momentum["price_roc"] = roc

        return momentum

    def calculate_volatility(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate price volatility metrics"""
        prices = data["close"].values
        returns = np.diff(np.log(prices))

        if len(returns) == 0:
            return {
                "daily_volatility": np.nan,
                "recent_volatility": np.nan,
                "price_range": np.nan,
            }

        volatility = {
            "daily_volatility": np.std(returns) * np.sqrt(252),
            "recent_volatility": np.std(returns[-20:]) * np.sqrt(252),
            "price_range": (np.max(prices[-20:]) - np.min(prices[-20:]))
            / np.min(prices[-20:])
            * 100,
        }

        return volatility

    def analyze_volume(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trading volume patterns"""
        if "volume" not in data.columns:
            return {"volume_signal": "NO_DATA"}

        volume = data["volume"].values
        avg_volume = np.mean(volume[-20:])
        current_volume = volume[-1]

        return {
            "volume_ratio": current_volume / avg_volume,
            "volume_trend": (
                "HIGH"
                if current_volume > avg_volume * 1.5
                else "LOW"
                if current_volume < avg_volume * 0.5
                else "NORMAL"
            ),
        }

    def generate_signal(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on analysis"""
        trend = analysis["trend"]["direction"]
        rsi = analysis["momentum"]["rsi"]
        volume_ratio = analysis["volume_analysis"].get("volume_ratio", 1)

        # Calculate base signal
        if trend.endswith("UPTREND") and rsi < 70:
            signal = "BUY"
            confidence = analysis["trend"]["strength"] * 0.01
        elif trend.endswith("DOWNTREND") and rsi > 30:
            signal = "SELL"
            confidence = analysis["trend"]["strength"] * 0.01
        else:
            signal = "NEUTRAL"
            confidence = 0.0

        # Adjust confidence based on volume
        confidence *= min(volume_ratio, 2.0)

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

        return {
            "signal": signal,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        if len(data) < period:
            return np.array([])
        return np.convolve(data, np.ones(period) / period, mode="valid")

    def _calculate_rsi(self, prices: np.ndarray) -> np.ndarray:
        """Calculate Relative Strength Index"""
        if len(prices) < self.rsi_period:
            return np.array([np.nan] * len(prices))
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.convolve(
            gains, np.ones(self.rsi_period) / self.rsi_period, mode="valid"
        )
        avg_loss = np.convolve(
            losses, np.ones(self.rsi_period) / self.rsi_period, mode="valid"
        )

        rs = avg_gain / np.where(avg_loss == 0, 1, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        # Pad the beginning to maintain array length
        pad_length = len(prices) - len(rsi)
        rsi = np.pad(rsi, (pad_length, 0), mode="edge")

        return rsi
