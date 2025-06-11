"""Data management utilities for the trading bot."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict
import statistics

import csv
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
    volatility: float


class DataManager:
    """Handles morning prep and provides reference data."""

    def __init__(self) -> None:
        self.trading_client = TradingClient(
            config.ALPACA_API_KEY,
            config.ALPACA_SECRET_KEY,
            paper=True,
        )
        self.data_client = StockHistoricalDataClient(
            config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY
        )
        self.low_float_assets: Dict[str, AssetInfo] = {}

    async def morning_prep(self) -> None:
        """Builds the low float universe and retrieves averages."""
        logging.info("Starting morning prep")
        with open("low_float_stocks.csv", newline="") as f:
            reader = csv.DictReader(f)
            symbols = [row["symbol"] for row in reader]

        sem = asyncio.Semaphore(20)
        tasks = [self._fetch_asset_info(symbol, sem) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, AssetInfo):
                self.low_float_assets[res.symbol] = res
        logging.info("Morning prep complete: %s stocks", len(self.low_float_assets))

    async def _fetch_asset_info(self, symbol: str, sem: asyncio.Semaphore):
        """Retrieve historical bars and build AssetInfo."""
        async with sem:
            return await asyncio.to_thread(self._sync_fetch_asset_info, symbol)

    def _sync_fetch_asset_info(self, symbol: str):
        try:
            bars_req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, limit=50)
            bars = self.data_client.get_stock_bars(bars_req).data.get(symbol)
            if not bars:
                return None
            avg_volume = sum(b.v for b in bars) / len(bars)
            prev_close = bars[-1].c
            returns = [(bars[i].c / bars[i-1].c) - 1 for i in range(1, len(bars))]
            volatility = (statistics.stdev(returns) if len(returns) > 1 else 0)
            return AssetInfo(
                symbol=symbol,
                prev_close=prev_close,
                avg_volume=avg_volume,
                volatility=volatility,
            )
        except Exception as exc:
            logging.error("Data request failed for %s: %s", symbol, exc)
            return None

    async def close(self) -> None:
        pass

