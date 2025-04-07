import pandas as pd
import numpy as np
import logging
from src.config import (
    STOP_LOSS_ATR_MULTIPLIER,
    TAKE_PROFIT1_ATR_MULTIPLIER,
    TAKE_PROFIT2_ATR_MULTIPLIER,
    WIN_RATE_ESTIMATE
)
from src.trading.strategy import Position

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('risk_management')

class RiskManagement:
    """
    Risk management module that implements stop loss and take profit logic
    """
    
    @staticmethod
    def calculate_stop_loss_level(entry_price, atr, position):
        """
        Calculate stop loss level based on ATR
        For LONG positions: entry_price - ATR * multiplier
        For SHORT positions: entry_price + ATR * multiplier
        """
        if position == Position.LONG:
            return entry_price - (atr * STOP_LOSS_ATR_MULTIPLIER)
        elif position == Position.SHORT:
            return entry_price + (atr * STOP_LOSS_ATR_MULTIPLIER)
        else:
            return None
    
    @staticmethod
    def calculate_take_profit_levels(entry_price, atr, position):
        """
        Calculate take profit levels based on ATR
        For LONG positions: entry_price + ATR * multiplier
        For SHORT positions: entry_price - ATR * multiplier
        
        Returns:
            tuple: (take_profit1, take_profit2)
        """
        if position == Position.LONG:
            tp1 = entry_price + (atr * TAKE_PROFIT1_ATR_MULTIPLIER)
            tp2 = entry_price + (atr * TAKE_PROFIT2_ATR_MULTIPLIER)
            return tp1, tp2
        elif position == Position.SHORT:
            tp1 = entry_price - (atr * TAKE_PROFIT1_ATR_MULTIPLIER)
            tp2 = entry_price - (atr * TAKE_PROFIT2_ATR_MULTIPLIER)
            return tp1, tp2
        else:
            return None, None
    
    @staticmethod
    def check_stop_loss_hit(current_price, stop_loss_level, position):
        """
        Check if the stop loss level is hit
        For LONG positions: current_price <= stop_loss_level
        For SHORT positions: current_price >= stop_loss_level
        """
        if position == Position.LONG:
            return current_price <= stop_loss_level
        elif position == Position.SHORT:
            return current_price >= stop_loss_level
        else:
            return False
    
    @staticmethod
    def check_take_profit_hit(current_price, take_profit_level, position):
        """
        Check if the take profit level is hit
        For LONG positions: current_price >= take_profit_level
        For SHORT positions: current_price <= take_profit_level
        """
        if position == Position.LONG:
            return current_price >= take_profit_level
        elif position == Position.SHORT:
            return current_price <= take_profit_level
        else:
            return False
    
    @staticmethod
    def apply_risk_management(data):
        """
        Apply risk management to trading data
        Adds stop loss and take profit levels, and exit signals based on those levels
        """
        # Initialize risk management columns
        data['stop_loss'] = np.nan
        data['take_profit1'] = np.nan
        data['take_profit2'] = np.nan
        data['position'] = None
        data['entry_price'] = np.nan
        data['exit_price'] = np.nan
        data['exit_reason'] = ""
        data['tp1_hit'] = False
        data['tp2_hit'] = False
        data['sl_hit'] = False
        
        # Track active position
        current_position = Position.NEUTRAL
        entry_price = 0
        entry_idx = 0
        stop_loss = 0
        take_profit1 = 0
        take_profit2 = 0
        
        # Track partial close
        tp1_exit_executed = False
        
        for idx in range(1, len(data)):
            # Check for entry signals
            long_signal = data['long_signal'].iloc[idx]
            short_signal = data['short_signal'].iloc[idx]
            
            # Check for exit signals
            exit_long_signal = data['exit_long_signal'].iloc[idx]
            exit_short_signal = data['exit_short_signal'].iloc[idx]
            
            # Update position tracking
            if current_position == Position.NEUTRAL:
                # New LONG position
                if long_signal:
                    current_position = Position.LONG
                    entry_price = data['close'].iloc[idx]
                    entry_idx = idx
                    
                    # Calculate stop loss and take profit levels
                    atr = data['atr'].iloc[idx]
                    stop_loss = RiskManagement.calculate_stop_loss_level(entry_price, atr, current_position)
                    take_profit1, take_profit2 = RiskManagement.calculate_take_profit_levels(entry_price, atr, current_position)
                    
                    # Update data
                    data.loc[data.index[idx], 'position'] = current_position.value
                    data.loc[data.index[idx], 'entry_price'] = entry_price
                    data.loc[data.index[idx], 'stop_loss'] = stop_loss
                    data.loc[data.index[idx], 'take_profit1'] = take_profit1
                    data.loc[data.index[idx], 'take_profit2'] = take_profit2
                    
                    # Reset partial exit tracking
                    tp1_exit_executed = False
                    
                    logger.info(f"LONG position opened at {data.index[idx]} - Price: {entry_price} - SL: {stop_loss} - TP1: {take_profit1} - TP2: {take_profit2}")
                
                # New SHORT position
                elif short_signal:
                    current_position = Position.SHORT
                    entry_price = data['close'].iloc[idx]
                    entry_idx = idx
                    
                    # Calculate stop loss and take profit levels
                    atr = data['atr'].iloc[idx]
                    stop_loss = RiskManagement.calculate_stop_loss_level(entry_price, atr, current_position)
                    take_profit1, take_profit2 = RiskManagement.calculate_take_profit_levels(entry_price, atr, current_position)
                    
                    # Update data
                    data.loc[data.index[idx], 'position'] = current_position.value
                    data.loc[data.index[idx], 'entry_price'] = entry_price
                    data.loc[data.index[idx], 'stop_loss'] = stop_loss
                    data.loc[data.index[idx], 'take_profit1'] = take_profit1
                    data.loc[data.index[idx], 'take_profit2'] = take_profit2
                    
                    # Reset partial exit tracking
                    tp1_exit_executed = False
                    
                    logger.info(f"SHORT position opened at {data.index[idx]} - Price: {entry_price} - SL: {stop_loss} - TP1: {take_profit1} - TP2: {take_profit2}")
            
            # Manage active positions
            elif current_position == Position.LONG:
                # Copy position data forward
                data.loc[data.index[idx], 'position'] = current_position.value
                data.loc[data.index[idx], 'entry_price'] = entry_price
                data.loc[data.index[idx], 'stop_loss'] = stop_loss
                data.loc[data.index[idx], 'take_profit1'] = take_profit1
                data.loc[data.index[idx], 'take_profit2'] = take_profit2
                
                # Current price
                current_price = data['close'].iloc[idx]
                
                # Check for stop loss hit
                if RiskManagement.check_stop_loss_hit(current_price, stop_loss, current_position):
                    # Exit position
                    data.loc[data.index[idx], 'exit_price'] = stop_loss
                    data.loc[data.index[idx], 'exit_reason'] = "STOP_LOSS"
                    data.loc[data.index[idx], 'sl_hit'] = True
                    
                    # Update position
                    current_position = Position.NEUTRAL
                    
                    logger.info(f"LONG position closed (STOP LOSS) at {data.index[idx]} - Price: {stop_loss}")
                
                # Check for take profit 1 hit (partial exit)
                elif not tp1_exit_executed and RiskManagement.check_take_profit_hit(current_price, take_profit1, current_position):
                    # Mark TP1 hit
                    data.loc[data.index[idx], 'tp1_hit'] = True
                    tp1_exit_executed = True
                    
                    logger.info(f"LONG position partial exit (TP1) at {data.index[idx]} - Price: {take_profit1}")
                
                # Check for take profit 2 hit (full exit)
                elif RiskManagement.check_take_profit_hit(current_price, take_profit2, current_position):
                    # Exit position
                    data.loc[data.index[idx], 'exit_price'] = take_profit2
                    data.loc[data.index[idx], 'exit_reason'] = "TAKE_PROFIT2"
                    data.loc[data.index[idx], 'tp2_hit'] = True
                    
                    # Update position
                    current_position = Position.NEUTRAL
                    
                    logger.info(f"LONG position closed (TAKE PROFIT2) at {data.index[idx]} - Price: {take_profit2}")
                
                # Check for strategy exit signal
                elif exit_long_signal:
                    # Exit position
                    data.loc[data.index[idx], 'exit_price'] = current_price
                    data.loc[data.index[idx], 'exit_reason'] = "STRATEGY_EXIT"
                    
                    # Update position
                    current_position = Position.NEUTRAL
                    
                    logger.info(f"LONG position closed (STRATEGY EXIT) at {data.index[idx]} - Price: {current_price}")
            
            # Manage active SHORT positions
            elif current_position == Position.SHORT:
                # Copy position data forward
                data.loc[data.index[idx], 'position'] = current_position.value
                data.loc[data.index[idx], 'entry_price'] = entry_price
                data.loc[data.index[idx], 'stop_loss'] = stop_loss
                data.loc[data.index[idx], 'take_profit1'] = take_profit1
                data.loc[data.index[idx], 'take_profit2'] = take_profit2
                
                # Current price
                current_price = data['close'].iloc[idx]
                
                # Check for stop loss hit
                if RiskManagement.check_stop_loss_hit(current_price, stop_loss, current_position):
                    # Exit position
                    data.loc[data.index[idx], 'exit_price'] = stop_loss
                    data.loc[data.index[idx], 'exit_reason'] = "STOP_LOSS"
                    data.loc[data.index[idx], 'sl_hit'] = True
                    
                    # Update position
                    current_position = Position.NEUTRAL
                    
                    logger.info(f"SHORT position closed (STOP LOSS) at {data.index[idx]} - Price: {stop_loss}")
                
                # Check for take profit 1 hit (partial exit)
                elif not tp1_exit_executed and RiskManagement.check_take_profit_hit(current_price, take_profit1, current_position):
                    # Mark TP1 hit
                    data.loc[data.index[idx], 'tp1_hit'] = True
                    tp1_exit_executed = True
                    
                    logger.info(f"SHORT position partial exit (TP1) at {data.index[idx]} - Price: {take_profit1}")
                
                # Check for take profit 2 hit (full exit)
                elif RiskManagement.check_take_profit_hit(current_price, take_profit2, current_position):
                    # Exit position
                    data.loc[data.index[idx], 'exit_price'] = take_profit2
                    data.loc[data.index[idx], 'exit_reason'] = "TAKE_PROFIT2"
                    data.loc[data.index[idx], 'tp2_hit'] = True
                    
                    # Update position
                    current_position = Position.NEUTRAL
                    
                    logger.info(f"SHORT position closed (TAKE PROFIT2) at {data.index[idx]} - Price: {take_profit2}")
                
                # Check for strategy exit signal
                elif exit_short_signal:
                    # Exit position
                    data.loc[data.index[idx], 'exit_price'] = current_price
                    data.loc[data.index[idx], 'exit_reason'] = "STRATEGY_EXIT"
                    
                    # Update position
                    current_position = Position.NEUTRAL
                    
                    logger.info(f"SHORT position closed (STRATEGY EXIT) at {data.index[idx]} - Price: {current_price}")
        
        return data

    @staticmethod
    def dynamic_position_sizing(capital, entry_price, stop_loss_price, max_risk):
        """
        Calculate position size based on risk per trade
        Using Kelly-inspired position sizing
        """
        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit == 0:
            return 0
        
        capital_at_risk = capital * max_risk
        position_size = capital_at_risk / risk_per_unit
        
        # Apply Kelly criterion 
        kelly_factor = WIN_RATE_ESTIMATE - ((1 - WIN_RATE_ESTIMATE) / ((entry_price - stop_loss_price) / stop_loss_price))
        
        # Use half-Kelly for safety
        half_kelly = max(0, kelly_factor * 0.5)
        
        # Adjust position size by Kelly factor
        position_size = position_size * half_kelly
        
        return position_size
