# Configuration for the trading bot

# Alpaca API credentials
ALPACA_API_KEY = 'YOUR_ALPACA_API_KEY'
ALPACA_SECRET_KEY = 'YOUR_ALPACA_SECRET_KEY'
BASE_URL = 'https://paper-api.alpaca.markets'
DATA_STREAM_URL = 'wss://stream.data.alpaca.markets/v2/sip'


# Risk management and scanner parameters
POSITION_SIZE = 1000  # dollars per trade
STOP_LOSS_PCT = 0.025
TAKE_PROFIT_PCT = 0.05

LOW_FLOAT_THRESHOLD = 10_000_000
MIN_PRICE = 2.0
MAX_PRICE = 20.0
MIN_PCT_CHANGE = 0.10
MIN_REL_VOLUME = 5
HOD_PROXIMITY_PCT = 0.03
