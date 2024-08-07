# from fastapi_cprofile.profiler import CProfileMiddleware
from api_helper import contracts, get_symbols, get_tkn_fm_sym
from api_helper import resp_to_lst, lst_to_tbl
from user_helper import order_place_by_user, order_modify_by_user, order_cancel_by_user
from user import load_all_users
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import starlette.status as status
import inspect
import uvicorn
import asyncio
import random

app = FastAPI()
"""
app.add_middleware(CProfileMiddleware, enable=True, server_app=app,
                   filename='output.pstats', strip_dirs=False, sort_by='cumulative')
"""
app.mount("/static", StaticFiles(directory="static"), name="static")
jt = Jinja2Templates(directory="templates")
pages = ["home", "margins", "orders", "trades", "positions", "new", "basket"]

L_USERS = load_all_users()


def get_broker_by_id(client_name: str):
    for a in L_USERS:
        if a.client_name == client_name:
            return a


def random_broker():
    i = random.randint(0, len(L_USERS) - 1)
    return L_USERS[i]


def orders(args=None):
    th, td, mh, md = [], [], [], []
    for a in L_USERS:
        resp = a.orders
        lst = resp_to_lst(resp)
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def trades():
    th, td, mh, md = [], [], [], []
    for a in L_USERS:
        resp = a.trades
        lst = resp_to_lst(resp)
        args = [
            "tradingsymbol",
            "optiontype",
            "transactiontype",
            "tradevalue",
            "fillprice",
        ]
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def positions():
    th, td, mh, md = [], [], [], []
    for a in L_USERS:
        resp = a.positions
        lst = resp_to_lst(resp)
        args = [
            "exchange",
            "tradingsymbol",
            "producttype",
            "optiontype",
            "netqty",
            "pnl",
            "ltp",
            "avgnetprice",
            "netprice",
        ]
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def margins(args=None):
    th, td, mh, md = [], [], [], []
    for a in L_USERS:
        resp = a.margins
        if resp.get("data") is not None:
            resp["data"]["userid"] = a._userid
        lst = resp_to_lst(resp)
        if not args:
            args = [
                "userid",
                "net",
                "availablecash",
                "m2munrealized",
                "utiliseddebits",
                "utilisedpayout",
            ]
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def get_ltp(exch, sym, tkn):
    brkr = random_broker()
    print(exch, sym, tkn)
    resp = brkr.obj.ltpData(exch, sym, tkn)
    print(f"{resp:}")
    lst = resp_to_lst(resp)
    print(f"{lst}")
    head, ltp = lst_to_tbl(lst, ["ltp"], client_name=brkr.client_name)
    print(f"{ltp}")
    return head, ltp


