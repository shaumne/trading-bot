import os
import sys
import logging
import time
import argparse
from datetime import datetime, timedelta
import pandas as pd

from src.mexc_api import MexcAPI
from src.indicators.technical import TechnicalIndicators
from src.trading.strategy import TradingStrategy, Position
from src.trading.risk_management import RiskManagement
from src.backtest.backtest import run_backtest
from src.config import SYMBOL, TIMEFRAMES, QUANTITY, TEST_MODE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('main')

def create_env_file():
    """Create an example .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("# MEXC API Credentials\n")
            f.write("MEXC_API_KEY=your_api_key_here\n")
            f.write("MEXC_API_SECRET=your_api_secret_here\n")
        logger.info("Created example .env file. Please edit it with your API credentials.")

def backtest_strategy():
    """Run backtesting on historical data"""
    mexc = MexcAPI()
    
    for timeframe in TIMEFRAMES:
        logger.info(f"Fetching historical data for {SYMBOL} on {timeframe} timeframe")
        
        # Get historical data (last month)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        # Calculate how many candles to fetch based on timeframe
        if timeframe == '5m':
            limit = 30 * 24 * 12  # 30 days of 5-minute candles
        elif timeframe == '15m':
            limit = 30 * 24 * 4   # 30 days of 15-minute candles
        else:
            limit = 1000  # Default
            
        historical_data = mexc.get_historical_data(SYMBOL, timeframe, limit=limit)
        
        if historical_data is None or len(historical_data) == 0:
            logger.error(f"Failed to retrieve historical data for {SYMBOL} on {timeframe} timeframe")
            continue
            
        logger.info(f"Running backtest on {len(historical_data)} candles for {timeframe} timeframe")
        
        # Run backtest
        backtest = run_backtest(historical_data, timeframe)

def live_trade():
    """Run the live trading bot"""
    if TEST_MODE:
        logger.warning("Running in TEST mode - no real orders will be executed")
    else:
        logger.warning("Running in LIVE mode - REAL orders will be executed")
    
    mexc = MexcAPI()
    
    # Track current positions and orders
    current_position = Position.NEUTRAL
    active_orders = {}
    tp1_executed = False
    stop_loss = 0
    take_profit1 = 0
    take_profit2 = 0
    entry_price = 0
    
    logger.info(f"Starting live trading for {SYMBOL}")
    
    try:
        while True:
            for timeframe in TIMEFRAMES:
                logger.info(f"Processing {timeframe} timeframe")
                
                # Get latest candles
                candles = mexc.get_historical_data(SYMBOL, timeframe, limit=100)
                
                if candles is None or len(candles) == 0:
                    logger.error(f"Failed to retrieve candles for {SYMBOL} on {timeframe} timeframe")
                    continue
                
                # Add indicators
                data = TechnicalIndicators.add_indicators(candles)
                
                # Generate signals
                data = TradingStrategy.generate_signals(data)
                
                # Get latest index
                idx = len(data) - 1
                
                # Check current position
                if current_position == Position.NEUTRAL:
                    # Check for entry signals
                    long_signal = data['long_signal'].iloc[idx]
                    short_signal = data['short_signal'].iloc[idx]
                    
                    if long_signal:
                        # Enter LONG position
                        current_price = data['close'].iloc[idx]
                        atr = data['atr'].iloc[idx]
                        
                        # Calculate stop loss and take profit levels
                        stop_loss = RiskManagement.calculate_stop_loss_level(current_price, atr, Position.LONG)
                        take_profit1, take_profit2 = RiskManagement.calculate_take_profit_levels(current_price, atr, Position.LONG)
                        
                        # Place market order
                        order = mexc.place_order(
                            symbol=SYMBOL,
                            order_type='market',
                            side='buy',
                            amount=QUANTITY
                        )
                        
                        if order:
                            current_position = Position.LONG
                            entry_price = current_price
                            tp1_executed = False
                            
                            logger.info(f"Entered LONG position at {current_price} - SL: {stop_loss} - TP1: {take_profit1} - TP2: {take_profit2}")
                            
                    elif short_signal:
                        # Enter SHORT position
                        current_price = data['close'].iloc[idx]
                        atr = data['atr'].iloc[idx]
                        
                        # Calculate stop loss and take profit levels
                        stop_loss = RiskManagement.calculate_stop_loss_level(current_price, atr, Position.SHORT)
                        take_profit1, take_profit2 = RiskManagement.calculate_take_profit_levels(current_price, atr, Position.SHORT)
                        
                        # Place market order
                        order = mexc.place_order(
                            symbol=SYMBOL,
                            order_type='market',
                            side='sell',
                            amount=QUANTITY
                        )
                        
                        if order:
                            current_position = Position.SHORT
                            entry_price = current_price
                            tp1_executed = False
                            
                            logger.info(f"Entered SHORT position at {current_price} - SL: {stop_loss} - TP1: {take_profit1} - TP2: {take_profit2}")
                
                # Manage active positions
                elif current_position == Position.LONG:
                    current_price = data['close'].iloc[idx]
                    
                    # Check for exit signals
                    exit_signal = data['exit_long_signal'].iloc[idx]
                    
                    # Check if stop loss or take profit is hit
                    sl_hit = RiskManagement.check_stop_loss_hit(current_price, stop_loss, current_position)
                    tp1_hit = not tp1_executed and RiskManagement.check_take_profit_hit(current_price, take_profit1, current_position)
                    tp2_hit = RiskManagement.check_take_profit_hit(current_price, take_profit2, current_position)
                    
                    if sl_hit or tp2_hit or exit_signal:
                        # Exit position
                        exit_reason = "STOP_LOSS" if sl_hit else ("TAKE_PROFIT2" if tp2_hit else "STRATEGY_EXIT")
                        
                        # Place market sell order
                        order = mexc.place_order(
                            symbol=SYMBOL,
                            order_type='market',
                            side='sell',
                            amount=QUANTITY if not tp1_executed else QUANTITY*0.5
                        )
                        
                        if order:
                            current_position = Position.NEUTRAL
                            logger.info(f"Exited LONG position at {current_price} - Reason: {exit_reason}")
                    
                    # Partial take profit
                    elif tp1_hit:
                        # Sell half position
                        order = mexc.place_order(
                            symbol=SYMBOL,
                            order_type='market',
                            side='sell',
                            amount=QUANTITY*0.5
                        )
                        
                        if order:
                            tp1_executed = True
                            logger.info(f"Partial exit (TP1) of LONG position at {current_price}")
                
                elif current_position == Position.SHORT:
                    current_price = data['close'].iloc[idx]
                    
                    # Check for exit signals
                    exit_signal = data['exit_short_signal'].iloc[idx]
                    
                    # Check if stop loss or take profit is hit
                    sl_hit = RiskManagement.check_stop_loss_hit(current_price, stop_loss, current_position)
                    tp1_hit = not tp1_executed and RiskManagement.check_take_profit_hit(current_price, take_profit1, current_position)
                    tp2_hit = RiskManagement.check_take_profit_hit(current_price, take_profit2, current_position)
                    
                    if sl_hit or tp2_hit or exit_signal:
                        # Exit position
                        exit_reason = "STOP_LOSS" if sl_hit else ("TAKE_PROFIT2" if tp2_hit else "STRATEGY_EXIT")
                        
                        # Place market buy order (to cover short)
                        order = mexc.place_order(
                            symbol=SYMBOL,
                            order_type='market',
                            side='buy',
                            amount=QUANTITY if not tp1_executed else QUANTITY*0.5
                        )
                        
                        if order:
                            current_position = Position.NEUTRAL
                            logger.info(f"Exited SHORT position at {current_price} - Reason: {exit_reason}")
                    
                    # Partial take profit
                    elif tp1_hit:
                        # Buy half position (to cover half of short)
                        order = mexc.place_order(
                            symbol=SYMBOL,
                            order_type='market',
                            side='buy',
                            amount=QUANTITY*0.5
                        )
                        
                        if order:
                            tp1_executed = True
                            logger.info(f"Partial exit (TP1) of SHORT position at {current_price}")
            
            # Wait for next iteration
            logger.info("Waiting for next cycle...")
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Error in trading loop: {str(e)}")
        raise

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description='MEXC Trading Bot')
    parser.add_argument('--backtest', action='store_true', help='Run backtesting')
    parser.add_argument('--live', action='store_true', help='Run live trading')
    
    args = parser.parse_args()
    
    create_env_file()
    
    if args.backtest:
        backtest_strategy()
    elif args.live:
        live_trade()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()