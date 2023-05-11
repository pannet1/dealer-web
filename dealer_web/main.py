from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import inspect
import user
from typing import List, Optional
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
jt = Jinja2Templates(directory="templates")

pages = ['home', 'margins', 'orders', 'trades', 'positions', 'new', 'basket']


@app.post("/orders/")
async def post_orders(request: Request,
                      qty: List[int], client_name: List[str],
                      symbol: str = Form(), token: str = Form(),
                      txn: Optional[str] = Form('off'), exchange: str = Form(),
                      ptype: int = Form('0'), otype: int = Form('0'),
                      price: float = Form(), trigger: float = Form()):
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


@app.post("/post_basket/")
async def posted_basket(request: Request,
    price: List[int], trigger: List[str]):
    print("request received")

    """
    quantity: List[str], client_name: List[str],
    transactiontype: List[str],exchange: List[str],
    tradingsymbol: List[str], token: List[str],
    ptype: List[str], otype: List[str],
    """
    mh, md, th, td = [], [], [], []
    """
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
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("table.html", ctx)
    """

@app.post("/bulk_modify/")
async def post_position_modify(request: Request, client_name: List[str],
                           orderid: List[str], quantity: List[str],
                           txn_type: str = Form(),
                           exchange: str = Form(), symboltoken: str = Form(),
                           tradingsymbol: str = Form(), otype: int = Form('0'),
                           producttype: str = Form(),
                           triggerprice: str = Form(),  price: str = Form()):

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

    for i, v in len(range(client_name)):
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
async def order_modify(request: Request, order_id: str = Form(),
                       qty: int = Form(), client_name: str = Form(),
                       symbol: str = Form(), token: str = Form(),
                       txn: Optional[str] = Form('off'),
                       exchange: str = Form(),
                       ptype: int = Form('0'), otype: int = Form('0'),
                       price: float = Form(), trigger: float = Form()):

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


@app.get("/home", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user.contracts()
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    return jt.TemplateResponse("table.html", ctx)


@app.get("/order_cancel/")
async def order_cancel(request: Request, client_name: str,
                       order_id: str, variety: str):
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


@app.get("/bulk_modify/", response_class=HTMLResponse)
async def get_bulk_modify(
        request: Request,
        exchange: str,
        tradingsymbol: str,
        symboltoken: str,
        transactiontype: str,
        producttype: str,
        status: str,
        ordertype: str):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
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
                fdata.append([f.get('client_name'),
                              f.get('orderid'),
                              f.get('price'),
                              f.get('triggerprice'),
                              f.get('quantity')
                              ])
            ctx['th'], ctx['data'] = ['client_name', 'orderid',
                                      'prc/trgr', 'quantity'], fdata
    remv, flt_ltp = user.get_ltp(
        subs['exchange'], subs['tradingsymbol'], subs['symboltoken'])
    subs['price'] = flt_ltp[0][0]
    subs['trigger'] = 0
    ctx['subs'] = [subs]
    return jt.TemplateResponse("modify.html", ctx)


@app.get("/pos_modify/", response_class=HTMLResponse)
async def get_pos_modify(
        request: Request,
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
        ords = []
        for tr in td:
            ords.append(dict(zip(th, tr)))
        print(ords)
        fltr = []
        for ord in ords:
            success = True
            for k, v in subs.items():
                if k == 'netqty':
                    if v > 0 and ord.get(k) < 0:
                        success = False
                        break
                    elif v < 0 and ord.get(k) > 0:
                        success = False
                        break
                    elif ord.get(k) == 0:
                        success = False
                        break
                elif ord.get(k) != v:
                    success = False
                    print(f"False: {k}{v}")
                    break
            if success:
                print(f"True: {k}{v}")
                fltr.append(ord)
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
        return jt.TemplateResponse("modify.html", ctx)


@ app.get("/orders", response_class=HTMLResponse)
async def orders(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    args = ['producttype', 'ordertype', 'price', 'triggerprice', 'quantity',
            'tradingsymbol', 'transactiontype', 'orderid', 'status', 'text',
            'exchange', 'symboltoken']
    mh, md, th, td = user.orders(args)
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        for ord in td:
            dct = dict(zip(th, ord))
            url = '/bulk_modify/?'
            for k, v in dct.items():
                url += f'{k}={v}&'
            ord.append(url)
            print(url)
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("orders.html", ctx)


@ app.get("/trades", response_class=HTMLResponse)
async def trades(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    mh, md, th, td = user.trades()
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("table.html", ctx)


@ app.get("/positions", response_class=HTMLResponse)
async def positions(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    mh, md, th, td = user.positions()
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        for ord in td:
            dct = dict(zip(th, ord))
            url = '/pos_modify/?'
            for k, v in dct.items():
                url += f'{k}={v}&'
            ord.append(url)
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("positions.html", ctx)


@ app.get("/new", response_class=HTMLResponse)
async def new(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    args = ['client_name', 'net']
    mh, md, th, td = user.margins(args)
    if any(mh):
        ctx['mh'], ctx['md'] = mh, md
    if any(th):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("new.html", ctx)


@app.get("/basket", response_class=HTMLResponse)
async def basket(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    args = ['client_name', 'net']
    mh, md, th, td = user.margins(args)
    if any(mh):
        ctx['mh'], ctx['md'] = mh, md
    if any(th):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("basket.html", ctx)


@ app.get("/margins", response_class=HTMLResponse)
async def margins(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    mh, md, th, td = user.margins()
    if len(mh) > 0:
        ctx['mh'], ctx['md'] = mh, md
    if (len(th) > 0):
        ctx['th'], ctx['data'] = th, td
    return jt.TemplateResponse("table.html", ctx)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