@app.get("/home", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
async def users(
    request: Request,
):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    ctx["th"] = ["message"]
    ctx["data"] = ["no data"]
    body = []
    for row in L_USERS:
        th = ["user id", "target", "max loss", "disabled", "orders", "pnl"]
        td = [
            row._userid,
            row._target,
            row._max_loss,
            row._disabled,
        ]
        u = row
        dict_orders = u.orders
        orders = dict_orders.get("data", [])
        completed_count = 0
        if isinstance(orders, list):
            for item in orders:
                if isinstance(item, dict) and item.get("orderstatus") == "complete":
                    completed_count += 1
        td.append(completed_count)
        pos = u.positions
        if pos:
            lst_pos = pos.get("data", [])
            sum = 0
            if lst_pos:
                for dct in lst_pos:
                    sum += int(float(dct.get("pnl", 0)))
            td.append(sum)
            body.append(td)
    if len(body) > 0:
        ctx["th"] = th
        ctx["data"] = body
    return jt.TemplateResponse("users.html", ctx)


"""
POST methods
"""


@app.post("/orders/")
async def post_orders(
    request: Request,
    qty: List[int],
    client_name: List[str],
    symbol: str = Form(),
    token: str = Form(),
    txn: Optional[str] = Form("off"),
    exchange: str = Form(),
    ptype: int = Form("0"),
    otype: int = Form("0"),
    price: float = Form(),
    lotsize: int = Form("1"),
    trigger: float = Form(),
):
    """
    places orders for all clients
    """
    mh, md, th, td = [], [], [], []
    for i in range(len(client_name)):
        obj_client = get_broker_by_id(client_name[i])
        if qty[i] > 0:
            txn_type = "BUY" if txn == "on" else "SELL"
            if otype == 1:
                ordertype = "LIMIT"
                variety = "NORMAL"
            elif otype == 2:
                ordertype = "MARKET"
                variety = "NORMAL"
                price = 0
            elif otype == 3:
                ordertype = "STOPLOSS_LIMIT"
                variety = "STOPLOSS"
            elif otype == 4:
                ordertype = "STOPLOSS_MARKET"
                variety = "STOPLOSS"

            if ptype == 1:
                producttype = "CARRYFORWARD"
            elif ptype == 2:
                producttype = "INTRADAY"
            elif ptype == 3:
                producttype = "DELIVERY"
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
                "quantity": str(qty[i]),
            }
            mh, md, th, td = order_place_by_user(obj_client, params)
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    if len(mh) > 0:
        ctx["mh"], ctx["md"] = mh, md
        if len(th) > 0:
            ctx["th"], ctx["data"] = th, td
        return jt.TemplateResponse("table.html", ctx)
    else:
        return RedirectResponse("/orders", status_code=status.HTTP_302_FOUND)


@app.post("/bulk_modified_order/")
async def post_bulk_modified_order(
    request: Request,
    client_name: List[str],
    order_id: List[str],
    quantity: List[str],
    txn_type: str = Form(),
    exchange: str = Form(),
    symboltoken: str = Form(),
    tradingsymbol: str = Form(),
    otype: int = Form("0"),
    producttype: str = Form(),
    triggerprice: str = Form(),
    price: str = Form(),
):
    """
    post modified orders in bulk
    """
    mh, md, th, td = [], [], [], []
    if otype == 1:
        ordertype = "LIMIT"
        variety = "NORMAL"
    elif otype == 2:
        ordertype = "MARKET"
        variety = "NORMAL"
    elif otype == 3:
        ordertype = "STOPLOSS_LIMIT"
        variety = "STOPLOSS"
    elif otype == 4:
        ordertype = "STOPLOSS_MARKET"
        variety = "STOPLOSS"

    try:
        for i in range(len(client_name)):
            obj_client = get_broker_by_id(client_name[i])
            params = {
                "orderid": order_id[i],
                "variety": variety,
                "tradingsymbol": tradingsymbol,
                "symboltoken": symboltoken,
                "transactiontype": txn_type,
                "exchange": exchange,
                "ordertype": ordertype,
                "producttype": producttype,
                "price": price,
                "quantity": quantity[i],
                "triggerprice": triggerprice,
                "duration": "DAY",
            }
            _, _, _, _ = order_modify_by_user(obj_client, params)
        """
            to be removed
        ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
        if len(mh) > 0:
            ctx['mh'], ctx['md'] = mh, md
        if (len(th) > 0):
            ctx['th'], ctx['data'] = th, td
        return jt.TemplateResponse("table.html", ctx)
        """
    except Exception as e:
        return JSONResponse(content={"E bulk order modifying": str(e)}, status_code=400)
    else:
        redirect_url = request.url_for("get_orders")
        return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


