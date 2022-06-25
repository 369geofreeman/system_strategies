import logging
from connectors.binance_futures import BinanceFuturesClient
from connectors.bitmex import BitmexClient
from config import BITMEX_TEST_API
from config import BINANCE_TEST_API


logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')

# log info to terminal
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

# log info to file
file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)


if __name__ == "__main__":
    test_net = True
    # binance = BinanceFuturesClient(BINANCE_TEST_API['API'],
                                   # BINANCE_TEST_API['SECRET'],
                                   # test_net)

    # print(binance.place_order('BTCUSDT', 'BUY', 0.01, "LIMIT", 20000, "GTC"))
    # print(binance.get_order_status("BTCUSDT", 2836286376))
    # print(binance.cancel_order("BTCUSDT", 2836286376))
    # print(binance._start_ws())

    print('\n--- Bitmex')
    bitmex = BitmexClient(BITMEX_TEST_API['ID'],
                          BITMEX_TEST_API['SECRET'],
                          test_net)
    # print(bitmex.contracts['XBTUSD'].base_asset, bitmex.contracts['XBTUSD'].price_decimals)
    # print(bitmex.balances['XBt'].wallet_balance)

    # print(bitmex.place_order(bitmex.contracts['XBTUSD'], "Limit", 100, "Buy", price=20000, tif="GoodTillCancel"))
    # print(bitmex.get_order_status('ff743098-cfcd-40f4-ace7-bafb1c36f0df', bitmex.contracts['XBTUSD']).status)
    # print(bitmex.cancel_order('ff743098-cfcd-40f4-ace7-bafb1c36f0df').status)
    print(bitmex.place_order(bitmex.contracts['XBTUSD'], 'Limit', 400.4, "Buy", 20000.3456789, 'GoodTillCancel'))

    # root = tk.Tk()
    # root.mainloop()