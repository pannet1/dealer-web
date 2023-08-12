import pandas as pd
from toolkit.logger import Logger

logging = Logger(10)


def db_changed(handler):
    print("updating db")
    handler.dump_memory("spread", handler.spread_data, ['status'])
    handler.dump_memory("items", handler.items_data)
    handler.set_items(handler.fetch_data(handler.qry_items))
    handler.set_spread(handler.fetch_data(handler.qry_spread))


def display_dfs(df_spread, df_items):
    if df_spread.empty:
        print("nothing to display")
        return

    for _, row in df_spread.iterrows():
        spread_id = row['id']
        spread_info = df_spread[df_spread['id'] == spread_id]
        related_items = df_items[df_items['spread_id'] == spread_id]
        print(spread_info.to_string(index=False))
        if related_items.empty:
            print("No Related Items")
        else:
            print(related_items.to_string(index=False))
        print()  # Print an empty line to separate spreads


def monitor(handler,  updated_item):
    print("monitoring")

    def calculate_mtm_perc(entry, mtm):
        if entry == 0 or mtm == 0:
            return mtm
        else:
            return round(mtm / entry * 100, 2)

    def calculate_percentage_change(initial_mtm, new_mtm):
        if initial_mtm == 0:
            return new_mtm
        percentage = ((new_mtm - initial_mtm) / abs(initial_mtm)) * 100
        return round(percentage, 2)

    def unsigned_perc_change(initial_mtm, new_mtm):
        if initial_mtm == 0:
            return new_mtm
        elif new_mtm == 0:
            return initial_mtm
        percentage = ((new_mtm - initial_mtm) / initial_mtm) * 100
        return round(percentage, 2)

    spread_mtm, spread_capital = {}, {}
    for item in handler.items_data:
        exchtok = item["exchange"] + ":" + str(item["token"])
        if updated_item.get(exchtok, False):
            item["ltp"] = updated_item[exchtok]
        item["mtm"] = item['side'] * (item['ltp'] -
                                      item['entry']) * item['quantity']
        capital = item['side'] * (item['entry']) * item['quantity']
        spread_id = item['spread_id']
        spread_mtm[spread_id] = round(spread_mtm.get(
            spread_id, 0) + item["mtm"], 2)
        spread_capital[spread_id] = spread_capital.get(
            spread_id, 0) + capital

        for spread in handler.spread_data:
            spread_id = spread['id']
            spread['mtm'] = spread_mtm.get(spread_id, 0)
            spread['capital'] = spread_capital.get(spread_id, 0)
            spread['max_mtm'] = max(spread['max_mtm'], spread['mtm'])

            # Trailing stop
            perc_max_mtm = calculate_mtm_perc(
                spread['capital'], spread['max_mtm']
            )
            # mtm vs cost
            perc_curr_mtm = calculate_mtm_perc(
                spread['capital'], spread['mtm']
            )
            if perc_max_mtm >= spread['trail_after']:
                unrealized = spread['mtm'] - spread['capital']
                trail_mtm_at = calculate_mtm_perc(
                    unrealized, spread['max_mtm']
                )
                print(
                    f"trailing .. max_mtm:{perc_max_mtm}% > trail_after:{spread['trail_after']}% | ",
                    f"unrealized:{unrealized} mtm:{spread['mtm']} max_mtm:{spread['max_mtm']} | ",
                    f"trail_mtm:{trail_mtm_at}% < trail_at:{spread['trail_at']}% ?")
                if trail_mtm_at < spread['trail_at']:
                    logging.info("TRAIL STOPPED")
            elif perc_curr_mtm >= spread['tp']:
                logging.info(
                    f"TARGET curr_mtm:{perc_curr_mtm}% > tp:{spread['tp']}%")
            elif perc_curr_mtm <= (-1 * abs(spread['sl'])):
                logging.info(
                    f"STOPPED  curr_mtm:{perc_curr_mtm}% < sl:{spread['sl']}%")
            else:
                logging.info(
                    f"{perc_curr_mtm}% = {spread['capital']} / {spread['mtm']} * 100")
    handler.set_items(handler.items_data)
    handler.set_spread(handler.spread_data)
    df_master = pd.DataFrame(handler.spread_data)
    df_related = pd.DataFrame(handler.items_data)
    display_dfs(df_master, df_related)
