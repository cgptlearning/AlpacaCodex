"""Real-time scanning engine using Alpaca streaming."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, List

from alpaca.data.live import StockDataStream
from alpaca.data.models import Trade

import config
from datamanager import AssetInfo, DataManager


@dataclass
class WatchItem:
    symbol: str
    hod_proximity: float


class Scanner:
    """Runs the streaming scanner and maintains a dynamic watchlist."""

    def __init__(
        self,
        data_manager: DataManager,
        trade_callback: Callable[[str, float], asyncio.Future],
    ) -> None:
        self.dm = data_manager
        self.trade_callback = trade_callback
        self.stream = StockDataStream(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)
        self.hod: Dict[str, float] = defaultdict(float)
        self.volume: Dict[str, int] = defaultdict(int)
        self.watchlist: List[WatchItem] = []
        self.running = False
        self.last_signal: str | None = None

    async def start(self) -> None:
        """Subscribe to trade updates and start processing."""
        self.running = True
        for symbol in self.dm.low_float_assets.keys():
            self.stream.subscribe_trades(self._on_trade, symbol)
        logging.info("Starting stream for %d symbols", len(self.dm.low_float_assets))
        try:
            await self.stream.run()
        finally:
            await self.stop()

    async def stop(self) -> None:
        if self.running:
            self.running = False
            await self.stream.stop_ws()
            await self.stream.close()

    async def _on_trade(self, trade: Trade):
        symbol = trade.symbol
        info = self.dm.low_float_assets.get(symbol)
        if not info:
            return

        price = trade.price
        self.hod[symbol] = max(self.hod[symbol], price)
        self.volume[symbol] += trade.size

        if self._meets_criteria(symbol, price, info):
            proximity = 1 - price / self.hod[symbol]
            self._update_watchlist(symbol, proximity)
            await self._check_trade_signal()

    def _meets_criteria(self, symbol: str, price: float, info: AssetInfo) -> bool:
        if not (config.MIN_PRICE <= price <= config.MAX_PRICE):
            return False
        if price < info.prev_close * (1 + config.MIN_PCT_CHANGE):
            return False
        if self.volume[symbol] < info.avg_volume * config.MIN_REL_VOLUME:
            return False
        if self.hod[symbol] == 0:
            return False
        if (self.hod[symbol] - price) / self.hod[symbol] > config.HOD_PROXIMITY_PCT:
            return False
        return True

    def _update_watchlist(self, symbol: str, proximity: float) -> None:
        """Add or update symbol in the watchlist sorted by HOD proximity."""
        self.watchlist = [w for w in self.watchlist if w.symbol != symbol]
        self.watchlist.append(WatchItem(symbol, proximity))
        self.watchlist.sort(key=lambda w: w.hod_proximity)
        logging.debug("Watchlist updated: %s", self.watchlist)

    async def _check_trade_signal(self) -> None:
        if not self.watchlist:
            return
        top = self.watchlist[0]
        if top.symbol != self.last_signal:
            self.last_signal = top.symbol
            await self.trade_callback(top.symbol, self.hod[top.symbol])

