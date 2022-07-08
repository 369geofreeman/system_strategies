"""
Order Book with Websocket Stream

- Get 5% of the book from buy sell side
- Store in a dict of deques for both sides
- run stats on flow
- Measure against current price
"""


import websocket
import threading
import json
import time


class BitmexWebsocket:
    def __init__(self):
        
        self._base_url = "https://www.bitmex.com"
        self._wss_url = "wss://ws.bitmex.com/realtime"

        self.symbol = "XBTUSD"

        ob_depth_pct = 0.05
        ob_buy_depth = 0
        ob_sell_depth = 0

        self.ws: websocket.WebSocketApp
        t = threading.Thread(target=self._start_ws)

        self.reconnect = True
        # self.topic = "orderBookL2"
        self.topic = "orderBookL2_25"

        t.start()

    def _start_ws(self):
        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self._on_close,
                                        on_error=self._on_error, on_message=self._on_message)
        
        while True:
            try:
                if self.reconnect:
                    self.ws.run_forever()
                else:
                    break

            except Exception as e:
                print(f"Bitmex error in run_forever() method: {e}")

            time.sleep(2)
        
    def _on_open(self, ws):
        print("Bitmex orderbook socket opened")
        self.subscribe_channel(self.topic)
    
    def _on_close(self, ws, close_status_code, close_msg):
        print("Bitmex websocket connection closed")
    
    def _on_error(self, ws, msg: str):
        print(f"Bitmex websocket connection error: {msg}")

    def subscribe_channel(self, topic: str):
        data = dict()
        data['op'] = "subscribe"
        data['args'] = []
        data['args'].append(topic)

        try:
            self.ws.send(json.dumps(data))

        except Exception as e:
            print(f"Websocket error while subscribing to {topic}: {e}")

    def _on_message(self, ws, msg: str):

        raw_book_data = {'total_buys': 0, 'sum_of_buys': 0, 'total_sells': 0, 'sum_of_sells': 0}
        raw_sell_nodes = {"size": [], "price": []}
        raw_buy_nodes = {"size": [], "price": []}

        response_data = json.loads(msg)

        if "table" in response_data:
            if response_data['table'] == self.topic:
                for d in response_data:
                    symbol = d['symbol']

                    if symbol == self.symbol:
                        for idx, data in enumerate(response_data):

                            if data['side'] == "Buy":
                                if data['price'] > k_buy:
                                    raw_book_data["sum_of_buys"] += data["size"]
                                    raw_book_data['total_buys'] += 1

                                    if raw_data:
                                        raw_buy_nodes['size'].append(data['size'])
                                        raw_buy_nodes['price'].append(data['price'])

                            elif data['side'] == "Sell":
                                if data['price'] < k_sell:
                                    raw_book_data["sum_of_sells"] += data["size"]
                                    raw_book_data['total_sells'] += 1

                                    if raw_data:
                                        raw_sell_nodes['size'].append(data['size'])
                                        raw_sell_nodes['price'].append(data['price'])

bws = BitmexWebsocket()

print(bws)