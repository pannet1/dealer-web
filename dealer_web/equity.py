import orjson
import pandas as pd
import pendulum
import concurrent.futures as cf
import user
from toolkit.fileutils import Fileutils
from time import sleep
from pprint import pprint
from keltner import get_kc
import warnings

# user preferences
PERC = 0.01
TRADE_DAY_TMINUS = 1
YESTERDAY_TMINUS = 2

futil = Fileutils()
lst_dohlcv = ["dtime", "o", "h", "l", "c", "v"]
df_empty = pd.DataFrame()
fpath = "../../"
cpath = fpath + "confid/"
dpath = fpath + "data/"
kpath = dpath + "keltner/"

warnings.filterwarnings(
    'ignore', 'A value is trying to be set on a copy of a slice from a DataFrame')

class Equity:

    def __init__(self):
        user.contracts()
        self.df = pd.DataFrame()
        self.sleep = 1
        self.max = pendulum.now().subtract(days=9)
        self.yday = pendulum.now().subtract(days=YESTERDAY_TMINUS)
        self.now = pendulum.now().subtract(days=TRADE_DAY_TMINUS)

    def set_symbols(self):
        try:
            csvfile = "1_symtok.csv"
            if futil.is_file_not_2day(dpath + csvfile):
                with open(cpath + "symbols.json", "rb") as ojsn:
                    data = orjson.loads(ojsn.read())
                df_tok = pd.DataFrame.from_dict(
                    data)
                columns = ["token", "symbol"]
                df_tok.query("exch_seg=='NSE'")[columns].rename(
                    columns={"token": "symboltoken"}, inplace=True)

                df_sym = futil.get_df_fm_csv(
                    dpath, "nifty_200", ["symbol", "enabled"])
                df_sym.dropna(inplace=True)
                df_sym.drop('enabled', inplace=True, axis=1)
                df = df_sym.merge(df_tok, how="left", on="symbol")
                df['pdh'] = 0
                df.to_csv(dpath + csvfile, index=False)
            else:
                df = pd.read_csv(dpath + csvfile, header=0)
        except Exception as e:
            print(f"{e} while set_symbols \n")
            SystemExit()
        else:
            return df

    def get_pdh(self, fm, to):
        try:
            csvfile =  "2_pdh.csv"
            if futil.is_file_not_2day(dpath + csvfile):
                print(f"getting PDH {fro} to {nto}")
                while (not self.df.query("pdh==0").empty) and (self.sleep < 15):
                    df_cp = self.df.query("pdh==0").copy()
                    for i, row in df_cp.iterrows():
                        self.df.loc[self.df.symbol == row.symbol,
                                    "pdh"] = self.get_high(row.symboltoken, fm, to)
                    self.sleep += 1
                self.sleep = 1
                df = self.df.query("pdh>0")
                df = pd.to_csv(dpath + csvfile, index=False)
            else:
                df = pd.read_csv(dpath + csvfile, header=0)
        except Exception as e:
            print(f"{e} while get_pdh")
            SystemExit()
        else:
            return df

    def get_pdhs(self, fm, to):
        df_cp = self.df.query("pdh==0")
        for i, row in df_cp.iterrows():
            self.df.loc[self.df.symbol == row.symbol,
                        "pdh"] = self.get_high(row.symboltoken, fm, to)

    def get_high(self, symboltoken, fro, nto):
        try:
            ao = user.random_broker()
            param = {
                "exchange": "NSE",
                "symboltoken": symboltoken,
                "interval": "ONE_DAY",
                "fromdate": fro,
                "todate": nto,
            }
            resp = ao.obj.getCandleData(param)
            pprint(resp)
            data = resp.get('data', None)
            if data:
                high = data[-1:][0][2]
            self.sleep = 1
            print(f"returning high {high}")
            return high
        except Exception as e:
            print(f"{e} while getting high \n sleeping for {self.sleep} sec(s)")
            sleep(self.sleep)
            self.sleep += 1
            return 0

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
                print(t)
                return t
            else:
                return empty_ohlc
        except Exception as e:
            print(f"{e} while getting ohlc")
            return empty_ohlc

    def get_candles_dump(self, symboltoken, fro, nto, mode="w"):
        try:
            ao = user.random_broker()
            param = {
                "exchange": "NSE",
                "symboltoken": symboltoken,
                "interval": "FIVE_MINUTE",
                "fromdate": fro,
                "todate": nto,
            }
            resp = ao.obj.getCandleData(param)
            if resp.get('data'):
                data = resp.get('data')
                df = pd.DataFrame(columns=lst_dohlcv, data=data)
                df.drop("v", inplace=True, axis=1)
                times = lst_dohlcv[0]
                df[times] = pd.to_datetime(df[times])
                df = df.set_index("dtime")
                print(df.tail(2))
                if mode == "w":
                    df.to_pickle(f"{dpath}pickle/{row.symbol}.pkl")
                else:
                    pkl_df = pd.read_pickle(f"{dpath}pickle/{row.symbol}.pkl")
                    df = pd.concat([pkl_df, df.iloc[[0]]])
                    df.to_pickle(f"{dpath}pickle/{row.symbol}.pkl")
                self.sleep = 1
                return df
            return df_empty
        except Exception as e:
            print(f"{e} while get_candles_dump \n sleeping for {self.sleep} sec(s)")
            sleep(self.sleep)
            self.sleep += 1
            return df_empty


    def is_low_broken(self, df):
        if df['Low'][0] < df['Low'].min():
            return True
        else:
            return False

    def fltr_upr_vltd(self, df):
        df = df.assign(upr_vltd=(df.c < df.upr) & (df.h > df.upr))
        return df

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
                executor.submit(place_order, symbol, ohlc)


