import pandas as pd
import numpy as np
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trading_strategy')

class Position(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"

class TradingStrategy:
    """
    Implementation of the trading strategy with the specified conditions
    for LONG and SHORT positions
    """
    
    @staticmethod
    def check_long_condition_1(data, idx):
        """
        Check LONG Condition 1:
        - Price is above VWAP (bullish bias)
        - EMA 9 crosses above EMA 21 (bullish crossover)
        - MACD line crosses above Signal line (bullish momentum shift)
        """
        if idx < 1:
            return False
            
        # Price above VWAP
        price_above_vwap = data['close'].iloc[idx] > data['vwap'].iloc[idx]
        
        # EMA 9 crosses above EMA 21
        ema_crossover = (data['ema_fast'].iloc[idx-1] <= data['ema_slow'].iloc[idx-1] and 
                         data['ema_fast'].iloc[idx] > data['ema_slow'].iloc[idx])
        
        # MACD crosses above Signal
        macd_crossover = (data['macd'].iloc[idx-1] <= data['macd_signal'].iloc[idx-1] and 
                         data['macd'].iloc[idx] > data['macd_signal'].iloc[idx])
        
        # All conditions must be met
        return price_above_vwap and ema_crossover and macd_crossover
    
    @staticmethod
    def check_long_condition_2(data, idx):
        """
        Check LONG Condition 2:
        - RSI Bullish Divergence: Price makes a lower low, but RSI makes a higher low
        - MACD Bullish Crossover: The MACD line crosses above the signal line
        """
        if idx < 1:
            return False
            
        # RSI Bullish Divergence
        rsi_bullish_divergence = data['rsi_bullish_divergence'].iloc[idx]
        
        # MACD crosses above Signal
        macd_crossover = (data['macd'].iloc[idx-1] <= data['macd_signal'].iloc[idx-1] and 
                         data['macd'].iloc[idx] > data['macd_signal'].iloc[idx])
        
        # All conditions must be met
        return rsi_bullish_divergence and macd_crossover
    
    @staticmethod
    def check_long_condition_3(data, idx):
        """
        Check LONG Condition 3:
        - EMA 9 crosses above EMA 21 (short-term bullish momentum)
        - MACD Bullish Crossover
        """
        if idx < 1:
            return False
            
        # EMA 9 crosses above EMA 21
        ema_crossover = (data['ema_fast'].iloc[idx-1] <= data['ema_slow'].iloc[idx-1] and 
                         data['ema_fast'].iloc[idx] > data['ema_slow'].iloc[idx])
        
        # MACD crosses above Signal
        macd_crossover = (data['macd'].iloc[idx-1] <= data['macd_signal'].iloc[idx-1] and 
                         data['macd'].iloc[idx] > data['macd_signal'].iloc[idx])
        
        # All conditions must be met
        return ema_crossover and macd_crossover
    
    @staticmethod
    def check_short_condition_1(data, idx):
        """
        Check SHORT Condition 1:
        - Price is below VWAP (bearish bias)
        - EMA 9 crosses below EMA 21 (bearish crossover)
        - MACD line crosses below Signal line (bearish momentum shift)
        - MACD histogram turns negative
        """
        if idx < 1:
            return False
            
        # Price below VWAP
        price_below_vwap = data['close'].iloc[idx] < data['vwap'].iloc[idx]
        
        # EMA 9 crosses below EMA 21
        ema_crossover = (data['ema_fast'].iloc[idx-1] >= data['ema_slow'].iloc[idx-1] and 
                         data['ema_fast'].iloc[idx] < data['ema_slow'].iloc[idx])
        
        # MACD crosses below Signal
        macd_crossover = (data['macd'].iloc[idx-1] >= data['macd_signal'].iloc[idx-1] and 
                         data['macd'].iloc[idx] < data['macd_signal'].iloc[idx])
        
        # MACD histogram negative
        macd_histogram_negative = data['macd_histogram'].iloc[idx] < 0
        
        # All conditions must be met
        return price_below_vwap and ema_crossover and macd_crossover and macd_histogram_negative
    
    @staticmethod
    def check_short_condition_2(data, idx):
        """
        Check SHORT Condition 2:
        - RSI Bearish Divergence: Price makes a higher high, but RSI makes a lower high
        - MACD Bearish Crossover: The MACD line crosses below the signal line
        """
        if idx < 1:
            return False
            
        # RSI Bearish Divergence
        rsi_bearish_divergence = data['rsi_bearish_divergence'].iloc[idx]
        
        # MACD crosses below Signal
        macd_crossover = (data['macd'].iloc[idx-1] >= data['macd_signal'].iloc[idx-1] and 
                         data['macd'].iloc[idx] < data['macd_signal'].iloc[idx])
        
        # All conditions must be met
        return rsi_bearish_divergence and macd_crossover
    
    @staticmethod
    def check_short_condition_3(data, idx):
        """
        Check SHORT Condition 3:
        - EMA 9 crosses below EMA 21 (short-term bearish momentum)
        - MACD Bearish Crossover
        """
        if idx < 1:
            return False
            
        # EMA 9 crosses below EMA 21
        ema_crossover = (data['ema_fast'].iloc[idx-1] >= data['ema_slow'].iloc[idx-1] and 
                         data['ema_fast'].iloc[idx] < data['ema_slow'].iloc[idx])
        
        # MACD crosses below Signal
        macd_crossover = (data['macd'].iloc[idx-1] >= data['macd_signal'].iloc[idx-1] and 
                         data['macd'].iloc[idx] < data['macd_signal'].iloc[idx])
        
        # All conditions must be met
        return ema_crossover and macd_crossover
    
    @staticmethod
    def check_ema_bearish_crossover(data, idx):
        """Check for EMA bearish crossover (EMA 9 crosses below EMA 21)"""
        if idx < 1:
            return False
            
        return (data['ema_fast'].iloc[idx-1] >= data['ema_slow'].iloc[idx-1] and 
                data['ema_fast'].iloc[idx] < data['ema_slow'].iloc[idx])
    
    @staticmethod
    def check_ema_bullish_crossover(data, idx):
        """Check for EMA bullish crossover (EMA 9 crosses above EMA 21)"""
        if idx < 1:
            return False
            
        return (data['ema_fast'].iloc[idx-1] <= data['ema_slow'].iloc[idx-1] and 
                data['ema_fast'].iloc[idx] > data['ema_slow'].iloc[idx])
    
    @staticmethod
    def generate_signals(data):
        """Generate trading signals based on strategy conditions"""
        # Initialize signals
        data['long_signal'] = False
        data['short_signal'] = False
        data['exit_long_signal'] = False
        data['exit_short_signal'] = False
        data['signal_trigger'] = ""
        
        # Track current position
        current_position = Position.NEUTRAL
        entry_price = 0
        entry_idx = 0
        
        for idx in range(1, len(data)):
            # Check for LONG entry conditions
            long_condition_1 = TradingStrategy.check_long_condition_1(data, idx)
            long_condition_2 = TradingStrategy.check_long_condition_2(data, idx)
            long_condition_3 = TradingStrategy.check_long_condition_3(data, idx)
            
            # Check for SHORT entry conditions
            short_condition_1 = TradingStrategy.check_short_condition_1(data, idx)
            short_condition_2 = TradingStrategy.check_short_condition_2(data, idx)
            short_condition_3 = TradingStrategy.check_short_condition_3(data, idx)
            
            # Check for exit conditions
            ema_bearish_crossover = TradingStrategy.check_ema_bearish_crossover(data, idx)
            ema_bullish_crossover = TradingStrategy.check_ema_bullish_crossover(data, idx)
            
            # Generate entry signals based on position
            if current_position == Position.NEUTRAL:
                # LONG signals
                if long_condition_1:
                    data.loc[data.index[idx], 'long_signal'] = True
                    data.loc[data.index[idx], 'signal_trigger'] = "LONG_COND1"
                    current_position = Position.LONG
                    entry_price = data['close'].iloc[idx]
                    entry_idx = idx
                    logger.info(f"LONG signal generated at {data.index[idx]} - Price: {entry_price} - Trigger: LONG_COND1")
                
                elif long_condition_2:
                    data.loc[data.index[idx], 'long_signal'] = True
                    data.loc[data.index[idx], 'signal_trigger'] = "LONG_COND2"
                    current_position = Position.LONG
                    entry_price = data['close'].iloc[idx]
                    entry_idx = idx
                    logger.info(f"LONG signal generated at {data.index[idx]} - Price: {entry_price} - Trigger: LONG_COND2")
                
                elif long_condition_3:
                    data.loc[data.index[idx], 'long_signal'] = True
                    data.loc[data.index[idx], 'signal_trigger'] = "LONG_COND3"
                    current_position = Position.LONG
                    entry_price = data['close'].iloc[idx]
                    entry_idx = idx
                    logger.info(f"LONG signal generated at {data.index[idx]} - Price: {entry_price} - Trigger: LONG_COND3")
                
                # SHORT signals
                elif short_condition_1:
                    data.loc[data.index[idx], 'short_signal'] = True
                    data.loc[data.index[idx], 'signal_trigger'] = "SHORT_COND1"
                    current_position = Position.SHORT
                    entry_price = data['close'].iloc[idx]
                    entry_idx = idx
                    logger.info(f"SHORT signal generated at {data.index[idx]} - Price: {entry_price} - Trigger: SHORT_COND1")
                
                elif short_condition_2:
                    data.loc[data.index[idx], 'short_signal'] = True
                    data.loc[data.index[idx], 'signal_trigger'] = "SHORT_COND2"
                    current_position = Position.SHORT
                    entry_price = data['close'].iloc[idx]
                    entry_idx = idx
                    logger.info(f"SHORT signal generated at {data.index[idx]} - Price: {entry_price} - Trigger: SHORT_COND2")
                
                elif short_condition_3:
                    data.loc[data.index[idx], 'short_signal'] = True
                    data.loc[data.index[idx], 'signal_trigger'] = "SHORT_COND3"
                    current_position = Position.SHORT
                    entry_price = data['close'].iloc[idx]
                    entry_idx = idx
                    logger.info(f"SHORT signal generated at {data.index[idx]} - Price: {entry_price} - Trigger: SHORT_COND3")
            
            # Generate exit signals
            elif current_position == Position.LONG:
                # Exit LONG on bearish EMA crossover
                if ema_bearish_crossover:
                    data.loc[data.index[idx], 'exit_long_signal'] = True
                    data.loc[data.index[idx], 'signal_trigger'] = "EXIT_LONG_EMA"
                    current_position = Position.NEUTRAL
                    logger.info(f"EXIT LONG signal generated at {data.index[idx]} - Price: {data['close'].iloc[idx]} - Trigger: EMA_BEARISH_CROSSOVER")
            
            elif current_position == Position.SHORT:
                # Exit SHORT on bullish EMA crossover
                if ema_bullish_crossover:
                    data.loc[data.index[idx], 'exit_short_signal'] = True
                    data.loc[data.index[idx], 'signal_trigger'] = "EXIT_SHORT_EMA"
                    current_position = Position.NEUTRAL
                    logger.info(f"EXIT SHORT signal generated at {data.index[idx]} - Price: {data['close'].iloc[idx]} - Trigger: EMA_BULLISH_CROSSOVER")
        
        return data
