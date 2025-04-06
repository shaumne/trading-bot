import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from datetime import datetime
from tabulate import tabulate

from src.indicators.technical import TechnicalIndicators
from src.trading.strategy import TradingStrategy
from src.trading.risk_management import RiskManagement
from src.config import SYMBOL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backtest')

class Backtest:
    """
    Backtesting module to evaluate trading strategies
    """
    
    def __init__(self, data, timeframe, initial_capital=10000, position_size=0.1):
        """
        Initialize the backtester
        
        Args:
            data: OHLCV data with indicators
            timeframe: Timeframe for the data
            initial_capital: Initial capital amount
            position_size: Position size as a fraction of capital
        """
        self.data = data
        self.timeframe = timeframe
        self.initial_capital = float(initial_capital)  # Ensure it's a float
        self.position_size = position_size
        self.results = None
        self.trades = []
        
    def run(self):
        """
        Run the backtest
        
        Returns:
            DataFrame with backtest results
        """
        # Add indicators
        logger.info("Adding technical indicators...")
        data_with_indicators = TechnicalIndicators.add_indicators(self.data.copy())
        
        # Generate trading signals
        logger.info("Generating trading signals...")
        data_with_signals = TradingStrategy.generate_signals(data_with_indicators)
        
        # Apply risk management
        logger.info("Applying risk management...")
        data_with_risk = RiskManagement.apply_risk_management(data_with_signals)
        
        # Calculate P&L
        logger.info("Calculating P&L...")
        results = self._calculate_pnl(data_with_risk)
        
        self.results = results
        logger.info("Backtest complete")
        
        return results
    
    def _calculate_pnl(self, data):
        """
        Calculate P&L for the backtest
        
        Args:
            data: DataFrame with trading signals and risk management
            
        Returns:
            DataFrame with P&L calculations
        """
        # Initialize P&L columns
        data['pnl'] = 0.0
        data['cumulative_pnl'] = 0.0
        data['equity'] = float(self.initial_capital)
        data['drawdown'] = 0.0
        data['max_equity'] = float(self.initial_capital)
        
        # Initialize position tracking
        current_position = None
        position_size = 0
        entry_price = 0
        
        # Track performance metrics
        trades = []
        
        for idx in range(1, len(data)):
            # Check current position
            if pd.isna(data['position'].iloc[idx-1]) and not pd.isna(data['position'].iloc[idx]):
                # New position opened
                current_position = data['position'].iloc[idx]
                entry_price = data['entry_price'].iloc[idx]
                position_size = self.position_size * data['equity'].iloc[idx-1] / entry_price
            
            # Position closed or TP1 hit
            if not pd.isna(data['position'].iloc[idx]) and data['exit_price'].iloc[idx] > 0:
                # Calculate P&L
                exit_price = data['exit_price'].iloc[idx]
                exit_reason = data['exit_reason'].iloc[idx]
                
                if current_position == "LONG":
                    pnl = position_size * (exit_price - entry_price)
                else:  # SHORT
                    pnl = position_size * (entry_price - exit_price)
                
                # Record P&L
                data.loc[data.index[idx], 'pnl'] = float(pnl)
                
                # Record trade
                trade = {
                    'entry_time': data.index[idx-1],
                    'exit_time': data.index[idx],
                    'position': current_position,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'exit_reason': exit_reason
                }
                trades.append(trade)
                
                # Reset position tracking
                current_position = None
                position_size = 0
                entry_price = 0
            
            # TP1 hit (partial exit)
            elif not pd.isna(data['position'].iloc[idx]) and data['tp1_hit'].iloc[idx]:
                # Calculate P&L for partial exit (50%)
                take_profit1 = data['take_profit1'].iloc[idx]
                
                if current_position == "LONG":
                    pnl = (position_size * 0.5) * (take_profit1 - entry_price)
                else:  # SHORT
                    pnl = (position_size * 0.5) * (entry_price - take_profit1)
                
                # Record P&L
                data.loc[data.index[idx], 'pnl'] = float(pnl)
                
                # Reduce position size by 50%
                position_size *= 0.5
                
                # Record trade
                trade = {
                    'entry_time': data.index[idx-1],
                    'exit_time': data.index[idx],
                    'position': current_position,
                    'entry_price': entry_price,
                    'exit_price': take_profit1,
                    'pnl': pnl,
                    'exit_reason': 'TAKE_PROFIT1'
                }
                trades.append(trade)
            
            # Calculate cumulative P&L and equity
            data.loc[data.index[idx], 'cumulative_pnl'] = float(data['pnl'].iloc[:idx+1].sum())
            data.loc[data.index[idx], 'equity'] = float(self.initial_capital) + float(data.loc[data.index[idx], 'cumulative_pnl'])
            
            # Calculate maximum equity and drawdown
            data.loc[data.index[idx], 'max_equity'] = float(max(data['equity'].iloc[:idx+1].max(), data['max_equity'].iloc[idx-1]))
            drawdown_pct = (data['max_equity'].iloc[idx] - data['equity'].iloc[idx]) / data['max_equity'].iloc[idx] * 100 if data['max_equity'].iloc[idx] > 0 else 0
            data.loc[data.index[idx], 'drawdown'] = float(drawdown_pct)
        
        # Store trades
        self.trades = trades
        
        return data
    
    def generate_report(self):
        """
        Generate a performance report
        
        Returns:
            dict: Performance metrics
        """
        if self.results is None:
            logger.error("No backtest results available. Run the backtest first.")
            return None
        
        # Calculate performance metrics
        total_pnl = self.results['pnl'].sum()
        final_equity = self.initial_capital + total_pnl
        returns = (final_equity / self.initial_capital - 1) * 100
        
        # Trade statistics
        num_trades = len(self.trades)
        if num_trades == 0:
            logger.warning("No trades executed during the backtest.")
            return {
                'total_pnl': 0,
                'final_equity': self.initial_capital,
                'returns': 0,
                'num_trades': 0,
                'win_rate': 0,
                'avg_profit_per_trade': 0,
                'avg_profit_winning': 0,
                'avg_loss_losing': 0,
                'profit_factor': 0,
                'max_drawdown': 0
            }
        
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        num_winning = len(winning_trades)
        num_losing = len(losing_trades)
        
        win_rate = num_winning / num_trades * 100
        
        avg_profit_per_trade = total_pnl / num_trades
        
        avg_profit_winning = sum([t['pnl'] for t in winning_trades]) / num_winning if num_winning > 0 else 0
        avg_loss_losing = sum([t['pnl'] for t in losing_trades]) / num_losing if num_losing > 0 else 0
        
        gross_profit = sum([t['pnl'] for t in winning_trades])
        gross_loss = abs(sum([t['pnl'] for t in losing_trades]))
        
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        
        max_drawdown = self.results['drawdown'].max()
        
        # Return metrics
        metrics = {
            'total_pnl': total_pnl,
            'final_equity': final_equity,
            'returns': returns,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'avg_profit_per_trade': avg_profit_per_trade,
            'avg_profit_winning': avg_profit_winning,
            'avg_loss_losing': avg_loss_losing,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown
        }
        
        return metrics
    
    def print_report(self):
        """Print a performance report to the console"""
        metrics = self.generate_report()
        if metrics is None:
            return
        
        print("\n" + "="*50)
        print(f"BACKTEST REPORT - {SYMBOL}")
        print("="*50)
        
        print(f"\nTest Period: {self.results.index[0]} to {self.results.index[-1]}")
        print(f"Initial Capital: ${self.initial_capital:.2f}")
        print(f"Final Equity: ${metrics['final_equity']:.2f}")
        print(f"Total Return: {metrics['returns']:.2f}%")
        print(f"Total P&L: ${metrics['total_pnl']:.2f}")
        print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        
        print("\nTrade Statistics:")
        print(f"Number of Trades: {metrics['num_trades']}")
        print(f"Win Rate: {metrics['win_rate']:.2f}%")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"Average Profit per Trade: ${metrics['avg_profit_per_trade']:.2f}")
        print(f"Average Profit (winning trades): ${metrics['avg_profit_winning']:.2f}")
        print(f"Average Loss (losing trades): ${metrics['avg_loss_losing']:.2f}")
        
        # Print trade breakdown
        print("\nTrade Breakdown:")
        trade_table = []
        for i, trade in enumerate(self.trades[:10]):  # Show first 10 trades
            trade_table.append([
                i+1,
                trade['entry_time'].strftime('%Y-%m-%d %H:%M'),
                trade['exit_time'].strftime('%Y-%m-%d %H:%M'),
                trade['position'],
                f"${trade['entry_price']:.2f}",
                f"${trade['exit_price']:.2f}",
                f"${trade['pnl']:.2f}",
                trade['exit_reason']
            ])
        
        print(tabulate(
            trade_table,
            headers=["#", "Entry Time", "Exit Time", "Position", "Entry Price", "Exit Price", "P&L", "Exit Reason"],
            tablefmt="grid"
        ))
        
        if len(self.trades) > 10:
            print(f"... and {len(self.trades) - 10} more trades")
        
        print("="*50)
    
    def plot_results(self, filename=None):
        """
        Plot backtest results
        
        Args:
            filename: If provided, save the plot to this file
        """
        if self.results is None:
            logger.error("No backtest results available. Run the backtest first.")
            return
        
        plt.figure(figsize=(12, 10))
        
        # Create subplots
        ax1 = plt.subplot(3, 1, 1)
        ax2 = plt.subplot(3, 1, 2, sharex=ax1)
        ax3 = plt.subplot(3, 1, 3, sharex=ax1)
        
        # Price chart with buy/sell signals
        ax1.plot(self.results.index, self.results['close'], label='Price', color='black', alpha=0.5)
        
        # Plot VWAP
        ax1.plot(self.results.index, self.results['vwap'], label='VWAP', color='blue', alpha=0.5)
        
        # Plot EMAs
        ax1.plot(self.results.index, self.results['ema_fast'], label=f'EMA {9}', color='green', alpha=0.5)
        ax1.plot(self.results.index, self.results['ema_slow'], label=f'EMA {21}', color='red', alpha=0.5)
        
        # Plot buy signals
        long_signals = self.results[self.results['long_signal']]
        ax1.scatter(long_signals.index, long_signals['close'], marker='^', color='green', s=100, label='Long Entry')
        
        # Plot sell signals
        short_signals = self.results[self.results['short_signal']]
        ax1.scatter(short_signals.index, short_signals['close'], marker='v', color='red', s=100, label='Short Entry')
        
        # Plot exit signals
        exit_longs = self.results[self.results['exit_long_signal']]
        exit_shorts = self.results[self.results['exit_short_signal']]
        exits = pd.concat([exit_longs, exit_shorts])
        ax1.scatter(exits.index, exits['close'], marker='X', color='black', s=100, label='Strategy Exit')
        
        # Plot take profits
        tp1_hits = self.results[self.results['tp1_hit']]
        tp2_hits = self.results[self.results['tp2_hit']]
        sl_hits = self.results[self.results['sl_hit']]
        
        ax1.scatter(tp1_hits.index, tp1_hits['take_profit1'], marker='d', color='purple', s=80, label='TP1 Hit')
        ax1.scatter(tp2_hits.index, tp2_hits['take_profit2'], marker='d', color='blue', s=80, label='TP2 Hit')
        ax1.scatter(sl_hits.index, sl_hits['stop_loss'], marker='d', color='orange', s=80, label='SL Hit')
        
        ax1.set_title(f'Price Chart with Signals - {SYMBOL}')
        ax1.set_ylabel('Price')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')
        
        # MACD chart
        ax2.plot(self.results.index, self.results['macd'], label='MACD', color='blue')
        ax2.plot(self.results.index, self.results['macd_signal'], label='Signal', color='red')
        ax2.bar(self.results.index, self.results['macd_histogram'], color='green', alpha=0.5, label='Histogram')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.2)
        ax2.set_title('MACD')
        ax2.set_ylabel('Value')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper left')
        
        # Equity curve
        ax3.plot(self.results.index, self.results['equity'], label='Equity', color='green')
        ax3.set_title('Equity Curve')
        ax3.set_xlabel('Date')
        ax3.set_ylabel('Equity')
        ax3.grid(True, alpha=0.3)
        
        # Format x-axis dates
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if filename:
            plt.savefig(filename)
            logger.info(f"Saved backtest plot to {filename}")
        else:
            plt.show()
            
        plt.close()

def run_backtest(data, timeframe, plot=True):
    """
    Run a backtest on the provided data
    
    Args:
        data: OHLCV data
        timeframe: Timeframe of the data
        plot: Whether to generate plots
        
    Returns:
        Backtest instance
    """
    logger.info(f"Starting backtest for {SYMBOL} on {timeframe} timeframe")
    
    # Initialize backtest
    backtest = Backtest(data.copy(), timeframe)
    
    # Run backtest
    results = backtest.run()
    
    # Print report
    backtest.print_report()
    
    # Plot results
    if plot:
        backtest.plot_results(filename=f"backtest_results_{SYMBOL.replace('/', '_')}_{timeframe}.png")
    
    return backtest
