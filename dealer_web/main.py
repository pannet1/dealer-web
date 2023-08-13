import traceback
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import starlette.status as status
import inspect
import user
from typing import List, Optional
import uvicorn
from sqlite.spreaddb import SpreadDB


try:
    import os
    import sys
    import sqlite3
except (ImportError, ModuleNotFoundError):
    os.system(f"{sys.executable} -m pip install sqlite3")
    import sqlite3

handler = SpreadDB("../../../spread.db")
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
jt = Jinja2Templates(directory="templates")
pages = ['home', 'margins', 'orders', 'trades',
         'positions', 'new', 'basket', 'spreads']
"""
POST methods
"""


@app.post("/orders/")
async def post_orders(request: Request,
                      qty: List[int],
                      client_name: List[str],
                      symbol: str = Form(),
                      token: str = Form(),
                      txn: Optional[str] = Form('off'),
                      exchange: str = Form(),
                      ptype: int = Form('0'),
                      otype: int = Form('0'),
                      price: float = Form(),
                      trigger: float = Form()):
    """
    places orders for all clients
    """
    mh, md, th, td = [], [], [], []
    for i in range(len(client_name)):
        if qty[i] > 0:
            txn_type = 'BUY' if txn == 'on' else 'SELL'
            if otype == 1:
                ordertype = 'LIMIT'
                variety = 'NORMAL'
            elif otype == 2:
                ordertype = 'MARKET'
                variety = 'NORMAL'
                price = 0
            elif otype == 3:
                ordertype = 'STOPLOSS_LIMIT'
                variety = 'STOPLOSS'
            elif otype == 4:
                ordertype = 'STOPLOSS_MARKET'
                variety = 'STOPLOSS'

            if ptype == 1:
                producttype = 'CARRYFORWARD'
            elif ptype == 2:
                producttype = 'INTRADAY'
            elif ptype == 3:
                producttype = 'DELIVERY'
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
                "quantity": str(qty[i])
            }
            mh, md, th, td = user.order_place_by_user(client_name[i], params)
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("table.html", ctx)


@app.post("/bulk_modified_order/")
async def post_bulk_modified_order(request: Request,
                                   client_name: List[str],
                                   orderid: List[str],
                                   quantity: List[str],
                                   txn_type: str = Form(),
                                   exchange: str = Form(),
                                   symboltoken: str = Form(),
                                   tradingsymbol: str = Form(),
                                   otype: int = Form('0'),
                                   producttype: str = Form(),
                                   triggerprice: str = Form(),
                                   price: str = Form()):
    """
    post modified orders in bulk
    """
    mh, md, th, td = [], [], [], []
    if otype == 1:
        ordertype = 'LIMIT'
        variety = 'NORMAL'
    elif otype == 2:
        ordertype = 'MARKET'
        variety = 'NORMAL'
    elif otype == 3:
        ordertype = 'STOPLOSS_LIMIT'
        variety = 'STOPLOSS'
    elif otype == 4:
        ordertype = 'STOPLOSS_MARKET'
        variety = 'STOPLOSS'

    for i in range(len(client_name)):
        params = {
            'variety': variety,
            'tradingsymbol': tradingsymbol,
            'symboltoken': symboltoken,
            "transactiontype": txn_type,
            'exchange': exchange,
            'ordertype': ordertype,
            "producttype": producttype,
            'price': price,
            'quantity': quantity[i],
            'triggerprice': triggerprice,
            'duration': 'DAY'
        }
        mh, md, th, td = user.order_place_by_user(client_name[i], params)
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("table.html", ctx)


@app.post("/order_modify/")
async def order_modify(request: Request,
                       order_id: str = Form(),
                       qty: int = Form(),
                       client_name: str = Form(),
                       symbol: str = Form(),
                       token: str = Form(),
                       txn: Optional[str] = Form('off'),
                       exchange: str = Form(),
                       ptype: int = Form('0'),
                       otype: int = Form('0'),
                       price: float = Form(),
                       trigger: float = Form()):
    """
    modify single order
    """
    if otype == 1:
        ordertype = 'LIMIT'
        variety = 'NORMAL'
    elif otype == 2:
        ordertype = 'MARKET'
        variety = 'NORMAL'
    elif otype == 3:
        ordertype = 'STOPLOSS_LIMIT'
        variety = 'STOPLOSS'
    elif otype == 4:
        ordertype = 'STOPLOSS_MARKET'
        variety = 'STOPLOSS'
    if ptype == 1:
        producttype = 'CARRYFORWARD'
    elif ptype == 2:
        producttype = 'INTRADAY'
    elif ptype == 3:
        producttype = 'DELIVERY'
    params = {
        "orderid": order_id,
        "variety": variety,
        "tradingsymbol": symbol,
        "symboltoken": token,
        "exchange": exchange,
        "ordertype": ordertype,
        "producttype": producttype,
        "duration": "DAY",
        "price": str(price),
        "triggerprice": str(trigger),
        "quantity": str(qty),
    }
    mh, md, th, td = user.order_modify_by_user(client_name, params)
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("table.html", ctx)


