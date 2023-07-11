import traceback
import orjson
import pendulum
import pandas as pd
import numpy as np
import concurrent.futures as cf
from toolkit.fileutils import Fileutils
from toolkit.utilities import Utilities
import user

fpath = "../../../"
dpath = fpath + "data/"

tutil = Utilities()
futil = Fileutils()
executor = cf.ThreadPoolExecutor()
# Extract the values into variables
preferences = futil.get_lst_fm_yml(fpath + "harshit_breakout.yaml")
Y_PERC = preferences['Y_PERC']
T_PERC = preferences['T_PERC']
MIN_PRC = preferences['MIN_PRC']
MAX_PRC = preferences['MAX_PRC']
GAPITAL = preferences['GAPITAL']
TRADE_DAY_TMINUS = preferences['TRADE_DAY_TMINUS']
ACCOUNT = preferences['ACCOUNT']
BUFFER = preferences['BUFFER']
MAX_TRADES = preferences['MAX_TRADES']
pd.options.mode.chained_assignment = None


class Breakout:

    def __init__(self):
        print(f"script started at {pendulum.now()}")
        user.contracts()
        YDAY_TMINUS = TRADE_DAY_TMINUS+1
        self.df = pd.DataFrame()
        self.max = pendulum.now().subtract(days=9)
        self.yday = pendulum.now().subtract(days=YDAY_TMINUS)
        self.now = pendulum.now().subtract(days=TRADE_DAY_TMINUS)
        self.orders_per_sec = self.orders_count = 0
        h = user.get_broker_by_id(ACCOUNT)
        if (h is not None
                and h.sess is not None):
            self.dct_ws_cred = dict(
                auth_token=h.sess['data']['jwtToken'].split(' ')[1],
                api_key=h._api_key,
                client_code=h._user_id,
                feed_token=h.obj.feed_token
            )
        else:
            print(f"unable to get login session for {ACCOUNT}")
            SystemExit()

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
                dpath, "nifty_200", ["symbol", "enabled"])
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
            tutil.slp_til_nxt_sec()
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
            tutil.slp_for(3)
            return 0

    def get_eod_data(self, df):
        fro = self.max.set(hour=9, minute=14).to_datetime_string()[:-3]
        nto = self.yday.set(hour=15, minute=30).to_datetime_string()[:-3]
        retry = 1
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
        print("eod data \n", df.tail(5))
        return df

    def apply_conditions(self, df):
        print("remove stocks for which we CANNOT get data")
        df = df.query("pdh>0")
        print(df.tail())

        print(f"remove stocks whose PDL < {MIN_PRC} and PDH > {MAX_PRC}")
        prc_fltr = (df['pdl'] < MIN_PRC) | (df['pdh'] > MAX_PRC)
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

        print(df.tail(5))
        df['open'] = 0
        df['is_entry'] = df['is_stop'] = 0
        return df

    def get_one_fm_ohlc(self, df, colname='open', i_at=1):
        fro = self.now.set(hour=9, minute=15).to_datetime_string()[:-3]
        nto = self.now.set(hour=15, minute=30).to_datetime_string()[:-3]
        print(f"{fro} to {nto}")
        param = {
            "exchange": "NSE",
            "interval": "FIVE_MINUTE",
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
        print("finding GAP")
        df['perc'] = np.where(df['dir'] == 1, (df['open'] - df['pdh']) /
                              df['pdh'], (df['pdl'] - df['open']) / df['open'])
        print(df.tail())

        print("removing excess GAPS")
        is_perc_grt = df['perc'] > T_PERC
        df = df[~is_perc_grt]
        print(df.tail())

        """
        print("sorting the perc for breakout trades")
        # df['perc'] = df['perc'].replace([np.inf, -np.inf], np.nan)
        df.sort_values(by='perc', ascending=False, inplace=True)
        df = df.reset_index(drop=True)
        """

        print("finding max and min to create columns")
        df['min'] = df[['open', 'pdl']].min(axis=1)
        df['max'] = df[['open', 'pdh']].max(axis=1)
        # df['break'] = np.where(df['dir'] == 1, np.maximum(df['open'], df['pdh']), np.minimum(df['open'], df['pdl']))

        lst_cols_to_drop = ['eod', 'pdo', 'pdc', 'yday_perc']
        print(f"dropping unwanted columns {lst_cols_to_drop}")
        df.drop(columns=lst_cols_to_drop, inplace=True)
        print(df.tail())

        print("calculating order quantity")
        df.query("open > 0", inplace=True)
        df['o_qty'] = (GAPITAL / df['open']).astype(int)
        # df['o_qty'] = 1
        print(df.tail())
        return df

    def _order_entry(self, row):
        entries = []
        results = []
        if self.orders_count < MAX_TRADES:
            self.orders_count += 1
            self.orders_per_sec += 1
            if self.orders_per_sec >= 9:
                tutil.slp_til_nxt_sec()
                self.orders_per_sec = 0
            side = "BUY" if row.dir == 1 else "SELL"
            """
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
                    traceback.print_exc()
                    results.append(None)
            # Update self.df['is_stop'] where symboltoken matches
            """
            self.df.at[self.df['symboltoken'] ==
                       row['symboltoken'], 'is_entry'] = 1
            row['is_entry'] = 1
            csvfile = dpath + "6_entry.csv"
            df = pd.DataFrame(row).T
            print("df \n", df)
            df.to_csv(csvfile, mode='a', index=False, header=False)
        return results

    def _order_exit(self, row):
        entries = []
        results = []
        self.orders_per_sec += 1
        if self.orders_per_sec >= 9:
            tutil.slp_til_nxt_sec()
            self.orders_per_sec = 0
        if row['dir'] == 1:
            side = "SELL"
            o_price = row['pdh']
        else:
            side = "BUY"
            o_price = row['pdl']
        """
        args = dict(
            variety='NORMAL',
            tradingsymbol=row['symbol'],
            symboltoken=row['symboltoken'],
            transactiontype=side,
            exchange="NSE",
            ordertype="SL-M",
            producttype="INTRADAY",
            duration="DAY",
            triggerprice=o_price,
            price=0,
            quantity=row['o_qty']
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
                print(f" str{e} in exits")
                traceback.print_exc()
                results.append(None)
        # Update self.df['is_stop'] where symboltoken matches
        """
        self.df.loc[self.df['symboltoken'] ==
                    row['symboltoken'], 'is_stop'] = 1
        row['is_stop'] = 1
        csvfile = dpath + "7_stop.csv"
        df = pd.DataFrame(row).T
        print("stop \n", df)
        df.to_csv(csvfile, mode='a', index=False, header=False)

    def entries(self, df):
        try:
            condition = (
                ((df['ltp'] < df['min']) & (df['dir'] == -1)) |
                ((df['ltp'] > df['max']) & (df['dir'] == 1)) &
                (df['is_entry'] == 0) &
                (df['is_stop'] == 0)
            )
            df = df[condition]
            # filter old entries
            if not df.empty:
                results = df.apply(self._order_entry, axis=1)
                for result in results:
                    if result:
                        print(result)
        except Exception as e:
            print(f"entry {e}")
            traceback.print_exc()

    def stops(self, df):
        try:
            if not df.empty:
                df = df[(df['is_entry'] == 1) &
                        (df['is_stop'] == 0)]
                if not df.empty:
                    df.apply(self._order_exit, axis=1)
        except Exception as e:
            print(f"exit {e}")
            traceback.print_exc()


class Live(Breakout):

    def __init__(self):
        super().__init__()
        print("Live")


class Backtest(Breakout):

    def __init__(self):
        super().__init__()
        print("Backtest")
