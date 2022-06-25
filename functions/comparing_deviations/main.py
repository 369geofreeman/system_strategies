import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import sklearn
from sklearn.metrics import mean_squared_error
from line_best_fit import line_of_best_fit
pio.renderers.default = "browser"


class deviations:
    def __init__(self, data, window, z_score=1, return_raw=True):
        self.df = data
        self.window = window
        self.z_score = z_score
        self.return_raw = return_raw

    def updateData(self):
        """
        Updates dataframe with trading columns
        ---
        time: Sets time in readable format
        """
        self.df['time'] = pd.to_datetime(self.df['time'], unit='ms')

    def remove_outliers(self, data):
        '''
        Find the values insidethe Interquartile range of the selected data.
        This is to remove any outliers in the set.
        '''
        x = np.array([7, 11, 3, 2, 96, 14, 8])
        np.sort(x)

        q25, q75 = np.percentile(x, [25, 75])
        x = [i for i in x if i > q25 and i < q75]
        x = np.insert(x, 0, q25)
        x = np.append(x, q75)
        return x

    def sma(self):
        '''
            Adds the sma to the dataframe
        '''
        self.df['sma_20'] = self.df['close'].rolling(window=self.window).mean()

    def std_dev(self):
        ''' Adds the standard deviation to the dataframe
            Estimated variance is used: n-1
        '''
        self.df['std_dev'] = self.df['sma_20'] + self.df['close'].\
            rolling(window=self.window).std() * self.z_score

    def mean_dev(self):
        """ Adds the mean deviation
            to the dataframe
        """
        mad = lambda x: np.fabs(x - x.mean()).mean()
        self.df['mean_dev'] = self.df['sma_20'] + self.df['close'].\
             rolling(window=self.window).apply(mad, raw=True) * self.z_score

    def mad(self):
        """ Adds the median absolute deviation
            to the dataframe
        """
        mad = lambda x: np.median(np.absolute(x - np.median(x)))
        self.df['mad_dev'] = self.df['sma_20'] + self.df['close'].\
            rolling(window=self.window).apply(mad, raw=True) * self.z_score

    def rmsd(self):
        """ Calculates the standard deviation of residuals
            or root-mean square error
        """
        self.df['rmsd'] = ['n/a']*len(self.df['close'])
        window = self.window

        for i in range(window, len(self.df.index)):
            actual = np.array(self.df['close'][i-window:i].values).reshape(-1, 1)
            predicted = line_of_best_fit(self.df[i-window:i])
            mse = sklearn.metrics.mean_squared_error(actual, predicted)
            self.df['rmsd'][i] = (mse * self.z_score) + self.df['close'][i]

    def plot(self):
        df = self.df
        self.remove_outliers(['Data goes here'])
        self.sma()
        self.std_dev()
        self.mean_dev()
        self.mad()
        self.rmsd()
        df = df[30:]

        if self.return_raw:
            return

        fig1 = go.Candlestick(
            x=df['time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            visible=True,
            showlegend=False
        )

        fig2 = go.Scatter(
            x=df['time'],
            y=df['std_dev'],
            visible=True,
            marker=dict(
                size=5,
                color='blue',
            ),
            name='Standard deviation',
            showlegend=True
        )

        fig3 = go.Scatter(
            x=df['time'],
            y=df['mean_dev'],
            visible=True,
            marker=dict(
                size=5,
                color='orange',
            ),
            name='Mean deviation',
            showlegend=True
        )

        fig4 = go.Scatter(
            x=df['time'],
            y=df['mad_dev'],
            visible=True,
            marker=dict(
                size=5,
                color='purple',
            ),
            name='Median absolute deviation',
            showlegend=True
        )

        fig5 = go.Scatter(
            x=df['time'],
            y=df['rmsd'],
            visible=True,
            marker=dict(
                size=5,
                color='black',
            ),
            name='RMSD',
            showlegend=True
        )

        layout = go.Layout(
            title=go.layout.Title(text="Deviation Tests"),
            xaxis=go.layout.XAxis(
                side="bottom",
                title="Date",
                rangeslider=go.layout.xaxis.Rangeslider(visible=False)
            ),
            yaxis=go.layout.YAxis(
                side="right",
                title='Price',
            ),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        fig = go.Figure(data=[fig1, fig2, fig3, fig4, fig5], layout=layout)

        fig.show()


def main():
    # Import price history and add to dataframe
    backtest_data = pd.read_csv('./data/ETH_15min_(may_15_2020_28_June_2021).csv')[:200]
    backtest_data = backtest_data.drop(columns='Unnamed: 0')

    # Set to true to get back raw data
    return_raw = False

    # Set the window for calculations
    window = 20

    # Set the z-score (amount we want each calculation to be multiplied from the buy in price)
    z_score = 2  # Need implimenting

    # 🚀🚀🚀 Initiate model! 🚀🚀🚀
    model = deviations(backtest_data, window, z_score, return_raw)

    # Update the dataframe to fit specifications
    model.updateData()

    # Backtest model 🚀
    model.plot()


if __name__ == '__main__':
    main()
