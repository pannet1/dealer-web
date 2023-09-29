import user
from time import sleep


def get_positions_and_place_market_order(params: dict):
    try:
        obj = user.get_broker_by_id(params['user'])
        if obj:
            resp = obj.positions
            sleep(1)
            print(f"positions {resp}")
            if (
                resp is not None
                and isinstance(resp, dict)
                and resp.get('data', False)
                and isinstance(resp['data'], list)
            ):
                lst_of_pos = resp['data']
                lst_of_pos = [dct for dct in lst_of_pos if dct.get(
                    'tradingsymbol') == params['tradingsymbol'] and abs(int(dct.get('netqty'), 0)) > 0]
                for dct in lst_of_pos:
                    order_params = {
                        "variety": 'NORMAL',
                        "tradingsymbol": params['tradingsymbol'],
                        "symboltoken": params['symboltoken'],
                        "transactiontype": "SELL" if params['side'] > 0 else "BUY",
                        "exchange": params['exchange'],
                        "ordertype": "MARKET",
                        "producttype": dct['producttype'],
                        "duration": "DAY",
                        "price": "0",
                        "triggerprice": "0",
                        "quantity": abs(int(dct['netqty']))
                    }
                    resp = obj.order_place(**order_params)
                    if resp is not None:
                        print(f"order placed: {resp}")
                    else:
                        print(
                            f"problem in placing order {dct} for {params['user']}")
                else:
                    print("position not found")

            else:
                print("problem getting positions")

        else:
            print("unable to get user object")
    except Exception as e:
        print(f"exception {e} when {params}")
    finally:
        return "COMPLETE"


def get_orders_and_cancel_order(params):
    return get_positions_and_place_market_order


def close(lst_of_ops):
    for params in lst_of_ops:
        params['func'] = get_orders_and_cancel_order

    for params in lst_of_ops:
        current_function = params['func']
        if current_function != 'COMPLETE':
            params['func'] = current_function(params)
        else:
            print(f"Operation completed: {params}")
            # delete this dictionary
            lst_of_ops.remove(params)

    return True
