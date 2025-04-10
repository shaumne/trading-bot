import os
import sys
import logging
import time
import argparse
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mexc_api import MexcAPI
from src.binance_api import BinanceAPI
from src.indicators.technical import TechnicalIndicators
from src.trading.strategy import TradingStrategy, Position
from src.trading.risk_management import RiskManagement
from src.backtest.backtest import Backtest
from src.config import SYMBOL, TIMEFRAMES, QUANTITY, TEST_MODE, EXCHANGE

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
            f.write("\n# Binance Testnet API Credentials\n")
            f.write("BINANCE_TESTNET_API_KEY=your_binance_testnet_api_key_here\n")
            f.write("BINANCE_TESTNET_SECRET_KEY=your_binance_testnet_secret_key_here\n")
        logger.info("Created example .env file. Please edit it with your API credentials.")

def get_exchange():
    """Get the appropriate exchange API instance based on configuration"""
    if EXCHANGE == 'binance':
        return BinanceAPI()
    elif EXCHANGE == 'mexc':
        return MexcAPI()
    else:
        raise ValueError(f"Unsupported exchange: {EXCHANGE}")

def backtest_strategy():
    """Run backtesting on historical data"""
    exchange = get_exchange()
    
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
            
        historical_data = exchange.get_historical_data(SYMBOL, timeframe, limit=limit)
        
        if historical_data is None or len(historical_data) == 0:
            logger.error(f"Failed to retrieve historical data for {SYMBOL} on {timeframe} timeframe")
            continue
            
        logger.info(f"Running backtest on {len(historical_data)} candles for {timeframe} timeframe")
        
        # Run backtest
        backtest = Backtest(historical_data, timeframe)
        results = backtest.run()
        
        # Generate report
        backtest.print_report()
        
        # Plot results
        backtest.plot_results(f"backtest_results_{timeframe}.png")

def live_trade():
    """Run the live trading bot"""
    if TEST_MODE:
        logger.warning("Running in TEST mode - no real orders will be executed")
    else:
        logger.warning("Running in LIVE mode - REAL orders will be executed")
    
    exchange = get_exchange()
    
    # Track current positions and orders
    current_position = Position.NEUTRAL
    active_orders = {}
    tp1_executed = False
    stop_loss = 0
    take_profit1 = 0
    take_profit2 = 0
    entry_price = 0
    
    # Track last processed time for each timeframe
    last_processed_time = {tf: None for tf in TIMEFRAMES}
    
    # Track last candle time for each timeframe
    last_candle_time = {tf: None for tf in TIMEFRAMES}
    
    logger.info(f"Starting live trading for {SYMBOL} on {EXCHANGE}")
    
    try:
        while True:
            current_time = datetime.now()
            
            for timeframe in TIMEFRAMES:
                # Calculate the time difference in minutes
                if last_processed_time[timeframe]:
                    time_diff = (current_time - last_processed_time[timeframe]).total_seconds() / 60
                    
                    # Skip if not enough time has passed for this timeframe
                    if timeframe == '5m' and time_diff < 5:
                        continue
                    elif timeframe == '15m' and time_diff < 15:
                        continue
                
                logger.info(f"Processing {timeframe} timeframe")
                
                # Get latest candles
                candles = exchange.get_historical_data(SYMBOL, timeframe, limit=100)
                
                if candles is None or len(candles) == 0:
                    logger.error(f"Failed to retrieve candles for {SYMBOL} on {timeframe} timeframe")
                    continue
                
                # Check if we have new data
                latest_candle_time = candles.index[-1]
                if last_candle_time[timeframe] and latest_candle_time <= last_candle_time[timeframe]:
                    logger.info(f"No new data available for {timeframe} timeframe")
                    continue
                
                # Update last processed time and last candle time
                last_processed_time[timeframe] = current_time
                last_candle_time[timeframe] = latest_candle_time
                
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
                        order = exchange.create_order(
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
                        order = exchange.create_order(
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
                        order = exchange.create_order(
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
                        order = exchange.create_order(
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
                        order = exchange.create_order(
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
                        order = exchange.create_order(
                            symbol=SYMBOL,
                            order_type='market',
                            side='buy',
                            amount=QUANTITY*0.5
                        )
                        
                        if order:
                            tp1_executed = True
                            logger.info(f"Partial exit (TP1) of SHORT position at {current_price}")
            
            # Sleep for a short time to avoid rate limiting
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Error in trading loop: {str(e)}")
        raise

def main():
    """Main entry point for the trading bot"""
    global EXCHANGE  # Move global declaration to the top
    
    parser = argparse.ArgumentParser(description='Crypto Trading Bot')
    parser.add_argument('--mode', choices=['backtest', 'live'], default='live',
                      help='Run mode: backtest or live trading')
    parser.add_argument('--exchange', choices=['mexc', 'binance'], default=EXCHANGE,
                      help='Exchange to use: mexc or binance')
    args = parser.parse_args()
    
    # Update exchange selection if provided via command line
    if args.exchange != EXCHANGE:
        EXCHANGE = args.exchange
        logger.info(f"Using exchange: {EXCHANGE}")
    
    if args.mode == 'backtest':
        backtest_strategy()
    else:
        live_trade()

if __name__ == '__main__':
    main()