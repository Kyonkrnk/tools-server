from fastapi import APIRouter, Response
from fastapi.responses import RedirectResponse

import re
from urllib.parse import quote
import router.media_dl_json as media_dl_json

router = APIRouter()

@router.get('/media_dl/api/status/{request_id}')
def media_status(request_id: str):
    info = media_dl_json.load_json(request_id)
    status = info["status"]
    if status == "no":
        return RedirectResponse(f"/media_dl/download/{request_id}")
    elif status == "downloading":
        # ニコニコでprogress_hookが機能しない、なんで。
        try:
            percent = info["percent"]
            return {"message": f"ダウンロード中です...(進捗状況：{percent}%)", "status": status}
        except:
            return {"message": f"ダウンロード中です...", "status": status}
    elif status == "silence_removing":
        return {"message": "空白を削除中です...", "status": status}
    elif status == "yes":
        return {"message": "ダウンロードが完了しました！", "status": status, "download_url": info["download_url"]}
    

@router.get('/media_dl/api/download/{request_id}')
def response_media(request_id: str):
    info = media_dl_json.load_json(request_id)
    path = info["path"]
    title = info["title"]
    format = info["format"]
    # ファイル名に使えない文字を除外する
    title = re.sub(r'[\\/:*?"<>|]+', '', title)
    # ファイル名が長すぎる場合保存できないので短くする
    while len(title.encode()) >= 160:
        title = title[:-2]
        if len(title.encode()) < 160:
            title += "_"

    # ファイルを返す
    with open(path, "rb") as f:
        data = f.read()
    response = Response(
        content = data, 
        media_type = "application/octet-stream",
        headers = {"Content-Length": str(len(data)), "Content-Disposition": f'attachment; filename="{quote(title)}.{quote(format)}"'},
        status_code = 200
    )
    return response


@router.get('/media_dl/api/info/{request_id}')
def response_info(request_id: str):
    data = media_dl_json.load_json(request_id)
    response = {
        "time": data["time"],
        "title": data["title"],
        "link": data["url"],
        "format": data["format"],
        "thumbnail": data["thumbnail"],
        "download_url": data["download_url"]
    }
    return response