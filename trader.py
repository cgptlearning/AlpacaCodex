"""Order management and trade execution module."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

from datamanager import DataManager

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
    def __init__(self, trading_client: TradingClient, data_manager: DataManager) -> None:
        self.client = trading_client
        self.dm = data_manager
        self.open_positions: Dict[str, float] = {}
        try:
            self.start_equity = float(self.client.get_account().equity)
        except Exception:
            self.start_equity = 0.0

    def _position_size(self, symbol: str, price: float) -> int:
        try:
            account = self.client.get_account()
            trade_value = config.POSITION_SIZE
            if config.SIZE_EQUITY_PCT > 0:
                trade_value = float(account.equity) * config.SIZE_EQUITY_PCT
            if config.USE_VOLATILITY_ADJUST:
                info = self.dm.low_float_assets.get(symbol)
                if info and info.volatility:
                    trade_value *= config.VOLATILITY_TARGET / max(info.volatility, 1e-6)
            qty = int(trade_value / price)
        except Exception:
            qty = int(config.POSITION_SIZE / price)
        return max(qty, 1)

    def _loss_limit_reached(self) -> bool:
        try:
            equity = float(self.client.get_account().equity)
            return self.start_equity - equity >= config.MAX_DAILY_LOSS
        except Exception:
            return False

    async def submit_trade(self, symbol: str, entry_price: float) -> None:
        if symbol in self.open_positions:
            return
        if len(self.open_positions) >= config.MAX_POSITIONS:
            logging.info("Max open positions reached")
            return
        if self._loss_limit_reached():
            logging.warning("Daily loss limit reached; trade blocked")
            return

        qty = self._position_size(symbol, entry_price)
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
        for attempt in range(3):
            try:
                res = await asyncio.to_thread(self.client.submit_order, order)
                self.open_positions[symbol] = entry_price
                logging.info("Submitted bracket order for %s: %s", symbol, res.id)
                return
            except Exception as exc:
                if attempt < 2:
                    logging.warning(
                        "Order submission failed for %s (attempt %d): %s",
                        symbol,
                        attempt + 1,
                        exc,
                    )
                    await asyncio.sleep(2)
                else:
                    logging.error(
                        "Order submission failed for %s after 3 attempts: %s",
                        symbol,
                        exc,
                    )

    def remove_position(self, symbol: str) -> None:
        """Remove symbol from tracked open positions."""
        self.open_positions.pop(symbol, None)

    def clear_positions(self) -> None:
        """Reset all tracked positions."""
        self.open_positions.clear()
