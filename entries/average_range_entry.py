'''
Average Range
---
'''


import pandas as pd
import numpy as np
from scipy import stats, signal
import plotly.graph_objects as go
import plotly.io as pio
import plotly.offline
pio.renderers.default = "browser"


class Average_range:
    def __init__(self, backtest_data,
                    balance,
                    fee,
                    bars_back,
                    std_dev_window,
                    std_devs,
                 return_raw):
        """
        Params
        ---
        :backtest_data: Dataframe
        :balance:       int - Starting balance
        :fee:           int - Fee per trade
        :bars_back:     int - How many bars bahind current bar
        :std_dev_window:int - Count of bars to use in std dev
        :std_devs:      int - Number of standard deviations
        :return_raw:    Bool- Return raw data or plotted chart
        :in_position: - Bool- Currently in a position or not
        """

        self.df = backtest_data
        self.balance = balance
        self.fee = fee
        self.bars_back = bars_back
        self.window = std_dev_window
        self.std_dev = std_devs
        self.return_raw = return_raw

        self.in_position = False

    def updateData(self):
        """
        Updates dataframe with readable time format
        """
        self.df['time'] = pd.to_datetime(self.df['time'], unit='ms')

    def long(self, data, idx):
        '''
        Checks to see if we should open a long position
        at the next candle open.
        params
        ---
        :data:          dataframe - Subset of dataframe to calculate long entry
        :idx:           int       - Index of latest candle
        :average_range  int       - average range of df (high - low)
        '''
        # latest candle range
        rrange = round(data['high'][idx] - data['low'][idx], 2)
        # All candle ranges
        all_ranges = [x - y for x, y in zip(data['high'], data['low'])]
        # mean
        average_range = np.array(all_ranges).mean()
        # Std dev
        std_dev_ranges = np.array(all_ranges).std()

        if rrange > ((2*std_dev_ranges) + average_range) and data['close'][idx] > data['close'][idx-self.bars_back]:
            return True
        return False

    def short(self, data):
        '''
        Checks to see if we should open a short position
        at the next candle open.
        params
        ---
        :data: dataframe - subset of dataframe to calculate short entry
        '''
        pass

    def backtest(self):
        data = self.df
        market_entry = 0
        entries = []

        if self.return_raw:
            return print(data.head())

        print('\nStarting backtest...\n')

        for idx, row in data.iterrows():
            if idx > data.index[0] + self.window and idx < data.index[-1]:
                # Check if in position
                if self.in_position:
                    pass
                else:
                    data_chunk = data.loc[idx-self.window:idx]
                    # Check for long entry
                    open_long = self.long(data_chunk, idx)
                    if open_long:
                        # self.in_position = True
                        market_entry = data.loc[idx+1, 'open']
                        entries.append(market_entry)
                    else:
                        entries.append(None)
            else:
                entries.append(None)

        # Show chart
        print('Building chart...\n')
        self.show_data(data, entries)
        print('Collecting data...\n')
        # Print results and data
        buy_arr_stripped = [i for i in entries if i is not None]
        print('-------\nComplete\n---')
        print("Total candles: {}".format(len(data)))
        print('Total buy signals: {}'.format(len(buy_arr_stripped)))
        print('Average buy price: ${}'.format(round(np.array(buy_arr_stripped).mean(), 2)))
        print('-------')

    def show_data(self, data, buy_signals):
        # Trim df so we don't use 0 on std dev
        data = data[self.window:]
        buy_signals = buy_signals[self.window:]
        # Plot chart
        fig = plotly.offline.plot({'data': [
                        go.Candlestick(
                            name='ETH 15min',
                            x=self.df['time'],
                            open=self.df['open'],
                            high=self.df['high'],
                            low=self.df['low'],
                            close=self.df['close']
                        ),
                        go.Scatter(
                            mode='markers',
                            name='Buy signals',
                            x=data['time'],
                            y=buy_signals,
                            marker_symbol='arrow-up',
                            marker_line_color="midnightblue",
                            marker_color="lightskyblue",
                            marker_line_width=2,
                            marker_size=15
                        ),
                        ]})
        print('below')
        return fig


def main():
    # Import price history and add to dataframe
    backtest_data = pd.read_csv('.././data/ETH_15min_(may_15_2020_28_June_2021).csv')[-1800:]
    backtest_data = backtest_data.drop(columns='Unnamed: 0')

    # Add balance & fees
    balance = 1000
    fee = 0.01

    # Set profile variables
    bars_back = 20
    std_dev_window = 20
    std_devs = 2
    return_raw = False

    #  Initiate model! 
    model = Average_range(backtest_data,
                           balance,
                           fee,
                           bars_back,
                           std_dev_window,
                           std_devs,
                           return_raw)

    # Update the dataframe to fit specifications
    model.updateData()
    # Add standard deviation
    # model.stdDev()

    # Backtest model
    model.backtest()


if __name__ == '__main__':
    main()