@app.post("/order_modify/")
async def order_modify(
    request: Request,
    order_id: str = Form(),
    qty: int = Form(),
    client_name: str = Form(),
    symbol: str = Form(),
    token: str = Form(),
    txn: Optional[str] = Form("off"),
    exchange: str = Form(),
    ptype: int = Form("0"),
    otype: int = Form("0"),
    price: float = Form(),
    trigger: float = Form(),
):
    """
    modify single order
    """
    try:
        obj_client = get_broker_by_id(client_name)
        if otype == 1:
            ordertype = "LIMIT"
            variety = "NORMAL"
        elif otype == 2:
            ordertype = "MARKET"
            variety = "NORMAL"
        elif otype == 3:
            ordertype = "STOPLOSS_LIMIT"
            variety = "STOPLOSS"
        elif otype == 4:
            ordertype = "STOPLOSS_MARKET"
            variety = "STOPLOSS"
        if ptype == 1:
            producttype = "CARRYFORWARD"
        elif ptype == 2:
            producttype = "INTRADAY"
        elif ptype == 3:
            producttype = "DELIVERY"
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
        mh, md, th, td = order_modify_by_user(obj_client, params)
        """
        ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
        if len(mh) > 0:
            ctx['mh'], ctx['md'] = mh, md
        if (len(th) > 0):
            ctx['th'], ctx['data'] = th, td
        return jt.TemplateResponse("table.html", ctx)
        """
    except Exception as e:
        return JSONResponse(content={"E order modifying": str(e)}, status_code=400)
    else:
        redirect_url = request.url_for("get_orders")
        return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


@app.post("/post_basket/")
async def posted_basket(
    request: Request,
    price: List[str] = Form(),
    trigger: List[str] = Form(),
    quantity: List[str] = Form(),
    client_name: List[str] = Form(),
    transactiontype: List[str] = Form(),
    exchange: List[str] = Form(),
    tradingsymbol: List[str] = Form(),
    token: List[str] = Form(),
    ptype: List[str] = Form(),
    otype: List[str] = Form(),
):
    """
    places basket orders
    """
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    mh, md, th, td = [], [], [], []
    for i in range(len(price)):
        obj_client = get_broker_by_id(client_name[i])
        if otype[i] == "LIMIT":
            variety = "NORMAL"
        elif otype[i] == "MARKET":
            variety = "NORMAL"
        elif otype[i] == "STOPLOSS_LIMIT":
            variety = "STOPLOSS"
        elif otype[i] == "STOPLOSS_MARKET":
            variety = "STOPLOSS"
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
        order_place_by_user(obj_client, params)
        """
        if len(mh) > 0:
            ctx['mh'] = mh
            ctx['md'].extend(md)
        if (len(th) > 0):
            ctx['th'] = th
            ctx.setdefault('data', []).extend(td)
        return jt.TemplateResponse("table.html", ctx)
        except Exception as e:
            return JSONResponse(content={"E place basket": str(e)}, status_code=400)
        else:
        """
    redirect_url = request.url_for("get_orders")
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


"""
GET methods
"""


@app.get("/order_cancel/")
async def get_order_cancel(
    request: Request, client_name: str, order_id: str, variety: str
):
    obj_client = get_broker_by_id(client_name)
    mh, md, th, td = order_cancel_by_user(obj_client, order_id, variety)
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    if len(mh) > 0:
        ctx["mh"], ctx["md"] = mh, md
    if len(th) > 0:
        ctx["th"], ctx["data"] = th, td
    return jt.TemplateResponse("table.html", ctx)


@app.get("/ltp/")
async def ltp(symbol: str, exchange: str, token: str):
    _, data = get_ltp(exchange, symbol, token)
    return data


@app.get("/mw/{search}")
async def mw(search):
    _, data = get_symbols(search)
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
    ordertype: str,
):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    subs = {
        "exchange": exchange,
        "tradingsymbol": tradingsymbol,
        "symboltoken": symboltoken,
        "transactiontype": transactiontype,
        "ordertype": ordertype,
        "status": status,
        "producttype": producttype,
    }
    mh, md, th, td = orders(args=None)
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
                fdata.append(
                    [
                        f.get("client_name"),
                        f.get("orderid"),
                        str(f.get("price")) + "/" + str(f.get("triggerprice")),
                        f.get("quantity"),
                    ]
                )
            ctx["th"], ctx["data"] = (
                ["client_name", "orderid", "prc/trgr", "quantity"],
                fdata,
            )
    _, flt_ltp = get_ltp(subs["exchange"], subs["tradingsymbol"], subs["symboltoken"])
    subs["price"] = flt_ltp[0][0]
    subs["trigger"] = 0
    ctx["subs"] = [subs]
    return jt.TemplateResponse("orders_modify.html", ctx)


