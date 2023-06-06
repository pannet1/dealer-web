import user


def posted_basket(
        price: list[str],
        trigger: list[str],
        quantity: list[str],
        client_name: list[str],
        transactiontype: list[str],
        exchange: list[str],
        tradingsymbol: list[str],
        token: list[str],
        ptype: list[str],
        otype: list[str]):
    """
    places basket orders
    """
    ctx = {}
    mh, md, th, td = [], [], [], []
    for i in range(len(price)):
        variety = ""
        if otype[i] == 'LIMIT':
            variety = 'NORMAL'
        elif otype[i] == 'MARKET':
            variety = 'NORMAL'
        elif otype[i] == 'STOPLOSS_LIMIT':
            variety = 'STOPLOSS'
        elif otype[i] == 'STOPLOSS_MARKET':
            variety = 'STOPLOSS'
        params = {
            "variety": variety,
            "tradingsymbol": tradingsymbol[i],
            "symboltoken": token[i],
            "transactiontype": transactiontype[i],
            "exchange": exchange[i],
            "ordertype": otype[i],
            "producttype": ptype[i],
            "duration": "DAY",
            "price": price[i],
            "triggerprice": trigger[i],
            "quantity": quantity[i],
        }
        mh, md, th, td = user.order_place_by_user(client_name[i], params)
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    print(ctx)


if __name__ == "__main__":
    posted_basket()
