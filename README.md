# AlpacaCodex

A simple trading bot that scans low-float stocks using Alpaca's live data.

1. Run `precompute_low_float.py` periodically (daily/weekly) to generate
   `low_float_stocks.csv` with tickers whose float is below the threshold
   defined in `config.py`.
2. Start the bot with `python main.py`. It loads the CSV, retrieves historical
   averages from Alpaca and begins streaming trade data for the filtered list.
   Risk controls such as a daily loss limit, maximum open positions and
   optional dynamic position sizing can be configured in `config.py`.

## Environment Variables

Set the following variables before running any of the scripts:

- `ALPACA_API_KEY` – your Alpaca API key
- `ALPACA_SECRET_KEY` – your Alpaca secret key

`config.py` reads these values from the environment at runtime.

## Warning

This project executes live orders if valid API keys are supplied. It is meant
for educational purposes only. Review the code and understand the risks before
running it with real funds.
