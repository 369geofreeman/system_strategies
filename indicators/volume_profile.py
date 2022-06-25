#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.io as pio
from scipy.signal import find_peaks
pio.renderers.default = "browser"


def volume_profile(df, price_pace=0.25, return_raw=False):
    """
    create volume profile
    :param df: time-indexed HOLCV bar or time-indexed P-V tick
    :param price_pace: price bucket, default 5 cents
    :param return_raw: return raw data or figure
    :return: raw data or figure obj
    """

    cmin = min(df['close'])
    cmax = max(df['close'])
    cmin_int = int(cmin / price_pace) * price_pace  # int(0.9) = 0
    cmax_int = int(cmax / price_pace) * price_pace
    if cmax_int < cmax:
        cmax_int += price_pace
    cmax_int += price_pace  # right bracket is not included in arrange

    price_buckets = np.arange(cmin_int, cmax_int, price_pace)
    price_coors = pd.Series(price_buckets).rolling(2).mean().dropna()
    vol_bars = np.histogram(df['close'], bins=price_buckets, weights=df['volume'])[0]

    # Find peaks
    indices = find_peaks(vol_bars, prominence=1, distance=8)[0]

    if return_raw:
        return (price_coors.values, vol_bars, indices)

    fig1 = go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        xaxis='x',
        yaxis='y2',
        visible=True,
        showlegend=False
    )

    fig2 = go.Bar(
        x=df.index,
        y=df['volume'],
        yaxis='y',
        name='Volume',
        showlegend=False
    )

    fig3 = go.Bar(
        x=vol_bars,
        y=price_coors.values,
        orientation='h',
        xaxis='x2',
        yaxis='y3',
        visible=True,
        showlegend=False,
        marker_color='dimgrey',
        width=4,
        opacity=0.6
    )
    # Add peaks to chart
    fig4 = go.Scatter(
        x=indices,
        y=[price_coors.values[j] for j in indices],
        orientation='h',
        xaxis='x2',
        yaxis='y3',
        visible=True,
        mode='markers',
        marker=dict(
            size=15,
            color='yellow',
            symbol='arrow-left'
        ),
        fill='tonexty',
        fillcolor="yellow",
        name='Detected POC'
    )

    low = cmin_int
    high = cmax_int
    layout = go.Layout(
        title=go.layout.Title(text="Volume Profile"),
        xaxis=go.layout.XAxis(
            side="bottom",
            title="Date",
            rangeslider=go.layout.xaxis.Rangeslider(visible=False)
        ),
        yaxis=go.layout.YAxis(
            side="right",
            title='Volume',
            showticklabels=False,
            domain=[0, 0.2]
        ),
        yaxis2=go.layout.YAxis(
            side="right",
            title='Price',
            range=[low, high],
            domain=[0.2, 1.0]
        ),
        xaxis2=go.layout.XAxis(
            side="top",
            showgrid=False,
            # volume bar on the right
            # unfortunately reversed is an auto-range
            # one solution is to add an invisible bar.
            # https://community.plotly.com/t/reversed-axis-with-range-specified/3806
            # autorange='reversed',
            ticks='',
            showticklabels=False,
            range=[0, int(vol_bars.max() * 5)],
            overlaying="x"
        ),
        yaxis3=go.layout.YAxis(
            side="left",
            range=[low, high],
            showticklabels=False,
            overlaying="y2",
            linecolor='firebrick',
        ),
    )

    fig = go.Figure(data=[fig1, fig2, fig3, fig4], layout=layout)

    return fig