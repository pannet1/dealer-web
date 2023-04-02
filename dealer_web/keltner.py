import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from termcolor import colored as cl
from math import floor

plt.rcParams['figure.figsize'] = (20, 10)
plt.style.use('fivethirtyeight')


def get_kc(h, l, c, kc_lookback, multiplier, atr_lookback):
    tr1 = pd.DataFrame(h - l)
    tr2 = pd.DataFrame(abs(h - c.shift()))
    tr3 = pd.DataFrame(abs(l - c.shift()))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.ewm(alpha=1/atr_lookback).mean()

    kc_middle = c.ewm(kc_lookback).mean()
    kc_upper = c.ewm(kc_lookback).mean() + multiplier * atr
    kc_lower = c.ewm(kc_lookback).mean() - multiplier * atr

    return kc_middle, kc_upper, kc_lower
