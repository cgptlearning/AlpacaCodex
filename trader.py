"""Order management and trade execution module."""

from __future__ import annotations

import logging
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


class Trader:
    def __init__(self, trading_client: TradingClient) -> None:
        self.client = trading_client
        self.open_positions: Dict[str, float] = {}

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
            self.open_positions[symbol] = entry_price
            logging.info("Submitted bracket order for %s: %s", symbol, res.id)
        except Exception as exc:
            logging.error("Order submission failed for %s: %s", symbol, exc)

