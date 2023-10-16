from fastapi import APIRouter, Response
from fastapi.responses import RedirectResponse

from urllib.parse import quote

import json
import re
import os

router = APIRouter()

@router.get('/media_dl/api/status/{request_id}')
def media_status(request_id: str):
    with open(f"media_info/{request_id}.json", encoding="utf-8") as f:
        info = json.load(f)
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
    with open(f"media_info/{request_id}.json", encoding="utf-8") as f:
        info = json.load(f)
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