from fastapi import APIRouter, Response, Request
from fastapi.templating import Jinja2Templates

import os
import json
import glob
from db import db

router = APIRouter()
templates_path = os.path.join("templates", "media_dl")
templates = Jinja2Templates(directory=templates_path)

# media_infoのrequest_id一覧を返す
@router.get('/media_dl/adm/history')
def history(p: str, request: Request):
    if p == None:
        return Response(status_code=404)
    with open("config.json") as f:
        data = json.load(f)
        if p != data["password"]:
            return Response(status_code=404)
        
    database = db.media_dl()
    request_data = database.load("time", desc=True)

    request_id = []
    info_count_all = 0
    info_count_yes = 0
    for info in request_data:
        info_count_all += 1
        if info[5] == "yes":
            info_count_yes += 1
            request_id.append(info[0])

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "request_id": request_id,
            "info_count_all": info_count_all,
            "info_count_yes": info_count_yes
        }
    )