if __name__ == "__main__":
    eqty = Equity()
    eqty.df = eqty.set_symbols()
    fro = self.max.set(hour=9, minute=14).to_datetime_string()[:-3]
    nto = self.yday.set(hour=15, minute=30).to_datetime_string()[:-3]
    eqty.df = eqty.get_pdh(fro, nto)
    """
    print(f"getting PDH {fro} to {nto}")
    while (not eqty.df.query("pdh==0").empty) and (eqty.sleep < 15):
        eqty.get_pdhs(fro, nto)
        sleep(eqty.sleep)
        print(f"sleeping for {eqty.sleep} sec(s)")
        eqty.sleep += 1
    eqty.sleep = 1
    eqty.df = eqty.df.query("pdh>0")
    print(eqty.df)
    eqty.df.to_csv(dpath + "2_pdh.csv", index=False)
    """
    df_ohlc = df_empty
    fro = eqty.now.set(hour=9, minute=14).to_datetime_string()[:-3]
    nto = eqty.now.set(hour=9, minute=19).to_datetime_string()[:-3]
    print(f"checking {PERC}%{fro} to {nto}")
    for i, row in eqty.df.iterrows():
        df = eqty.get_ohlc(row.symboltoken, fro, nto, "1Min")
        df['symbol'] = row.symbol
        if df_ohlc.empty:
            df_ohlc = df
        else:
            df_ohlc = pd.concat([df_ohlc, df], ignore_index=True)

    if not df_ohlc.empty:
        # filter only those with valid highs
        df_ohlc = df_ohlc.query("h>0")
        df_ohlc = eqty.df.merge(df_ohlc, how="left", on=['symbol'])
        # distance between low and pdh
        df_ohlc["lminuspdh"] = df_ohlc.eval("pdh - l")
        # percentage rule on 1st Min candle
        str_eval = f"lminuspdh / l <={PERC}"
        df_ohlc["pct_rule"] = df_ohlc.eval(str_eval)
        df_ohlc = df_ohlc.query("pct_rule==True")
        df_ohlc.drop(
            ['lminuspdh', 'o', 'h', 'l', 'c'],
            inplace=True, axis=1)
        print(df_ohlc)
        eqty.df = df_ohlc
        df_ohlc.to_csv(dpath + "3_pct_rule.csv", index=False)
    """
    keltner channel
    """
    print("GETTING KELTNER CHANNEL BANDS FOR YESTERDAY")
    empty_symb = []
    fro = eqty.yday.set(hour=9, minute=14).to_datetime_string()[:-3]
    nto = eqty.yday.set(hour=15, minute=30).to_datetime_string()[:-3]
    print(f"{fro} to {nto}")
    for i, row in eqty.df.iterrows():
        df = eqty.get_candles_dump(row.symboltoken, fro, nto)
        if df.empty:
            empty_symb.append(row.symboltoken)
    if len(empty_symb) > 0:
        print(f"unable to get KELTNER for following symbols \n {empty_symb}")

    print("GETTING KELTNER CHANNEL BANDS FOR TODAY")
    fro = eqty.now.set(hour=9, minute=14).to_datetime_string()[:-3]
    nto = eqty.now.set(hour=9, minute=19).to_datetime_string()[:-3]
    print(f"{fro} to {nto}")
    for i, row in eqty.df.iterrows():
        df = eqty.get_candles_dump(row.symboltoken, fro, nto, mode="append")
        print(df.tail(2))

    df_lstrows = pd.DataFrame()
    pkls = futil.get_files_with_extn("pkl", dpath + "pickle/")
    for pkl in pkls:
        df_sym = pd.read_pickle(dpath + "pickle/" + pkl)
        df_sym['upr'] = get_kc(df_sym['h'], df_sym['l'],
                               df_sym['c'], 50, 5, 50)
        last_row = df_sym.iloc[-1]
        last_row['symbol'] = pkl[:-4]
        last_row = last_row[['h', 'l', 'c', 'upr', 'symbol']]
        if df_lstrows.empty:
            df_lstrows = last_row.to_frame().T
        else:
            df_lstrows = pd.concat([df_lstrows, last_row.to_frame().T])
        # reset the index of the concatenated DataFrame
        df_lstrows = df_lstrows.reset_index(drop=True)
        df_sym.to_csv(kpath + pkl[:-4] + ".csv")
    eqty.df = pd.merge(eqty.df, df_lstrows, how='left', on=['symbol'])
    print(eqty.df.tail(5))

    print("PDH VIOLATED")
    df = eqty.df.copy()
    df = df.assign(h_gr_pdh=df.h > df.pdh)
    df = df.query("h_gr_pdh==True")
    df['is_valid'] = True
    if not df.empty:
        print(df.head(5))
        eqty.df = df
        df.to_csv(dpath + "4_pdh_violated.csv", index=False)
        """cols = ["symbol", "symboltoken", "pdh",
            "pct_rle", "h", "l", "c", "upr", "h_gr_pdh"]
        """
        df = pd.read_csv(dpath + "4_pdh_violated.csv", header=0)
        print(df.head(5))
        print("KELTNER VIOLATED")
        eqty.df = eqty.fltr_upr_vltd(df)
        df_trades = eqty.df.query('upr_vltd == True').copy()
        df_trades = df_trades.filter(items=['symbol', 'upr_vltd'], axis=1).rename({'upr_vltd': 'entry'})

        print(df_trades)
        eqty.df.to_csv(dpath + "5_upr_violated.csv", index=False)

    """
    till = "10:00"
    df_ohlc = df_empty
    fro = eqty.now.set(hour=9, minute=21).to_datetime_string()[:-3]
    nto = eqty.now.set(hour=9, minute=25).to_datetime_string()[:-3]
    print(f"{fro} to {nto}")
    for i, row in eqty.df.iterrows():
        df = eqty.get_ohlc(row.symboltoken, fro, nto, "5Min")
        df['symbol'] = row.symbol
        if df_ohlc.empty:
            df_ohlc = df
        else:
            df_ohlc = pd.concat([df_ohlc, df], ignore_index=True)
    df_cl = df_ohlc.filter(['symbol', 'c'+'0', 'l'+'0'])
    eqty.df = pd.merge(eqty.df, df_cl, how='left', on='symbol')
"""
