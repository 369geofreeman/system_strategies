from cProfile import label
from turtle import color
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import datetime
import dateutil
import requests
import sqlite3

from vol_functions import garman_klass, hodges_tompkins, kurtosis, parkinson, std_dev, rogers_satchell, skew, yang_zhang


class VolComparisons:
    def __init__(self, from_time: str, to_time: str, tf: str, contract: str, trading_periods: int):
        self.from_time = from_time
        self.to_time = to_time
        self.tf = tf
        self.contract = contract
        self.trading_periods = trading_periods

        # boolean indicated if we have to set the trading days
        self.functions = [(garman_klass, True), (hodges_tompkins, True), (kurtosis, False), (parkinson, True),
                    (std_dev, True), (rogers_satchell, True), (skew, False), (yang_zhang, True)]

        self.data = self.collect_data()
        self.vol_dataframe = self.set_vol_dataframe()
    
    def collect_data(self) -> pd.DataFrame:

        # See if data in database
        conn = sqlite3.connect('volatility_data.db')
        c = conn.cursor()

        table_name = f"{self.contract}_{self.from_time[:3]+self.from_time[5:7]+self.from_time[8:10]}_{self.to_time[:3]+self.to_time[5:7]+self.to_time[8:10]}"
        c.execute("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name=?;
            """, (table_name, ))

        if bool(c.fetchone()):
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, conn)
            conn.commit()
            conn.close()
            print(f'\nFetching data from {table_name}\n')
            return df

        # Collect data from Bitmex if not in database
        url = "https://www.bitmex.com/api/v1/trade/bucketed"
        candles = {'timestamp': [], 'Open': [], 'High': [], 'Low': [], 'Close': []}

        data = dict()
        data['symbol'] = self.contract
        data['partial'] = True  # returns a candle if it is not finished yet
        data['binSize'] = self.tf
        data['count'] = 500   # how many candles we can return (500 max)
        data['reverse'] = True

        data["startTime"] = datetime.datetime.strptime(self.from_time, '%Y-%m-%d %H:%M')
        data["endTime"] = datetime.datetime.strptime(self.to_time, '%Y-%m-%d %H:%M')

        BITMEX_TF_MINUTES = {"1m": 1, "5m": 5, "10m": 10, "15m": 15, "1h": 60, "1d": 1440}


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
            for idx, cand in enumerate(reversed(raw_candles)):
                ts = dateutil.parser.isoparse(cand['timestamp'])
                ts = ts - datetime.timedelta(minutes=BITMEX_TF_MINUTES[tf])
                candles['timestamp'].append(ts)
                candles["Open"].append(cand["open"])
                candles["High"].append(cand["high"])
                candles["Low"].append(cand["low"])
                candles["Close"].append(cand["close"])

        return_data = pd.DataFrame(candles)

        # Write data to db
        return_data.to_sql(name=table_name, con=conn)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM return_data"
        conn.execute(query)
        conn.commit()
        print(f"{self.contract} - {table_name} written to database")

        return pd.DataFrame(candles)
    
    def set_vol_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame()

        for f, td in self.functions:
            if td:
                r = f(self.data, trading_periods=self.trading_periods)
                df[f.__name__] = r
            else:
                r = f(self.data)
                df[f.__name__] = r
        
        return df

    def plot_data(self, display_type):

        if display_type == 1:
            # Returns all volatility measures over 2 plots
            fig, axis = plt.subplots(2, 2)
            fig.suptitle(f'{self.contract}: {self.from_time[:11]}-{self.to_time[:11]}')

            axis[0, 0].plot(self.vol_dataframe['garman_klass'], label="garman_klass")
            axis[0, 0].plot(self.vol_dataframe['hodges_tompkins'], label="hodges_tompkins")
            axis[0, 0].plot(self.vol_dataframe['parkinson'], label="parkinson")
            axis[0, 0].plot(self.vol_dataframe['std_dev'], label="std_dev")
            axis[0, 0].plot(self.vol_dataframe['rogers_satchell'], label="rogers_satchell")
            axis[0, 0].plot(self.vol_dataframe['yang_zhang'], label="yang_zhang")
            axis[0, 0].grid()
            axis[0, 0].legend()

            axis[0, 1].plot(self.vol_dataframe['kurtosis'], label="kurtosis")
            axis[0, 1].plot(self.vol_dataframe['skew'], label="skew")
            axis[0, 1].grid()
            axis[0, 1].legend()

            axis[1, 0].plot(self.data['Close'], label=f"{self.contract}")
            axis[1, 0].grid()
            axis[1, 0].legend()

            axis[1, 1].plot(self.data['Close'], label=f"{self.contract}")
            axis[1, 1].grid()
            axis[1, 1].legend()

        elif display_type == 2:
            # returns each vol plot individually
            for func, _ in self.functions:
                fig, axs = plt.subplots(2)
                axs[0].plot(self.data['Close'][30:], label=self.contract)
                axs[0].grid()
                axs[0].legend()
                axs[1].plot(self.vol_dataframe[func.__name__], label=func.__name__)
                axs[1].grid()
                axs[1].legend()
                plt.show()
        
        elif display_type == 3:
            # applies each vol to the close price (2 bands above & below sma30)
            for func, _ in self.functions:
                df = pd.DataFrame()
                df['Close'] = self.data['Close'][30:]
                df['sma30'] = self.data['Close'].rolling(window=30).mean()
                df['vol'] = self.vol_dataframe[func.__name__]
                df['b+1'] = df['sma30'] + df['vol']
                df['b+2'] = df['sma30'] + df['vol'] * 4
                df['b-1'] = df['sma30'] - df['vol']
                df['b-2'] = df['sma30'] - df['vol'] * 4

                plt.plot(df['Close'], label=self.contract)
                plt.plot(df['b+1'], linestyle='--', color='g')
                plt.plot(df['b+2'], linestyle='--', color='g')
                plt.plot(df['b-1'], linestyle='--', color='g')
                plt.plot(df['b-2'], linestyle='--', color='g')

                plt.grid()
                plt.legend()
                plt.title(func.__name__)
                plt.show()


from_time = "2022-08-01 00:00"
to_time = "2022-08-01 16:00"
tf = "5m"
contract = "ETHUSD"
trading_periods = (60 // int(tf.replace('m', ''))) * 24

# 1: list all on one chart 2: list each individually, 3: apply to close price 
display_type = 3

vol_comparisons = VolComparisons(from_time, to_time, tf, contract, trading_periods)
# print(vol_comparisons.vol_dataframe)
vol_comparisons.plot_data(display_type)