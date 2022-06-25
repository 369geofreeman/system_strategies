# Vwap strategy
# ---

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math


class Vwap_Strat:
    def __init__(self, backtest_data, balance, fee, candles, window, sd):
        self.df = backtest_data
        self.balance = balance
        self.fee = fee
        self.candles = candles
        self.window = window
        self.sd = sd

        self.buy_price = []
        self.sell_price = []

    def updateData(self):
        """
            Adds the time, balance position and gains columns
            to the dataframe.
            updates the size of the df.
        """
        self.df['time'] = pd.to_datetime(self.df['time'], unit='ms')
        self.df['balance'] = ['n/a']*len(self.df['close'])
        self.df['in_position'] = ['n/a']*len(self.df['close'])
        self.df['%_balance'] = ['0%']*len(self.df['close'])

    def vwap(self):
        '''
            Calculated the VWAP and adds it to the dataframe
        '''
        rolling_volume = 0
        cumulative_total = 0
        candle_period = self.candles
        # Add empty vwap column to df
        self.df['vwap'] = [0.0]*len(self.df['close'])

        for i in self.df.index:
            # Fix 0 division if volume = 0
            if self.df['volume'][i] == 0:
                self.df.at[i, 'volume'] = 1
            # ---
            if candle_period == 0:
                rolling_volume = self.df['volume'][i]
                cumulative_total = 0
                candle_period = self.candles
            else:
                rolling_volume += self.df['volume'][i]
                candle_period -= 1
            # Set typical price ((HP + LP + CP) / 3)
            tp = round((self.df['high'][i] + self.df['low'][i] + self.df['close'][i]) / 3, 2)
            tp = tp * self.df['volume'][i]
            cumulative_total += tp 
            self.df.at[i, 'vwap'] = cumulative_total / rolling_volume

    def std_dev_bands(self):
        '''
            Calculates the higher and lower standared deviations
            and adds them to the dataFrame
        '''
        self.df['upper_band'] = self.df['vwap'] + self.df['close'].\
            rolling(window=self.window).std() * self.sd
        self.df['lower_band'] = self.df['vwap'] - self.df['close'].\
            rolling(window=self.window).std() * self.sd
        self.df = self.df[self.candles:]
        self.df = self.df.reset_index()

    def strategy(self):
        pass

    def positions(self):
        pass

    def backtest(self):
        data = self.df
        position = 'no'
        bal = self.balance
        fee = self.fee
        no_of_trades = 0
        price_bought_at = 0
        percentage_gain = '0%'
        biggest_balance = [0, 0]

        for i in data.index:
            if position == 'no':
                if data['close'][i] <= data['lower_band'][i]:
                    position = 'yes'
                    price_bought_at = data['close'][i]
                    no_of_trades += 1
                    self.buy_price.append(data['close'][i])
                    self.sell_price.append(np.nan)
                else:
                    self.buy_price.append(np.nan)
                    self.sell_price.append(np.nan)
                pg = 0
            else:
                if data['close'][i] >= data['upper_band'][i]:
                    position = 'no'
                    no_of_trades += 1
                    pg = round(((data['close'][i] - price_bought_at) / price_bought_at) * 100, 2)
                    bal = bal + ((bal * pg) / 100)
                    self.buy_price.append(np.nan)
                    self.sell_price.append(data['close'][i])
                    # print rolling profits/percentage gains or losses
                    print('Date: {}'.format(data['time'][i]))
                    print('Index: {}'.format(data.index[i]))
                    print("Gains: {}% \nBalance: ${}\n".format(pg, round(bal, 2)))
                else:
                    self.buy_price.append(np.nan)
                    self.sell_price.append(np.nan)
            # Save largest balance
            if bal > biggest_balance[0]:
                biggest_balance[0] = bal
                biggest_balance[1] = data.index[i]

            # format % calculations
            percentage_gain = "{}%".format(pg)

            # Set Dataframe
            data.at[i, 'in_position'] = position
            data.at[i, "%_balance"] = percentage_gain
            data.at[i, "balance"] = '${}'.format(round(bal, 2))

        # Adjust for fees
        data.at[i, "balance"] = bal 
        - (no_of_trades * fee)
        # Print dataframe
        print(data)
        print("Total trades:", no_of_trades)
        print("End balance: ${}".format(round(data['balance'][i], 2)))
        print("Largest balance in backtest: ${} found at index: {}".format(round(biggest_balance[0]), biggest_balance[1]))

    def plotData(self):
        '''Plots the data with the VWAP, entry and exit markers'''

        self.df['close'].plot(label='CLOSE PRICES',
                              color='pink',
                              linewidth=0.5,
                              alpha=0.3)
        self.df['upper_band'].plot\
            (label='UPPER BAND', linestyle='--', linewidth=1, color='red')
        self.df['vwap'].plot\
            (label='VWAP', linestyle='--', linewidth=1.2, color='grey')
        self.df['lower_band'].plot\
            (label='LOWER BAND', linestyle='--', linewidth=1, color='black')
        plt.scatter(self.df.index, self.buy_price, marker='^', color='green', label='BUY', s=200)
        plt.scatter(self.df.index, self.sell_price, marker='v', color='red', label='SELL', s=200)
        plt.legend(loc='upper left')
        plt.title('ETH 1H VWAP')
        plt.show()


def main():
    # Import price history
    backtest_data = pd.read_csv('./data/ETH_1h_(may_15_May_28_June).csv')
    backtest_data = backtest_data.drop(columns='Unnamed: 0')

    # Add balance & fees
    balance = 1000
    fee = 0.01
    # Set timeframe for vwap
    candles = 24
    # Set window for std deviation
    window = 20
    # Set standard deviation
    sd = 2.5

    #  Initiate model! 
    model = Vwap_Strat(backtest_data, balance, fee, candles, window, sd)
    # Add sma and standard deviation to model
    model.vwap()
    model.std_dev_bands()
    # Update the dataframe to fit specifications
    model.updateData()

    # Back test model
    model.backtest()

    # Visualise model
    model.plotData()


if __name__ == '__main__':
    main()