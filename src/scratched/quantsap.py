from toolkit.logger import Logger
from positions import close
from sqlite.spreaddb import SpreadDB
import time
import pandas as pd
import random


def rand_price():
    return random.randint(1, 255)


def db_changed(lst_keys_to_rm=['status']):
    handler.dump_memory("spread", handler.spread_data, lst_keys_to_rm)
    handler.set_spread(handler.fetch_data(handler.qry_spread))
    handler.dump_memory("items", handler.items_data)
    handler.set_items(handler.fetch_data(handler.qry_items))


def display_dfs(df_spread, df_items):
    if df_spread.empty or df_items.empty:
        logging.info("nothing to display")
        return
    for _, row in df_spread.iterrows():
        if row['status'] > 0:
            spread_id = row['id']
            spread_info = df_spread[df_spread['id'] == spread_id]
            related_items = df_items[df_items['spread_id'] == spread_id]
            print(spread_info.to_string(index=False))
            if related_items.empty:
                print("No Related Items", "\n")
            else:
                print(related_items.to_string(index=False), "\n")


def aggregate_items():
    try:
        spread_mtm, spread_capital = {}, {}
        for item in handler.items_data:
            """
            _, lst_user_item = user.get_ltp(
                item['exchange'], item['symbol'], item['token'])
            item['ltp'] = lst_user_item[0][0]
            """
            item['ltp'] = rand_price()
            time.sleep(0.5)
            item["mtm"] = item['side'] * \
                (item['ltp'] - item['entry']) * item['quantity']
            capital = item['side'] * (item['entry']) * item['quantity']
            spread_id = item['spread_id']
            spread_mtm[spread_id] = round(spread_mtm.get(
                spread_id, 0) + item["mtm"], 2)
            spread_capital[spread_id] = spread_capital.get(
                spread_id, 0) + capital
        return spread_mtm, spread_capital
    except Exception as e:
        print(f"while aggregating items {e}")


def monitor(spread_mtm, spread_capital):
    try:
        def calc_perc(bigger, smaller):
            if bigger == 0 or smaller == 0:
                return smaller
            else:
                return round(smaller / bigger * 100, 2)

        for spread in handler.spread_data:
            if spread['status'] > 0:
                spread_id = spread['id']
                spread['mtm'] = spread_mtm.get(spread_id, 0)
                spread['capital'] = spread_capital.get(spread_id, 0)
                spread['max_mtm'] = max(spread['max_mtm'], spread['mtm'])

                # maximum mtm vs capital
                perc_max_mtm = calc_perc(
                    abs(spread['capital']), spread['max_mtm']
                )
                # mtm vs capital
                perc_curr_mtm = calc_perc(
                    abs(spread['capital']), spread['mtm']
                )
                logtext = f"trailing: {perc_max_mtm=}% >= trail_after:{spread['trail_after']}% "

                if perc_max_mtm >= spread['trail_after']:
                    trail_mtm_at = calc_perc(spread['max_mtm'], spread['mtm'])
                    logtext = f"{trail_mtm_at=}% < trail_at:{spread['trail_at']}% ?"
                    if trail_mtm_at < spread['trail_at']:
                        logging.info(
                            f"TRLSTP:{trail_mtm_at=}% < trail_at{spread['trail_at']}%")
                        attach_users_to_positions(spread_id)
                elif perc_curr_mtm >= spread['tp']:
                    logging.info(
                        f"TARGET: {perc_curr_mtm=} > tp:{spread['tp']}%")
                    attach_users_to_positions(spread_id)
                elif perc_curr_mtm <= (-1 * abs(spread['sl'])):
                    logging.info(
                        f"STOPPED: {perc_curr_mtm=} < sl:{spread['sl']}%")
                    attach_users_to_positions(spread_id)
                else:
                    logtext = f"{perc_curr_mtm=} cap:{spread['capital']} / mtm:{spread['mtm']} * 100"
                logging.info(f"{spread['name']}: {logtext}")
    except Exception as e:
        print(f"error while monitoring {e}")


def attach_users_to_positions(spread_id):
    try:
        db_changed([])
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
        for username in lst_user_dct:
            for item in big_list:
                item_copy = item.copy()
                item_copy['user'] = username
                result_list.append(item_copy)

        is_complete = close(result_list)
        if is_complete:
            logging.info("all positions squared off")
            for spread in handler.spread_data:
                print(f"{spread['id']} == {spread_id}?")
                if spread['id'] == spread_id:
                    spread['status'] = -1
        return

    except Exception as e:
        logging.warning(f" {e} some error occured")


if __name__ == "__main__":
    logging = Logger(10)
    handler = SpreadDB("../../../spread.db")
    while True:
        curr_time = handler._get_curr_time()
        last_time = handler.last_update_time.add(minutes=5)
        if curr_time > last_time:
            db_changed()
            handler._set_update_time(last_time)
        else:
            spread_mtm, spread_capital = aggregate_items()
            if any(spread_mtm) and any(spread_capital):
                monitor(spread_mtm, spread_capital)
            display_dfs(pd.DataFrame(handler.spread_data),
                        pd.DataFrame(handler.items_data))
