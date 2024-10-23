import asyncio
import websockets
import json
from datetime import datetime
import os
from typing import Dict, Any

class BTCPriceMonitor:
    def __init__(self):
        self.ws_url = "wss://ws-feed.exchange.coinbase.com"
        self.last_price = None
        self.price_history = []
        self.max_history_size = 1000  # Store last 1000 prices
        
    async def connect(self):
        """Connect to Coinbase WebSocket feed"""
        async with websockets.connect(self.ws_url) as websocket:
            # Subscribe to BTC-USD channel
            subscribe_message = {
                "type": "subscribe",
                "product_ids": ["BTC-USD"],
                "channels": ["ticker"]
            }
            await websocket.send(json.dumps(subscribe_message))
            
            # Process incoming messages
            while True:
                try:
                    message = await websocket.recv()
                    await self.process_message(json.loads(message))
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
    async def process_message(self, message: Dict[str, Any]):
        """Process incoming WebSocket messages"""
        if message.get('type') == 'ticker':
            price = float(message.get('price', 0))
            time = message.get('time')
            size = float(message.get('last_size', 0))
            
            self.last_price = price
            self.price_history.append({
                'price': price,
                'time': time,
                'size': size
            })
            
            # Keep history size manageable
            if len(self.price_history) > self.max_history_size:
                self.price_history.pop(0)
            
            # Calculate price change
            price_change = 0
            if len(self.price_history) > 1:
                previous_price = self.price_history[-2]['price']
                price_change = ((price - previous_price) / previous_price) * 100
            
            # Print update
            os.system('clear' if os.name == 'posix' else 'cls')  # Clear screen
            print(f"""
Bitcoin Price Monitor
-------------------
Current Price: ${price:,.2f}
Change: {price_change:+.2f}%
Time: {datetime.fromisoformat(time.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')} UTC
Trade Size: {size} BTC
            """)
            
            # Alert on significant price changes
            if abs(price_change) > 0.5:  # Alert on 0.5% or greater change
                print(f"!!! ALERT: Price changed by {price_change:+.2f}% !!!")

async def main():
    monitor = BTCPriceMonitor()
    print("Starting Bitcoin price monitor...")
    await monitor.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor stopped by user")