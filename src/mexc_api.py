import requests
import time
import hmac
import hashlib
import base64
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.config import MEXC_API_KEY, MEXC_API_SECRET, TEST_MODE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mexc_api')

class MexcAPI:
    """
    MEXC Exchange API connector for the trading bot
    """
    
    def __init__(self):
        """Initialize the MEXC API connector"""
        self.base_url = "https://api.mexc.com"
        self.api_key = MEXC_API_KEY
        self.api_secret = MEXC_API_SECRET
        self.test_mode = TEST_MODE
        logger.info("MEXC API connector initialized")
    
    def _generate_signature(self, params):
        """Generate signature for authenticated requests"""
        query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params.keys())])
        signature = hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature
    
    def _make_request(self, method, endpoint, params=None, auth=False):
        """Make API request to MEXC"""
        
        # In test mode, return dummy data for certain endpoints
        if self.test_mode:
            if endpoint == "/api/v3/klines":
                return self._get_test_klines(params)
            elif endpoint == "/api/v3/account":
                return self._get_test_account()
            elif "order" in endpoint:
                return self._get_test_order(params)
        
        url = self.base_url + endpoint
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        if auth:
            timestamp = int(time.time() * 1000)
            if params is None:
                params = {}
            params['timestamp'] = timestamp
            params['recvWindow'] = 5000
            params['signature'] = self._generate_signature(params)
            headers['X-MEXC-APIKEY'] = self.api_key
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error making API request: {str(e)}")
            return None
    
    def get_historical_data(self, symbol, timeframe, limit=1000, start_time=None, end_time=None):
        """Get historical kline data"""
        if self.test_mode:
            logger.info(f"Retrieved {limit} {timeframe} candles for {symbol}")
            return self._get_test_klines({"symbol": symbol, "interval": timeframe, "limit": limit})
            
        endpoint = "/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": timeframe,
            "limit": limit
        }
        
        if start_time:
            params["startTime"] = int(start_time.timestamp() * 1000)
        if end_time:
            params["endTime"] = int(end_time.timestamp() * 1000)
        
        response = self._make_request("GET", endpoint, params)
        
        if response:
            # Convert to DataFrame
            df = pd.DataFrame(response, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Convert columns to numeric
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
            
            logger.info(f"Retrieved {len(df)} {timeframe} candles for {symbol}")
            return df
        else:
            logger.error(f"Failed to retrieve historical data for {symbol}")
            return None
    
    def get_account_info(self):
        """Get account information"""
        if self.test_mode:
            return self._get_test_account()
            
        endpoint = "/api/v3/account"
        response = self._make_request("GET", endpoint, auth=True)
        
        if response:
            logger.info("Retrieved account information")
            return response
        else:
            logger.error("Failed to retrieve account information")
            return None
    
    def place_order(self, symbol, order_type, side, amount, price=None):
        """Place an order"""
        if self.test_mode:
            logger.info(f"Test mode: Placing {side} {order_type} order for {amount} {symbol}" + (f" at {price}" if price else ""))
            return {"orderId": "test-order-" + str(int(time.time()))}
            
        endpoint = "/api/v3/order"
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "quantity": amount,
            "timestamp": int(time.time() * 1000)
        }
        
        if order_type.lower() == "limit":
            params["type"] = "LIMIT"
            params["price"] = price
            params["timeInForce"] = "GTC"
        else:
            params["type"] = "MARKET"
        
        response = self._make_request("POST", endpoint, params, auth=True)
        
        if response:
            logger.info(f"Order placed successfully: {response['orderId']}")
            return response
        else:
            logger.error("Failed to place order")
            return None
    
    def get_order_status(self, symbol, order_id):
        """Get order status"""
        if self.test_mode:
            return {
                "orderId": order_id,
                "status": "FILLED",
                "executedQty": "0.001",
                "price": "50000"
            }
            
        endpoint = "/api/v3/order"
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        
        response = self._make_request("GET", endpoint, params, auth=True)
        
        if response:
            logger.info(f"Retrieved order status for {order_id}")
            return response
        else:
            logger.error(f"Failed to get order status for {order_id}")
            return None
    
    def cancel_order(self, symbol, order_id):
        """Cancel an order"""
        if self.test_mode:
            logger.info(f"Test mode: Cancelling order {order_id} for {symbol}")
            return {"orderId": order_id, "status": "CANCELED"}
            
        endpoint = "/api/v3/order"
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        
        response = self._make_request("DELETE", endpoint, params, auth=True)
        
        if response:
            logger.info(f"Order {order_id} cancelled successfully")
            return response
        else:
            logger.error(f"Failed to cancel order {order_id}")
            return None
    
    def _get_test_klines(self, params):
        """Generate test kline data for backtesting"""
        symbol = params.get("symbol", "BTCUSDT")
        interval = params.get("interval", "15m")
        limit = params.get("limit", 1000)
        
        # Generate random price data
        np.random.seed(42)  # For reproducibility
        
        # Start from a base price
        base_price = 83000  # Starting BTC price
        
        # Generate timestamps
        end_time = datetime.now()
        
        if interval == "5m":
            start_time = end_time - timedelta(minutes=5 * limit)
            freq = "5min"
        elif interval == "15m":
            start_time = end_time - timedelta(minutes=15 * limit)
            freq = "15min"
        elif interval == "1h":
            start_time = end_time - timedelta(hours=limit)
            freq = "1H"
        elif interval == "4h":
            start_time = end_time - timedelta(hours=4 * limit)
            freq = "4H"
        elif interval == "1d":
            start_time = end_time - timedelta(days=limit)
            freq = "1D"
        else:
            start_time = end_time - timedelta(minutes=15 * limit)
            freq = "15min"
        
        dates = pd.date_range(start=start_time, end=end_time, freq=freq)[:limit]
        
        # Generate OHLCV data
        data = []
        current_price = base_price
        
        for i, timestamp in enumerate(dates):
            # Random price movement (more volatile)
            price_change_pct = np.random.normal(0, 0.015)  # Mean 0, std 1.5%
            price_change = current_price * price_change_pct
            
            # Calculate OHLC
            open_price = current_price
            close_price = current_price + price_change
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
            
            # Volume (in BTC)
            volume = abs(np.random.normal(5, 2))
            
            # Update current price for next iteration
            current_price = close_price
            
            # Create row
            row = {
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 3),
                'quote_volume': round(volume * close_price, 2)
            }
            
            data.append(row)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def _get_test_account(self):
        """Return test account data"""
        return {
            "makerCommission": 10,
            "takerCommission": 10,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(time.time() * 1000),
            "accountType": "SPOT",
            "balances": [
                {
                    "asset": "BTC",
                    "free": "0.1",
                    "locked": "0.0"
                },
                {
                    "asset": "USDT",
                    "free": "10000",
                    "locked": "0.0"
                }
            ]
        }
    
    def _get_test_order(self, params):
        """Return test order data"""
        return {
            "symbol": params.get("symbol", "BTCUSDT"),
            "orderId": "test-order-" + str(int(time.time())),
            "orderListId": -1,
            "clientOrderId": "test-client-order",
            "price": params.get("price", "0"),
            "origQty": params.get("quantity", "0.001"),
            "executedQty": params.get("quantity", "0.001"),
            "cummulativeQuoteQty": "0",
            "status": "FILLED",
            "timeInForce": "GTC",
            "type": params.get("type", "MARKET"),
            "side": params.get("side", "BUY"),
            "stopPrice": "0",
            "icebergQty": "0",
            "time": int(time.time() * 1000),
            "updateTime": int(time.time() * 1000),
            "isWorking": True,
            "origQuoteOrderQty": "0"
        }
