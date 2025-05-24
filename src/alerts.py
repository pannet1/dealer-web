from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND
from jsondb import JsonDB  # Adjust based on your layout
from jinja_template import jt
import inspect
from api_helper import pages

router = APIRouter()


def get_jsondb():
    return JsonDB("../../alerts.json")


"""
    alerts
"""


@router.get("/alerts", response_class=HTMLResponse)
async def view_alerts(request: Request, db: JsonDB = Depends(get_jsondb)):
    return jt.TemplateResponse(
        "alerts.html",
        {
            "request": request,
            "alerts": db.get_alerts(),
            "title": inspect.stack()[0][3],
            "pages": pages,
        },
    )


@router.post("/alerts", response_class=HTMLResponse)
async def add_alert(
    request: Request,
    name: str = Form(...),
    above: str = Form(...),
    below: str = Form(...),
    db: JsonDB = Depends(get_jsondb),
):
    new_alert = db.add_alert(name, above, below)
    return RedirectResponse("/alerts", status_code=302)


@router.post("/alerts/{alert_id}")
async def delete_alert(alert_id: int, db: JsonDB = Depends(get_jsondb)):
    db.delete_alert(alert_id)
    return RedirectResponse("/alerts", status_code=302)


"""
action
"""


@router.post("/alerts/{alert_id}/action")
async def add_action(
    alert_id: int,
    event: str = Form(...),
    action: str = Form(...),
    db: JsonDB = Depends(get_jsondb),
):
    if event != "0" and action != "0":
        db.add_action(alert_id, event, action)
    return RedirectResponse("/alerts", status_code=HTTP_302_FOUND)


@router.post("/alerts/{alert_id}/action/{action_id}")
async def delete_action(
    alert_id: int, action_id: int, db: JsonDB = Depends(get_jsondb)
):
    db.delete_action(alert_id, action_id)
    return RedirectResponse("/alerts", status_code=HTTP_302_FOUND)