@app.post("/post_basket/")
async def posted_basket(request: Request,
                        price: List[str] = Form(),
                        trigger: List[str] = Form(),
                        quantity: List[str] = Form(),
                        client_name: List[str] = Form(),
                        transactiontype: List[str] = Form(),
                        exchange: List[str] = Form(),
                        tradingsymbol: List[str] = Form(),
                        token: List[str] = Form(),
                        ptype: List[str] = Form(),
                        otype: List[str] = Form()):
    """
    places basket orders
    """
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    mh, md, th, td = [], [], [], []
    for i in range(len(price)):
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
            ctx['mh'] = mh
            ctx['md'].extend(md)
        if (len(th) > 0):
            ctx['th'] = th
            ctx.setdefault('data', []).extend(td)
    return jt.TemplateResponse("table.html", ctx)


@app.post("/toggle_status")
async def toggle_status(id: int, status: int):
    handler.update_data("spread", id, {"status": status})
    return {"status": status}


@app.post("/spread_item")
async def spread_item(request: Request):
    form_data = await request.form()

    # Validate the form data
    required_fields = ["spread_id", "token", "exchange",
                       "symbol", "ltp", "entry", "qty"]
    if not all(field in form_data for field in required_fields):
        return JSONResponse(content={"error": "Missing or invalid fields in the form data"}, status_code=400)
    try:
        side = -1 if form_data.get("txn_type", "off") == "off" else 1
        spread_id = int(form_data.get("spread_id"))
        token = form_data.get("token")
        exchange = form_data.get("exchange")
        ltp = float(form_data.get("ltp"))
        symbol = form_data.get("symbol")
        entry = float(form_data.get("entry"))
        quantity = int(form_data.get("qty"))
    except (ValueError, TypeError) as e:
        print(e)
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=400)

    items_data = {
        "spread_id": spread_id,
        "token": token,
        "side": side,
        "exchange": exchange,
        "symbol": symbol,
        "ltp": ltp,
        "entry": entry,
        "quantity": quantity,
        "mtm": 0
    }
    try:
        print(f"new item: {items_data}")
        handler.insert_data("items", items_data)
    except Exception as db:
        return JSONResponse(content={"error": str(db)}, status_code=400)
    else:
        redirect_url = request.url_for('spreads')
        return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


@app.post("/spread_user")
async def post_spread_user(request: Request,
                           spread_id: int = Form(...),
                           users: List = Form(...)):

    if not isinstance(users, list) or len(users) == 0:
        return JSONResponse(content={"error": "you should have atleast one user"}, status_code=400)
    for user_id in users:
        try:
            spread_user = {"spread_id": spread_id, "broker_id": user_id}
            handler.insert_data("spread_user", spread_user)
        except Exception as db:
            return JSONResponse(content={"error": str(db)}, status_code=400)
    redirect_url = request.url_for('spreads')
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


@app.post("/spread")
async def post_spread(request: Request):
    form_data = await request.form()
    spread_data = {
        "name": form_data.get("name"),
        "tp": int(form_data.get("tp")),
        "sl": int(form_data.get("sl")),
        "trail_after": int(form_data.get("trail_after")),
        "trail_at": int(form_data.get("trail_at")),
        "status": 0,
        "capital": 0,
        "mtm": 0,
        "max_mtm": 0,
    }
    try:
        handler.insert_data("spread", spread_data)
    except Exception as db:
        return JSONResponse(content={"error": str(db)}, status_code=400)
    else:
        redirect_url = request.url_for('spreads')
        return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


"""
GET methods
"""


