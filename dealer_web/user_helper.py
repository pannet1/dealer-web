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


def _gtt_order_place_by_user(client, kwargs):
    """client, qty, symbol, token, txn, exchange, ptype, price, trigger"""
    try:
        print("gtt args", kwargs)
        rule_id = client.obj.gttCreateRule(kwargs)
        print("The GTT rule id is: {}".format(rule_id))
    except Exception as e:
        print("GTT Rule creation failed: {}".format(e))


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
        producttype = {1: "CARRYFORWARD", 2: "INTRADAY", 3: "DELIVERY", 4: "GTT"}.get(
            ptype, "INTRADAY"
        )
        params = {
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": txn_type,
            "exchange": exchange,
            "price": str(price),
            "triggerprice": str(trigger),
        }

        if producttype == "GTT":
            gtt_args = {
                "qty": str(qty),
                "disclosedqty": str(qty),
                "timeperiod": 365,
            }
            params.update(gtt_args)
            return _gtt_order_place_by_user(client, params)

        else:
            order_args = {
                "quantity": str(qty),
                "ordertype": ordertype,
                "producttype": producttype,
                "variety": variety,
                "duration": "DAY",
            }
            params.update(order_args)
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
