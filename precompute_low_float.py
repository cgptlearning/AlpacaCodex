import csv
import logging

from alpaca.trading.client import TradingClient
import yfinance as yf

import config


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def fetch_symbols() -> list[str]:
    client = TradingClient(
        config.ALPACA_API_KEY,
        config.ALPACA_SECRET_KEY,
        paper=True,
    )
    assets = client.get_assets()
    return [
        a.symbol
        for a in assets
        if a.tradable and a.exchange in {"NYSE", "NASDAQ"}
    ]


def find_low_float_symbols(threshold: int) -> list[str]:
    symbols = fetch_symbols()
    low_float: list[str] = []
    for sym in symbols:
        try:
            info = yf.Ticker(sym).info
            shares = info.get("floatShares") or info.get("sharesOutstanding")
            if shares and shares < threshold:
                low_float.append(sym)
                logging.info("%s float: %s", sym, shares)
        except Exception as exc:  # network or data issue
            logging.warning("Failed to fetch float for %s: %s", sym, exc)
    return low_float


def main() -> None:
    low_float = find_low_float_symbols(config.LOW_FLOAT_THRESHOLD)
    with open("low_float_stocks.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol"])
        for s in low_float:
            writer.writerow([s])
    logging.info("Saved %d symbols", len(low_float))


if __name__ == "__main__":
    main()