@app.get("/order_cancel/")
async def order_cancel(request: Request,
                       client_name: str,
                       order_id: str,
                       variety: str):
    mh, md, th, td = user.order_cancel(client_name, order_id, variety)
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("table.html", ctx)


@app.get("/ltp/")
async def ltp(symbol: str, exchange: str, token: str):
    th, data = user.get_ltp(exchange, symbol, token)
    return data


@app.get("/mw/{search}")
async def mw(search):
    th, data = user.get_symbols(search)
    return data


@app.get("/bulk_modify_order/", response_class=HTMLResponse)
async def get_bulk_modify_order(
        request: Request,
        exchange: str,
        tradingsymbol: str,
        symboltoken: str,
        transactiontype: str,
        producttype: str,
        status: str,
        ordertype: str):
    ctx = {"request": request,
           "title": inspect.stack()[0][3],
           'pages': pages}
    subs = {
        "exchange": exchange,
        "tradingsymbol": tradingsymbol,
        "symboltoken": symboltoken,
        "transactiontype": transactiontype,
        "ordertype": ordertype,
        "status": status,
        "producttype": producttype
    }
    mh, md, th, td = user.orders()
    if len(th) > 0:
        ords = []
        for tr in td:
            ords.append(dict(zip(th, tr)))
        fltr = []
        for ord in ords:
            success = True
            for k, v in subs.items():
                if ord.get(k) != v:
                    success = False
                    break
            if success:
                fltr.append(ord)
        if any(fltr):
            fdata = []
            for f in fltr:
                print(f)
                fdata.append([f.get('client_name'),
                              f.get('orderid'),
                              str(f.get('price')) + "/" +
                              str(f.get('triggerprice')),
                              f.get('quantity')
                              ])
            ctx['th'], ctx['data'] = ['client_name', 'orderid',
                                      'prc/trgr', 'quantity'], fdata
    remv, flt_ltp = user.get_ltp(
        subs['exchange'], subs['tradingsymbol'], subs['symboltoken'])
    subs['price'] = flt_ltp[0][0]
    subs['trigger'] = 0
    ctx['subs'] = [subs]
    return jt.TemplateResponse("orders_modify.html", ctx)


@app.get("/close_position_by_users/", response_class=HTMLResponse)
async def get_close_position_by_users(request: Request,
                                      exchange: str,
                                      tradingsymbol: str,
                                      netqty: int,
                                      producttype: str,):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    subs = {
        "exchange": exchange,
        "tradingsymbol": tradingsymbol,
        "producttype": producttype
    }
    transaction_type = "SELL" if netqty > 0 else "BUY"
    mh, md, th, td = user.positions()
    if len(th) > 0:
        posn = []
        for tr in td:
            posn.append(dict(zip(th, tr)))
        print(posn)
        fltr = []
        for pos in posn:
            success = True
            for k, v in subs.items():
                if k == 'netqty':
                    if v > 0 and pos.get(k) < 0:
                        success = False
                        break
                    elif v < 0 and pos.get(k) > 0:
                        success = False
                        break
                    elif pos.get(k) == 0:
                        success = False
                        break
                elif pos.get(k) != v:
                    success = False
                    print(f"False: {k}{v}")
                    break
            if success:
                print(f"True: {k}{v}")
                fltr.append(pos)
        if any(fltr):
            print(fltr)
            fdata = []
            for f in fltr:
                fdata.append([
                    f.get('client_name'),
                    abs(int(f.get('netqty')))
                ])
            ctx['th'], ctx['data'] = ['client_name', 'quantity'], fdata
    try:
        token = user.get_tkn_fm_sym(subs['tradingsymbol'])
        remv, flt_ltp = user.get_ltp(
            subs['exchange'], subs['tradingsymbol'], token)
        subs['price'] = flt_ltp[0][0]
        subs['trigger'] = 0
        subs['transactiontype'] = transaction_type
        subs['symboltoken'] = token
        ctx['subs'] = [subs]
    except Exception as e:
        print(f"{e} in get_pos_modify")
    else:
        return jt.TemplateResponse("positions_modify.html", ctx)


