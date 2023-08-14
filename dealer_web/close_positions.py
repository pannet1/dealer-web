import user


def get_positions_and_place_market_order(params):
    print(params['number'] * params['value'])
    return get_positions_and_place_limit_order


def get_positions_and_place_limit_order(params):
    print(params['number'] * params['value'])
    return get_orders_and_cancel_order


def get_orders_and_cancel_order(params):
    print(params['number'] * params['value'])
    return get_positions_and_place_limit_order


def close(lst_of_ops):
    print("inside close")
    lst_of_ops = [dct.update(
        {'func': get_positions_and_place_market_order}) for dct in lst_of_ops]

    # Continue the loop until all 'func' values become None
    while any(params['func'] for params in lst_of_ops):
        for params in lst_of_ops:
            current_function = params['func']
            if current_function:
                next_function = current_function(params)
                params['func'] = next_function
            else:
                print(f"Unknown operation: {params['func']}")
