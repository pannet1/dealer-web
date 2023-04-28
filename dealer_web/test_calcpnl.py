from equity import Equity
import pandas as pd


eqty = Equity()
lst_dohlcv = ["dtime", "o", "h", "l", "c", "v"]
df_empty = pd.DataFrame()
fpath = "../../"
cpath = fpath + "confid/"
dpath = fpath + "data/"
kpath = dpath + "keltner/"

csvfile = dpath + "5_upr_violated.csv"
eqty.df = pd.read_csv(csvfile, header=0)
if __name__ == "__main__":
    # Merge the two dataframes
merged_df = pd.merge(ticks_df, params_df, on='symbol')

# Initialize variables for tracking trade signals and positions
prev_pdh = merged_df['pdh'].iloc[0]
is_in_position = False
entries = []

# Loop through the dataframe
for i, row in merged_df.iterrows():
    symbol = row['symbol']
    time = row['time']
    close = row['close']
    keltner = row['keltner']
    pdh = row['pdh']

    # Check if a short entry can be taken
    if not is_in_position and close < keltner:
        # Check if any of the previous candles closed above pdh
        if merged_df.loc[:i, 'high'].max() < prev_pdh:
            # Take a short entry
            is_in_position = True
            entries.append({'symbol': symbol, 'time': time,
                           'price': close, 'type': 'entry'})

    # Check if the position needs to be exited
    if is_in_position and (close > pdh or time == '15:20'):
        # Exit the position
        is_in_position = False
        entries.append({'symbol': symbol, 'time': time,
                       'price': close, 'type': 'exit'})

    # Update prev_pdh
    prev_pdh = max(prev_pdh, pdh)

# Convert the entries list into a dataframe
entries_df = pd.DataFrame(entries)

# Pivot the entries dataframe to get entry and exit prices in separate columns
trades_df = entries_df.pivot(
    index='symbol', columns='type', values=['time', 'price'])
trades_df.columns = ['entry_time', 'exit_time', 'entry_price', 'exit_price']

# Print the trades dataframe
print(trades_df)
