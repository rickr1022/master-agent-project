import logging
from datetime import datetime
from typing import Dict, Any
import requests

class ResearchAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        self.logger.info(f"Research Agent initializing with config: {config}")
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration"""
        # Create logger
        logger = logging.getLogger('research_agent')
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create file handler
        try:
            handler = logging.FileHandler(
                f'logs/research_agent_{datetime.now().strftime("%Y%m%d")}.log'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        except Exception as e:
            print(f"Error setting up file handler: {e}")
            # Fallback to stream handler
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def analyze_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze market sentiment for a given symbol"""
        self.logger.info(f"Analyzing market sentiment for {symbol}")
        
        try:
            # Simple example using CoinGecko API
            response = requests.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": symbol.lower(),
                    "vs_currencies": "usd"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                price = data.get(symbol.lower(), {}).get("usd", 0)
                
                return {
                    "symbol": symbol,
                    "price_usd": price,
                    "timestamp": datetime.now().isoformat(),
                    "sentiment": "neutral",  # Placeholder for actual sentiment analysis
                    "confidence": 0.5
                }
            else:
                self.logger.error(f"Error getting price data: {response.status_code}")
                return {
                    "symbol": symbol,
                    "error": f"API Error: {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error in market sentiment analysis: {str(e)}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    def generate_report(self, data: Dict[str, Any]) -> str:
        """Generate a research report from analyzed data"""
        self.logger.info("Generating research report")
        
        report = f"""
Market Research Report
---------------------
Symbol: {data.get('symbol', 'Unknown')}
Price (USD): ${data.get('price_usd', 0):,.2f}
Timestamp: {data.get('timestamp', 'Unknown')}
Sentiment: {data.get('sentiment', 'Unknown')}
Confidence: {data.get('confidence', 0)*100:.1f}%
        """
        
        self.logger.info("Research report generated successfully")
        return report
        
    def start(self):
        """Start the research agent"""
        self.logger.info("Research Agent starting...")
        
    def stop(self):
        """Stop the research agent"""
        self.logger.info("Research Agent stopping...")