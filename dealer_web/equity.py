import pandas as pd
import pendulum
from breakout import TRADE_DAY_TMINUS, dpath, futil
from breakout import Backtest, Live
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import threading
from time import sleep


class WebsocketClient(threading.Thread):
    def __init__(self, kwargs, lst_tkn):
        self.ticks = {}
        self.token_list = lst_tkn
        self.correlation_id = "abc123"
        self.action = 1
        self.mode = 1
        self.auth_token = kwargs['auth_token'],
        self.api_key = kwargs['api_key'],
        self.client_code = kwargs['client_code'],
        self.feed_token = kwargs['feed_token']
        self.sws = SmartWebSocketV2(**kwargs)
        threading.Thread.__init__(self)

    def on_data(self, wsapp, msg):
        self.ticks[int(msg.get('token'))] = msg.get('last_traded_price')

    def on_open(self, wsapp):
        print("on open")
        self.sws.subscribe(self.correlation_id, self.mode, self.token_list)
        # self.sws.unsubscribe(self.correlation_id, self.mode, self.token_list1)

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


if __name__ == "__main__":
    if TRADE_DAY_TMINUS == 0:
        eqty = Live()
        """
        eqty.df = eqty.set_symbols()

        eqty.df = eqty.get_eod_data(eqty.df)
        csvfile = dpath + "2_eod_data.csv"
        eqty.df.to_csv(csvfile, index=False)

        eqty.df = eqty.apply_conditions(eqty.df)
        csvfile = dpath + "3_conditions.csv"
        eqty.df.to_csv(csvfile, index=False)
        """
        csvfile = dpath + "3_conditions.csv"
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
            pendulum.now() < pendulum.now().replace(
                hour=12, minute=50, second=0, microsecond=0)
        ):
            # eqty.df['open'] = eqty.df.apply(eqty.get_preopen, axis=1)
            if any(t1.ticks):
                eqty.df['ltp'] = eqty.df['symboltoken'].replace(t1.ticks)
                eqty.df.tail()
            else:
                print("tick is empty ?")
            sleep(1)
        eqty.df.rename(columns={'ltp': 'open'})

        eqty.df = eqty.trim_df(eqty.df)
        while True:
            # eqty.df['last_traded_price'] = eqty.df.apply(eqty.get_preopen, axis=1)
            eqty.df['ltp'] = eqty.df['symboltoken'].replace(t1.ticks)
            df = eqty.get_entry_cond(eqty.df)
            eqty.entries(df)
            eqty.stops()
    else:
        eqty = Backtest()
        eqty.df = eqty.set_symbols()

        csvfile = dpath + "2_eod_data.csv"
        if futil.is_file_not_2day(csvfile):
            eqty.df = eqty.get_eod_data(eqty.df)
            eqty.df.to_csv(csvfile, index=False)
        else:
            eqty.df = pd.read_csv(csvfile, header=0)

        csvfile = dpath + "3_conditions.csv"
        if futil.is_file_not_2day(csvfile):
            eqty.df = eqty.apply_conditions(eqty.df)
            eqty.df.to_csv(csvfile, index=False)
        else:
            eqty.df = pd.read_csv(csvfile, header=0)

        csvfile = dpath + "4_today_open.csv"
        if futil.is_file_not_2day(csvfile):
            eqty.df = eqty.get_one_fm_ohlc(eqty.df)
            eqty.df.to_csv(csvfile, index=False)
        else:
            eqty.df = pd.read_csv(csvfile, header=0)

        csvfile = dpath + "5_trim.csv"
        if futil.is_file_not_2day(csvfile):
            eqty.df = eqty.trim_df(eqty.df)
            eqty.df = eqty.get_one_fm_ohlc(eqty.df, 'ltp', 4)
            eqty.df.to_csv(csvfile, index=False)
        else:
            eqty.df = pd.read_csv(csvfile, header=0)

        # get a subset of dataframe with entry conditons
        df = eqty.get_entry_cond(eqty.df)
        entries = eqty.entries(df)
        entries.to_csv(dpath + "6_entry.csv", index=False)
        stops = eqty.stops()
        stops.to_csv(dpath + "7_stop.csv", index=False)
