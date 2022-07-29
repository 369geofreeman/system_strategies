from datetime import datetime, timedelta
import numpy as np
import time

from binance import BinanceWS
from kraken import KrakenWS
from ftx import FTXWS

from chart import show_chart


def run():
    end_time = datetime.now() + timedelta(minutes=run_time)
    orderbooks = {
        "Binance": {"bid": 0, "bid_stream": []},
        "Ftx": {"bid": 0, "bid_stream": []},
        "Kraken": {"bid": 0, "bid_stream": []},
    }

    while True:
        if datetime.now() > end_time:
            if print_chart:
                binance.ws_connected = False
                ftx.ws_connected = False
                kraken.ws_connected = False
                show_chart(orderbooks)
            break

        try:
            orderbooks['Binance']["bid"] = binance.ticker_price
            orderbooks['Ftx']["bid"] = ftx.ticker_price
            orderbooks['Kraken']["bid"] = kraken.ticker_price

            # if 0 not in orderbooks.values():
                # for key, value in orderbooks.items():
                    # print(f"{key} => {value['bid']}")

            if print_chart:
                if float(binance.ticker_price) > 0:
                    orderbooks['Binance']["bid_stream"].append(float(binance.ticker_price))
                if float(ftx.ticker_price) > 0:
                    orderbooks['Ftx']["bid_stream"].append(float(ftx.ticker_price))
                if float(kraken.ticker_price) > 0:
                    orderbooks['Kraken']["bid_stream"].append(float(kraken.ticker_price))

            time.sleep(0.1)

        except Exception as e:
            print(f"ERROR => {e}")


if __name__ == "__main__":
    # Management
    contract = "BTC"
    run_time = 5   # minutes
    print_chart = True

    # Create websocket threads
    binance = BinanceWS(contract+"USDT")
    ftx = FTXWS(contract+"-PERP")
    kraken = KrakenWS(contract)

    # Run
    run()
