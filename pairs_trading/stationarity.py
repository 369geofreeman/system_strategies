'''
Stationarity
---
Stationarity means that the statistical properties of a process generating
a time series do not change over time.
1) It should have a constant mean*
2) It should have a constant variance*
3) Auto covariance* does not depend on the time
It does not mean that that the series does not change over time, just the
way it changes does not itself change over time.
The algebratic equivalent would be a linear function; the valuse changes as x
grows, but the way it changes remains constant. A constant slope; one that
captures that rate of change
---
*Mean – it is the average value of all the data
*Variance – it is a difference of each point value from the mean
*Auto covariance –it is a relationship between any two values at a certain amount of time.
'''


import numpy as np
import pandas as pd

from statsmodels.tsa.stattools import coint, adfuller

import matplotlib.pyplot as plt


# use this is show all charts
plot_charts = False


def generate_datapoint(params):
    mu = params[0]
    sigma = params[1]
    return np.random.normal(mu, sigma)


# Set the parameters and the number of datapoints
params = (0, 1)
T = 100

A = pd.Series(index=range(T), dtype='int64')
A.name = 'A'

for t in range(T):
    A[t] = generate_datapoint(params)

if plot_charts:
    plt.plot(A)
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend(['Series A'])
    plt.show()


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
    plt.plot(B)
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend(['Series B'])
    plt.show()

'''
Why Non-Stationarity is Dangerous
Many statistical tests, deep down in the fine print of their assumptions, require that the data being tested are stationary. Also, if you naively use certain statistics on a non-stationary data set, you will get garbage results. As an example, let's take an average through our non-stationary .
'''

m = np.mean(B)

if plot_charts:
    plt.plot(B)
    plt.hlines(m, 0, len(B), linestyles='dashed', colors='r')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend(['Series B', 'Mean'])
    plt.show()


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


check_for_stationarity(A)
check_for_stationarity(B)


# Let's try an example that might be a little more subtle.

# Set the number of datapoints
T = 100

C = pd.Series(index=range(T), dtype='int64')
C.name = 'C'

for t in range(T):
    # Now the parameters are dependent on time
    # Specifically, the mean of the series changes over time
    params = (np.sin(t), 1)
    C[t] = generate_datapoint(params)

if plot_charts:
    plt.plot(C)
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend(['Series C'])
    plt.show()

check_for_stationarity(C)