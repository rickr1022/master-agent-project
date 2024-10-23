import os
import logging
from typing import Dict, Any, Optional, List
import hmac
import hashlib
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CoinbaseClient:
    def __init__(self):
        self.api_key = os.getenv('COINBASE_API_KEY')
        self.api_secret = os.getenv('COINBASE_API_SECRET')
        self.base_url = 'https://api.exchange.coinbase.com'  # Updated URL for Advanced Trade
        self.logger = self._setup_logging()
        
        if not self.api_key or not self.api_secret:
            self.logger.warning("Using public API endpoints only - credentials not found")
    
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('coinbase_client')
        logger.setLevel(logging.INFO)
        
        os.makedirs('logs', exist_ok=True)
        handler = logging.FileHandler(
            f'logs/coinbase_client_{datetime.now().strftime("%Y%m%d")}.log'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _generate_signature(self, timestamp: str, method: str, 
                          request_path: str, body: str = '') -> str:
        """Generate signature for authenticated requests"""
        message = f"{timestamp}{method}{request_path}{body}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _request(self, method: str, endpoint: str, 
                params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Make API request with authentication"""
        timestamp = str(int(time.time()))
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        if self.api_key and self.api_secret:
            headers.update({
                'CB-ACCESS-KEY': self.api_key,
                'CB-ACCESS-TIMESTAMP': timestamp,
                'CB-ACCESS-SIGN': self._generate_signature(
                    timestamp, method, endpoint, str(data or '')
                )
            })
        
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            if response := getattr(e, 'response', None):
                self.logger.error(f"Response: {response.text}")
            return None
    
    def get_product_ticker(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get current ticker for a product"""
        endpoint = f'/products/{product_id}/ticker'
        response = self._request('GET', endpoint)
        if response:
            self.logger.info(f"Got ticker for {product_id}: {response}")
            return response
        return None
    
    def get_product_candles(self, 
                          product_id: str,
                          start: str = None,
                          end: str = None,
                          granularity: int = 60) -> List[Dict[str, Any]]:
        """Get historical candles for a product"""
        endpoint = f'/products/{product_id}/candles'
        params = {'granularity': granularity}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
            
        response = self._request('GET', endpoint, params=params)
        if response:
            self.logger.info(f"Got candles for {product_id}")
            return response
        return []
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get list of accounts"""
        if not (self.api_key and self.api_secret):
            self.logger.error("API credentials required for account information")
            return []
            
        endpoint = '/accounts'
        response = self._request('GET', endpoint)
        if response:
            self.logger.info("Got account information")
            return response
        return []
    
    def place_market_order(self, 
                          product_id: str,
                          side: str,
                          size: str) -> Optional[Dict[str, Any]]:
        """Place a market order"""
        if not (self.api_key and self.api_secret):
            self.logger.error("API credentials required for placing orders")
            return None
            
        endpoint = '/orders'
        data = {
            'product_id': product_id,
            'side': side,
            'size': size,
            'type': 'market'
        }
        
        response = self._request('POST', endpoint, data=data)
        if response:
            self.logger.info(f"Placed market order: {response}")
            return response
        return None
    
    def get_fills(self, product_id: str = None) -> List[Dict[str, Any]]:
        """Get list of fills"""
        if not (self.api_key and self.api_secret):
            self.logger.error("API credentials required for fill information")
            return []
            
        endpoint = '/fills'
        params = {}
        if product_id:
            params['product_id'] = product_id
            
        response = self._request('GET', endpoint, params=params)
        if response:
            self.logger.info("Got fills information")
            return response
        return []