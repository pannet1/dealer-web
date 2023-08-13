from sqlite.spreaddb import SpreadDB
import pendulum


def get_curr_time():
    tobj = pendulum.now('UTC').add(hours=5, minutes=30)
    return tobj.format('YYYY-MM-DD HH:mm:ss')


def close_positions(spread_id, items_data, users, reason):
    dct = {}
    for item in items_data:
        if item["spread_id"] == spread_id:
            dct[spread_id] = {"now":  get_curr_time(),
                              "last_update": get_curr_time(),
                              "symbol": item['symbol'],
                              "token": item['token'],
                              "exchange": item['exchange'],
                              "reason": reason,
                              "status": "INIT"}

    if any(dct):
        print(dct)


handler = SpreadDB("../../../spread.db")
items_data = handler.items_data
close_positions(spread_id=2, items_data=items_data, users=[],
                reason="TRAIL STOPPED")
