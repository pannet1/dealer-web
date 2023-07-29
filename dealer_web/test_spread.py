import random
from toolkit.utilities import Utilities
from toolkit.fileutils import Fileutils
from database_handler import DatabaseHandler
import pandas as pd
from copy import deepcopy

# CONSTANTS
DB = "../../../spread.db"
qry_items = """
    SELECT items.id, items.token, items.symbol, items.exchange, items.side, items.spread_id,
    items.entry, items.quantity, items.ltp
    FROM items, spread
    WHERE spread.status >= 0
    AND spread.id = items.spread_id
"""
qry_spread = """
    SELECT spread.*
    FROM spread
    WHERE spread.status >= 0
"""

# OBJECTS
handler = DatabaseHandler(DB)
futils = Fileutils()

# Methods
items_data = handler.fetch_data(qry_items)
spread_data = handler.fetch_data(qry_spread)

# GLOBALS
mtime = ""


def yield_random_price() -> float:
    return int(random.uniform(50, 200))


def dump_memory_to_db():
    for spread in spread_data:
        param = deepcopy(spread)
        param.pop('status')
        id = param.pop('id')
        handler.update_data("spread", id, param)

    for item in items_data:
        param = deepcopy(item)
        id = param.pop('id')
        handler.update_data("items", id, param)


def read_symbols():
    qry_symbols = """
        SELECT exchange, token
        FROM items, spread
        WHERE spread.status >= 0
        AND spread.id = items.spread_id
    """
    symbols = handler.fetch_data(qry_symbols)
    # Use a set to store unique combinations of exchange and token
    unique_exch_tokens = set()
    for item in symbols:
        exchange = item["exchange"]
        token = str(item["token"])
        exch_token = f"{exchange}:{token}"

        # Add the combination to the set (which ensures uniqueness)
        unique_exch_tokens.add(exch_token)
    # Convert the set back to a list if needed
    exch_token_list = list(unique_exch_tokens)
    return exch_token_list


lst_exch_token = read_symbols()


def run(updated_item):
    def calculate_percentage_change(initial_mtm, new_mtm):
        if initial_mtm == 0:
            return new_mtm  # Return the percentage change as the difference between new_mtm and initial_mtm
        percentage = ((new_mtm - initial_mtm) / abs(initial_mtm)) * 100
        return round(percentage, 2)

    def unsigned_perc_change(initial_mtm, new_mtm):
        if initial_mtm == 0:
            return new_mtm  # Return the percentage change as the difference between new_mtm and initial_mtm
        percentage = ((new_mtm - initial_mtm) / initial_mtm) * 100
        return round(percentage, 2)

    global mtime
    newtime = futils.get_file_mtime(DB)
    if newtime != mtime:
        # Update the row, excluding the 'mtm' field
        print(f"DB changed {mtime} != {newtime}")
        mtime = newtime
        dump_memory_to_db()
    else:
        # Update item_data with the new ltp values from updated_item
        spread_mtm = {}
        for item in items_data:
            key = item["exchange"] + ":" + str(item["token"])
            if key in updated_item:
                item["ltp"] = updated_item[key]
                item["mtm"] = item['side'] * (item['ltp'] -
                                              item['entry']) * item['quantity']
                spread_id = item['spread_id']
                spread_mtm[spread_id] = spread_mtm.get(
                    spread_id, 0) + item["mtm"]

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
            if perc_max_mtm >= spread['trail_after']:
                unrealized = spread['mtm'] - spread['capital']
                trail_mtm_at = unsigned_perc_change(
                    unrealized, spread['max_mtm']
                )
                print(
                    f"trailing .. max_mtm:{perc_max_mtm}% > trail_after:{spread['trail_after']}% | ",
                    f"unrealized:{unrealized} mtm:{spread['mtm']} max_mtm:{spread['max_mtm']} | ",
                    f"trail_mtm:{trail_mtm_at}% < trail_at:{spread['trail_at']}% ?")
                if trail_mtm_at < spread['trail_at']:
                    print("TRAIL STOPPED")
            elif perc_curr_mtm >= spread['tp']:
                print(
                    f"TARGET curr_mtm:{perc_curr_mtm}% > tp:{spread['tp']}%")
            elif perc_curr_mtm <= (-1 * abs(spread['sl'])):
                print(
                    f"STOPPED  curr_mtm:{perc_curr_mtm}% < sl:{spread['sl']}%")
            else:
                print(
                    f"{perc_curr_mtm}% = {spread['capital']} / {spread['mtm']} * 100")

        print(pd.DataFrame(spread_data))
        print(pd.DataFrame(items_data), "\n")


while True:
    updated_item = {k: yield_random_price() for k in lst_exch_token}
    run(updated_item)

    # Fetch symbols inside the loop to get updated data
    Utilities().slp_for(1)
