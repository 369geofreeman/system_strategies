from binance import BinanceWS
from kraken import KrakenWS
from ftx import FTXWS


contract = "BTC"

# binance = BinanceWS(contract+"USDT")
# print(binance)

# ftx = FTXWS(contract+"-PERP")
# print(ftx)

kraken = KrakenWS(contract)



