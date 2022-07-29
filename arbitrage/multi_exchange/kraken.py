import json
import time
import websocket
import requests
import threading

class KrakenWS:
    def __init__(self, contract):
        self.contract = "PF_XBTUSD" if contract == "BTC" else "PF_" + contract + "USD"
        self.ticker_price = 0

        self._base_url = ""
        self._wss_url = "wss://futures.kraken.com/ws/v1"

        # Websocket ID and set websocket variable
        self.ws: websocket.WebSocketApp
        self.reconnect = True
        self.ws_connected = False

        # Threads for multiple connections
        t = threading.Thread(target=self._start_ws)
        t.start()

    def _start_ws(self):
        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self._on_close,
                                         on_error=self._on_error, on_message=self._on_message)

        while True:
            try:
                if self.reconnect:  # Reconnect unless the interface is closed by the user
                    self.ws.run_forever()  # Blocking method that ends only if the websocket connection drops
                else:
                    break

            except Exception as e:
                print(f"Kraken error in run_forever() method: {e}")

            time.sleep(2)

    def _on_open(self, ws):
        print("Kraken: connection opened")
        self.ws_connected = True
        self.subscribe_channel(self.contract, reconnection=True)

    def _on_close(self, ws):
        print("Kraken: Websocket connection closed")
        self.ws_connected = False
    
    def _on_error(self, ws, msg: str):
        print(f"Kraken: connection error: {msg}")

    def subscribe_channel(self, contract: str, reconnection=False):

        data = dict()
        data['event'] = "subscribe"
        data['feed'] = "ticker"
        data['product_ids'] = [contract]

        try:
            self.ws.send(json.dumps(data))  # Converts the JSON object (dictionary) to a JSON string
            print(f"Kraken: subscribing to: {contract}")

        except Exception as e:
            print(f"Websocket error while subscribing to @bookTicker and @aggTrade: {e}")

    def _on_message(self, ws, msg: str):

        message = json.loads(msg)

        print(message['bid'], end="\r")
            
    def get_contracts(self):
        r = requests.get('https://futures.kraken.com/derivatives/api/v3/instruments').json()
        return print({e['symbol'].upper(): e['symbol'].upper() for e in r['instruments']})
