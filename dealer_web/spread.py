import random
from toolkit.utilities import Utilities
from toolkit.fileutils import Fileutils
from database_handler import DatabaseHandler
import pandas as pd
from copy import deepcopy

# Create an instance of the DatabaseHandler
db = "../../../spread.db"
handler = DatabaseHandler(db)
futils = Fileutils()
mtime = futils.get_file_mtime(db)
global spread_data


def yield_random_price() -> float:
    return int(random.uniform(50, 200))


def calculate_percentage_change(initial_mtm, new_mtm):
    if initial_mtm == 0:
        return new_mtm  # Return the percentage change as the difference between new_mtm and initial_mtm

    percentage = ((new_mtm - initial_mtm) / abs(initial_mtm)) * 100
    return round(percentage)


# Fetch the data from the "spread" and "items" tables
qry_items = """
    SELECT items.instrument, items.exchange, items.side, items.spread_id,
    items.entry, items.quantity, items.ltp
    FROM items, spread
    WHERE spread.status >= 0
    AND spread.id = items.spread_id
"""
items_data = handler.fetch_data(qry_items)
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
        for spread in spread_data:
            param = deepcopy(spread)
            param.pop('status')
            id = param.pop('id')
            handler.update_data("spread", id, param)
    else:
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
            spread['max_mtm'] = max(spread['max_mtm'], spread['mtm'])

            # Trailing stop
            perc_max_mtm = calculate_percentage_change(
                spread['capital'], spread['max_mtm']
            )
            # mtm vs cost
            perc_curr_mtm = calculate_percentage_change(
                spread['capital'], spread['mtm']
            )
            if perc_curr_mtm >= spread['tp']:
                print(
                    f"TARGET curr_mtm:{perc_curr_mtm}% > tp:{spread['tp']}%")
            elif perc_curr_mtm <= (-1 * abs(spread['sl'])):
                print(
                    f"STOPPED  curr_mtm:{perc_curr_mtm}% < sl:{spread['sl']}%")
            elif perc_max_mtm >= spread['trail_after']:
                print(
                    f"trailing .. max_mtm:{perc_max_mtm}% > trail_after:{spread['trail_after']}%")
                unrealized = spread['mtm'] - spread['capital']
                print(
                    f"unrealized:{unrealized} = mtm:{spread['mtm']} - initial:{spread['capital']}")
                trail_mtm_at = calculate_percentage_change(
                    unrealized, spread['max_mtm']
                )
                if trail_mtm_at < spread['trail_at']:
                    print(
                        f"TRAIL STOP trail_mtm:{perc_max_mtm}% < trail_at:{spread['trail_at']}%")
            else:
                print(
                    f"{perc_curr_mtm}% = {spread['capital']} / {spread['mtm']} * 100")

        print(pd.DataFrame(spread_data))

    # Fetch instruments inside the loop to get updated data
    Utilities().slp_for(3)
