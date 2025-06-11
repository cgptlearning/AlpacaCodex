"""Entrypoint for the trading bot."""

import asyncio
import logging
import contextlib

import config
from datamanager import DataManager
from scanner import Scanner
from trader import Trader


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    dm = DataManager()
    await dm.morning_prep()

    trader = Trader(dm.trading_client)
    trader.clear_positions()
    position_task = asyncio.create_task(trader.monitor_positions())

    async def trade_callback(symbol: str, hod_price: float):
        await trader.submit_trade(symbol, hod_price)

    scanner = Scanner(dm, trade_callback)

    try:
        await scanner.start()
    finally:
        position_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await position_task
        await scanner.stop()
        await dm.close()


if __name__ == "__main__":
    asyncio.run(main())