@app.get("/close_position_by_users/", response_class=HTMLResponse)
async def get_close_position_by_users(
    request: Request,
    exchange: str,
    tradingsymbol: str,
    netqty: int,
    producttype: str,
):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    subs = {
        "exchange": exchange,
        "tradingsymbol": tradingsymbol,
        "producttype": producttype,
    }
    transaction_type = "SELL" if netqty > 0 else "BUY"
    mh, md, th, td = positions()
    if len(th) > 0:
        posn = []
        for tr in td:
            posn.append(dict(zip(th, tr)))
        print(posn)
        fltr = []
        for pos in posn:
            success = True
            for k, v in subs.items():
                if k == "netqty":
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
                fdata.append([f.get("client_name"), abs(int(f.get("netqty")))])
            ctx["th"], ctx["data"] = ["client_name", "quantity"], fdata
    try:
        token = get_tkn_fm_sym(subs["tradingsymbol"], subs["exchange"])
        _, flt_ltp = get_ltp(subs["exchange"], subs["tradingsymbol"], token)
        print(f"LTP: {flt_ltp}")
        subs["price"] = flt_ltp[0][0]
        subs["trigger"] = 0
        subs["transactiontype"] = transaction_type
        subs["symboltoken"] = token
        ctx["subs"] = [subs]
    except Exception as e:
        print(f"{e} in get_pos_modify")
    else:
        return jt.TemplateResponse("positions_modify.html", ctx)


