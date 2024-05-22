from fastapi import APIRouter, Response, Header
from fastapi.responses import FileResponse, RedirectResponse
import json

router = APIRouter()

@router.get('/chart_dl/api/v1/version')
def chart_dl_version():
    return {"App-Version": "0.0.0"}

@router.get('/chart_dl/api/v2/version')
def chart_dl_version():
    return {"App-Version": "2.2.1"}

@router.get('/chart_dl/download')
def chart_dl_download(password: str = Header()):
    with open("config.json") as f:
        data = json.load(f)
    
    if password != data["password"]:
        return Response(
            status_code=404
        )
    
    return FileResponse("file/pjsekai_chart_dl.exe")