@ app.get("/orders", response_class=HTMLResponse)
async def orders(request: Request):
    ctx = {"request": request,
           "title": inspect.stack()[0][3],
           'pages': pages}
    args = ['cancel_modify',
            'producttype',
            'ordertype',
            'price',
            'triggerprice',
            'quantity',
            'tradingsymbol',
            'transactiontype',
            'orderid',
            'status',
            'text',
            'exchange',
            'symboltoken']
    mh, md, th, td = user.orders(args)
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        for ord in td:
            dct = dict(zip(th, ord))
            url = '/bulk_modify_order/?'
            for k, v in dct.items():
                url += f'{k}={v}&'
            ord.insert(0, url)
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("orders.html", ctx)


@ app.get("/positions", response_class=HTMLResponse)
async def positions(request: Request):
    ctx = {"request": request,
           "title": inspect.stack()[0][3],
           'pages': pages}
    mh, md, th, td = user.positions()
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        for ord in td:
            dct = dict(zip(th, ord))
            url = '/close_position_by_users/?'
            for k, v in dct.items():
                url += f'{k}={v}&'
            ord.insert(0, url)
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("positions.html", ctx)


@ app.get("/new", response_class=HTMLResponse)
async def new(request: Request):
    ctx = {"request": request,
           "title": inspect.stack()[0][3],
           'pages': pages}
    args = ['client_name',
            'net']
    mh, md, th, td = user.margins(args)
    if any(mh):
        ctx['mh'], ctx['md'] = mh, md
    if any(th):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("new.html", ctx)


@app.get("/basket", response_class=HTMLResponse)
async def basket(request: Request):
    ctx = {"request": request,
           "title": inspect.stack()[0][3],
           'pages': pages}
    args = ['client_name', 'net']
    mh, md, th, td = user.margins(args)
    if any(mh):
        ctx['mh'], ctx['md'] = mh, md
    if any(th):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("basket.html", ctx)


@ app.get("/margins", response_class=HTMLResponse)
async def margins(request: Request):
    ctx = {"request": request,
           "title": inspect.stack()[0][3],
           'pages': pages}
    mh, md, th, td = user.margins()
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("table.html", ctx)


@ app.get("/trades", response_class=HTMLResponse)
async def trades(request: Request):
    ctx = {"request": request,
           "title": inspect.stack()[0][3],
           'pages': pages}
    mh, md, th, td = user.trades()
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("table.html", ctx)


@app.get("/oldhome", response_class=HTMLResponse)
async def home(request: Request):
    user.contracts()
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    return jt.TemplateResponse("table.html", ctx)


