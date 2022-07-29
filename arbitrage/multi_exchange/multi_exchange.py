from binance import BinanceWS
from kraken import KrakenWS
from ftx import FTXWS


contract = "BTC"

binance = BinanceWS(contract+"USDT")
ftx = FTXWS(contract+"-PERP")
kraken = KrakenWS(contract)


