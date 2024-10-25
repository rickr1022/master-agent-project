from src.utils.coinbase_client import CoinbaseClient


def test_connection():
    client = CoinbaseClient()

    # Test public endpoint
    ticker = client.get_product_ticker("BTC-USD")
    print("BTC-USD Ticker:", ticker)

    # Test historical data
    candles = client.get_product_candles("BTC-USD", granularity=3600)
    print("Got", len(candles), "hourly candles")


if __name__ == "__main__":
    test_connection()
