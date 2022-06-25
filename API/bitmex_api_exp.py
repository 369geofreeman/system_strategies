from collections import deque
import logging
import requests
import time
import typing
import datetime
import dateutil.parser

import pandas as pd
import numpy as np

from scipy.stats import zscore, linregress
from urllib.parse import urlencode
from threading import Timer

import hmac
import hashlib

import threading
import websocket
import json

from models import *
from strategy_base import AlphaStrategy
from post_to_slack import send_message_to_slack


logger = logging.getLogger()


class BitmexClient:
    def __init__(self, public_key: str, secret_key: str, testnet: bool, strategy: AlphaStrategy):

        if testnet:
            self._base_url = "https://testnet.bitmex.com"
            self._wss_url = "wss://ws.testnet.bitmex.com/realtime"
        else:
            self._base_url = "https://www.bitmex.com"
            self._wss_url = "wss://ws.bitmex.com/realtime"
        
        self._public_key = public_key
        self._secret_key = secret_key
        self.strategy = strategy
        self.trade_start_time = None

        self.ongoing_position = False
        self.trades = deque()

        self.ws: websocket.WebSocketApp
        self.reconnect = True
        
        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.active_trading = False

        self.curr_contract = None
        self.selected_coins = {"alpha": None, "beta": None}
        self.prices = dict()
        self.tf = '5m'
        self.tf_equiv = 300000

        self.candles = {"alpha": deque(), "beta": deque(), "mean": 0.0, "std_dev": 0.0}
        self.start_trading_time = time.time() - 90000  # 86400 seconds in 24h
        self.regression_data = {'timestamp': [], "close": []}
        self.logs = []

        t = threading.Thread(target=self._start_ws)
        t.start()

        logger.info("Bitmex client succefully initialized")

    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})

