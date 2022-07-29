from datetime import datetime
import threading
import time

from binance import BinanceWS
from kraken import KrakenWS
from ftx import FTXWS


def run():
    orderbooks = {
        "Binance": 0,
        "Ftx": 0,
        "Kraken": 0,
    }

    while True:
        try:
            orderbooks['Binance'] = binance.ticker_price
            orderbooks['Ftx'] = ftx.ticker_price
            orderbooks['Kraken'] = kraken.ticker_price

            if 0 not in orderbooks.values():
                for key, value in orderbooks.items():
                    print(f"{key} => {value}")

            time.sleep(0.1)

        except Exception as e:
            print(f"ERROR => {e}")


if __name__ == "__main__":
    # Management
    contract = "BTC"

    # Create websocket threads
    binance = BinanceWS(contract+"USDT")
    ftx = FTXWS(contract+"-PERP")
    kraken = KrakenWS(contract)

    # Run
    run()
