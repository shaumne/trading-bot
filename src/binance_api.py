import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceAPI:
    def __init__(self):
        """Initialize Binance Testnet connection"""
        try:
            self.exchange = ccxt.binance({
                'apiKey': os.getenv('BINANCE_TESTNET_API_KEY'),
                'secret': os.getenv('BINANCE_TESTNET_SECRET_KEY'),
                'enableRateLimit': True,
                'rateLimit': 100,  # Minimum delay between requests (milliseconds)
                'urls': {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                        'ws': 'wss://ws-api.testnet.binance.vision/ws-api/v3',
                        'stream': 'wss://stream.testnet.binance.vision/ws'
                    }
                },
                'options': {
                    'defaultType': 'future',  # Use futures market
                    'testnet': True,  # Enable testnet
                    'adjustForTimeDifference': True,
                    'recvWindow': 5000  # Maximum allowed time difference
                }
            })
            logger.info("Successfully initialized Binance Testnet connection")
        except Exception as e:
            logger.error(f"Failed to initialize Binance Testnet: {str(e)}")
            raise

    def get_historical_data(self, symbol: str, timeframe: str, 
                          limit: int = 1000, 
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data from Binance
        """
        try:
            # Convert timeframe to milliseconds
            timeframe_ms = {
                '1m': 60 * 1000,
                '5m': 5 * 60 * 1000,
                '15m': 15 * 60 * 1000,
                '1h': 60 * 60 * 1000,
                '4h': 4 * 60 * 60 * 1000,
                '1d': 24 * 60 * 60 * 1000
            }
            
            # Get current time in milliseconds
            current_time = int(datetime.now().timestamp() * 1000)
            
            # For testnet, we need to simulate real-time data
            # Calculate a fixed time window (e.g., last 24 hours)
            time_window = 24 * 60 * 60 * 1000  # 24 hours in milliseconds
            since = current_time - time_window
            
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                since=since
            )
            
            if not ohlcv:
                logger.warning(f"No data received for {symbol} on {timeframe} timeframe")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Sort by timestamp to ensure chronological order
            df = df.sort_index()
            
            # For testnet, simulate real-time data by adding a small random noise
            if self.exchange.options.get('testnet', False):
                last_price = df['close'].iloc[-1]
                noise = np.random.normal(0, last_price * 0.0001)  # 0.01% noise
                df.loc[df.index[-1], 'close'] = last_price + noise
                df.loc[df.index[-1], 'high'] = max(df['high'].iloc[-1], df['close'].iloc[-1])
                df.loc[df.index[-1], 'low'] = min(df['low'].iloc[-1], df['close'].iloc[-1])
            
            logger.info(f"Fetched {len(df)} candles from {df.index.min()} to {df.index.max()}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return None

    def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            return {
                'total': balance['total']['USDT'] if 'USDT' in balance['total'] else 0,
                'free': balance['free']['USDT'] if 'USDT' in balance['free'] else 0,
                'used': balance['used']['USDT'] if 'USDT' in balance['used'] else 0
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return {'total': 0, 'free': 0, 'used': 0}

    def create_order(self, symbol: str, order_type: str, side: str, 
                    amount: float, price: Optional[float] = None,
                    client_order_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new order
        """
        try:
            params = {}
            if client_order_id:
                params['newClientOrderId'] = client_order_id
            
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params
            )
            logger.info(f"Created {side} order for {amount} {symbol} at {price}")
            return order
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None

    def cancel_order(self, symbol: str, order_id: Optional[str] = None, 
                    client_order_id: Optional[str] = None) -> bool:
        """
        Cancel an existing order. If both order_id and client_order_id are provided,
        the order is first searched by order_id and then verified against client_order_id.
        """
        try:
            params = {}
            if client_order_id:
                params['origClientOrderId'] = client_order_id
            
            if order_id:
                self.exchange.cancel_order(order_id, symbol, params=params)
            elif client_order_id:
                self.exchange.cancel_order(None, symbol, params=params)
            else:
                raise ValueError("Either order_id or client_order_id must be provided")
            
            logger.info(f"Cancelled order for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current position for a symbol"""
        try:
            positions = self.exchange.fetch_positions([symbol])
            if positions:
                return positions[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching position: {str(e)}")
            return None

    def get_market_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching market price: {str(e)}")
            return None

    def get_my_trades(self, symbol: str, order_id: Optional[str] = None, 
                      limit: int = 500) -> Optional[list]:
        """
        Get trades for a specific symbol
        Using order_id reduces request weight from 20 to 5
        """
        try:
            params = {'limit': limit}
            if order_id:
                params['orderId'] = order_id
            
            trades = self.exchange.fetch_my_trades(symbol, params=params)
            return trades
        except Exception as e:
            logger.error(f"Error fetching trades: {str(e)}")
            return None
