import pandas as pd
from toolkit.logger import Logger
from test_dict_funcs import close
logging = Logger(10)


def db_changed(handler, lst_keys_to_rm=['status']):
    logging.debug("updating db")
    handler.dump_memory("spread", handler.spread_data, lst_keys_to_rm)
    handler.dump_memory("items", handler.items_data)
    handler.set_items(handler.fetch_data(handler.qry_items))
    handler.set_spread(handler.fetch_data(handler.qry_spread))


def display_dfs(df_spread, df_items):
    if df_spread.empty or df_items.empty:
        logging.info("nothing to display")
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
    logging.debug("monitoring")

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
                logging.debug(
                    f"trailing .. max_mtm:{perc_max_mtm}% > trail_after:{spread['trail_after']}% ")
                logging.debug(
                    f"unrealized:{unrealized} mtm:{spread['mtm']} max_mtm:{spread['max_mtm']}")
                logging.debug(
                    f"trail_mtm:{trail_mtm_at}% < trail_at:{spread['trail_at']}% ?")
                if trail_mtm_at < spread['trail_at']:
                    logging.info(
                        f"TRAIL STOPPED: trail_mtm{trail_mtm_at}% < trail_at{spread['trail_at']}%")
                    attach_users_to_positions(spread_id, handler)
            elif perc_curr_mtm >= spread['tp']:
                logging.info(
                    f"TARGET curr_mtm:{perc_curr_mtm}% > tp:{spread['tp']}%")
                attach_users_to_positions(spread_id, handler)
            elif perc_curr_mtm <= (-1 * abs(spread['sl'])):
                logging.info(
                    f"STOPPED  curr_mtm:{perc_curr_mtm}% < sl:{spread['sl']}%")
                attach_users_to_positions(spread_id, handler)
            else:
                logging.debug(
                    f"{perc_curr_mtm}% = {spread['capital']} / {spread['mtm']} * 100")
    handler.set_items(handler.items_data)
    handler.set_spread(handler.spread_data)
    display_dfs(pd.DataFrame(handler.spread_data),
                pd.DataFrame(handler.items_data))


def attach_users_to_positions(spread_id, handler):
    db_changed(handler, [])
    # create a list of items for each spread
    items_data = handler.items_data
    big_list = []
    for item in items_data:
        if item["spread_id"] == spread_id:
            dct = dict(
                tradingsymbol=item['symbol'],
                symboltoken=item['token'],
                exchange=item['exchange'],
                side=item['side'],
            )
            big_list.append(dct)

    # create a list of users for each spread
    lst_user_dct = handler.get_users(spread_id)
    lst_user_dct = [dct['user'] for dct in lst_user_dct]

    # merge list to dict and make a product
    result_list = []
    for user in lst_user_dct:
        for item in big_list:
            item_copy = item.copy()
            item_copy['user'] = user
            result_list.append(item_copy)

    is_complete = close(result_list)
    if is_complete:
        logging.info("all positions squared off")
        for spread in handler.spread_data:
            if spread['id'] == spread_id:
                spread['status'] = -1
