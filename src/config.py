import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API configuration
MEXC_API_KEY = os.getenv('MEXC_API_KEY', '')
MEXC_API_SECRET = os.getenv('MEXC_API_SECRET', '')

# Trading parameters
SYMBOL = 'BTC/USDT'
TIMEFRAMES = ['5m', '15m']  # 5-minute and 15-minute timeframes
QUANTITY = 0.001  # Trading quantity in BTC
TEST_MODE = True  # Set to False for real trading

# Technical indicators parameters
VWAP_PERIOD = 14
EMA_FAST = 9
EMA_SLOW = 21
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_PERIOD = 14

# Risk management parameters
STOP_LOSS_ATR_MULTIPLIER = 1.5
TAKE_PROFIT1_ATR_MULTIPLIER = 3.5
TAKE_PROFIT2_ATR_MULTIPLIER = 3.5

# Backtesting parameters
BACKTEST_START_DATE = '2023-01-01'
BACKTEST_END_DATE = '2023-12-31'
