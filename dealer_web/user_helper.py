from api_helper import resp_to_lst, lst_to_tbl


def _order_place_by_user(obj_client, kwargs):
    th, td, mh, md = [], [], [], []
    resp = obj_client.order_place(**kwargs)
    if resp:
        lst = resp_to_lst(resp)
        th1, td1 = lst_to_tbl(lst, client_name=obj_client.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def order_place_by_user(
    client, qty, symbol, token, txn, exchange, ptype, otype, price, lotsize, trigger
):
    try:
        if qty <= 0:
            return None  # Skip invalid quantity

        txn_type = "BUY" if txn == "on" else "SELL"

        # Determine order type and variety
        if otype == 1:
            ordertype, variety = "LIMIT", "NORMAL"
        elif otype == 2:
            ordertype, variety = "MARKET", "NORMAL"
            price = 0
        elif otype == 3:
            ordertype, variety = "STOPLOSS_LIMIT", "STOPLOSS"
        elif otype == 4:
            ordertype, variety = "STOPLOSS_MARKET", "STOPLOSS"

        # Determine product type
        producttype = {1: "CARRYFORWARD", 2: "INTRADAY", 3: "DELIVERY"}.get(
            ptype, "INTRADAY"
        )

        params = {
            "variety": variety,
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": txn_type,
            "exchange": exchange,
            "ordertype": ordertype,
            "producttype": producttype,
            "duration": "DAY",
            "price": str(price),
            "triggerprice": str(trigger),
            "quantity": str(qty),
        }

        return _order_place_by_user(client, params)
    except Exception as e:
        return {"error": str(e), "user": getattr(client, "_userid", "unknown")}


def order_modify_by_user(obj_client, kwargs):
    th, td, mh, md = [], [], [], []

    try:
        resp = obj_client.order_modify(kwargs)
        lst = resp_to_lst(resp)
        th1, td1 = lst_to_tbl(lst, client_name=obj_client.client_name)

        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1

    except Exception as e:
        mh = ["Exception"]
        md = [[obj_client.client_name, str(e)]]

    return mh, md, th, td


def order_cancel_by_user(obj_client, order_id, variety):
    th, td, mh, md = [], [], [], []
    resp = obj_client.order_cancel(order_id, variety)
    lst = resp_to_lst(resp)
    th1, td1 = lst_to_tbl(lst, client_name=obj_client.client_name)
    if "message" in th1:
        mh = th1
        md += td1
    else:
        th = th1
        td += td1
    return mh, md, th, td
