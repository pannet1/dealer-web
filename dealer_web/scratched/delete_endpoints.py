"""
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
"""
