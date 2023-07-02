
import orjson
import pendulum
import pandas as pd
import numpy as np
import concurrent.futures as cf
from toolkit.fileutils import Fileutils
from toolkit.utilities import Utilities
import user
from websocket_client import WebsocketClient

# user preferences
Y_PERC = 0.03
T_PERC = 0.01
MIN_PRC = 100
MAX_PRC = 10000
GAPITAL = 100000
TRADE_DAY_TMINUS = 2
ACCOUNT = "HARSHITBONI"
BUFFER = 0.01

futil = Fileutils()
lst_dohlcv = ["dtime", "o", "h", "l", "c", "v"]
fpath = "../../../"
dpath = fpath + "data/"
pd.options.mode.chained_assignment = None
tutils = Utilities()
executor = cf.ThreadPoolExecutor()


class Equity:

    def __init__(self):
        print(f"script started at {pendulum.now()}")
        user.contracts()
        YDAY_TMINUS = TRADE_DAY_TMINUS+1
        self.df = pd.DataFrame()
        self.max = pendulum.now().subtract(days=9)
        self.yday = pendulum.now().subtract(days=YDAY_TMINUS)
        self.now = pendulum.now().subtract(days=TRADE_DAY_TMINUS)
        self.count = 0
        h = user.get_broker_by_id(ACCOUNT)
        self.dct_ws_cred = dict(
            auth_token=h.sess['data']['jwtToken'].split(' ')[1],
            api_key=h._api_key,
            client_code=h._user_id,
            feed_token=h.obj.feed_token
        )

    def is_run(self, csv):
        """
        if BACKTESTING mode or file written only yesterday
        """
        if TRADE_DAY_TMINUS == 0:  # live trade
            return True
        elif futil.is_file_not_2day(csv):  # file modified
            return True
        print(f"reading {csv}")
        return False

    def set_symbols(self):
        try:
            csvfile = dpath + "1_symtok.csv"
            with open(fpath + "symbols.json", "rb") as ojsn:
                data = orjson.loads(ojsn.read())
            df_tok = pd.DataFrame.from_dict(
                data)
            columns = ["token", "symbol"]
            df_tok = df_tok.query("exch_seg=='NSE'")[columns].rename(
                columns={"token": "symboltoken"})
            df_sym = futil.get_df_fm_csv(
                dpath, "nifty_500", ["symbol", "enabled"])
            df_sym.dropna(inplace=True)
            df_sym.drop('enabled', inplace=True, axis=1)
            df = df_sym.merge(df_tok, how="left", on="symbol")
            df['pdh'] = 0
            df.to_csv(csvfile, index=False)
        except Exception as e:
            print(f"{e} while set_symbols \n")
            SystemExit()
        else:
            print("symbols \n", df.tail())
            return df

    def _get_ohlc(self, **kwargs):
        try:
            tutils.slp_til_nxt_sec()
            ao = user.random_broker()
            param = {
                "exchange": "NSE",
            }
            t = kwargs.pop('tminus', 0)
            param.update(kwargs)
            print(param)
            resp = ao.obj.getCandleData(param)
            if (
                resp is not None
                and isinstance(resp, dict)
                and isinstance(resp['data'], list)
                and isinstance(resp['data'][t:], list)
                and isinstance(resp['data'][t:][0], list)
            ):
                return resp['data'][t:][0]
            print(resp)
            return 0
        except Exception as e:
            print(
                f"{str(e)} while calling sub routine _get_ohlc \n")
            tutils.slp_for(3)
            return 0

    def get_eod_data(self, df):
        fro = self.max.set(hour=9, minute=14).to_datetime_string()[:-3]
        nto = self.yday.set(hour=15, minute=30).to_datetime_string()[:-3]
        print(f"getting PDH for {nto}")
        csvfile = dpath + "2_eod_data.csv"
        retry = 1
        if self.is_run(csvfile):
            while (not df.query("pdh==0").empty) and retry <= 5:
                df_cp = df.query("pdh==0").copy()
                for i, row in df_cp.iterrows():
                    kwargs = {
                        'symboltoken': row.symboltoken,
                        'fromdate': fro,
                        'todate': nto,
                        'interval': 'ONE_DAY',
                        'tminus': -1
                    }
                    lst = self._get_ohlc(**kwargs)
                    if isinstance(lst, list):
                        df.at[i, 'pdo'] = lst[1]
                        df.at[i, 'pdh'] = lst[2]
                        df.at[i, 'pdl'] = lst[3]
                        df.at[i, 'pdc'] = lst[4]
                        print(row.symbol, str(lst))
                    else:
                        df.at[i, 'pdh'] = 0
                        retry += 1
                        print(f"retrying attempt: {retry}")
            # add a new columns
            self.df['eod'] = nto
            self.df.to_csv(csvfile, index=False)
        else:
            df = pd.read_csv(csvfile, header=0)
            print("found today fresh EOD")
        print("eod data \n", df.tail(5))
        return df

    def apply_conditions(self, df):
        csvfile = dpath + "3_conditions.csv"
        print("remove stocks for which we CANNOT get data")
        df = df.query("pdh>0")
        print(df.tail())

        print(f"remove stocks whose PDL < {MIN_PRC} and PDH > {MAX_PRC}")
        prc_fltr = (df['pdl'] < MIN_PRC) & (df['pdh'] > MAX_PRC)
        df = df[~prc_fltr]
        print(df.tail())

        print("find direction based on candle colour")
        df['dir'] = 0
        df.loc[df['pdc'] > df['pdo'], 'dir'] = -1
        df.loc[df['pdc'] < df['pdo'], 'dir'] = 1
        print(df.tail())

        print("distance between PDL and PDH")
        df["yday_perc"] = df.eval('(pdh-pdl)/pdl')
        rm_big_gaps = (df['yday_perc'] > Y_PERC) | (
            df['dir'] == 0)
        df = df[~rm_big_gaps]

        df.to_csv(csvfile, index=False)
        print(df.tail(5))
        return df

    def get_one_fm_ohlc(self, df, colname='open', i_at=1):
        fro = self.now.set(hour=9, minute=15).to_datetime_string()[:-3]
        nto = self.now.set(hour=15, minute=30).to_datetime_string()[:-3]
        print(f"{fro} to {nto}")
        param = {
            "exchange": "NSE",
            "interval": "ONE_MINUTE",
            "fromdate": fro,
            "todate": nto,
            "tminus": 0
        }
        for i, row in self.df.iterrows():
            param["symboltoken"] = int(row.symboltoken)
            lst = self._get_ohlc(**param)
            if isinstance(lst, list):
                df.at[i, colname] = lst[i_at]
                print(row.symbol, str(lst))
        print(df.tail())
        return df

    def get_preopen(self, row):
        ao = user.random_broker()
        resp = ao.obj.ltpData("NSE", row.symbol, row.symboltoken)
        if (
            resp is not None
            and isinstance(resp, dict)
            and isinstance(resp['data'], dict)
        ):
            print(row.symbol, resp['data']['ltp'])
            return resp['data']['ltp']
        return None

    def trim_df(self, df):
        csvfile = dpath + "5_trim.csv"
        if eqty.is_run(csvfile):
            print("finding GAP")
            df['perc'] = np.where(df['dir'] == 1, (df['open'] - df['pdh']) /
                                  df['pdh'], (df['pdl'] - df['open']) / df['open'])
            print(df.tail())

            print("removing excess GAPS")
            is_perc_grt = df['perc'] > T_PERC
            df = df[~is_perc_grt]
            print(df.tail())

            print("marking GAP trades for Truth")
            str_perc = f"perc>0&perc<={T_PERC}"
            df['is_gap'] = df.eval(str_perc)
            print(df.tail())

            print("sorting the perc for breakout trades")
            # df['perc'] = df['perc'].replace([np.inf, -np.inf], np.nan)
            df['perc'] = df['perc'].round(4)
            df.sort_values(by='perc', ascending=False, inplace=True)
            df = df.reset_index(drop=True)
            # df['perc'] = df['perc'].round(3).sort_values().reset_index(drop=True)

            print("finding max and min to create columns")
            df['min'] = df[['open', 'pdl']].min(axis=1)
            df['max'] = df[['open', 'pdh']].max(axis=1)
            # df['break'] = np.where(df['dir'] == 1, np.maximum(df['open'], df['pdh']), np.minimum(df['open'], df['pdl']))

            lst_cols_to_drop = ['eod', 'pdo', 'pdc', 'yday_perc']
            print(f"dropping unwanted columns {lst_cols_to_drop}")
            df.drop(columns=lst_cols_to_drop, inplace=True)
            print(df.tail())
            print(f"saving to {csvfile}")
            df.to_csv(csvfile, index=False)
        else:
            df = pd.read_csv(csvfile, header=0)
        return df

    def gaps_entry(self, row):
        entries = []
        results = []
        self.count += 1
        if self.count >= 9:
            tutils.slp_til_nxt_sec()
            self.count = 0
        side = "BUY" if row.dir == 1 else "SELL"
        args = dict(
            variety='NORMAL',
            tradingsymbol=row.symbol,
            symboltoken=row.symboltoken,
            transactiontype=side,
            exchange="NSE",
            ordertype="MARKET",
            producttype="INTRADAY",
            duration="DAY",
            price=0,
            triggerprice=0,
            quantity=row.o_qty
        )
        h = user.get_broker_by_id(ACCOUNT)
        # Submit the API call function to the executor
        entry = executor.submit(h.order_place, **args)
        entries.append(entry)
        for future in cf.as_completed(entries):
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                print(f" in cf entries {e}")
                results.append(None)

    def gaps_stop(self, row):
        entries = []
        results = []
        self.count += 1
        if self.count >= 9:
            tutils.slp_til_nxt_sec()
            self.count = 0
        if row.dir == 1:
            side = "SELL"
            o_price = row.pdh
        else:
            side = "BUY"
            o_price = row.pdl
        args = dict(
            variety='NORMAL',
            tradingsymbol=row.symbol,
            symboltoken=row.symboltoken,
            transactiontype=side,
            exchange="NSE",
            ordertype="SL-M",
            producttype="INTRADAY",
            duration="DAY",
            triggerprice=o_price,
            price=0,
            quantity=row.o_qty
        )
        h = user.get_broker_by_id(ACCOUNT)
        # Submit the API call function to the executor
        entry = executor.submit(h.order_place, **args)
        entries.append(entry)
        for future in cf.as_completed(entries):
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                print(f" in cf entries {e}")
                results.append(None)

    def do_orders(self, df):
        fltr_df = df[(df['ltp'] < df['min']) & (df['dir'] == -1)
                     | (df['ltp'] > df['max']) & (df['dir'] == 1)]
        if not fltr_df.empty:
            results = fltr_df.apply(self.gaps_entry, axis=1)
            for result in results:
                print(result)
            results = fltr_df.apply(self.gaps_stop, axis=1)
            for res in results:
                print(result)
            df.to_csv("trades.csv", index=False)


