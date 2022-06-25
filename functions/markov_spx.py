# -*- coding: utf-8 -*-

import yfinance as yf


# SPY = yf.Ticker("SPY", start="2010-01-01").history(period="max")
SPY = yf.download("SPY", start="2010-01-01", end="2018-12-31")

data = SPY[['Open', 'High', 'Low', 'Close', 'Adj Close']].copy()

# Add daily return
data['pct_ret'] = data['Adj Close'].pct_change()

# Compute the states
data['state'] = data['pct_ret'].apply(lambda x: 'Up' if (x > 0.001)
                                      else ('Down' if (x < -0.001)
                                            else 'Flat'))

# Add the previous days state (up/down)
data['prior_state'] = data['state'].shift(1)

# frequency distributions
states = data[['prior_state', 'state']].dropna()
states_mat = states.groupby(['prior_state', 'state']).size().unstack()


# Initial transition matrix
transition_matrix = states_mat.apply(lambda x: x / float(x.sum()), axis=1)

# This would be our transition matrix in t0, we can build the Markov Chain by
# multiplying this transition matrix by itself to obtain the probability matrix
# in t1 which would allow us to make one-day forecasts.
t0 = transition_matrix.copy()

# Find the converged matrix
i = 1
a = t0.copy()
b = t0.dot(t0)

while(not(a.equals(b))):
    print("Iteration number:", str(i))
    i += 1
    a = b.copy()
    b = b.dot(t0)

print(b)

# Giving us the results:

# After 11 iterations

# state            Down      Flat        Up
# prior_state
# Down         0.377546  0.152936  0.469518
# Flat         0.377546  0.152936  0.469518
# Up           0.377546  0.152936  0.469518

# Or:

# state            Down      Flat        Up
# prior_state
# Down          37.75%      15.29%    46.95%
# Flat          37.75%      15.29%    46.95%
# Up            37.75%      15.29%    46.95%