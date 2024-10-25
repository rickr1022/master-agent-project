import os
import sys
import unittest

import pandas as pd

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from market_analyzer import MarketAnalyzer


class TestMarketAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = MarketAnalyzer(config={"max_risk": 0.5})
        self.data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
                "volume": [
                    1000,
                    1100,
                    1200,
                    1300,
                    1400,
                    1500,
                    1600,
                    1700,
                    1800,
                    1900,
                    2000,
                ],
            }
        )

    def test_analyze_market(self):
        result = self.analyzer.analyze_market(self.data)
        self.assertIn("signal", result)
        self.assertIn("confidence", result)
        if "is_valid" in result:
            self.assertIn("is_valid", result)
            self.assertIn("suggested_size", result)
        else:
            self.assertIn("reason", result)

    def test_analyze_trend(self):
        result = self.analyzer.analyze_trend(self.data)
        self.assertIn("direction", result)
        self.assertIn("strength", result)

    def test_calculate_momentum(self):
        result = self.analyzer.calculate_momentum(self.data)
        self.assertIn("rsi", result)
        self.assertIn("price_roc", result)

    def test_calculate_volatility(self):
        result = self.analyzer.calculate_volatility(self.data)
        self.assertIn("daily_volatility", result)
        self.assertIn("recent_volatility", result)

    def test_analyze_volume(self):
        result = self.analyzer.analyze_volume(self.data)
        self.assertIn("volume_ratio", result)
        self.assertIn("volume_trend", result)


if __name__ == "__main__":
    unittest.main()
