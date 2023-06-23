import orjson
import pandas as pd
import pendulum
import concurrent.futures as cf
import user
from toolkit.fileutils import Fileutils
from toolkit.utilities import Utilities
from time import sleep
from keltner import get_kc

# user preferences
PERC = 0.03
TRADE_DAY_TMINUS = 2
YESTERDAY_TMINUS = 1

futil = Fileutils()
lst_dohlcv = ["dtime", "o", "h", "l", "c", "v"]
df_empty = pd.DataFrame()
fpath = "../../../"
cpath = fpath
dpath = fpath + "data/"
kpath = dpath + "keltner/"

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
            csvfile = dpath + "1_symtok.csv"
            if futil.is_file_not_2day(csvfile):
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

    def get_eod_data(self):
        def _get_ohlc(symboltoken, fro, nto):
            try:
                sleep(2)
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
                if (
                    data is not None
                    and isinstance(data, list)
                    and isinstance(data[-1:], list)
                    and isinstance(data[-1:][0], list)
                ):
                    return data[-1:][0]
                else:
                    raise ValueError("data is 0")
            except ValueError as ve:
                print(
                    f"ValueError: {str(ve)} while getting high\nSleeping for {self.sleep} sec(s)")
            except Exception as e:
                print(
                    f"{str(e)} while getting high \n sleeping for {self.sleep} sec(s)")
                return 0

        try:
            fro = self.max.set(hour=9, minute=14).to_datetime_string()[:-3]
            nto = self.yday.set(hour=15, minute=30).to_datetime_string()[:-3]
            print(f"getting PDH {fro} to {nto}")
            csvfile = dpath + "2_eod_data.csv"
            if futil.is_file_not_2day(csvfile):
                while (not self.df.query("pdh==0").empty) and (self.sleep < 15):
                    df_cp = self.df.query("pdh==0").copy()
                    for i, row in df_cp.iterrows():
                        lst = _get_ohlc(row.symboltoken, fro, nto)
                        self.df.at[i, 'pdo'] = lst[1]
                        self.df.at[i, 'pdh'] = lst[2]
                        self.df.at[i, 'pdl'] = lst[3]
                        self.df.at[i, 'pdc'] = lst[4]
                        print(row.symbol, str(lst))
                    self.sleep += 1
                self.sleep = 1
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
        combined_condition = (df['yday_perc'] > PERC) | (
            df['dir'] == 0)
        df = df[~combined_condition]
        df.to_csv(csvfile, index=False)
        df = pd.read_csv(csvfile, header=0)
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


if __name__ == "__main__":
    eqty = Equity()
    eqty.df = eqty.set_symbols()
    eqty.df = eqty.get_eod_data()
    eqty.df = eqty.eval_direction(eqty.df)
    eqty.df = eqty.apply_conditions(eqty.df)

    """
    print("KELTNER VIOLATED")
    csvfile = dpath + "5_upr_violated.csv"
    eqty.df = eqty.fltr_upr_vltd(eqty.df)
    eqty.df['upr'] = eqty.df['upr'].apply(lambda x: round(x, 2))
    eqty.df.drop(['is_valid', 'h_gr_pdh'], axis=1, inplace=True)
    df_trades = eqty.df.query('upr_vltd == True').copy()
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
    fro = eqty.now.set(hour=9, minute=20).to_datetime_string()[:-3]
    nto = eqty.now.set(hour=15, minute=20).to_datetime_string()[:-3]
    print(f"{fro} to {nto}")
    param = {
        "exchange": "NSE",
        "interval": "FIVE_MINUTE",
        "fromdate": fro,
        "todate": nto,
    }
    for i, row in eqty.df.iterrows():
        param["symboltoken"] = row.symboltoken
        df = eqty.get_candles(param, "5Min")
        df['symbol'] = row.symbol
        if df_ohlc.empty:
            df_ohlc = df
        else:
            df_ohlc = pd.concat([df_ohlc, df], ignore_index=True)
    df_ohlc.to_csv(dpath + "7_5min.csv")

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
