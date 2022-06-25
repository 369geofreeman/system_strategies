# Clusters (top platform)
# ---

import pandas as pd
import numpy as np


class Volume_Profile:
    def __init__(self, backtest_data,
                 platform_block,
                 return_raw):
        """
        Params
        ---
        :backtest_data: Dataframe (150 cxandles)
        :profile_block: int - Bars in each platform
        :return_raw:    Bool- Return raw data or plotted chart
        """

        self.df = backtest_data
        self.platform_block = platform_block
        self.return_raw = return_raw

    def updateData(self):
        """
        Updates dataframe with trading columns
        ---
        :time: Sets time in readable format
        """
        self.df['time'] = pd.to_datetime(self.df['time'], unit='ms')

    def max_platforms(self):
        """
        Seperates the candles into blocks and
        finds the peak of each block.
        
        Returns: Sorted array.
        """
        
        data = self.df
        closes = np.array(data['close'])
        closes = np.split(closes, self.platform_block)
        closes = np.sort(list(map(max, closes)))
        
        
        return print(closes)
       


def main():
    # Import price history and add to dataframe
    backtest_data = pd.read_csv('./data/ETH_15min_(may_15_2020_28_June_2021).csv')[-150:]
    backtest_data = backtest_data.drop(columns='Unnamed: 0')

    # Set profile variables
    platform_block = 15
    return_raw = False

    # Initiate model!
    model = Volume_Profile(backtest_data,
                           platform_block,
                           return_raw)

    # Update the dataframe to fit specifications
    model.updateData()

    # Backtest model ğŸš€
    model.max_platforms()


if __name__ == '__main__':
    main()
