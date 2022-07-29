import json
import time
import websocket
import threading

class BinanceWS:
    def __init__(self, contract):
        self.contract = contract
        self.ticker_price = 0    

        self._base_url = "https://fapi.binance.com"
        self._wss_url = "wss://fstream.binance.com/ws"

        # Websocket ID and set websocket variable
        self._ws_id = 1
        self.ws: websocket.WebSocketApp
        self.reconnect = True
        self.ws_connected = False
        self.ws_subscriptions = {"bookTicker": [], "aggTrade": []}

        # Threads for multiple connections
        t = threading.Thread(target=self._start_ws)
        t.start()


    def _start_ws(self):
        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self.on_close,
                                         on_error=self._on_error, on_message=self._on_message)

        while True:
            try:
                if self.reconnect:  # Reconnect unless the interface is closed by the user
                    self.ws.run_forever()  # Blocking method that ends only if the websocket connection drops
                else:
                    break

            except Exception as e:
                print(f"Binance error in run_forever() method: {e}")

            time.sleep(2)

    def _on_open(self, ws):
        print("Binance: connection opened")

        self.ws_connected = True

        for channel in ["bookTicker", "aggTrade"]:
            self.subscribe_channel(self.contract, channel, reconnection=True)

        if "BTCUSDT" not in self.ws_subscriptions["bookTicker"]:
            self.subscribe_channel(self.contract, "bookTicker")

    def on_close(self, ws):
        print("Binance Websocket connection closed")
        self.ws_connected = False

    def _on_error(self, ws, msg: str):
        print(f"Binance connection error: {msg}")

    def _on_message(self, ws, msg: str):

        data = json.loads(msg)

        # Best bid price
        if "e" in data:
            if data['e'] == "bookTicker":
                symbol = data['s']

                if symbol == self.contract:
                    self.ticker_price = data['b']
                    # print(f"{self.contract} price => {self.ticker_price}", end="\r")

    def subscribe_channel(self, contract: str, channel: str, reconnection=False):

        data = dict()
        data['method'] = "SUBSCRIBE"
        data['params'] = []

        if not contract:
            data['params'].append(channel)

        else:
            if contract not in self.ws_subscriptions[channel] or reconnection:
                data['params'].append(contract.lower() + "@" + channel)

                if contract not in self.ws_subscriptions[channel]:
                    self.ws_subscriptions[channel].append(contract)

            if len(data['params']) == 0:
                return

        data['id'] = self._ws_id

        try:
            self.ws.send(json.dumps(data))  # Converts the JSON object (dictionary) to a JSON string
            print(f"Binance: subscribing to: {','.join(data['params'])}")

        except Exception as e:
            print(f"Websocket error while subscribing to @bookTicker and @aggTrade: {e}")

        self._ws_id += 1
