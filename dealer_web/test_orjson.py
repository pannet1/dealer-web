import orjson
import pandas as pd
from toolkit.fileutils import Fileutils


futil = Fileutils()
with open("../../../confid/symbols.json", "rb") as ojsn:
    data = orjson.loads(ojsn.read())
    df_tok = pd.DataFrame.from_dict(
        data)
    df_tok = df_tok.query("exch_seg=='NSE'")
    columns = ["token", "symbol"]
    df_tok = df_tok.filter(columns)


df_sym = futil.get_df_fm_csv("../../../confid/", "nifty500", ["symbol", "enabled"])
print(df_sym.head(5))
df_sym.dropna(inplace=True)
df_sym.drop('enabled', inplace=True, axis=1)
print(df_sym.head(5))

df_sym_tok = df_sym.merge(df_tok, how="left", on="symbol")
print(df_sym_tok)
