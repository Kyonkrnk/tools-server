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
from db import db
from urllib.parse import quote

router = APIRouter()
templates_path = os.path.join("templates", "media_dl")
templates = Jinja2Templates(directory=templates_path)
with open("config.json", encoding="utf-8") as f:
    conf = json.load(f)
    host = conf["Host"]


@router.get('/media_dl')
def media_dl_form():
    path = os.path.join("templates", "media_dl", "index.html")
    return FileResponse(path)

@router.post('/media_dl')
def media_dl_info(
    request: Request,
    url = Form(None), 
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

    # 水板もしくは芋葉からのダウンロード
    if ("cc.sevenc7c.com" in url) or ("chcy-" in url):
        subdomain = "cc"
        plefix = "chcy"
    if ("ptlv.sevenc7c.com" in url) or ("ptlv-" in url):
        subdomain = "ptlv"
        plefix = "ptlv"
    if "plefix" in locals():
        if "http" in url:
            url = url.split('/')
            url = url[-1]
        if "chcy-" in url:
            url = url.replace(f"{plefix}-", "")
        level_url = f"https://{subdomain}.sevenc7c.com/sonolus/levels/{plefix}-{url}"
        info_resp = requests.get(level_url)
        if info_resp.status_code != 200:
            return "正しいurlか確認してください。"
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
    request_url = f"{host}/media_dl/api/status/{request_id}"
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        data = {
            'request_id': request_id,
            'status': "no",
            'time': now,
            'id': info["id"],
            'title': info['title'],
            'url': url,
            'thumbnail': info['thumbnail']
        }
        database = db.media_dl()
        database.save(data)
    
    if "youtu" in url:
        return templates.TemplateResponse(
                    "info_youtube.html",
                    {   
                        "request": request,
                        "request_id": request_id,
                        "url": url, 
                        "v_id": data["id"],
                        "request_url": request_url
                    }
                )
    elif "nico" in url:
        return templates.TemplateResponse(
                    "info_niconico.html",
                    {   
                        "request": request,
                        "request_id": request_id,
                        "title": data['title'], 
                        "v_id": data["id"],
                        "request_url": request_url
                    }
                )
    else:
        return templates.TemplateResponse(
                    "info.html",
                    {   
                        "request": request,
                        "request_id": request_id,
                        "url": url, 
                        "v_id": data["id"], 
                        "thumbnail": data["thumbnail"],
                        "request_url": request_url
                    }
                )    