# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import plotly.offline
pio.renderers.default = "browser"


class RSI_tests:
    def __init__(self, data, plot_chart, data_title):
        self.data = data
        self.plot_chart = plot_chart
        self.data_title = data_title

    def updateData(self):
        """
        Updates dataframe with readable time format
        """
        self.data['time'] = pd.to_datetime(self.data['time'], unit='ms')

    def rma(self, x, n, y0):
        a = (n-1) / n
        ak = a**np.arange(len(x)-1, -1, -1)
        return np.r_[np.full(n, np.nan), y0, np.cumsum(ak * x) / ak / n + y0 * a**np.arange(1, len(x)+1)]

    def split_given_size(self, a, size):
        '''
        Splits np.arry into equal parts with remainder.
        Params
        ---
        :a:     numpy array
        :size:  int
        '''
        return np.split(a, np.arange(size, len(a), size))

    def multi_rsi(self):
        '''
        Pulls and charts all the coins from folder and charts them
        '''
        coin_names = []
        df_dict = {}

        number_files = os.listdir('../data/1_day')
        number_files = [f for f in os.listdir('../data/1_day/') if f[-4:] == '.csv']

        print('\n\n')
        print('#'*12, 'READING FOLDER', '#'*12)
        print('Total coins: {}\n------\n'.format(len(number_files)))
        print('Data from: 01-10-20 | 22-09-21\n---\n\n')

        # Build df dict and seperate coins
        for idx, df in enumerate(number_files):
            coin_name = df[:3] if df[3] == 'U' else df[:4]
            print('Gathering file {}: {}\n'.format(idx+1, df))
            curr_df = pd.read_csv('../data/1_day/{}'.format(df))
            df_dict[coin_name] = pd.DataFrame({'close': curr_df['close']})
            coin_names.append(coin_name)
            sample_df = curr_df

        print('---------\nRunning stat_arb backtest with the following trading pairs')
        print('each against BTC & ETH:\n---------\n')
        [print('* -', coin) for coin in coin_names]
        print('\n\n')

        upper_band = 84
        lower_band = 29
        n = 14

        print('\nBuilding coins RSI... \n')
        for df in df_dict.values():
            df['change'] = df['close'].diff()
            df['gain'] = df.change.mask(df.change < 0, 0.0)
            df['loss'] = -df.change.mask(df.change > 0, -0.0)
            df['avg_gain'] = self.rma(df.gain[n+1:].to_numpy(), n, np.nansum(df.gain.to_numpy()[:n+1])/n)
            df['avg_loss'] = self.rma(df.loss[n+1:].to_numpy(), n, np.nansum(df.loss.to_numpy()[:n+1])/n)
            df['rs'] = df.avg_gain / df.avg_loss
            df['rsi_{}'.format(n)] = 100 - (100 / (1 + df.rs))

        print('\nBuilding charts...\n\n')

        stable_chart = []
        sample_df['time'] = pd.to_datetime(sample_df['time'], unit='ms')

        for coin in df_dict.keys():
            stable_chart.append(go.Scatter(name=coin,
                                        x=sample_df['time'],
                                        y=df_dict[coin]['rsi_{}'.format(n)]))
        stable_chart.append(go.Scatter(name='Upper Band {}'.format(upper_band),
                                       x=sample_df['time'],
                                       y=[upper_band]*len(sample_df)))
        stable_chart.append(go.Scatter(name='Lower Band {}'.format(lower_band),
                                       x=sample_df['time'],
                                       y=[lower_band]*len(sample_df)))

        print('\nBuilding chart...\n')
        fig1 = plotly.offline.plot({'data': stable_chart, "layout": go.Layout(title='Multi-coin RSI')})
        fig1

        return print('\n\n------- Fin --------\n\n')

    def rsi(self):
        '''
        Returns RSI of dataframe
        -------
        # Seems to only work with chunks of 10,000, so we
        split the values of close and patch them back togather
        after the calculations are done
        '''
        df = pd.DataFrame()
        n = 14

        split_array = self.split_given_size(self.data['close'], 10000)

        for array in split_array:
            df1 = pd.DataFrame({'close': array})
            df1['change'] = df1['close'].diff()
            df1['gain'] = df1.change.mask(df1.change < 0, 0.0)
            df1['loss'] = -df1.change.mask(df1.change > 0, -0.0)
            df1['avg_gain'] = self.rma(df1.gain[n+1:].to_numpy(), n, np.nansum(df1.gain.to_numpy()[:n+1])/n)
            df1['avg_loss'] = self.rma(df1.loss[n+1:].to_numpy(), n, np.nansum(df1.loss.to_numpy()[:n+1])/n)
            df1['rs'] = df1.avg_gain / df1.avg_loss
            df1['rsi_{}'.format(n)] = 100 - (100 / (1 + df1.rs))
            df = pd.concat([df, df1])

        high_band = 80
        count_high = 0
        high_markers = []

        low_band = 40
        count_low = 0
        low_markers = []

        for i in df['rsi_{}'.format(n)]:
            if i >= high_band:
                count_high += 1
                high_markers.append(i)
            else:
                high_markers.append(None)
            if i <= low_band:
                count_low += 1
                low_markers.append(i)
            else:
                low_markers.append(None)

        print('------------------------')
        print('Above {}: {}'.format(high_band, count_high))
        print('Below: {}: {}'.format(low_band, count_low))
        print('------------------------')

        if self.plot_chart:
            self.plot_results(df['rsi_{}'.format(n)], n, high_markers, low_markers)
        return

    def plot_results(self, rsi, n, high_markers, low_markers):
        '''
        Plots chart with TSI entries and exits
        -------
        '''
        data = self.data['time']

        print('\nBuilding chart...\n')

        fig = plotly.offline.plot({'data': [
                        go.Scatter(
                            name='RSI',
                            x=data,
                            y=rsi,
                        ),
                        go.Scatter(
                            mode='markers',
                            name='Sell signals',
                            x=data,
                            y=high_markers,
                            marker_symbol='arrow-down',
                            marker_line_color="black",
                            marker_color="white",
                            marker_line_width=2,
                            marker_size=10
                        ),
                        go.Scatter(
                            mode='markers',
                            name='Buy signals',
                            x=data,
                            y=low_markers,
                            marker_symbol='arrow-up',
                            marker_line_color="blue",
                            marker_color="black",
                            marker_line_width=2,
                            marker_size=10)
                        ],
                        "layout": go.Layout(title=self.data_title)
        })

        fig
        return print('\nChart complete.\n')


def main():
    # Get data
    data_1day = pd.read_csv('.././data/1_day/ETHUSDT1d(1_Oct,_2020"-22_Sept,_2021).csv')

    # Variables
    plot_chart = True
    data_title = 'ETH 1D [15 July 2020 | 14 Sep 2021]'

    # Build model
    model = RSI_tests(data_1day, plot_chart, data_title)
    model.updateData()
    # model.rsi()
    model.multi_rsi()


if __name__ == '__main__':
    main()