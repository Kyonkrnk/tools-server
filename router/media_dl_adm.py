from fastapi import APIRouter, Response, Request
from fastapi.templating import Jinja2Templates

import os
import json
import glob

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
    
    request_id = []
    info_count_all = 0
    info_count_yes = 0
    info_list = glob.glob("media_info/*.json")
    for info in info_list:
        info_count_all += 1
        with open(info, encoding="utf-8") as f:
            data = json.load(f)
            if data["status"] == "yes":
                info_count_yes += 1
                request_id.append(os.path.basename(info).split(".", 1)[0])

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "request_id": request_id,
            "info_count_all": info_count_all,
            "info_count_yes": info_count_yes
        }
    )