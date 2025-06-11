"""Entrypoint for the trading bot."""

import asyncio
import logging

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

    async def trade_callback(symbol: str, hod_price: float):
        await trader.submit_trade(symbol, hod_price)

    scanner = Scanner(dm, trade_callback)

    try:
        await scanner.start()
    finally:
        await scanner.stop()
        await dm.close()


if __name__ == "__main__":
    asyncio.run(main())

