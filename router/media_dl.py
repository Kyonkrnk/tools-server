from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, Response, HTMLResponse

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

with open(
    os.path.join("templates", "media_dl", "index.html"),
    "r",
    encoding="UTF-8"
) as f:
    mdl_content = f.read()

@router.get('/media_dl', response_class=HTMLResponse)
def media_dl_form():
    return mdl_content

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
        #json.dump(info["formats"], open("test.json", "w", encoding="utf-8"), indent=4, ensure_ascii=False)
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
    

    info["formats"].sort(key=lambda x: int(x["abr"]) if x.get("abr") else 0)    
    info["formats"].sort(key=lambda x: x.get("vcodec", ""))
    info["formats"].reverse()

    if "youtu" in url:
        audio_formats = ""
        mp4_v_formats = ""
        mp4_a_formats = ""
        webm_v_formats = ""
        webm_a_formats = ""
        for fmt in info["formats"]:
            if fmt["ext"] == "mhtml":
                continue
            # .mp4
            # 音声
            if fmt["vbr"] == 0 and "Default" not in fmt["format"]:
                audio_formats += f'<option value="{fmt["format_id"]}">{fmt["acodec"].split(".")[0]} ( {round(fmt["abr"])}kbps )</option>'
                if "mp4a" in fmt["acodec"]:
                    mp4_a_formats += f'<option value="{fmt["format_id"]}">{fmt["acodec"].split(".")[0]} ( {round(fmt["abr"])}kbps )</option>'
                else:
                    webm_a_formats += f'<option value="{fmt["format_id"]}">{fmt["acodec"].split(".")[0]} ( {round(fmt["abr"])}kbps )</option>'
            elif fmt["abr"] == 0:
                if "avc1" in fmt["vcodec"]:
                    mp4_v_formats += f'<option value="{fmt["format_id"]}%2B">{fmt["vcodec"].split(".")[0]} ( {fmt["resolution"]} / {round(fmt["vbr"])}kbps / {round(fmt["fps"])}fps )</option>'
                elif "vp09" in fmt["vcodec"] or "av01" in fmt["vcodec"]:
                    webm_v_formats += f'<option value="{fmt["format_id"]}%2B">{fmt["vcodec"].split(".")[0]} ( {fmt["resolution"]} / {round(fmt["vbr"])}kbps / {round(fmt["fps"])}fps )</option>'
        
        return templates.TemplateResponse(
                    "info_youtube.html",
                    {   
                        "request": request,
                        "request_id": request_id,
                        "url": url, 
                        "v_id": data["id"],
                        "request_url": request_url,
                        "audio_formats": audio_formats,
                        "mp4_audio_formats": mp4_a_formats,
                        "mp4_video_formats": mp4_v_formats,
                        "webm_audio_formats": webm_a_formats,
                        "webm_video_formats": webm_v_formats
                    }
                )
    
    elif "nico" in url:
        v_formats = ""
        a_formats = ""
        for fmt in info["formats"]:
            if "audio" in fmt["format"]:
                a_formats += f'<option value="{fmt["format_id"]}">{fmt["acodec"]} ({round(fmt["abr"])}kbps)</option>'
            elif "video" in fmt["format"]:
                v_formats += f'<option value="{fmt["format_id"]}%2B">{fmt["vcodec"].split(".")[0]} ({fmt["resolution"]} {round(fmt["fps"])}fps)</option>'
        
        return templates.TemplateResponse(
                    "info_niconico.html",
                    {   
                        "request": request,
                        "request_id": request_id,
                        "title": data['title'], 
                        "v_id": data["id"],
                        "request_url": request_url,
                        "audio_formats": a_formats,
                        "video_formats": v_formats
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