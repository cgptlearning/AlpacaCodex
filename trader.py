"""Order management and trade execution module."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.requests import (
    MarketOrderRequest,
    TakeProfitRequest,
    StopLossRequest,
    OrderRequest,
)

import config


@dataclass
class PositionInfo:
    """Tracked details for an open order."""

    order_id: str
    entry_price: float


class Trader:
    def __init__(self, trading_client: TradingClient) -> None:
        self.client = trading_client
        self.open_positions: Dict[str, PositionInfo] = {}

    def _position_size(self, price: float) -> int:
        qty = int(config.POSITION_SIZE / price)
        return max(qty, 1)

    async def submit_trade(self, symbol: str, entry_price: float) -> None:
        if symbol in self.open_positions:
            return
        qty = self._position_size(entry_price)
        order = OrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            order_class="bracket",
            take_profit=TakeProfitRequest(
                limit_price=round(entry_price * (1 + config.TAKE_PROFIT_PCT), 2)
            ),
            stop_loss=StopLossRequest(
                stop_price=round(entry_price * (1 - config.STOP_LOSS_PCT), 2)
            ),
        )
        try:
            res = self.client.submit_order(order)
            self.open_positions[symbol] = PositionInfo(order_id=res.id, entry_price=entry_price)
            logging.info("Submitted bracket order for %s: %s", symbol, res.id)
        except Exception as exc:
            logging.error("Order submission failed for %s: %s", symbol, exc)

    def remove_position(self, symbol: str) -> None:
        """Remove symbol from tracked open positions."""
        self.open_positions.pop(symbol, None)

    def clear_positions(self) -> None:
        """Reset all tracked positions."""
        self.open_positions.clear()

    async def monitor_positions(self, poll_interval: int = 60) -> None:
        """Periodically refresh open positions and drop filled orders."""
        while True:
            await asyncio.sleep(poll_interval)
            try:
                orders = self.client.get_orders(status="open")
                open_ids = {o.id for o in orders}
                stale = [sym for sym, info in self.open_positions.items() if info.order_id not in open_ids]
                for sym in stale:
                    logging.info("Removing closed position %s", sym)
                    self.remove_position(sym)
            except Exception as exc:
                logging.error("Position update failed: %s", exc)