if __name__ == "__main__":
    eqty = Equity()
    eqty.df = eqty.set_symbols()
    eqty.df = eqty.get_eod_data(eqty.df)
    eqty.df = eqty.apply_conditions(eqty.df)

    lst_tokens = eqty.df['symboltoken'].tolist()
    t1 = WebsocketClient(eqty.dct_ws_cred, lst_tokens)
    t1.start()

    csvfile = dpath + "4_today_open.csv"
    COPY_JOB = False
    while (
            TRADE_DAY_TMINUS == 0
            and pendulum.now() < pendulum.now().replace(
                hour=9, minute=15, second=0, microsecond=0)
    ):
        print("LIVE MODE ON")
        # eqty.df['open'] = eqty.df.apply(eqty.get_preopen, axis=1)
        eqty.df['ltp'] = eqty.df['symboltoken'].map(t1.ticks)
        eqty.df.tail()
        COPY_JOB = True
    else:
        if COPY_JOB:
            eqty.df.rename(columns={'ltp': 'open'})
            eqty.df.to_csv(csvfile, index=False)

    if eqty.is_run(csvfile):
        print("BACKTESTING MODE ON ..", end="\n",)
        eqty.df = eqty.get_one_fm_ohlc(eqty.df)
        eqty.df.to_csv(csvfile, index=False)
    elif TRADE_DAY_TMINUS > 0:
        eqty.df = pd.read_csv(csvfile, header=0)

    eqty.df = eqty.trim_df(eqty.df)
    cnt_gap_trd = eqty.df['is_gap'].sum()
    print(f"no of gap trades: {cnt_gap_trd}")

    print("calculating order quantity")
    eqty.df['o_qty'] = (GAPITAL / eqty.df['open']).astype(int)
    eqty.df['o_qty'].fillna(0, inplace=True)
    print(eqty.df.tail())

    while TRADE_DAY_TMINUS == 0:
        eqty.df['ltp'] = eqty.df['symboltoken'].map(t1.ticks)
        # eqty.df['ltp'] = eqty.df.apply(eqty.get_preopen, axis=1)
        eqty.do_orders(eqty.df)
    else:
        eqty.df = eqty.get_one_fm_ohlc(eqty.df, 'ltp', 4)
        eqty.do_orders(eqty.df)

    """
    df_trades = df_trades.filter(items=['symbol', 'c'], axis=1)
    df_trades = df_trades.rename(columns={'c': 'close'})
    df_trades['dtime'] = "09:20:00"
    print(eqty.df)
    print("TRADES")
    print(df_trades)
    eqty.df.to_csv(csvfile, index=False)
    df_trades.to_csv(dpath + "6_trades.csv", index=False)

    eqty.df = pd.read_csv(csvfile, header=0)
    print("CALCULATE P&L")
    till = "10:00"
    df_ohlc = df_empty

    csvfile = dpath + "7_5min.csv"
    tick_df = pd.read_csv(csvfile, header=0)
    tick_df = tick_df.filter(['symbol', 'dtime', 'c'])
    tick_df = tick_df.rename(columns={'c': 'close'})

    merged = pd.merge(eqty.df, tick_df, on='symbol')
    filtered = merged[merged['close'] > merged['h']]
    filtered['dtime'] = pd.to_datetime(filtered['dtime'])
    start_time = pd.to_datetime('09:20').time()
    end_time = pd.to_datetime('10:00').time()
    filtered = filtered[(filtered['dtime'].dt.time >= start_time) & (
        filtered['dtime'].dt.time <= end_time)]
    result = filtered.groupby('symbol').agg({'dtime': 'min', 'close': 'first'})

    csvfile = dpath + "6_trades.csv"
    trades = pd.read_csv(csvfile, header=0)
    trades.set_index('symbol', inplace=True)
    new_trades = trades[~trades.index.isin(result.index)]
    merged_trades = pd.concat([result, new_trades], axis=0)
    print(merged_trades)
    """
