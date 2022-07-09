"""
Order Book with Websocket Stream

- Get 5% of the book from buy sell side
- Store in a dict of deques for both sides
- run stats on flow
- Measure against current price
"""


import websocket
import threading
import requests
import json
import time


class BitmexWebsocket:
    def __init__(self):
        
        self._base_url = "https://www.bitmex.com"
        self._wss_url = "wss://ws.bitmex.com/realtime"

        self.symbol = "XBTUSD"
        self.curr_price = self._get_curr_price()

        ob_depth_pct = 0.05 # GET CURRENT PRICE AND BUILD THESE ;)
        self.ob_buy_depth = self.curr_price - (self.curr_price * ob_depth_pct)
        self.ob_sell_depth = self.curr_price + (self.curr_price * ob_depth_pct)

        self.raw_book_data = {'total_buys': 0, 'sum_of_buys': 0, 'total_sells': 0, 'sum_of_sells': 0}
        self.raw_sell_nodes = {"size": [], "price": []}
        self.raw_buy_nodes = {"size": [], "price": []}

        self.ws: websocket.WebSocketApp
        t = threading.Thread(target=self._start_ws)

        self.reconnect = True
        # self.topic = "orderBookL2"
        self.topic = "orderBookL2_25"

        t.start()

    def _get_curr_price(self):

        url = "https://www.bitmex.com/api/v1/trade/bucketed"

        data = dict()
        data['symbol'] = self.symbol
        data['partial'] = True  # returns a candle if it is not finished yet
        data['binSize'] = '1m'
        data['count'] = 1   # how many candles we can return (500 max)
        data['reverse'] = True

        try:
            response = requests.get(url, params=data)
        except Exception as e:
            print(f"Connecton error while making GET request to {url}: {e}")
            return

        if response.status_code == 200:
            raw_candles = response.json()
        else:
            print(f"Error while making GET request to {url}: {response.status_code}")
            print(response.headers)
            return None
        
        if raw_candles is not None:
            return raw_candles[0]['close']

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

        buys, total_buys = 0, 0
        sells, total_sells = 0, 0

        response_data = json.loads(msg)

        if "table" in response_data:
            if response_data['table'] == self.topic:
                for data in response_data['data']:
                    if data['symbol'] == self.symbol:
                        # print(data)
                        # time.sleep(5)

                        if data['side'] == "Buy":
                            if 'size' in data:
                                buys += data["size"]
                                total_buys += 1

                        elif data['side'] == "Sell":
                            if 'size' in data:
                                sells += data["size"]
                                total_sells += 1
        
        if buys > 0:
            self.raw_book_data["sum_of_buys"] = buys
            self.raw_book_data['total_buys'] = total_buys
            print(f"Total buy volume: {buys}\nTotal buys: {total_buys}")

        if sells > 0:
            self.raw_book_data["sum_of_sells"] = sells
            self.raw_book_data['total_sells'] = total_sells
            print(f"Total sell volume: {sells}\nTotal sells: {total_sells}\n")

bws = BitmexWebsocket()

print(bws)