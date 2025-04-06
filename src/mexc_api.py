import time
import ccxt
import pandas as pd
from datetime import datetime
import logging
from src.config import MEXC_API_KEY, MEXC_API_SECRET, TEST_MODE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mexc_api')

class MexcAPI:
    """
    MEXC Exchange API Connector
    Handles market data retrieval and order execution
    """
    
    def __init__(self):
        self.exchange = ccxt.mexc({
            'apiKey': MEXC_API_KEY,
            'secret': MEXC_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        
        logger.info("MEXC API connector initialized")
        if TEST_MODE:
            logger.warning("Running in TEST mode - no real orders will be executed")
        
    def get_historical_data(self, symbol, timeframe, limit=1000):
        """
        Fetch historical OHLCV data from MEXC
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candlestick timeframe (e.g., '5m', '15m', '1h')
            limit: Number of candles to fetch
            
        Returns:
            pandas.DataFrame with OHLCV data
        """
        try:
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Retrieved {len(df)} {timeframe} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return None
    
    def place_order(self, symbol, order_type, side, amount, price=None, params={}):
        """
        Place an order on MEXC exchange
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            order_type: Order type (e.g., 'limit', 'market')
            side: Order side ('buy' or 'sell')
            amount: Order quantity
            price: Order price (required for limit orders)
            params: Additional parameters
            
        Returns:
            Order information if successful, None otherwise
        """
        try:
            if TEST_MODE:
                logger.info(f"TEST MODE: Would place {order_type} {side} order for {amount} {symbol} at {price if price else 'market price'}")
                return {"test_order": True, "symbol": symbol, "type": order_type, "side": side, "amount": amount, "price": price}
            
            order = self.exchange.create_order(symbol, order_type, side, amount, price, params)
            logger.info(f"Order placed: {order['id']} - {side} {amount} {symbol} at {price if price else 'market price'}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None
    
    def cancel_order(self, order_id, symbol):
        """
        Cancel an existing order
        
        Args:
            order_id: Order ID to cancel
            symbol: Trading pair
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if TEST_MODE:
                logger.info(f"TEST MODE: Would cancel order {order_id} for {symbol}")
                return True
            
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order {order_id} for {symbol} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    def get_open_orders(self, symbol=None):
        """
        Get open orders
        
        Args:
            symbol: Trading pair (optional)
            
        Returns:
            List of open orders
        """
        try:
            orders = self.exchange.fetch_open_orders(symbol=symbol)
            return orders
            
        except Exception as e:
            logger.error(f"Error fetching open orders: {str(e)}")
            return []
    
    def get_order_status(self, order_id, symbol):
        """
        Get the status of an order
        
        Args:
            order_id: Order ID
            symbol: Trading pair
            
        Returns:
            Order status information
        """
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
            
        except Exception as e:
            logger.error(f"Error fetching order status: {str(e)}")
            return None
    
    def get_account_balance(self):
        """
        Get account balance
        
        Returns:
            Account balance information
        """
        try:
            balance = self.exchange.fetch_balance()
            return balance
            
        except Exception as e:
            logger.error(f"Error fetching account balance: {str(e)}")
            return None