@app.get("/orders", response_class=HTMLResponse)
async def get_orders(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    args = [
        "cancel_modify",
        "producttype",
        "ordertype",
        "price",
        "triggerprice",
        "quantity",
        "tradingsymbol",
        "transactiontype",
        "orderid",
        "status",
        "text",
        "exchange",
        "symboltoken",
    ]
    mh, md, th, td = orders(args)
    if len(mh) > 0:
        ctx["mh"], ctx["md"] = mh, md
    if len(th) > 0:
        for ord in td:
            dct = dict(zip(th, ord))
            url = "/bulk_modify_order/?"
            for k, v in dct.items():
                url += f"{k}={v}&"
            ord.insert(0, url)
        ctx["th"], ctx["data"] = th, td
    return jt.TemplateResponse("orders.html", ctx)


@app.get("/positions", response_class=HTMLResponse)
async def get_positions(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    mh, md, th, td = positions()
    if len(mh) > 0:
        ctx["mh"], ctx["md"] = mh, md
    if len(th) > 0:
        for ord in td:
            dct = dict(zip(th, ord))
            url = "/close_position_by_users/?"
            for k, v in dct.items():
                url += f"{k}={v}&"
            ord.insert(0, url)
        ctx["th"], ctx["data"] = th, td
    return jt.TemplateResponse("positions.html", ctx)


@app.get("/new", response_class=HTMLResponse)
async def new(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    args = ["client_name", "net"]
    mh, md, th, td = margins(args)
    if any(mh):
        ctx["mh"], ctx["md"] = mh, md
    if any(th):
        ctx["th"], ctx["data"] = th, td
    return jt.TemplateResponse("new.html", ctx)


@app.get("/basket", response_class=HTMLResponse)
async def basket(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    args = ["client_name", "net"]
    mh, md, th, td = margins(args)
    if any(mh):
        ctx["mh"], ctx["md"] = mh, md
    if any(th):
        ctx["th"], ctx["data"] = th, td
    return jt.TemplateResponse("basket.html", ctx)


@app.get("/margins", response_class=HTMLResponse)
async def get_margins(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    mh, md, th, td = margins(args=None)
    if len(mh) > 0:
        ctx["mh"], ctx["md"] = mh, md
    if len(th) > 0:
        ctx["th"], ctx["data"] = th, td
    return jt.TemplateResponse("table.html", ctx)


@app.get("/trades", response_class=HTMLResponse)
async def get_trades(
    request: Request,
):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}

    mh, md, th, td = trades()
    if len(mh) > 0:
        ctx["mh"], ctx["md"] = mh, md
    if len(th) > 0:
        ctx["th"], ctx["data"] = th, td
    return jt.TemplateResponse("table.html", ctx)


@app.get("/positionbook/")
async def positionbook(
    request: Request,
    user_id: str = "no data",
    txn_type: str = "",
):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    ctx["th"] = ["message"]
    ctx["data"] = [user_id]

    for obj in L_USERS:
        if obj._userid == user_id:
            u = obj
            break
    if u:
        body = []
        pos = u.positions
        lst_pos = pos.get("data", [])
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
            "close",
        ]
        if lst_pos:
            for f_dct in lst_pos:
                [f_dct.pop(key) for key in pop_keys]
                quantity = f_dct.pop("netqty", 0)
                lotsize = f_dct.pop("lotsize", 0)
                try:
                    lots = int(quantity) / int(lotsize)
                except Exception as e:
                    print({e})
                    f_dct["netqty"] = quantity
                else:
                    f_dct["netqty"] = int(lots)
                k = f_dct.keys()
                th = list(k)
                v = f_dct.values()
                td = list(v)
                body.append(td)
            if len(body) > 0:
                ctx["th"] = th
                ctx["data"] = body

    if txn_type != "":
        list_of_dicts = [dict(zip(th, row)) for row in body]
        filtered_rows = [
            {key: value for key, value in row.items()}
            for row in list_of_dicts
            if (txn_type == "Buy" and row["netqty"] > 0)
            or (txn_type == "Sell" and row["netqty"] < 0)
        ]
        return JSONResponse(content=filtered_rows)

    return jt.TemplateResponse("table.html", ctx)


@app.get("/orderbook/{user_id}", response_class=HTMLResponse)
async def orderbook(request: Request, user_id: str = "no data"):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    ctx["th"] = ["message"]
    ctx["data"] = [user_id]
    for obj in L_USERS:
        if obj._userid == user_id:
            u = obj
            break
    if u:
        body = []
        pos = u.orders
        lst_pos = pos.get("data", [])
        pop_keys = [
            "variety",
            "producttype",
            "duration",
            "price",
            "squareoff",
            "trailingstoploss",
            "stoploss",
            "triggerprice",
            "disclosedquantity",
            "exchange",
            "symboltoken",
            "ordertag",
            "instrumenttype",
            "expirydate",
            "strikeprice",
            "optiontype",
            "filledshares",
            "unfilledshares",
            "cancelsize",
            "status",
            "exchtime",
            "exchorderupdatetime",
            "fillid",
            "filltime",
            "parentorderid",
        ]
        if lst_pos:
            for f_dct in lst_pos:
                [f_dct.pop(key) for key in pop_keys]
                quantity = f_dct.pop("quantity", 0)
                lotsize = f_dct.pop("lotsize", 0)
                try:
                    lots = int(quantity) / int(lotsize)
                except Exception as e:
                    print({e})
                    f_dct["quantity"] = quantity
                else:
                    f_dct["quantity"] = int(lots)
                k = f_dct.keys()
                th = list(k)
                v = f_dct.values()
                td = list(v)
                body.append(td)
            if len(body) > 0:
                ctx["th"] = th
                ctx["data"] = body
    return jt.TemplateResponse("table.html", ctx)


@app.on_event("startup")
async def startup_event():
    if __import__("sys").platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    contracts()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
