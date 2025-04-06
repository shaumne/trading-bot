# MEXC Trading Bot

A cryptocurrency trading bot for MEXC Exchange that implements automated trading strategies based on technical indicators.

## Features

- Automated trading on MEXC Exchange
- Technical indicators: VWAP, EMA, MACD, RSI, ATR
- Multiple trading conditions for LONG and SHORT positions
- Stop loss and take profit management
- Backtesting capabilities
- Support for multiple timeframes (5m, 15m)

## Trading Strategy

The bot implements a trading strategy with the following conditions:

### LONG Conditions

1. **Condition 1**: Price above VWAP + EMA and MACD Crossovers
   - Price is above VWAP (bullish bias)
   - EMA 9 crosses above EMA 21 (bullish crossover)
   - MACD line crosses above Signal line (bullish momentum shift)

2. **Condition 2**: RSI Bullish Divergence + MACD Confirmation
   - RSI Bullish Divergence: Price makes a lower low, but RSI makes a higher low
   - MACD Bullish Crossover: The MACD line crosses above the signal line

3. **Condition 3**: EMA (9,21) Bullish Crossover + MACD Crossover
   - EMA 9 crosses above EMA 21 (short-term bullish momentum)
   - MACD Bullish Crossover: Confirms strength in the move

### SHORT Conditions

1. **Condition 1**: Price below VWAP + EMA and MACD Bearish Crossovers
   - Price is below VWAP (bearish bias)
   - EMA 9 crosses below EMA 21 (bearish crossover)
   - MACD line crosses below Signal line (bearish momentum shift)
   - MACD histogram turns negative

2. **Condition 2**: RSI Bearish Divergence + MACD Confirmation
   - RSI Bearish Divergence: Price makes a higher high, but RSI makes a lower high
   - MACD Bearish Crossover: The MACD line crosses below the signal line

3. **Condition 3**: EMA (9,21) Bearish Crossover + MACD Crossover
   - EMA 9 crosses below EMA 21 (short-term bearish momentum)
   - MACD Bearish Crossover: Confirms downward pressure

### Risk Management

- **Stop Loss**: 1.5X ATR value from entry
- **Take Profit 1** (50% position): 3.5X ATR value or EMA bearish crossover for LONG (or bullish crossover for SHORT)
- **Take Profit 2** (remaining 50%): 3.5X ATR value or EMA bearish crossover for LONG (or bullish crossover for SHORT)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/shaumne/trading-bot
cd mexc-trading-bot
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project directory with your MEXC API credentials:

```
MEXC_API_KEY=your_api_key_here
MEXC_API_SECRET=your_api_secret_here
```

## Configuration

Edit the `src/config.py` file to customize trading parameters:

- `SYMBOL`: Trading pair (default: 'BTC/USDT')
- `TIMEFRAMES`: Timeframes to trade on (default: ['5m', '15m'])
- `QUANTITY`: Trading quantity in BTC (default: 0.001)
- `TEST_MODE`: Test mode without actual trading (default: True, set to False for real trading)
- Technical indicator parameters (VWAP, EMA, RSI, MACD, ATR periods)
- Risk management parameters (stop loss and take profit multipliers)

## Usage

### Backtesting

To run backtesting on the last month of data:

```bash
python .\src\main.py --backtest
```

This will generate performance reports and charts for each timeframe.

### Live Trading

To start live trading:

```bash
python .\src\main.py --live
```

**IMPORTANT**: Before running in live mode, make sure to:
1. Set up proper API keys with trading permissions in your `.env` file
2. Set `TEST_MODE = False` in `src/config.py` when you are ready for real trading
3. Adjust `QUANTITY` to an appropriate value based on your account balance

## Disclaimer

This trading bot is provided for educational and research purposes only. Use at your own risk. Cryptocurrency trading involves significant risk and you can lose a substantial amount of money. The creators of this bot are not responsible for any financial losses incurred while using it.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
