from binance import BinanceWS
from ftx import FTXWS


testnet = False
contract = "BTC"

# binance = BinanceWS(testnet, contract+"USDT")
# print(binance)

ftx = FTXWS(testnet, contract+"-PERP")
print(ftx)


