import json
import time
import websocket
import threading

class BinanceWS:
    def __init__(self, testnet, contract):
        self.contract = contract
        self.ticker_price = 0
        self.testnet = testnet
    
        self.platform = "binance_futures"
        if self.testnet:
            self._base_url = "https://testnet.binancefuture.com"
            self._wss_url = "wss://stream.binancefuture.com/ws"
        else:
            self._base_url = "https://fapi.binance.com"
            self._wss_url = "wss://fstream.binance.com/ws"

        # Wbsocket ID and set websocket variable
        self._ws_id = 1
        self.ws: websocket.WebSocketApp
        self.reconnect = True
        self.ws_connected = False
        self.ws_subscriptions = {"bookTicker": [], "aggTrade": []}

        # Threads for multiple connections
        t = threading.Thread(target=self._start_ws)
        t.start()


    def _start_ws(self):

        """
        Infinite loop (thus has to run in a Thread) that reopens the websocket connection in case it drops
        :return:
        """

        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self._on_close,
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

    def _on_close(self, ws):

        """
        Callback method triggered when the connection drops
        :return:
        """

        print("Binance Websocket connection closed")
        self.ws_connected = False

    def _on_error(self, ws, msg: str):

        """
        Callback method triggered in case of error
        :param msg:
        :return:
        """

        print(f"Binance connection error: {msg}")

    def _on_message(self, ws, msg: str):

        """
        The websocket updates of the channels the program subscribed to will go through this callback method
        :param msg:
        :return:
        """

        data = json.loads(msg)

        if "e" in data:
            if data['e'] == "aggTrade":
                symbol = data['s']

                if self.contract == symbol:
                    self.ticker_price = data['p']
                    print(f"{self.contract} price => {self.ticker_price}", end="\r")

    def subscribe_channel(self, contract: str, channel: str, reconnection=False):

        """
        Subscribe to updates on a specific topic for all the symbols.
        If your list is bigger than 300 symbols, the subscription will fail (observed on Binance Spot).
        :param contracts:
        :param channel: aggTrades, bookTicker...
        :param reconnection: Force to subscribe to a symbol even if it already in self.ws_subscriptions[symbol] list
        :return:
        """

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
