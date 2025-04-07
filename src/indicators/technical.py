import pandas as pd
import numpy as np
import logging
from ..config import (
    VWAP_PERIOD,
    EMA_FAST,
    EMA_SLOW,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
    RSI_PERIOD,
    ATR_PERIOD,
    EMA_TREND
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('technical_indicators')

class TechnicalIndicators:
    """
    Technical indicators calculation for trading strategy
    """
    
    @staticmethod
    def calculate_ema(data, period):
        """Calculate Exponential Moving Average"""
        return data['close'].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_vwap(data):
        """Calculate Volume Weighted Average Price (VWAP)"""
        # Typical price = (high + low + close) / 3
        data['typical_price'] = (data['high'] + data['low'] + data['close']) / 3
        # Calculate VWAP
        data['vwap'] = (data['typical_price'] * data['volume']).rolling(window=VWAP_PERIOD).sum() / data['volume'].rolling(window=VWAP_PERIOD).sum()
        return data['vwap']
    
    @staticmethod
    def calculate_macd(data, fast_period=MACD_FAST, slow_period=MACD_SLOW, signal_period=MACD_SIGNAL):
        """Calculate Moving Average Convergence Divergence (MACD)"""
        # Calculate EMA fast and slow
        ema_fast = data['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_rsi(data, period=RSI_PERIOD):
        """Calculate Relative Strength Index (RSI)"""
        # Calculate price changes
        delta = data['close'].diff()
        
        # Get gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS
        rs = avg_gain / avg_loss
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_atr(data, period=ATR_PERIOD):
        """Calculate Average True Range (ATR)"""
        high_low = data['high'] - data['low']
        high_close_prev = np.abs(data['high'] - data['close'].shift(1))
        low_close_prev = np.abs(data['low'] - data['close'].shift(1))
        
        # True range is the maximum of these three
        tr = pd.DataFrame({
            'hl': high_low,
            'hcp': high_close_prev,
            'lcp': low_close_prev
        }).max(axis=1)
        
        # Calculate ATR
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def detect_rsi_divergence(data, period=5):
        """
        Detect RSI divergence patterns
        Returns bullish and bearish divergence signals
        """
        rsi = data['rsi']
        price = data['close']
        
        # Initialize divergence signals
        bullish_divergence = pd.Series(False, index=data.index)
        bearish_divergence = pd.Series(False, index=data.index)
        
        # Look for local extrema in the price and RSI
        for i in range(period, len(data) - period):
            # Check for price local minimum (lower low)
            if (price.iloc[i] < price.iloc[i-period:i].min() and 
                price.iloc[i] < price.iloc[i+1:i+period+1].min()):
                
                # Look back for another minimum within a reasonable window
                for j in range(i-period*3, i-period):
                    if j < 0:
                        continue
                        
                    if (price.iloc[j] < price.iloc[max(0, j-period):j].min() and 
                        price.iloc[j] < price.iloc[j+1:j+period+1].min()):
                        
                        # Bullish divergence: price makes lower low, RSI makes higher low
                        if price.iloc[i] < price.iloc[j] and rsi.iloc[i] > rsi.iloc[j]:
                            bullish_divergence.iloc[i] = True
                            break
            
            # Check for price local maximum (higher high)
            if (price.iloc[i] > price.iloc[i-period:i].max() and 
                price.iloc[i] > price.iloc[i+1:i+period+1].max()):
                
                # Look back for another maximum within a reasonable window
                for j in range(i-period*3, i-period):
                    if j < 0:
                        continue
                        
                    if (price.iloc[j] > price.iloc[max(0, j-period):j].max() and 
                        price.iloc[j] > price.iloc[j+1:j+period+1].max()):
                        
                        # Bearish divergence: price makes higher high, RSI makes lower high
                        if price.iloc[i] > price.iloc[j] and rsi.iloc[i] < rsi.iloc[j]:
                            bearish_divergence.iloc[i] = True
                            break
        
        return bullish_divergence, bearish_divergence
        
    @staticmethod
    def add_indicators(data):
        """Add all technical indicators to the dataframe"""
        # Calculate EMAs
        data['ema_fast'] = TechnicalIndicators.calculate_ema(data, EMA_FAST)
        data['ema_slow'] = TechnicalIndicators.calculate_ema(data, EMA_SLOW)
        data['ema_trend'] = TechnicalIndicators.calculate_ema(data, EMA_TREND)
        
        # Calculate VWAP
        data['vwap'] = TechnicalIndicators.calculate_vwap(data)
        
        # Calculate MACD
        data['macd'], data['macd_signal'], data['macd_histogram'] = TechnicalIndicators.calculate_macd(data)
        
        # Calculate RSI
        data['rsi'] = TechnicalIndicators.calculate_rsi(data)
        
        # Calculate ATR
        data['atr'] = TechnicalIndicators.calculate_atr(data)
        
        # Detect RSI divergence
        data['rsi_bullish_divergence'], data['rsi_bearish_divergence'] = TechnicalIndicators.detect_rsi_divergence(data)
        
        # Drop rows with NaN values
        data.dropna(inplace=True)
        
        logger.info(f"Added technical indicators to {len(data)} data points")
        
        return data
