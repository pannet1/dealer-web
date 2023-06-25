
import orjson
import pendulum
import pandas as pd
import numpy as np
import concurrent.futures as cf
from toolkit.fileutils import Fileutils
from toolkit.utilities import Utilities
import user


# user preferences
Y_PERC = 0.03
T_PERC = 0.01
MODE_TRADE = 0

YESTERDAY_TMINUS = 3
TRADE_DAY_TMINUS = 2

futil = Fileutils()
lst_dohlcv = ["dtime", "o", "h", "l", "c", "v"]
df_empty = pd.DataFrame()
fpath = "../../../"
dpath = fpath + "data/"
pd.options.mode.chained_assignment = None
tutils = Utilities()


class Equity:

    def __init__(self):
        user.contracts()
        self.df = pd.DataFrame()
        self.max = pendulum.now().subtract(days=9)
        self.yday = pendulum.now().subtract(days=YESTERDAY_TMINUS)
        self.now = pendulum.now().subtract(days=TRADE_DAY_TMINUS)

    def is_mode_trades(self, csv):
        # testing mode
        if MODE_TRADE == 0 and futil.is_file_not_2day(csv):
            return True
        return False

    def set_symbols(self):
        try:
            csvfile = dpath + "1_symtok.csv"
            if self.is_mode_trades(csvfile):
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
            else:
                df = pd.read_csv(csvfile, header=0)
        except Exception as e:
            print(f"{e} while set_symbols \n")
            SystemExit()
        else:
            print(df.tail())
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
            resp = ao.obj.getCandleData(param)
            if (
                resp is not None
                and isinstance(resp, dict)
                and isinstance(resp['data'], list)
                and isinstance(resp['data'][t:], list)
                and isinstance(resp['data'][t:][0], list)
            ):
                return resp['data'][t:][0]
            return 0
        except Exception as e:
            print(
                f"{str(e)} while get_ohlc \n sleeping for {tutils.sec} sec(s)")
            tutils.slp_for(tutils.sec)
            return 0

    def get_eod_data(self):
        try:
            fro = self.max.set(hour=9, minute=14).to_datetime_string()[:-3]
            nto = self.yday.set(hour=15, minute=30).to_datetime_string()[:-3]
            print(f"getting PDH for {nto}")
            csvfile = dpath + "2_eod_data.csv"
            if self.is_mode_trades(csvfile):
                while (not self.df.query("pdh==0").empty):
                    df_cp = self.df.query("pdh==0").copy()
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
                            self.df.at[i, 'pdo'] = lst[1]
                            self.df.at[i, 'pdh'] = lst[2]
                            self.df.at[i, 'pdl'] = lst[3]
                            self.df.at[i, 'pdc'] = lst[4]
                            print(row.symbol, str(lst))
                        else:
                            self.df.at[i, 'pdh'] = 0
                df = self.df.query("pdh>0")
                df.to_csv(csvfile, index=False)
            else:
                df = pd.read_csv(csvfile, header=0)
        except Exception as e:
            print(f"{e} while get_eod_data")
            SystemExit()
        else:
            print(df.tail(5))
            return df

    def eval_direction(self, df):
        print("EOD Data")
        csvfile = dpath + "3_direction.csv"
        # distance between low and pdh
        df["yday_perc"] = df.eval('(pdh-pdl)/pdl')
        df['dir'] = 0
        # Update 'dir' column based on conditions
        df.loc[df['pdc'] > df['pdo'], 'dir'] = -1
        df.loc[df['pdc'] < df['pdo'], 'dir'] = 1
        df.to_csv(csvfile, index=False)
        print(df.tail(5))
        return df

    def apply_conditions(self, df):
        print("YESTERDAY CONDITIONS")
        csvfile = dpath + "4_yday_conditions.csv"
        combined_condition = (df['yday_perc'] > Y_PERC) | (
            df['dir'] == 0)
        df = df[~combined_condition]
        df.to_csv(csvfile, index=False)
        df = pd.read_csv(csvfile, header=0)
        print(df.tail(5))
        return df

    def gap_condtions(self, df):
        """ 
            used in backtesting mode
        """
        fro = self.now.set(hour=9, minute=15).to_datetime_string()[:-3]
        nto = self.now.set(hour=9, minute=20).to_datetime_string()[:-3]
        print(f"{fro} to {nto}")
        param = {
            "exchange": "NSE",
            "interval": "FIVE_MINUTE",
            "fromdate": fro,
            "todate": nto,
            "tminus": 0,
        }
        for i, row in self.df.iterrows():
            param["symboltoken"] = row.symboltoken
            lst = self._get_ohlc(**param)
            if isinstance(lst, list):
                df.at[i, 'open'] = lst[1]
                print(row.symbol, str(lst))
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


if __name__ == "__main__":
    eqty = Equity()
    eqty.df = eqty.set_symbols()
    eqty.df = eqty.get_eod_data()
    eqty.df = eqty.eval_direction(eqty.df)
    eqty.df = eqty.apply_conditions(eqty.df)

    print("FINDING GAP TRADES ..", end="\n",)
    csvfile = dpath + "5.gap_conditions.csv"
    if MODE_TRADE == 0:
        eqty.df['open'] = eqty.df.apply(eqty.get_preopen, axis=1)
    else:
        df = eqty.gap_condtions(eqty.df)
    df['perc'] = np.where(df['dir'] == 1, (df['open'] - df['pdh']) /
                          df['pdh'], (df['pdl'] - df['open']) / df['open'])
    is_perc_grt = df['perc'] > T_PERC
    df = df[~is_perc_grt]
    str_perc = f"perc>0&perc<={T_PERC}"
    df['is_gap'] = df.eval(str_perc)
    df.to_csv(csvfile, index=False)
    print(df.tail())
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
