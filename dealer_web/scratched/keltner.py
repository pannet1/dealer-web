# import numpy as np
# import matplotlib.pyplot as plt
import pandas as pd
# from termcolor import colored as cl
# from math import floor

"""
plt.rcParams['figure.figsize'] = (20, 10)
plt.style.use('fivethirtyeight')
"""


def get_kc(high, low, close, kc_lookback, multiplier, atr_lookback):
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift()))
    tr3 = pd.DataFrame(abs(low - close.shift()))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.ewm(alpha=1/atr_lookback).mean()

    # kc_middle = close.ewm(kc_lookback).mean()
    kc_upper = close.ewm(kc_lookback).mean() + multiplier * atr
    # kc_lower = close.ewm(kc_lookback).mean() - multiplier * atr

    return kc_upper


"""
unused
"""

   def is_low_broken(self, df):
        if df['Low'][0] < df['Low'].min():
            return True
        else:
            return False

    def fltr_upr_vltd(self, df):
        df = df.assign(upr_vltd=(df.c < df.upr) & (df.h > df.upr))
        return df

    def get_candles(self, param, tf):
        try:
            sleep(0.5)
            lst_col = ["o", "h", "l", "c"]
            empty_ohlc = pd.DataFrame(columns=lst_col, data=[[0, 0, 0, 0]])
            ao = user.random_broker()
            resp = ao.obj.getCandleData(param)
            data = resp.get('data')
            if data:
                df = pd.DataFrame(columns=lst_dohlcv, data=data)
                df.drop("v", inplace=True, axis=1)
                times = lst_dohlcv[0]
                df[times] = pd.to_datetime(df[times])
                df = df.set_index("dtime")
                dct = {
                    "o": "first",
                    "h": "max",
                    "l": "min",
                    "c": "last"
                }
                t = df.groupby(pd.Grouper(freq=tf)).agg(dct)
                t.columns = lst_col
                t = t.reset_index().rename(columns={'index': 'dtime'})
                print(t.tail())
                return t
            else:
                return empty_ohlc
        except Exception as e:
            print(f"{e} failed to get candles for {param['symboltoken']}")
        else:
            return df

    def get_ohlc(self, symboltoken, fro, nto, tf):
        try:
            lst_col = ["o", "h", "l", "c"]
            empty_ohlc = pd.DataFrame(columns=lst_col, data=[[0, 0, 0, 0]])
            ao = user.random_broker()
            param = {
                "exchange": "NSE",
                "symboltoken": symboltoken,
                "interval": "ONE_MINUTE",
                "fromdate": fro,
                "todate": nto,
            }
            resp = ao.obj.getCandleData(param)
            # print(f"response is {resp.get('data')} for param \n {param}")
            if resp.get('data'):
                data = resp.get('data')
                df = pd.DataFrame(columns=lst_dohlcv, data=data)
                times = lst_dohlcv[0]
                df[times] = pd.to_datetime(df[times])
                df = df.set_index("dtime")
                dct = {
                    "o": "first",
                    "h": "max",
                    "l": "min",
                    "c": "last"
                }
                t = df.groupby(pd.Grouper(freq=tf)).agg(dct)
                t.columns = lst_col
                t.reset_index(drop=True, inplace=True)
                t = t.loc[[0]]
                return t
            else:
                return empty_ohlc
        except Exception as e:
            print(f"{e} while getting ohlc")
            return empty_ohlc


    def place_order(symbol, ohlc):
        df = pd.DataFrame.from_dict(ohlc)
        df['Datetime'] = pd.to_datetime(df['Datetime'], unit='ms')
        df.set_index('Datetime', inplace=True)
        yesterday_high = df['High'][-1]
        if len(df) == 5 and is_low_broken(df) and is_closed_above_yesterday_high(df, yesterday_high) and \
                not is_any_candle_closed_above_1st_high(df) and is_range_within_1_percent(df):
            entry_price = df['Low'][0]
            stop_loss = df['High'][0]
            target_price = entry_price - (entry_price - stop_loss) * 2
            print(
                f"Short trade order placed for {symbol} at {entry_price} with stop loss at {stop_loss} and target price at {target_price}")

    def scan_stocks(stocks, ohlc_data):
        with cf.ThreadPoolExecutor() as executor:
            for symbol in stocks:
                ohlc = ohlc_data.get(symbol)
                # executor.submit(place_order, symbol, ohlc)



