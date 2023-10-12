from fastapi import APIRouter
from fastapi.responses import Response

import os
import re
import json
import yt_dlp
import subprocess
from urllib.parse import quote

currentpath = os.getcwd()
router = APIRouter()

@router.post('/media_dl/download')
def download_media(
    request_id: str
):  
    path = os.path.join("media_info", f"{request_id}.json")
    with open(path, encoding="UTF-8") as fileobj:
        info = json.load(fileobj)
        url = info["url"]
        title = info["title"]
        format = info["format"]
        silence = bool(info["silence"])

        # ファイル名に使えない文字を除外する
        title = re.sub(r'[\\/:*?"<>|]+', '', title)
        # ファイル名が長すぎる場合保存できないので短くする
        while len(title.encode()) >= 160:
            title = title[:-2]
            if len(title.encode()) < 160:
                title += "_"

    # ダウンロード
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[ext=mp4]',
        'outtmpl': f'./media/{title}',
        'noplaylist': True,
        'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }
    if format == 'wav':
        ydl_opts['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav'
            }
        ]
        ydl_opts['format'] = 'bestaudio/best'
    if format == 'mp3':
        ydl_opts['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320k'
            }
        ]
        ydl_opts['format'] = 'bestaudio/best'   

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


    # 空白カットが選択されていた場合
    if (silence == True) and (format != "mp4"):
        filepath = os.path.join(currentpath, "media", f"{title}.wav")
        command = [
            'ffmpeg',
            '-i', filepath,
            '-af', 'silencedetect=n=-50dB:d=0.001',
            '-f', 'null', '-'
        ]
        calc_silence_time = subprocess.run(command, stderr=subprocess.PIPE)
        text = calc_silence_time.stderr.decode()
        for line in text.split("\n"):
            if "silence_start:" in line:
                silence_time = re.search(r'silence_start: (\d+\.\d+)', line)
                if silence_time == None:
                    continue
                if float(silence_time.group(1)) < 10:
                    silence_time = f"00:00:0{silence_time.group(1)}"
                elif 10 <= float(silence_time.group(1)) < 60:
                    silence_time = f"00:00:{silence_time.group(1)}"
                else:
                    return "空白が1分以上あるため処理に失敗しました。"
                break

            else:
                search_end = re.search(r'silence_end: (\d+\.\d+)', line)
                search_duration = re.search(r'silence_duration: (\d+\.\d+)', line)
                if (search_end == None) or (search_duration == None):
                    continue
                if search_end.group(1) == search_duration.group(1):
                    silence_end_time = float(search_end.group(1))
                    if silence_end_time < 10:
                        silence_time = f"00:00:0{search_end.group(1)}"
                    elif 10 <= silence_end_time < 60:
                        silence_time = f"00:00:{search_end.group(1)}"
                    else:
                        return "空白が1分以上あるため処理に失敗しました。"
                    break
        if format == "mp3":
            command = [
                'ffmpeg',
                '-y',
                '-ss', f'{silence_time}',
                '-i', filepath,
                '-b:a', '320k',
                f"media/cut_{title}.{format}"
            ]
        if format == "wav":
            command = [
                'ffmpeg',
                '-y',
                '-ss', f'{silence_time}',
                '-i', filepath,
                f"media/cut_{title}.{format}"
            ]
        subprocess.run(command)
        os.remove(f"media/{title}.wav")

        # ファイルを送信する
        with open(f"media/cut_{title}.{format}", "rb") as f:
            data = f.read()
        response = Response(
            content = data, 
            media_type = "application/octet-stream",
            headers = {"Content-Length": str(len(data)), "Content-Disposition": f'attachment; filename="{quote(title)}.{quote(format)}"'},
            status_code = 200
        )
        return response
    

    # ファイルを送信する
    with open(f"media/{title}.{format}", "rb") as f:
        data = f.read()
    response = Response(
        content = data, 
        media_type = "application/octet-stream",
        headers = {"Content-Length": str(len(data)), "Content-Disposition": f'attachment; filename="{quote(title)}.{quote(format)}"'},
        status_code = 200
    )
    return response
