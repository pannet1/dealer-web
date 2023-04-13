from equity import Equity
import pandas as pd
from toolkit.fileutils import Fileutils

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

eqty = Equity()
"""
try:
    eqty.set_symbols()
    eqty.df.to_csv(dpath + "1_symtok.csv", index=False)

    print("GETTING PREVOUS DAY HIGH")
    fro = eqty.max.set(hour=9, minute=14).to_datetime_string()[:-3]
    nto = eqty.yday.set(hour=15, minute=30).to_datetime_string()[:-3]
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
except Exception as e:
    print(e)
"""
cols = ["symbol", "symboltoken", "pdh",
        "pct_rule", "h", "l", "c", "upr", "h_gr_pdh"]




df = futil.get_df_fm_csv(dpath, "4_pdh_violated")
df = pd.read_csv(dpath + "4_pdh_violated.csv", header=0)
print(df.head(5))
print("KELTNER VIOLATED")
eqty.df = eqty.fltr_upr_vltd(df)
df_trades = eqty.df.query('upr_vltd == True').copy()
df_trades = df_trades.filter(items=['symbol', 'upr_vltd'], axis=1).rename({'upr_vltd': 'entry'})
print(df_trades)
eqty.df.to_csv(dpath + "5_upr_violated.csv", index=False)
