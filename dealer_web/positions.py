import user


def get_positions_and_place_market_order(params: dict):
    obj = user.get_broker_by_id(params['user'])
    if obj:
        resp = obj.positions
        if (
            resp is not None
            and isinstance(resp, dict)
            and resp.get('data', None)
            and isinstance(resp['data'], list)
        ):
            lst_of_pos = resp['data']
            pos = None
            for dct in lst_of_pos:
                if (
                    dct.get('tradingsymbol') == params['tradingsymbol']
                    and (int(dct.get('netqty')) * params['side']) > 0
                ):
                    pos = dct
                    break
            if pos:
                print(pos)
                order_params = {
                    "variety": 'NORMAL',
                    "tradingsymbol": params['tradingsymbol'],
                    "symboltoken": params['symboltoken'],
                    "transactiontype": "SELL" if params['side'] > 0 else "BUY",
                    "exchange": params['exchange'],
                    "ordertype": "MARKET",
                    "producttype": pos['producttype'],
                    "duration": "DAY",
                    "price": "0",
                    "triggerprice": "0",
                    "quantity": abs(int(pos['netqty']))
                }
                resp = obj.order_place(**order_params)
                if resp is not None:
                    print(f"order placed: {resp}")
                    return "COMPLETE"
            else:
                "position not found"
                return "COMPLETE"

        else:
            print("problem getting positions")

    else:
        print("unable to get user object")
    return get_positions_and_place_limit_order


def get_positions_and_place_limit_order(params):
    return get_orders_and_cancel_order


def get_orders_and_cancel_order(params):
    return get_positions_and_place_limit_order


def close(lst_of_ops):

    function_reference = get_positions_and_place_market_order
    for dct in lst_of_ops:
        dct['func'] = function_reference
        print(lst_of_ops)

    # Continue the loop until all 'func' values become 'COMPLETE'
    while any(params['func'] != 'COMPLETE' for params in lst_of_ops):
        for params in lst_of_ops:
            current_function = params['func']
            if current_function != 'COMPLETE':
                next_function = current_function(params)
                params['func'] = next_function
            else:
                print(f"Operation completed: {params}")
                break
        else:
            return True

    return False
