from fastapi import APIRouter, Response, Header
from fastapi.responses import FileResponse
import json

router = APIRouter()

@router.get('/chart_dl/version')
def chart_dl():
    return {"App-Version": "1.0.0"}

@router.get('/chart_dl/download')
def chart_dl_download(password: str = Header()):
    with open("config.json") as f:
        data = json.load(f)
    
    if password != data["password"]:
        return Response(
            status_code=404
        )
    
    return FileResponse("file/pjsekai_chart_dl.exe")