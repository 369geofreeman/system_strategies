import json
import time
import websocket
import threading

class FTXWS:
    def __init__(self, contract):
        self.contract = contract
        self.ticker_price = 0

        self._base_url = "https://ftx.com/api"
        self._wss_url = "wss://ftx.com/ws/"

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
                print(f"FTX error in run_forever() method: {e}")

            time.sleep(2)

    def _on_open(self, ws):
        print("FTX: connection opened")
        self.ws_connected = True
        self.subscribe_channel(self.contract, reconnection=True)

    def on_close(self, ws):
        print("FTX: Websocket connection closed")
        self.ws_connected = False
    
    def _on_error(self, ws, msg: str):
        print(f"FTX: connection error: {msg}")

    def _on_message(self, ws, msg: str):

        data = json.loads(msg)
        message_type = data['type']

        if message_type in {'subscribed', 'unsubscribed'}:
            return

        elif message_type == 'info':
            if data['code'] == 20001:
                self._start_ws()
                return

        elif message_type == 'error':
            raise Exception(data)
        
        channel = data['channel']

        if channel == "ticker":
            # print(data['data']) = {'bid': 22907.0, 'ask': 22908.0, 'bidSize': 1.8324, 'askSize': 11.1524, 'last': 22908.0, 'time': 1659016082.8891184}
            self.ticker_price = data['data']['bid']
            # print(f"{self.contract} price => {self.ticker_price}", end="\r")

    def subscribe_channel(self, contract: str, reconnection=False):

        data = dict()
        data['op'] = "subscribe"
        data['channel'] = 'ticker'
        data['market'] = contract

        try:
            self.ws.send(json.dumps(data))  # Converts the JSON object (dictionary) to a JSON string
            print(f"FTX: subscribing to: {contract}")

        except Exception as e:
            print(f"Websocket error while subscribing to @bookTicker and @aggTrade: {e}")
