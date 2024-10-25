import asyncio
import unittest

from src.utils.btc_monitor import BTCPriceMonitor


class TestBTCPriceMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = BTCPriceMonitor()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_initialization(self):
        """Test if monitor initializes properly"""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(self.monitor.max_history_size, 1000)
        self.assertEqual(len(self.monitor.price_history), 0)

    def test_process_message(self):
        """Test message processing"""
        test_message = {
            "type": "ticker",
            "price": "50000",
            "time": "2024-10-22T00:00:00Z",
            "last_size": "0.1",
        }

        async def run_test():
            await self.monitor.process_message(test_message)
            self.assertEqual(len(self.monitor.price_history), 1)
            self.assertEqual(self.monitor.last_price, 50000.0)

        self.loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main()
