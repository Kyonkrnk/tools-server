from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, Response

import re
import os
import yt_dlp
import requests
import json
import uuid
import datetime
from urllib.parse import quote

router = APIRouter()
templates_path = os.path.join("templates", "media_dl")
templates = Jinja2Templates(directory=templates_path)


@router.get('/media_dl')
async def media_dl_form():
    path = os.path.join("templates", "media_dl", "index.html")
    return FileResponse(path)

@router.post('/media_dl')
async def media_dl_info(
    request: Request,
    url = Form(None), 
    format = Form(), 
    silence: bool = Form(),
    ):
    # urlが入力されていない場合
    if url == None:
        return 'urlを入力してください'
    
    # listのパラメータをurlから消し去る
    if "list=" in url:
        url = url.split('?')
        query = [i for i in url[1].split('&') if "list=" not in i]
        query = "?" + "&".join(query)
        url = url[0] + query

    # 水板からのダウンロードが選択された場合
    if format == "cc":
        if "chcy-" in url:
            url = url.replace("chcy-", "")
        level_url = f"https://cc.sevenc7c.com/sonolus/levels/chcy-{url}"
        info_resp = requests.get(level_url)
        if info_resp.status_code != 200:
            return "正しい譜面IDか確認してください。"
        song_name = quote(info_resp.json()["item"]["title"])
        song_name = re.sub(r'[\\/:*?"<>|]+', '', song_name)
        bgm_url = info_resp.json()["item"]["bgm"]["url"]
        bgm_data = requests.get(bgm_url).content        
        response = Response(
            content = bgm_data, 
            media_type = "application/octet-stream",
            headers = {"Content-Length": str(len(bgm_data)), "Content-Disposition": f'attachment; filename="{song_name}.mp3"'},
            status_code = 200
        )
        return response
    
    request_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        info_dict = {
            'time': now,
            'id': info["id"],
            'title': info['title'],
            'url': url,
            'format': format,
            'silence': silence,
            'thumbnail': info['thumbnail']
        }
        path = os.path.join("media_info", f"{request_id}.json")
        with open(path, "w", encoding="UTF-8") as fileobj:
            json.dump(info_dict, fileobj, indent=4, ensure_ascii=False)

    if "youtu" in url:
        return templates.TemplateResponse(
                    "info_youtube.html",
                    {   
                        "request": request,
                        "title": info_dict['title'], 
                        "url": url, 
                        "format": format, 
                        "v_id": info_dict["id"], 
                        "request_id": request_id
                    }
                )
    elif "nico" in url:
        return templates.TemplateResponse(
                    "info_niconico.html",
                    {   
                        "request": request,
                        "title": info_dict['title'], 
                        "url": url, 
                        "format": format, 
                        "v_id": info_dict["id"], 
                        "request_id": request_id
                    }
                )
    else:
        return templates.TemplateResponse(
                    "info.html",
                    {   
                        "request": request,
                        "title": info_dict['title'], 
                        "url": url, 
                        "format": format, 
                        "v_id": info_dict["id"], 
                        "thumbnail": info["thumbnail"],
                        "request_id": request_id
                    }
                )    