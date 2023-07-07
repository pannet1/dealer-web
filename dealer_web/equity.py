import pandas as pd
import pendulum
from breakout import TRADE_DAY_TMINUS, dpath, futil
from breakout import Backtest, Live
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import threading


class WebsocketClient(threading.Thread):
    def __init__(self, kwargs, lst_tkn):
        self.ticks = {}
        self.token_list = lst_tkn
        self.auth_token = kwargs['auth_token'],
        self.api_key = kwargs['api_key'],
        self.client_code = kwargs['client_code'],
        self.feed_token = kwargs['feed_token']
        self.sws = SmartWebSocketV2(**kwargs)
        threading.Thread.__init__(self)

    def on_data(self, wsapp, msg):
        self.ticks[int(msg.get('token'))] = msg.get(
            'last_traded_price') / 100

    def on_open(self, wsapp):
        print("on open")
        self.subscribe("subs1", 1, self.token_list)

    def on_error(self, wsapp, error):
        print(error)

    def on_close(self, wsapp):
        print("Close")

    def close_connection(self):
        self.sws.close_connection()

    def run(self):
        # Assign the callbacks.
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close
        self.sws.connect()

    def subscribe(self, correlation_id, mode, lst_token):
        print("subscribe")
        self.sws.subscribe(correlation_id, mode, lst_token)

    def unsubscribe(self, correlation_id, mode, lst_token):
        # self.sws.unsubscribe(correlation_id, mode, self.token_list)
        pass


if __name__ == "__main__":
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
        eqty.df['ltp'] = None
        while (
            pendulum.now() < pendulum.now().replace(
                hour=23, minute=59, second=0, microsecond=0)
        ):
            # eqty.df['open'] = eqty.df.apply(eqty.get_preopen, axis=1)
            if any(t1.ticks):
                eqty.df['open'] = eqty.df['symboltoken'].map(t1.ticks)
                print(eqty.df[['symbol', 'open']])
            else:
                print("tick is empty ?")
        print(eqty.df)

        eqty.df = eqty.trim_df(eqty.df)
        while True:
            # eqty.df['last_traded_price'] = eqty.df.apply(eqty.get_preopen, axis=1)
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
