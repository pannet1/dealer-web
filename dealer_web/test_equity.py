import orjson
import pandas as pd
import pendulum
import concurrent.futures as cf
import user
from toolkit.fileutils import Fileutils
from time import sleep

# user preferences
PERC = 0.01
futil = Fileutils()

lst_dohlcv = ["dtime", "o", "h", "l", "c", "v"]
df_empty = pd.DataFrame()
fpath = "../../../confid/"


class Equity:

    def __init__(self):
        user.contracts()
        self.df = pd.DataFrame()
        self.sleep = 1
        self.yday = pendulum.yesterday()
        self.now = pendulum.now()

    def get_ohlc(self, symboltoken, to, tf):
        try:
            fro = self.now.set(hour=9, minute=14).to_datetime_string()[:-3]
            nto = self.now.set(hour=9, minute=to).to_datetime_string()[:-3]
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
            print(f"{e} while getting pdh")
            return empty_ohlc

    def set_symbols(self):
        with open("../../../confid/symbols.json", "rb") as ojsn:
            data = orjson.loads(ojsn.read())
            df_tok = pd.DataFrame.from_dict(
                data)
            df_tok = df_tok.query("exch_seg=='NSE'")
            columns = ["token", "symbol"]
            df_tok = df_tok.filter(columns)
            df_tok.rename(columns={"token": "symboltoken"}, inplace=True)

        df_sym = futil.get_df_fm_csv(
            fpath, "nifty500", ["symbol", "enabled"])
        df_sym.dropna(inplace=True)
        df_sym.drop('enabled', inplace=True, axis=1)
        df_sym_tok = df_sym.merge(df_tok, how="left", on="symbol")
        df_sym_tok['pdh'] = 0
        print(df_sym_tok.head(5))
        self.df = df_sym_tok

    def get_high(self, symboltoken, fm, to):
        try:
            ao = user.random_broker()
            param = {
                "exchange": "NSE",
                "symboltoken": symboltoken,
                "interval": "ONE_DAY",
                "fromdate": fm,
                "todate": to,
            }
            resp = ao.obj.getCandleData(param)
            high = resp.get('data')[:-1][0][2]
            self.sleep = 1
            print(f"returning high {high}")
            return high
        except Exception as e:
            print(f"{e} while getting high \n sleeping for {self.sleep} sec(s)")
            sleep(self.sleep)
            self.sleep += 1
            return 0

    def get_pdhs(self, fm, to):
        df_cp = self.df.query("pdh==0")
        for i, row in df_cp.iterrows():
            self.df.loc[self.df.symbol == row.symbol,
                        "pdh"] = self.get_high(row.symboltoken, fm, to)

    def is_low_broken(df):
        if df['Low'][0] < df['Low'].min():
            return True
        else:
            return False

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
    eqty.set_symbols()
    eqty.df.to_csv(fpath + "1_symtok.csv", index=False)

    """
    get high of the previous days
    """
    tmin4 = eqty.now.subtract(days=5)
    fro = tmin4.set(hour=9, minute=14).to_datetime_string()[:-3]
    nto = eqty.yday.set(hour=15, minute=31).to_datetime_string()[:-3]
    print(f"{fro} to {nto}")
    while (not eqty.df.query("pdh==0").empty) and (eqty.sleep < 15):
        eqty.get_pdhs(fro, nto)
        sleep(eqty.sleep)
        print(f"sleeping for {eqty.sleep} sec(s)")
        eqty.sleep += 1
    # SystemExit()
    eqty.sleep = 1
    eqty.df = eqty.df.query("pdh>0")
    print(eqty.df)
    eqty.df.to_csv(fpath + "2_pdh.csv", index=False)

    """
    check if difference between 1sec low and yesterday high < percentage
    """
    print("CHECKING FOR PERCENTAGE")
    df_ohlc = df_empty
    for i, row in eqty.df.iterrows():
        df = eqty.get_ohlc(row.symboltoken, 17, "1Min")
        df['symbol'] = row.symbol
        if df_ohlc.empty:
            df_ohlc = df
        else:
            df_ohlc = pd.concat([df_ohlc, df], ignore_index=True)
    if not df_ohlc.empty:
        df_ohlc = df_ohlc.query("h>0")
        df_ohlc = eqty.df.merge(df_ohlc, how="left", on=['symbol'])
        df_ohlc["lminuspdh"] = df_ohlc.eval("pdh - l")
        str_eval = f"lminuspdh / l <={PERC}"
        df_ohlc["pct_rule"] = df_ohlc.eval(str_eval)
        df_ohlc = df_ohlc.query("pct_rule==True")
        df_ohlc.drop('lminuspdh', inplace=True, axis=1)
        df_ohlc.to_csv(fpath + "3_pct_rule.csv", index=False)
        print(df_ohlc)
