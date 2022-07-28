from binance import BinanceWS


testnet = False
contract = "BTCUSDT"

binance = BinanceWS(testnet, contract)
print(binance)


