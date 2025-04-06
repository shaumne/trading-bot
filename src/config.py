import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
MEXC_API_KEY = os.getenv('MEXC_API_KEY')
MEXC_API_SECRET = os.getenv('MEXC_API_SECRET')

# Trading Configuration
SYMBOL = 'BTCUSDT'  # Trading pair
TIMEFRAMES = ['5m', '15m']  # Timeframes to analyze
QUANTITY = 0.001  # Trading quantity in BTC
TEST_MODE = True  # Set to False for live trading

# Technical Analysis Parameters
VWAP_PERIOD = 14  # Period for VWAP calculation
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
EMA_FAST = 9
EMA_SLOW = 21
ATR_PERIOD = 14

# Risk Management Parameters
STOP_LOSS_ATR_MULTIPLIER = 1.5
TAKE_PROFIT1_ATR_MULTIPLIER = 2.0  # First take profit level
TAKE_PROFIT2_ATR_MULTIPLIER = 3.5  # Second take profit level
MAX_POSITION_SIZE = 0.01  # Maximum position size in BTC
MAX_DAILY_LOSS = 0.02  # Maximum daily loss as percentage of account balance

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FILE = 'trading_bot.log'

# Backtesting Parameters
BACKTEST_START_DATE = '2024-01-01'
BACKTEST_END_DATE = '2024-02-01'
INITIAL_BALANCE = 10000  # Initial balance in USDT