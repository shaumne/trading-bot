import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
MEXC_API_KEY = os.getenv('MEXC_API_KEY')
MEXC_API_SECRET = os.getenv('MEXC_API_SECRET')
BINANCE_TESTNET_API_KEY = os.getenv('BINANCE_TESTNET_API_KEY')
BINANCE_TESTNET_SECRET_KEY = os.getenv('BINANCE_TESTNET_SECRET_KEY')

# Exchange Selection
EXCHANGE = 'binance'  # Options: 'mexc' or 'binance'

# Trading Configuration
SYMBOL = 'BTCUSDT'  # Trading pair
TIMEFRAMES = ['5m', '15m']  # Timeframes to analyze
QUANTITY = 0.001  # Trading quantity in BTC
TEST_MODE = True  # Set to False for live trading

# Technical Analysis Parameters
VWAP_PERIOD = 14  # Period for VWAP calculation
RSI_PERIOD = 14
RSI_OVERBOUGHT = 75  # Artırıldı (70'ten)
RSI_OVERSOLD = 25    # Azaltıldı (30'dan)
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
EMA_FAST = 9
EMA_SLOW = 25  # 21'den 25'e değiştirildi
EMA_TREND = 50  # Trend EMA'sı eklendi
ATR_PERIOD = 14

# Risk Management Parameters
STOP_LOSS_ATR_MULTIPLIER = 2.0  # 1.5'tan 2.0'a artırıldı
TAKE_PROFIT1_ATR_MULTIPLIER = 1.5  # 2.0'dan 1.5'e azaltıldı
TAKE_PROFIT2_ATR_MULTIPLIER = 3.0  # 3.5'tan 3.0'a azaltıldı
MAX_POSITION_SIZE = 0.01  # Maximum position size in BTC
MAX_DAILY_LOSS = 0.02  # Maximum daily loss as percentage of account balance

# Timeframe önceliği
PRIMARY_TIMEFRAME = '15m'  # 15 dakikalık timeframe'i öncelikli olarak belirle

# Kelly Kriterine göre risk ayarları
MAX_RISK_PER_TRADE = 0.02  # Her trade için maksimum sermaye riski %2
WIN_RATE_ESTIMATE = 0.55   # Tahmini kazanma oranı

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FILE = 'trading_bot.log'

# Backtesting Parameters
BACKTEST_START_DATE = '2024-01-01'
BACKTEST_END_DATE = '2024-02-01'
INITIAL_BALANCE = 10000  # Initial balance in USDT

# Email Configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USERNAME = 'your_email@gmail.com'  # Replace with your email
EMAIL_PASSWORD = 'your_app_password'      # Replace with your app password
EMAIL_RECIPIENT = 'aoraya@gmail.com'      # Recipient email
EMAIL_USE_TLS = True