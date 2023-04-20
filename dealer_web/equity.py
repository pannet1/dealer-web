import orjson
import pandas as pd
import pendulum
import concurrent.futures as cf
import user
from toolkit.fileutils import Fileutils
from time import sleep
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

pd.options.mode.chained_assignment = None


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
            if futil.is_file_not_2day(dpath + csvfile) is not False:
                with open(cpath + "symbols.json", "rb") as ojsn:
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
                df.to_csv(dpath + csvfile, index=False)
            else:
                df = pd.read_csv(dpath + csvfile, header=0)
        except Exception as e:
            print(f"{e} while set_symbols \n")
            SystemExit()
        else:
            print(df.tail(3))
            return df

    def get_pdh(self):
        def get_high(symboltoken, fro, nto):
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
                data = resp.get('data', None)
                if data:
                    high = data[-1:][0][2]
                # self.sleep = 1
                print(f"returning high {high}")
                return high
            except Exception as e:
                print(f"{e} while getting high \n sleeping for {self.sleep} sec(s)")
                sleep(self.sleep)
                self.sleep += 1
                return 0

        try:
            fro = self.max.set(hour=9, minute=14).to_datetime_string()[:-3]
            nto = self.yday.set(hour=15, minute=30).to_datetime_string()[:-3]
            print(f"getting PDH {fro} to {nto}")
            csvfile = "2_pdh.csv"
            if futil.is_file_not_2day(dpath + csvfile) is not False:
                while (not self.df.query("pdh==0").empty) and (self.sleep < 15):
                    df_cp = self.df.query("pdh==0").copy()
                    for i, row in df_cp.iterrows():
                        self.df.loc[self.df.symbol == row.symbol,
                                    "pdh"] = get_high(row.symboltoken, fro, nto)
                    self.sleep += 1
                self.sleep = 1
                df = self.df.query("pdh>0")
                df.to_csv(dpath + csvfile, index=False)
            else:
                df = pd.read_csv(dpath + csvfile, header=0)
        except Exception as e:
            print(f"{e} while get_pdh")
            SystemExit()
        else:
            print(df.tail(5))
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

    def eval_perc_rule(self, df_ohlc):
        print("PERCENTAGE RULE")
        csvfile = dpath + "3_pct_rule.csv"
        if futil.is_file_not_2day(csvfile) is not False:
            df = self.df.merge(df_ohlc, how="left", on=['symbol'])
            # distance between low and pdh
            df["lminuspdh"] = df.eval("pdh - l")
            # percentage rule on 1st Min candle
            str_eval = f"lminuspdh / l <={PERC}"
            df["is_valid"] = df.eval(str_eval)
            df = df.query("is_valid==True")
            df.drop(
                ['lminuspdh', 'o', 'h', 'l', 'c'],
                inplace=True, axis=1)
            df.to_csv(csvfile, index=False)
        else:
            df = pd.read_csv(csvfile, header=0)
        print(df.tail(5))
        return df

    def is_low_broken(self, df):
        if df['Low'][0] < df['Low'].min():
            return True
        else:
            return False

    def fltr_upr_vltd(self, df):
        df = df.assign(upr_vltd=(df.c < df.upr) & (df.h > df.upr))
        return df

    def get_keltner_2day(self):
        def get_candles_dump(symboltoken, fro, nto, mode="w"):
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
                sleep(0.5)
                if resp.get('data'):
                    data = resp.get('data')
                    df = pd.DataFrame(columns=lst_dohlcv, data=data)
                    df.drop("v", inplace=True, axis=1)
                    times = lst_dohlcv[0]
                    df[times] = pd.to_datetime(df[times])
                    df = df.set_index("dtime")
                    if mode == "w":
                        df.to_pickle(f"{dpath}pickle/{row.symbol}.pkl")
                    else:
                        pkl_df = pd.read_pickle(
                            f"{dpath}pickle/{row.symbol}.pkl")
                        df = pd.concat([pkl_df, df.iloc[[0]]])
                        df.to_pickle(f"{dpath}pickle/{row.symbol}.pkl")
                    return df
            except Exception as e:
                print(e)

        print("GET KELTNER")
        empty_symb = []
        fro = self.yday.set(hour=9, minute=14).to_datetime_string()[:-3]
        nto = self.yday.set(hour=15, minute=30).to_datetime_string()[:-3]
        print(f"{fro} to {nto}")
        for i, row in self.df.iterrows():
            df = get_candles_dump(row.symboltoken, fro, nto)
            if df.empty:
                empty_symb.append(row.symboltoken)
        if len(empty_symb) > 0:
            print(
                f"unable to get KELTNER for following symbols \n {empty_symb}")

        print("GETTING KELTNER CHANNEL BANDS FOR TODAY")
        fro = self.now.set(hour=9, minute=14).to_datetime_string()[:-3]
        nto = self.now.set(hour=9, minute=19).to_datetime_string()[:-3]
        print(f"{fro} to {nto}")
        for i, row in self.df.iterrows():
            df = get_candles_dump(row.symboltoken, fro, nto, mode="append")

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
            df_lstrows = df_lstrows.reset_index(drop=True)
            df_sym.to_csv(kpath + pkl[:-4] + ".csv")
        df = pd.merge(self.df, df_lstrows, how='left', on=['symbol'])
        print(df.tail(5))
        return df

    def eval_pdh_violated(self):
        print("PDH VIOLATED")
        csvfile = dpath + "4_pdh_violated.csv"
        if futil.is_file_not_2day(csvfile) is not False:
            df = self.df.copy()
            df = df.assign(h_gr_pdh=df.h > df.pdh)
            df = df.query("h_gr_pdh==True")
            df['is_valid'] = True
            df.to_csv(csvfile, index=False)
        else:
            df = pd.read_csv(csvfile, header=0)
        print(df.tail(5))
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
    eqty.df = eqty.get_pdh()

    fro = eqty.now.set(hour=9, minute=14).to_datetime_string()[:-3]
    nto = eqty.now.set(hour=9, minute=19).to_datetime_string()[:-3]
    print(f"checking {PERC}%{fro} to {nto}")
    df_ohlc = pd.DataFrame()
    for i, row in eqty.df.iterrows():
        df = eqty.get_ohlc(row.symboltoken, fro, nto, "1Min")
        df['symbol'] = row.symbol
        if df_ohlc.empty:
            df_ohlc = df
        else:
            df_ohlc = pd.concat([df_ohlc, df], ignore_index=True)
        # sleep(eqty.sleep)

    eqty.df = eqty.eval_perc_rule(df_ohlc)
    eqty.df = eqty.get_keltner_2day()
    eqty.df = eqty.eval_pdh_violated()

    print("KELTNER VIOLATED")
    csvfile = dpath + "5_upr_violated.csv"
    eqty.df = eqty.fltr_upr_vltd(eqty.df)
    df_trades = eqty.df.query('upr_vltd == True').copy()
    df_trades = df_trades.filter(
        items=['symbol', 'upr_vltd'], axis=1)
    df_trades = df_trades.rename(columns={'upr_vltd': 'entry'})
    print(eqty.df)
    print("TRADES")
    print(df_trades)
    eqty.df.to_csv(csvfile, index=False)

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
