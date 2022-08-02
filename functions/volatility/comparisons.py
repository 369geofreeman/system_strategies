import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import datetime
import dateutil
import requests

import os
import sqlite3

from vol_functions import garman_klass, hodges_tompkins, kurtosis, parkinson, std_dev, rogers_satchell, skew, yang_zhang


class VolComparisons:
    def __init__(self, from_time: str, to_time: str, tf: str, contract: str, trading_periods: int):
        self.from_time = from_time
        self.to_time = to_time
        self.tf = tf
        self.contract = contract
        self.trading_periods = trading_periods

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

        return pd.DataFrame(candles)
    
    def set_vol_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame()
        # boolean indicated if we have to set the trading days
        functions = [(garman_klass, True), (hodges_tompkins, True), (kurtosis, False), (parkinson, True),
                    (std_dev, True), (rogers_satchell, True), (skew, False), (yang_zhang, True)]

        for f, td in functions:
            if td:
                r = f(self.data, trading_periods=self.trading_periods)
                df[f.__name__] = r
            else:
                r = f(self.data)
                df[f.__name__] = r
        
        return df

    def plot_data(self):

        fig, (ax1, ax2) = plt.subplots(1, 2)
        fig.suptitle(f'{self.contract}: {self.from_time[:11]}-{self.to_time[:11]}')

        ax1.plot(self.vol_dataframe['garman_klass'], label="garman_klass")
        ax1.plot(self.vol_dataframe['hodges_tompkins'], label="hodges_tompkins")
        ax1.plot(self.vol_dataframe['parkinson'], label="parkinson")
        ax1.plot(self.vol_dataframe['std_dev'], label="std_dev")
        ax1.plot(self.vol_dataframe['rogers_satchell'], label="rogers_satchell")
        ax1.plot(self.vol_dataframe['yang_zhang'], label="yang_zhang")
        ax1.grid()
        ax1.legend()

        ax2.plot(self.vol_dataframe['kurtosis'], label="kurtosis")
        ax2.plot(self.vol_dataframe['skew'], label="skew")
        ax2.grid()
        ax2.legend()

        plt.show()



from_time = "2022-08-01 00:00"
to_time = "2022-08-01 16:00"
tf = "5m"
contract = "XBTUSD"
trading_periods = (60 // int(tf.replace('m', ''))) * 24

vol_comparisons = VolComparisons(from_time, to_time, tf, contract, trading_periods)
print(vol_comparisons.vol_dataframe)
vol_comparisons.plot_data()