# Rest API

    def _generate_signature(self, method: str, endpoint: str, expires: str, data: typing.Dict) -> str:

        message = method + endpoint + "?" + urlencode(data) + expires if len(data) > 0 else method + endpoint + expires
        return hmac.new(self._secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()

    def _make_request(self, method: str, endpoint: str, data: typing.Dict):

        headers = dict()
        expires = str(int(time.time()) + 5)
        headers["api-expires"] = expires
        headers['api-key'] = self._public_key
        headers['api-signature'] = self._generate_signature(method, endpoint, expires, data)

        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=headers)
            except Exception as e:
                logger.error("Connecton error while making %s request to %s: %s", method, endpoint, e)
                return None
        
        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=headers)
            except Exception as e:
                logger.error("Connecton error while making %s request to %s: %s", method, endpoint, e)
                return None
        
        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=headers)
            except Exception as e:
                logger.error("Connecton error while making %s request to %s: %s", method, endpoint, e)
                return None

        else:
            raise ValueError()

        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
            method, endpoint, response.json(), response.status_code)
        return None              

    def get_contracts(self) -> typing.Dict[str, Contract]:
        
        instruments = self._make_request("GET", "/api/v1/instrument/active", dict())

        contracts = dict()

        if instruments is not None:
            for s in instruments:
                # if s['symbol'].endswith("USD"):
                if s['symbol'].endswith("USD") or s['symbol'].endswith("USDT") and "_" not in s['symbol']:
                    contracts[s['symbol']] = Contract(s, "bitmex")
        
        return contracts
    
    def get_balances(self) -> typing.Dict[str, Balance]:
        data = dict()
        data['currency'] = "all"

        margin_data = self._make_request("GET", "/api/v1/user/margin", data)

        balances = dict()

        if margin_data is not None:
            for a in margin_data:
                balances[a['currency']] = Balance(a, "bitmex")

        return balances

    def get_historical_candles(self, contract: Contract, timeframe: str,
                              end_time: typing.Optional[int] = None) -> pd.DataFrame:

        BITMEX_TF_MINUTES = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}

        data = dict()
        data['symbol'] = contract
        data['partial'] = True  # returns a candle if it is not finished yet
        data['binSize'] = timeframe
        data['count'] = 500   # how many candles we can return (500 max)
        data['reverse'] = True

        if end_time is not None:
            data['endTime'] = end_time

        raw_candles = self._make_request("GET", "/api/v1/trade/bucketed", data)
        candles = {'timestamp': [], 'close': []}

        if raw_candles is not None:
            for c in reversed(raw_candles):
                ts = dateutil.parser.isoparse(c['timestamp'])
                ts = ts - datetime.timedelta(minutes=BITMEX_TF_MINUTES[timeframe])
                ts = int(ts.timestamp() * 1000)
                candles['timestamp'].append(ts)
                candles["close"].append(c["close"])
        
        all_candles = pd.DataFrame(candles)
        all_candles = all_candles.set_index('timestamp')

        return all_candles

    def _ms_to_dt(self, ms: int) -> datetime.datetime:
        return datetime.datetime.utcfromtimestamp(ms / 1000)


    def _place_order(self, contract: Contract, order_type: str, quantity: int, side: str, price=None, tif=None) -> OrderStatus:
        
        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side.capitalize()  # Buy or Sell
        data['orderQty'] = round(quantity / contract.lot_size) * contract.lot_size
        data['ordType'] = order_type.capitalize()

        if price is not None:
            data['price'] = round(round(price / contract.tick_size) * contract.tick_size, 8)
        
        if tif is not None:
            data['timeInForce'] = tif
        
        order_status = self._make_request("POST", "/api/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status, "bitmex")
        
        return order_status
    
    def cancel_order(self, order_id: str) -> OrderStatus:

        data = dict()
        data['orderID'] = order_id
        
        order_status = self._make_request("DELETE", "/api/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status[0], "bitmex")
        
        return order_status

    def get_order_status(self, contract: Contract, order_id: str) -> OrderStatus:
        
        data = dict()
        data['symbol'] = contract.symbol
        data['reverse'] = True      # first elements of list will be newer ids

        order_status = self._make_request("GET", "/api/v1/order", data)

        if order_status is not None:
            for order in order_status:
                if order['orderID'] == order_id:
                    return OrderStatus(order_status[0], "bitmex")

    def _check_order_status(self, order_id):
        
        order_status = self.get_order_status(self.curr_contract, order_id)

        if order_status is not None:

            logger.info("Order status: %s", order_status.status)

            if order_status.status == "filled":
                for trade in self.trades:
                    if trade.entry_id == order_id:
                        trade.entry_price = order_status.avg_price
                        break
                return
        
        t = Timer(2.0, lambda: self._check_order_status(order_id))
        t.start()

    def _open_position(self, signal_result: str):

        trade_size = self._get_trade_size(self.curr_contract, self.candles['beta'][-1].close)
        if trade_size is None:
            print("error in getting trade size")
            return
        
        order_side = 'buy' if signal_result == 'ol' else 'sell'
        position_side = "long" if signal_result == "ol" else "short"

        self._add_log(f"{position_side.capitalize()} signal on {self.selected_coins['beta']}")

        order_status = self._place_order(self.curr_contract, "MARKET", trade_size, order_side)

        if order_status is not None:
            self._add_log(f"{order_side.capitalize()} order placed | Status {order_status.status}")

            self.ongoing_position = True

            avg_filled_price = None

            if order_status == "filled":
                avg_filled_price = order_status.avg_price

            else:
                t = Timer(2.0, lambda: self._check_order_status(order_status.order_id))
                t.start()

            new_trade = Trade({"time": int(time.time() * 1000), "entry_price": avg_filled_price,
                                "contract": self.curr_contract, "side": position_side, "status": "open", "pnl": 0,
                                "quantity": trade_size, "entry_id": order_status.order_id})

            self.trades.append(new_trade)

    def _close_position(self, trade: Trade):

        order_side = "SELL" if trade.side == 'long' else "BUY"
        order_status = self._place_order(self.curr_contract, "MARKET", trade.quantity, order_side)

        if order_status is not None:
            balances = self.get_balances()
            xbt_bal = balances['XBt'].wallet_balance
            usdt_bal = balances['USDt'].wallet_balance

            send_message_to_slack(trade, xbt_bal, usdt_bal)
            self._add_log(f"Exit order on {self.curr_contract.symbol} placed successfully")
            trade.status = "closed"
            self.ongoing_position = False

# Websocket

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
                logger.error("Bitmex error in run_forever() method: %s", e)
            time.sleep(2)
        
    def _on_open(self, ws):
        logger.info("Bitmex connection opened")

        self.subscribe_channel("instrument")
        self.subscribe_channel("trade")
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning("Bitmex websocket connection closed")
    
    def _on_error(self, ws, msg: str):
        logger.error("Bitmex connection error: %s", msg)

    def _on_message(self, ws, msg: str):

        if self.active_trading:

            data = json.loads(msg)

            # get candles
            if "table" in data:
                if data['table'] == "instrument":

                    for d in data['data']:
                        symbol = d['symbol']

                        if symbol not in self.prices:
                            self.prices[symbol] = {"bid": None, "ask": None}
                        
                        if 'bidPrice' in d:
                            self.prices[symbol]['bid'] = d['bidPrice']
                        if 'askPrice' in d:
                            self.prices[symbol]['ask'] = d['askPrice']
                        
                        # PNL calculation (come back to this part, seems slow in theory)
                        if len(self.trades) > 0:
                            try:
                                if self.selected_coins["beta"] == symbol:
                                    for trade in self.trades:
                                        if trade.contract.multiplier and trade.quantity:
                                            if trade.status == "open" and trade.entry_price > 0:

                                                if trade.side == "long":
                                                    price = self.prices[symbol]['bid']
                                                else:
                                                    price = self.prices[symbol]['ask']
                                                multiplier = trade.contract.multiplier

                                                if trade.contract.inverse:
                                                    if trade.side == "long":
                                                        trade.pnl = (1 / trade.entry_price - 1 / price) * multiplier * trade.quantity
                                                    elif trade.side == "short":
                                                        trade.pnl = (1 / price - 1 / trade.entry_price) * multiplier * trade.quantity
                                                else:
                                                    if trade.side == 'long':
                                                        trade.pnl = (price - trade.entry_price) * multiplier * trade.quantity
                                                    elif trade.side == "short":
                                                        trade.pnl = (trade.entry_price - price) * multiplier * trade.quantity 
                            
                            except RuntimeError as e:
                                logger.error("Error while looping through the trades: %s", e)
            
                if data['table'] == 'trade':

                    for d in data['data']:
                        symbol = d['symbol']
                        ts = int(dateutil.parser.isoparse(d['timestamp']).timestamp() * 1000)

                        if self.selected_coins['alpha'] == symbol:
                            self.parse_trades(float(d['price']), float(d['size']), ts, "alpha")
                            
                        if self.selected_coins["beta"] == symbol:
                            self.parse_trades(float(d['price']), float(d['size']), ts, "beta")

            signal = None

    def subscribe_channel(self, topic: str):
        data = dict()
        data['op'] = "subscribe"
        data['args'] = []
        data['args'].append(topic)

        try:
            self.ws.send(json.dumps(data))
        except Exception as e:
            logger.error("Websocket error while subscribing to %s: %s", topic, e)

    def _get_trade_size(self, contract: Contract, price: float):

        balance = self.get_balances()

        trading_size = 0

        if balance is not None:
            if self.selected_coins["beta"].endswith("USD"):
                if 'XBt' in balance:
                    balance = balance['XBt'].wallet_balance
                    trading_size = balance
                else:
                    return None

            elif self.selected_coins["beta"].endswith("USDT"):
                if 'USDt' in balance:
                    balance = balance['USDt'].wallet_balance
                    trading_size = balance
                else:
                    return None
            else:
                return None
        else:
            return None

        if trading_size > 0:

            if contract.inverse:
                contracts_number = trading_size / (contract.multiplier / price)
            elif contract.quanto:
                contracts_number = trading_size / (contract.multiplier * price)
            else:
                contracts_number = trading_size / (contract.multiplier * price)

            logger.info("Current XBT balance: %s, contracts: %s", balance, contracts_number)

        return int(contracts_number)

# Get 5min candles deque

    def parse_trades(self, price: float, size: float, timestamp: int, coin: str) -> str:

        # Check the trade time and real time are synched
        timestamp_diff = int(time.time() * 1000) - timestamp
        if timestamp_diff >= 2000:
            logger.warning("%s: %s milliseconds of difference between the current time and the trade time",
                            coin, timestamp_diff)

        # Insert first candle
        if len(self.candles[coin]) == 0:
            new_ts = timestamp
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
            new_candle = Candle(candle_info, self.tf, "parse_trade")

            self.candles[coin].append(new_candle)

            logger.info("New candle for %s %s", self.selected_coins[coin], self.tf)

            return "new_candle"

        last_candle = self.candles[coin][-1]

        # Same Candle
        if timestamp < last_candle.timestamp + self.tf_equiv:
            last_candle.close = price
            last_candle.volume += size

            if price > last_candle.high:
                last_candle.high = price
            elif price < last_candle.low:
                last_candle.low = price
            
            return "same_candle"

        # Missing Candles
        elif timestamp >= last_candle.timestamp + 2 * self.tf_equiv:
            missing_candles = int((timestamp - last_candle.timestamp) / self.tf_equiv) - 1
            logger.info("%s missing candles for %s %s (%s %s)", missing_candles, self.selected_coins[coin],
                        self.tf, timestamp, last_candle.timestamp)
            
            for _ in range(missing_candles):
                new_ts = last_candle.timestamp + self.tf_equiv
                candle_info = {'ts': new_ts, 'open': last_candle.close, 'high': last_candle.close,
                               'low': last_candle.close, 'close': last_candle.close, 'volume': 0}
                new_candle = Candle(candle_info, self.tf, "parse_trade")

                self.candles[coin].append(new_candle)
                last_candle = new_candle

                if len(self.candles[coin]) > self.zscore_window:
                    self.candles[coin].popleft()

            new_ts = last_candle.timestamp + self.tf_equiv
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
            new_candle = Candle(candle_info, self.tf, "parse_trade")

            self.candles[coin].append(new_candle)

            return "new_candle"

        # New Candle
        elif timestamp >= last_candle.timestamp + self.tf_equiv:

            new_ts = last_candle.timestamp + self.tf_equiv
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
            new_candle = Candle(candle_info, self.tf, "parse_trade")

            self.candles[coin].append(new_candle)

            if len(self.candles[coin]) == self.zscore_window + 1:
                self.candles[coin].popleft()

            logger.info("New candle for %s %s", self.selected_coins[coin], self.tf)

            return "new_candle"