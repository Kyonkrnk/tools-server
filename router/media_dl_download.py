from fastapi import APIRouter

import os
import re
import yt_dlp
import subprocess
from db import db

currentpath = os.getcwd()
router = APIRouter()

def update_status(request_id, status, database):
    data = {
        "status": status
    }
    database.update(request_id, data)

def update_info(request_id, path, database):
    data = {
        "path": path,
        "status": "yes",
        "download_url": f"/media_dl/api/download/{request_id}"
    }
    database.update(request_id, data)

pattern = re.compile(r'(\d+\.\d+)%')
def progress_hook(progress_data, request_id, database):
    if progress_data['status'] == 'downloading':
        percent = re.search(pattern, progress_data['_percent_str'])
        if percent != None:
            data = {
                "percent": percent.group(1)
            }
            database.update(request_id, data)



@router.get('/media_dl/download/{request_id}')
def download_media(request_id: str):  
    database = db.media_dl()
    request_data = database.load_request_data(request_id)
    url = request_data[2]
    title = request_data[1]
    ext = request_data[7]
    format = request_data[12]
    silence = request_data[8]
    # ファイル名に使えない文字を除外する
    title = re.sub(r'[\\/:*?"<>|\']+','', title)
    # ファイル名が長すぎる場合保存できないので短くする
    while len(title.encode()) >= 150:
        title = title[:-2]
        if len(title.encode()) < 150:
            title += "_"

    # ファイル名が重複していないか確認する
    a = 0
    while True:
        if os.path.exists(f'./media/{title}_{a}.{ext}'):
            a += 1
        else:
            fp = f'./media/{title}_{a}.{ext}'
            break

    if format == "None":
        format = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080][ext=mp4]+bestaudio[ext=aac]/best[height<=1080][ext=mp4]/best[ext=mp4]'

    # ダウンロード
    ydl_opts = {
        'format': format,
        'outtmpl': f"./media/{title}_{a}.%(ext)s",
        'noplaylist': True,
        'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        'progress_hooks': [lambda progress_data: progress_hook(progress_data, request_id, database)],
    }
    if ext == 'wav':
        ydl_opts['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav'
            }
        ]
    if ext == 'mp3':
        ydl_opts['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320'
            }
        ]

    update_status(request_id, "downloading", database)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


    # 空白カットが選択されていた場合
    if (silence == "true") and (ext != "mp4") and (ext != "webm"):
        update_status(request_id, "silence_removing", database)
        filepath = os.path.join(currentpath, fp)
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
                if search_end and search_duration:
                    if search_end.group(1) == search_duration.group(1):
                        silence_end_time = float(search_end.group(1))
                        if silence_end_time < 10:
                            silence_time = f"00:00:0{search_end.group(1)}"
                        elif 10 <= silence_end_time < 60:
                            silence_time = f"00:00:{search_end.group(1)}"
                        else:
                            return "空白が1分以上あるため処理に失敗しました。"
                        break
        
        fp = fp[:8] + "cut_" + fp[8:]
        if ext == "mp3":
            command = [
                'ffmpeg',
                '-y',
                '-ss', f'{silence_time}',
                '-i', filepath,
                '-b:a', '320k',
                fp
            ]
        if ext == "wav":
            command = [
                'ffmpeg',
                '-y',
                '-ss', f'{silence_time}',
                '-i', filepath,
                fp
            ]
        subprocess.run(command)

        update_info(request_id, fp, database)
        return
    
    update_info(request_id, fp, database)
    return