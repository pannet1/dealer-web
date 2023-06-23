import orjson
import pandas as pd
from toolkit.fileutils import Fileutils


sec_dir = "../../../"
dumpfile = sec_dir + "symbols.json"
futil = Fileutils()
with open(dumpfile, "rb") as ojsn:
    data = orjson.loads(ojsn.read())
    df_tok = pd.DataFrame.from_dict(
        data)
    df_tok = df_tok.query("exch_seg=='NSE'")
    columns = ["token", "symbol"]
    df_tok = df_tok.filter(columns)

data_dir = sec_dir + "data/"
df_sym = futil.get_df_fm_csv(data_dir, "nifty_200", ["symbol", "enabled"])
df_sym.dropna(inplace=True)
df_sym.drop('enabled', inplace=True, axis=1)
print(f"SYMBOLS \n {df_sym.head(5)}")

df_sym_tok = df_sym.merge(df_tok, how="left", on="symbol")
print(f"TOKENS \n {df_sym_tok.head(5)}")
