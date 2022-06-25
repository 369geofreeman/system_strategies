'''
Integration
---
If we find that a series is stationary, then it must also be I(0).
Let's take our original stationary series A (from stationarity.py).
Because A is stationary, we know it's also I(0).
'''

import numpy as np
import pandas as pd

import statsmodels
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint, adfuller

import matplotlib.pyplot as plt


''' ------ .: Helper funtions:. ------- '''

# use this is show all charts
plot_charts = True


def generate_datapoint(params):
    mu = params[0]
    sigma = params[1]
    return np.random.normal(mu, sigma)


# Set the parameters and the number of datapoints
params = (0, 1)
T = 100


def check_for_stationarity(X, cutoff=0.01):
    # H_0 in adfuller is unit root exists (non-stationary)
    # We must observe significant p-value to convince ourselves that the series is stationary
    pvalue = adfuller(X)[1]
    if pvalue < cutoff:
        print('p-value = ' + str(pvalue) + ' The series ' + X.name + ' is likely stationary.')
        return True
    else:
        print('p-value = ' + str(pvalue) + ' The series ' + X.name + ' is likely non-stationary.')
        return False


''' --------------- END ---------------- '''

A = pd.Series(index=range(T), dtype='int64')
A.name = 'A'

for t in range(T):
    A[t] = generate_datapoint(params)


# Set the number of datapoints
T = 100

B = pd.Series(index=range(T), dtype='int64')
B.name = 'B'

for t in range(T):
    # Now the parameters are dependent on time
    # Specifically, the mean of the series changes over time
    params = (t * 0.1, 1)
    B[t] = generate_datapoint(params)


if plot_charts:
    plt.plot(A)
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend(['Series A'])
    plt.show()

'''
Inductively Building Up Orders of Integration
---
If one takes an I(0) series and cumulatively sums it (discrete integration),
the new series will be I(1). Notice how this is related to the calculus concept
of integration. The same relation applies in general, to get I(n) take an I(0)
series and iteratively take the cumulative sum n times.
Now let's make an I(1) series by taking the cumulative sum of A.
'''

A1 = np.cumsum(A)

if plot_charts:
    plt.plot(A1)
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend(['Series A1'])
    plt.show()

''' Now let's make one  by taking the cumlulative sum again. '''

A2 = np.cumsum(A1)

if plot_charts:
    plt.plot(A2)
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend(['Series A2'])
    plt.show()


''' Testing on real data '''

symbol_list = ['MSFT']
# We don't have this function but it returns a 1 year timeseries of prices
prices = get_pricing(symbol_list, fields=['price']
                               , start_date='2014-01-01', end_date='2015-01-01')['price']
prices.columns = map(lambda x: x.symbol, prices.columns)
X = prices['MSFT']

check_for_stationarity(X)

# >>> p-value = 0.666326790934 The series MSFT is likely non-stationary.


# Now let's take the delta of the series, giving us the additive returns.
# We'll check if this is stationary.

X1 = X.diff()[1:]
X1.name = X.name + ' Additive Returns'
check_for_stationarity(X1)

# >>> p-value = 1.48184901469e-28 The series MSFT Additive Returns is likely stationary.

# Seems like the additive returns are stationary over 2014. That means we will
# probably be able to model the returns much better than the price.
# It also means that the price was I(1).

# Let's also check the multiplicative returns.

X1 = X.pct_change()[1:]
X1.name = X.name + ' Multiplicative Returns'
check_for_stationarity(X1)

# >>> p-value = 8.05657888734e-29 The series MSFT Multiplicative Returns is likely stationary.

'''
Seems like the multiplicative returns are also stationary. Both the multiplicative
and additive deltas on a series get at similar pieces of information, so it's not
surprising both are stationary.
'''