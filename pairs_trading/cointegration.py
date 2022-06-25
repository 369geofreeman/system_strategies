'''
Testing for Cointegration
---
The formal definition of cointegration is as follows.
For some set of time series (X₁, X₂, ... X𝒏,), if all series are I(1) and
some linera combination of them are I(0), we say the set of time series
is cointegrated
Example
---
X₁, X₂ and X₃ are all I(1), and 2X₁ + X₂ + 0X₃ = 2X₁ + X₂ is I(0)
in this case the time series are cointegrated
The intuition here is that for some linear combination of the series, the result
lacks much auto-covariance and is mostly noise. This is useful for cases such as
pairs trading, in which we find two assets whose prices are cointegrated. Since
the linear combination of their prices b₁A₁ + b₂A₂ is noise, we can bet on the
relationship b₁A₁ + b₂A₂ mean reverting and place trades accordingly
'''

# Simulated Data Example

''' Let's make some data to demonstrate this. '''
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller
import matplotlib.pyplot as plt


''' Helper function '''
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


# Length of series
N = 100

# Generate a stationary random X1
X1 = np.random.normal(0, 1, N)
# Integrate it to make it I(1)
X1 = np.cumsum(X1)
X1 = pd.Series(X1)
X1.name = 'X1'

# Make an X2 that is X1 plus some noise
X2 = X1 + np.random.normal(0, 1, N)
X2.name = 'X2'

plt.plot(X1)
plt.plot(X2)
plt.xlabel('Time')
plt.ylabel('Series Value')
plt.legend([X1.name, X2.name])
plt.show()

'''
Because X₂ is just an I(1) series plus some stationary noise, it should still be I(1).
Let's check this.
'''
Z = X2.diff()[1:]
Z.name = 'Z'

check_for_stationarity(Z)
# >>> p-value = 3.06566830522e-19 The series Z is likely stationary.
'''
Looks good. Now to show cointegration we'll need to find some linear combination
of X₁ and X₂ that is stationary. We can take X₂-X₁. All that's left over should be
stationary noise by design. Let's check this.
'''
Z = X2 - X1
Z.name = 'Z'

plt.plot(Z)
plt.xlabel('Time')
plt.ylabel('Series Value')
plt.legend(['Z']);

check_for_stationarity(Z)

# >>> p-value = 1.03822288113e-18 The series Z is likely stationary.


''' There are also pre-built tests for cointegration '''

from statsmodels.tsa.stattools import coint

print('Results from coint => ', coint(X1, X2))
score, pvalue, _ = coint(X1,X2)
print('coint score =>', score)
print('coint Pvalue =>', pvalue)
'''
The docs can be found here -> https://www.statsmodels.org/devel/_modules/statsmodels/tsa/stattools.html
This was based on the work by Delaney Granizo-Mackenzie and Maxwell Margenot
https://github.com/quantopian/research_public/blob/master/notebooks/lectures/Integration_Cointegration_and_Stationarity/notebook.ipyn
b'''