from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND
from jsondb import JsonDB  # Adjust based on your layout
from jinja_template import jt

router = APIRouter()


def get_jsondb():
    return JsonDB("../../alerts.json")


@router.get("/alerts", response_class=HTMLResponse)
async def view_alerts(request: Request, db: JsonDB = Depends(get_jsondb)):
    return jt.TemplateResponse(
        "alerts.html", {"request": request, "alerts": db.get_alerts()}
    )


@router.post("/alerts", response_class=HTMLResponse)
async def add_alert(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    db: JsonDB = Depends(get_jsondb),
):
    new_alert = db.add_alert(name, description)
    return RedirectResponse("/alerts", status_code=302)


@router.post("/alerts", response_class=HTMLResponse)
async def create_alert(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    db: JsonDB = Depends(get_jsondb),
):

    alert = db.add_alert(name, description)
    # Render only the single alert item partial
    return jt.TemplateResponse(
        "alerts/alert_item.html",
        {"request": request, "alert": alert},  # Note: not alerts, just single `alert`
    )


@router.post("/alerts/{alert_id}/delete")
async def delete_alert(alert_id: int, db: JsonDB = Depends(get_jsondb)):
    db.delete_alert(alert_id)
    return RedirectResponse("/alerts", status_code=302)


@router.post("/alerts/{alert_id}/action")
async def add_action(
    alert_id: int,
    type: str = Form(...),
    db: JsonDB = Depends(get_jsondb),
    **params: str
):
    db.add_action(alert_id, type, params)
    return RedirectResponse("/alerts", status_code=HTTP_302_FOUND)


@router.delete("/alerts/{alert_id}/{action_id}")
async def delete_action(
    alert_id: int, action_id: int, db: JsonDB = Depends(get_jsondb)
):
    db.delete_action(alert_id, action_id)
    return RedirectResponse("/alerts", status_code=HTTP_302_FOUND)
