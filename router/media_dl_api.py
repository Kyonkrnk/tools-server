from fastapi import APIRouter
from fastapi.responses import RedirectResponse, FileResponse

import re
from db import db

router = APIRouter()

@router.get('/media_dl/api/status/{request_id}')
def media_status(
    request_id: str,
    ext: str = None,
    format: str = None,
    silence: str = False
):
    database = db.media_dl()
    request_data = database.load_request_data(request_id)
    status = request_data[5]
    if status == "no":
        database.update(request_id, data={"ext": ext, "format": format, "silence": silence, "status": None})
        return RedirectResponse(f"/media_dl/download/{request_id}")
    elif status == "downloading":
        try:
            percent = request_data[9]
            return {"message": f"ダウンロード中です...(進捗状況：{percent}%)", "status": status}
        except:
            return {"message": f"ダウンロード中です...", "status": status}
    elif status == "silence_removing":
        return {"message": "空白を削除中です...", "status": status}
    elif status == "yes":
        return {"message": "ダウンロードが完了しました！", "status": status, "download_url": request_data[11]}
    

@router.get('/media_dl/api/download/{request_id}')
def response_media(request_id: str):
    database = db.media_dl()
    request_data = database.load_request_data(request_id)
    path = request_data[10]
    title = request_data[1]
    ext = request_data[7]
    # ファイル名に使えない文字を除外する
    title = re.sub(r'[\\/:*?"<>|]+', '', title)
    # ファイル名が長すぎる場合保存できないので短くする
    while len(title.encode()) >= 160:
        title = title[:-2]
        if len(title.encode()) < 160:
            title += "_"

    return FileResponse(path, filename=f"{title}.{ext}")


@router.get('/media_dl/api/info/{request_id}')
def response_info(request_id: str):
    database = db.media_dl()
    request_data = database.load_request_data(request_id)
    response = {
        "time": request_data[6],
        "title": request_data[1],
        "link": request_data[2],
        "ext": request_data[7],
        "thumbnail": request_data[3],
        "download_url": request_data[11]
    }
    return response