@ app.get("/home", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
async def users(request: Request):
    user.contracts()
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    ctx['th'] = ['message']
    ctx['data'] = ["no data"]
    body = []
    ao = user.get_users()
    for row in ao:
        th = ['user id', 'target', 'max loss', 'disabled', 'orders', 'pnl']
        td = [
            row._userid,
            row._target,
            row._max_loss,
            row._disabled,
        ]
        u = row
        dict_orders = u.orders
        orders = dict_orders.get('data', [])
        completed_count = 0
        if isinstance(orders, list):
            for item in orders:
                if isinstance(item, dict) and item.get('orderstatus') == 'complete':
                    completed_count += 1
        td.append(completed_count)
        pos = u.positions
        lst_pos = pos.get('data', [])
        sum = 0
        if lst_pos:
            for dct in lst_pos:
                sum += int(float(dct.get('pnl', 0)))
        td.append(sum)
        body.append(td)
    if len(body) > 0:
        ctx['th'] = th
        ctx['data'] = body
    return jt.TemplateResponse("users.html", ctx)


@app.get("/positionbook/")
async def positionbook(request: Request,
                       user_id: str = 'no data',
                       txn_type: str = '',
                       ):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    ctx['th'] = ['message']
    ctx['data'] = [user_id]
    ao = user.get_users()
    for obj in ao:
        if obj._userid == user_id:
            u = obj
            break
    if u:
        body = []
        pos = u.positions
        lst_pos = pos.get('data', [])
        pop_keys = [
            "instrumenttype",
            "symbolname",
            "optiontype",
            "strikeprice",
            "expirydate",
            "priceden",
            "pricenum",
            "genden",
            "gennum",
            "precision",
            "multiplier",
            "boardlotsize",
            "symbolgroup",
            "cfbuyqty",
            "cfsellqty",
            "cfbuyamount",
            "cfsellamount",
            "buyavgprice",
            "sellavgprice",
            "netvalue",
            "totalbuyvalue",
            "totalsellvalue",
            "cfbuyavgprice",
            "cfsellavgprice",
            "totalbuyavgprice",
            "totalsellavgprice",
            "netprice",
            "buyqty",
            "sellqty",
            "buyamount",
            "sellamount",
            "close"
        ]
        if lst_pos:
            for f_dct in lst_pos:
                [f_dct.pop(key) for key in pop_keys]
                quantity = f_dct.pop('netqty', 0)
                lotsize = f_dct.pop('lotsize', 0)
                try:
                    lots = int(quantity) / int(lotsize)
                except Exception as e:
                    print({e})
                    f_dct['netqty'] = quantity
                else:
                    f_dct['netqty'] = int(lots)
                k = f_dct.keys()
                th = list(k)
                v = f_dct.values()
                td = list(v)
                body.append(td)
            if len(body) > 0:
                ctx['th'] = th
                ctx['data'] = body

    if txn_type != "":
        list_of_dicts = [dict(zip(th, row)) for row in body]
        filtered_rows = [
            {key: value for key, value in row.items()}
            for row in list_of_dicts
            if (txn_type == 'Buy' and row['netqty'] > 0) or
            (txn_type == 'Sell' and row['netqty'] < 0)
        ]
        return JSONResponse(content=filtered_rows)

    return jt.TemplateResponse("table.html", ctx)


@app.get("/orderbook/{user_id}", response_class=HTMLResponse)
async def orderbook(request: Request,
                    user_id: str = 'no data'):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    ctx['th'] = ['message']
    ctx['data'] = [user_id]
    ao = user.get_users()
    for obj in ao:
        if obj._userid == user_id:
            u = obj
            break
    if u:
        body = []
        pos = u.orders
        lst_pos = pos.get('data', [])
        pop_keys = [
            'variety',
            'producttype',
            'duration',
            'price',
            'squareoff',
            'trailingstoploss',
            'stoploss',
            'triggerprice',
            'disclosedquantity',
            'exchange',
            'symboltoken',
            'ordertag',
            'instrumenttype',
            'expirydate',
            'strikeprice',
            'optiontype',
            'filledshares',
            'unfilledshares',
            'cancelsize',
            'status',
            'exchtime',
            'exchorderupdatetime',
            'fillid',
            'filltime',
            'parentorderid'
        ]
        if lst_pos:
            for f_dct in lst_pos:
                [f_dct.pop(key) for key in pop_keys]
                quantity = f_dct.pop('quantity', 0)
                lotsize = f_dct.pop('lotsize', 0)
                try:
                    lots = int(quantity) / int(lotsize)
                except Exception as e:
                    print({e})
                    f_dct['quantity'] = quantity
                else:
                    f_dct['quantity'] = int(lots)
                k = f_dct.keys()
                th = list(k)
                v = f_dct.values()
                td = list(v)
                body.append(td)
            if len(body) > 0:
                ctx['th'] = th
                ctx['data'] = body
    return jt.TemplateResponse("table.html", ctx)


@app.get("/spreads", response_class=HTMLResponse)
async def spreads(request: Request):
    ctx = {"request": request,
           "title": inspect.stack()[0][3],
           'pages': pages}
    query = """
        SELECT spread.*
        FROM spread
        WHERE status >= 0
        ORDER BY id DESC
    """
    spreads = handler.fetch_data(query)

    user_query = """
        SELECT user.*
        FROM user
        """
    users = handler.fetch_data(user_query)

    # Fetch related items data for each spread and add it to the context
    for spread in spreads:
        items_query = f"""
            SELECT items.*
            FROM items
            WHERE spread_id = {spread['id']}
        """
        items = handler.fetch_data(items_query)
        spread['items'] = items

    # Fetch related users data foro each spread and add it to the context
    for spread in spreads:
        user_query = f"""
            SELECT u.user
            FROM user u
            INNER JOIN spread_user su ON u.broker_id = su.broker_id
            WHERE su.spread_id = {spread['id']}
        """
        rslt = handler.fetch_data(user_query)
        spread['users'] = rslt

    ctx['users'] = users
    ctx['spreads'] = spreads
    return jt.TemplateResponse("spreads.html", ctx)


@ app.get("/spread", response_class=HTMLResponse)
async def get_spread(request: Request):
    ctx = {"request": request,
           "title": inspect.stack()[0][3],
           'pages': pages}
    return jt.TemplateResponse("new_spread.html", ctx)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
