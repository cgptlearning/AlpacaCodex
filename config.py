# Configuration for the trading bot

# Alpaca API credentials
ALPACA_API_KEY = 'YOUR_ALPACA_API_KEY'
ALPACA_SECRET_KEY = 'YOUR_ALPACA_SECRET_KEY'
BASE_URL = 'https://paper-api.alpaca.markets'
DATA_STREAM_URL = 'wss://stream.data.alpaca.markets/v2/sip'


# Risk management and scanner parameters
POSITION_SIZE = 1000  # dollars per trade (used if SIZE_EQUITY_PCT == 0)
STOP_LOSS_PCT = 0.025
TAKE_PROFIT_PCT = 0.05

# Daily loss and position limits
MAX_DAILY_LOSS = 1000  # dollars
MAX_POSITIONS = 5

# Dynamic position sizing
# If SIZE_EQUITY_PCT > 0, position size will be calculated as a percentage of
# current account equity. Otherwise POSITION_SIZE is used.
SIZE_EQUITY_PCT = 0.01  # 1% of equity per trade
USE_VOLATILITY_ADJUST = False  # scale size by VOLATILITY_TARGET / asset_vol
VOLATILITY_TARGET = 0.02  # target daily vol used when adjusting by volatility

LOW_FLOAT_THRESHOLD = 10_000_000
MIN_PRICE = 2.0
MAX_PRICE = 20.0
MIN_PCT_CHANGE = 0.10
MIN_REL_VOLUME = 5
HOD_PROXIMITY_PCT = 0.03
