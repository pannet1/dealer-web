# from fastapi_cprofile.profiler import CProfileMiddleware
from concurrent.futures import ThreadPoolExecutor
from api_helper import contracts, get_symbols, get_tkn_fm_sym
from api_helper import resp_to_lst, lst_to_tbl
from user_helper import (
    order_place_by_user,
    _order_place_by_user,
    order_modify_by_user,
    order_cancel_by_user,
    order_gtt_modify_by_user,
)
from user import (
    # load_all_users,
    get_broker_by_id,
    gtt,
    orders,
    trades,
    positions,
    margins,
    get_ltp,
)
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import starlette.status as status
import inspect
import uvicorn
import asyncio
from jinja_template import jt
from alerts import router as alerts_router


def load_all_users():
    return []


app = FastAPI()
"""
app.add_middleware(CProfileMiddleware, enable=True, server_app=app,
                   filename='output.pstats', strip_dirs=False, sort_by='cumulative')
"""
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(alerts_router)
pages = [
    "home",
    "margins",
    "gtt",
    "orders",
    "trades",
    "positions",
    "new",
    "basket",
    "alerts",
]


@app.get("/home", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
async def users(
    request: Request,
):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    ctx["th"] = ["message"]
    ctx["data"] = ["no data"]
    body = []
    for row in load_all_users():
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

executor = ThreadPoolExecutor(
    max_workers=max(len(load_all_users()), 1)
)  # Or define globally in your app


@app.post("/orders/")
async def post_orders(
    request: Request,
    client_name: List[str],
    qty: List[int],
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
    Places orders for all clients concurrently.
    """
    tasks = []
    loop = asyncio.get_running_loop()

    for i in range(len(client_name)):
        client = get_broker_by_id(client_name[i])
        if client is not None:
            tasks.append(
                loop.run_in_executor(
                    executor,
                    order_place_by_user,
                    client,
                    qty[i],
                    symbol,
                    token,
                    txn,
                    exchange,
                    ptype,
                    otype,
                    price,
                    lotsize,
                    trigger,
                )
            )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge all results
    mh, md, th, td, errs = [], [], [], [], []

    for result in results:
        if isinstance(result, Exception):
            # Catch any user-level failures
            errs.append({"error": str(result)})
        elif result:
            mhi, mdi, thi, tdi = result
            mh += mhi
            md += mdi
            th += thi
            td += tdi
    redirect_url = "/gtt" if ptype == 4 else "/orders"
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    if mh:
        ctx["mh"], ctx["md"] = mh, md
        if th:
            ctx["th"], ctx["data"] = th, td
        return jt.TemplateResponse("table.html", ctx)
    else:
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
    TODO
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
        _order_place_by_user(obj_client, params)
    redirect_url = request.url_for("get_orders")
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


@app.post("/bulk_modified_order_gtt/")
async def post_bulk_modified_order_gtt(
    request: Request,
    client_name: List[str],
    order_id: List[str],
    quantity: List[str],
    txn_type: str = Form(),
    exchange: str = Form(),
    symboltoken: str = Form(),
    tradingsymbol: str = Form(),
    triggerprice: str = Form(),
    price: str = Form(),
):
    """
    Post modified orders in bulk gtt concurrently.
    """
    loop = asyncio.get_running_loop()
    tasks = []
    for i in range(len(client_name)):
        obj_client = get_broker_by_id(client_name[i])
        if not obj_client:
            continue
        params = {
            "id": order_id[i],
            "tradingsymbol": tradingsymbol,
            "symboltoken": symboltoken,
            "txn": txn_type,
            "exchange": exchange,
            "price": price,
            "qty": quantity[i],
            "triggerprice": triggerprice,
            "producttype": "MARGIN",
        }
        tasks.append(
            loop.run_in_executor(
                executor,
                order_gtt_modify_by_user,
                obj_client,
                params,
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Optional: Collect and log errors
    errors = [r for r in results if isinstance(r, dict) and "error" in r]
    if errors:
        print(f"Some order modifications failed:  {errors}")

    redirect_url = request.url_for("get_gtt")
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


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
    triggerprice: str = Form(),
    price: str = Form(),
    # otype: int = Form("0"),
    producttype: str = Form(),
):

    loop = asyncio.get_running_loop()
    tasks = []

    for i in range(len(client_name)):
        obj_client = get_broker_by_id(client_name[i])
        if not obj_client:
            continue

        params = {
            "orderid": order_id[i],
            # "variety": variety,
            "tradingsymbol": tradingsymbol,
            "symboltoken": symboltoken,
            "transactiontype": txn_type,
            "exchange": exchange,
            # "ordertype": ordertype,
            "producttype": producttype,
            "price": price,
            "quantity": quantity[i],
            "triggerprice": triggerprice,
            "duration": "DAY",
        }

        tasks.append(
            loop.run_in_executor(
                executor,
                order_modify_by_user,
                obj_client,
                params,
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Optional: Collect and log errors
    errors = [r for r in results if isinstance(r, dict) and "error" in r]
    if errors:
        print("Some order modifications failed:  {errors}")

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
    except Exception as e:
        return JSONResponse(content={"E order modifying": str(e)}, status_code=400)
    else:
        redirect_url = request.url_for("get_orders")
        return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


"""
GET methods
"""


@app.get("/alerts")
def get_alerts(request: Request): ...


@app.get("/order_gtt_cancel/")
def order_gtt_cancel(
    request: Request,
    client_name: str,
    tradingsymbol: str,
    symboltoken: str,
    exchange: str,
    producttype: str,
    id: str,
):
    client = get_broker_by_id(client_name)
    params = {
        "id": id,
        "tradingsymbol": tradingsymbol,
        "symboltoken": symboltoken,
        "exchange": exchange,
        "producttype": producttype,
    }
    resp = client.obj.gttCancelRule(params)
    print(resp)
    if resp:
        redirect_url = request.url_for("get_gtt")
        return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


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


@app.get("/bulk_modify_gtt_order/", response_class=HTMLResponse)
async def get_bulk_modify_gtt_order(
    request: Request,
    exchange: str,
    tradingsymbol: str,
    symboltoken: str,
    transactiontype: str,
    status: str,
):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    subs = {
        "exchange": exchange,
        "tradingsymbol": tradingsymbol,
        "symboltoken": symboltoken,
        "transactiontype": transactiontype,
        "status": status,
    }
    mh, md, th, td = gtt()
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
                fdata.append(
                    [
                        f.get("client_name"),
                        f.get("id"),
                        str(f.get("price")) + "/" + str(f.get("triggerprice")),
                        f.get("qty"),
                    ]
                )
            ctx["th"], ctx["data"] = (
                ["client_name", "id", "prc/trgr", "quantity"],
                fdata,
            )
    _, flt_ltp = get_ltp(subs["exchange"], subs["tradingsymbol"], subs["symboltoken"])
    subs["price"] = flt_ltp[0][0]
    subs["trigger"] = 0
    subs["producttype"] = "GTT"
    ctx["subs"] = [subs]
    return jt.TemplateResponse("orders_gtt_modify.html", ctx)


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


@app.get("/gtt", response_class=HTMLResponse)
async def get_gtt(
    request: Request,
):
    th, mh, md, td = [], [], [], []
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    ctx["th"] = ["message"]
    ctx["data"] = ["no data"]
    args = [
        # "stoplossprice",
        # "stoplosstriggerprice",
        # "gttType",
        "status",
        "createddate",
        # "updateddate",
        # "expirydate",
        "clientid",
        "tradingsymbol",
        "symboltoken",
        "exchange",
        "producttype",
        "transactiontype",
        "price",
        "qty",
        "triggerprice",
        # "disclosedqty",
        "id",
    ]
    for a in load_all_users():
        status = ["FORALL"]
        resp = a.obj.gttLists(status=status, page=1, count=100)
        lst = resp_to_lst(resp)
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    if len(mh) > 0:
        ctx["mh"], ctx["md"] = mh, md
    if len(th) > 0:
        for ord in td:
            dct = dict(zip(th, ord))
            url1 = "/bulk_modify_gtt_order/?"
            url2 = "/order_gtt_cancel/?"
            for k, v in dct.items():
                url1 += f"{k}={v}&"
                url2 += f"{k}={v}&"
            ord.insert(0, url1)
            ord.insert(0, url2)
        ctx["th"], ctx["data"] = th, td
    return jt.TemplateResponse("orders_gtt.html", ctx)


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

    for obj in load_all_users():
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
    for obj in load_all_users():
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
    contracts()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
