"""Data management utilities for the trading bot."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List

import aiohttp
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient

import config


@dataclass
class AssetInfo:
    symbol: str
    prev_close: float
    avg_volume: float


class DataManager:
    """Handles morning prep and provides reference data."""

    def __init__(self) -> None:
        self.trading_client = TradingClient(
            config.ALPACA_API_KEY,
            config.ALPACA_SECRET_KEY,
            paper=True,
            url_override=config.BASE_URL,
        )
        self.data_client = StockHistoricalDataClient(
            config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY
        )
        self.polygon_session = aiohttp.ClientSession()
        self.low_float_assets: Dict[str, AssetInfo] = {}

    async def morning_prep(self) -> None:
        """Builds the low float universe and retrieves averages."""
        logging.info("Starting morning prep")
        assets = self.trading_client.get_all_assets()
        symbols = [
            a.symbol
            for a in assets
            if a.tradable and a.shortable and a.easy_to_borrow and a.exchange in {"NYSE", "NASDAQ"}
        ]

        tasks = [self._check_low_float(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, AssetInfo):
                self.low_float_assets[res.symbol] = res
        logging.info("Morning prep complete: %s stocks", len(self.low_float_assets))

    async def _check_low_float(self, symbol: str):
        """Check polygon for shares outstanding and return AssetInfo if low float."""
        try:
            url = f"https://api.polygon.io/v3/reference/tickers/{symbol}?apiKey={config.POLYGON_API_KEY}"
            async with self.polygon_session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except Exception as exc:  # network or JSON error
            logging.error("Polygon request failed for %s: %s", symbol, exc)
            return None

        shares = data.get("results", {}).get("share_class_shares_outstanding")
        if shares is None or shares >= config.LOW_FLOAT_THRESHOLD:
            return None

        bars_req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, limit=50)
        bars = self.data_client.get_stock_bars(bars_req).data.get(symbol)
        if not bars:
            return None
        avg_volume = sum(b.v for b in bars) / len(bars)
        prev_close = bars[-1].c

        return AssetInfo(symbol=symbol, prev_close=prev_close, avg_volume=avg_volume)

    async def close(self) -> None:
        await self.polygon_session.close()

