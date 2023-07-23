import pandas as pd
import pendulum
from breakout import TRADE_DAY_TMINUS, dpath, futil, tutil
from breakout import Backtest, Live
from websocket_client import WebsocketClient

if TRADE_DAY_TMINUS == 0:
    eqty = Live()
    eqty.df = eqty.set_symbols()

    csvfile = dpath + "2_eod_data.csv"
    eqty.df = eqty.get_eod_data(eqty.df)
    eqty.df.to_csv(csvfile, index=False)
    eqty.df = pd.read_csv(csvfile, header=0)

    eqty.df = eqty.apply_conditions(eqty.df)
    csvfile = dpath + "3_conditions.csv"
    eqty.df.to_csv(csvfile, index=False)
    eqty.df = pd.read_csv(csvfile, header=0)

    lst_tokens = eqty.df['symboltoken'].tolist()
    token_list = [
        {
            "exchangeType": 1,
            "tokens": lst_tokens
        }
    ]
    t1 = WebsocketClient(eqty.dct_ws_cred, token_list)
    t1.start()
    while (
            not any(t1.ticks)
    ):
        print(f"{t1.ticks} is empty ?")
        tutil.slp_til_nxt_sec
    eqty.df['ltp'] = None
    while (
        pendulum.now() < pendulum.now().replace(
            hour=9, minute=15, second=0, microsecond=0)
    ):
        eqty.df['open'] = eqty.df['symboltoken'].map(t1.ticks)
        print(eqty.df[['symbol', 'open']])
    print(eqty.df)

    eqty.df = eqty.trim_df(eqty.df)
    while True:
        eqty.df['ltp'] = eqty.df['symboltoken'].map(t1.ticks)
        # print(eqty.df[['symbol', 'ltp']])
        eqty.entries(eqty.df)
        eqty.stops(eqty.df)
else:
    eqty = Backtest()
    eqty.df = eqty.set_symbols()

    csvfile = dpath + "2_eod_data.csv"
    if futil.is_file_not_2day(csvfile):
        eqty.df = eqty.get_eod_data(eqty.df)
        eqty.df.to_csv(csvfile, index=False)
    else:
        eqty.df = pd.read_csv(csvfile, header=0)
    print("2_eod \n", eqty.df.tail())

    csvfile = dpath + "3_conditions.csv"
    if futil.is_file_not_2day(csvfile):
        eqty.df = eqty.apply_conditions(eqty.df)
        eqty.df.to_csv(csvfile, index=False)
    else:
        eqty.df = pd.read_csv(csvfile, header=0)
    print("3_conditions \n", eqty.df.tail())

    csvfile = dpath + "4_today_open.csv"
    if futil.is_file_not_2day(csvfile):
        eqty.df = eqty.get_one_fm_ohlc(eqty.df)
        eqty.df.to_csv(csvfile, index=False)
    else:
        eqty.df = pd.read_csv(csvfile, header=0)
    print("4_today_open \n", eqty.df.tail())

    csvfile = dpath + "5_trim.csv"
    if futil.is_file_not_2day(csvfile):
        eqty.df = eqty.trim_df(eqty.df)
        eqty.df = eqty.get_one_fm_ohlc(eqty.df, 'ltp', 4)
        eqty.df.to_csv(csvfile, index=False)
    else:
        eqty.df = pd.read_csv(csvfile, header=0)
    print("5_trim \n", eqty.df.tail())
    # get a subset of dataframe with entry conditons
    #
    eqty.entries(eqty.df)
    eqty.stops(eqty.df)
    eqty.stops(eqty.df)
