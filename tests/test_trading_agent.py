import unittest

from src.agents.trading_agent import TradingAgent


class TestTradingAgent(unittest.TestCase):
    def setUp(self):
        self.config = {
            "name": "test_trading_agent",
            "max_position_size": 1000,
            "risk_percentage": 1.0,
        }
        self.agent = TradingAgent(self.config)

    def test_initialization(self):
        """Test if trading agent initializes properly"""
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.logger)

    def test_analyze_trade_opportunity(self):
        """Test trade opportunity analysis"""
        # Test with minimal data
        result = self.agent.analyze_trade_opportunity(
            "BTC-USD", {"price": 50000, "history": [50000, 51000, 52000, 53000, 54000]}
        )

        # Verify all required fields are present
        required_fields = {"action", "confidence", "symbol", "timestamp"}
        self.assertTrue(all(field in result for field in required_fields))

        # Verify types
        self.assertIsInstance(result["action"], str)
        self.assertIsInstance(result["confidence"], float)
        self.assertIsInstance(result["symbol"], str)
        self.assertIsInstance(result["timestamp"], str)

        # Verify value ranges
        self.assertIn(result["action"], ["buy", "sell", "hold"])
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)

    def test_insufficient_data(self):
        """Test behavior with insufficient price history"""
        result = self.agent.analyze_trade_opportunity("BTC-USD", {"price": 50000})

        self.assertEqual(result["action"], "hold")
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("reason", result)


if __name__ == "__main__":
    unittest.main()
