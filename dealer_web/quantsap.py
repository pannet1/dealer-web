import pandas as pd


def db_changed(handler, newtime):
    handler.dump_memory("spread", handler.spread_data, ['status'])
    handler.dump_memory("items", handler.items_data)
    handler.set_items(handler.fetch_data(handler.qry_items))
    handler.set_spread(handler.fetch_data(handler.qry_spread))
    handler.set_file_mtime(newtime)


def monitor(handler,  updated_item):
    def calculate_percentage_change(initial_mtm, new_mtm):
        if initial_mtm == 0:
            return new_mtm
        percentage = ((new_mtm - initial_mtm) / abs(initial_mtm)) * 100
        return round(percentage, 2)

    def unsigned_perc_change(initial_mtm, new_mtm):
        if initial_mtm == 0:
            return new_mtm
        percentage = ((new_mtm - initial_mtm) / initial_mtm) * 100
        return round(percentage, 2)

    spread_data = handler.spread_data
    items_data = handler.items_data
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
    handler.set_items(items_data)
    handler.set_spread(spread_data)
    print(pd.DataFrame(spread_data))
    print(pd.DataFrame(items_data), "\n")