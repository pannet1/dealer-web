from time import sleep
from equity import Equity
import pandas as pd
from toolkit.fileutils import Fileutils

# user preferences
PERC = 0.01
TRADE_DAY_TMINUS = 2
YESTERDAY_TMINUS = 4

futil = Fileutils()
lst_dohlcv = ["dtime", "o", "h", "l", "c", "v"]
df_empty = pd.DataFrame()
fpath = "../../"
cpath = fpath + "confid/"
dpath = fpath + "data/"
kpath = dpath + "keltner/"

eqty = Equity()
try:
    eqty.set_symbols()
    eqty.df.to_csv(dpath + "1_symtok.csv", index=False)

    """
    get high of the previous days
    """
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
