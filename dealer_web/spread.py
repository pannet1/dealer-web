import random
from toolkit.utilities import Utilities
from toolkit.fileutils import Fileutils
from database_handler import DatabaseHandler
import pandas as pd

# Create an instance of the DatabaseHandler
db = "../../../spread.db"
handler = DatabaseHandler(db)
futils = Fileutils()
mtime = futils.get_file_mtime(db)
print(mtime)


def yield_random_price() -> float:
    return int(random.uniform(10, 300))


# Fetch the data from the "spread" and "items" tables
qry_items = """
    SELECT items.instrument, items.exchange, items.side, items.spread_id,
    items.entry, items.quantity, items.ltp
    FROM items, spread
    WHERE spread.status >= 0
    AND spread.id = items.spread_id
"""
items_data = handler.fetch_data(qry_items)
print(pd.DataFrame(items_data))
qry_spread = """
    SELECT spread.*
    FROM spread
    WHERE spread.status >= 0
"""
spread_data = handler.fetch_data(qry_spread)

while True:

    updated_item = {
        "ACC27JUL231840CE": yield_random_price(),
        "PEL27JUL23920PE": yield_random_price()  # Updated ltp value
    }
    newtime = futils.get_file_mtime(db)
    if newtime != mtime:
        # Update the row, excluding the 'mtm' field
        print(f"db changed {mtime} != {newtime}")
        mtime = newtime
    else:
        print("db is not changed")
        spread_mtm = {}
        # Update item_data with the new ltp values from updated_item
        for item in items_data:
            instrument = item["instrument"]
            if instrument in updated_item:
                item["ltp"] = updated_item[instrument]
                item["mtm"] = item['side'] * (item['ltp'] -
                                              item['entry']) * item['quantity']
                spread_id = item['spread_id']
                spread_mtm[spread_id] = spread_mtm.get(
                    spread_id, 0) + item["mtm"]
        print(pd.DataFrame(items_data))

        for spread in spread_data:
            spread_id = spread['id']
            spread['mtm'] = spread_mtm.get(spread_id, 0)
        print(pd.DataFrame(spread_data))

    # Fetch instruments inside the loop to get updated data
    Utilities().slp_for(3)
