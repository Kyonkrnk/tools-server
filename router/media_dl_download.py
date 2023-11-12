from fastapi import APIRouter

import os
import re
import yt_dlp
import subprocess
import router.media_dl_json as media_dl_json

currentpath = os.getcwd()
router = APIRouter()

def update_status(request_id, status):
    write_data = {
        "status": status
    }
    media_dl_json.write_json(request_id, write_data)

def update_info(request_id, path):
    write_data = {
        "path": path,
        "status": "yes",
        "download_url": f"/media_dl/api/download/{request_id}"
    }
    media_dl_json.write_json(request_id, write_data)

pattern = re.compile(r'(\d+\.\d+)%')
def progress_hook(progress_data, request_id):
    if progress_data['status'] == 'downloading':
        percent = re.search(pattern, progress_data['_percent_str'])
        if percent != None:
            info = {
                "percent": percent.group(1)
            }
            media_dl_json.write_json(request_id, info)



@router.get('/media_dl/download/{request_id}')
def download_media(request_id: str):  
    info = media_dl_json.load_json(request_id)
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
        'outtmpl': f'./media/{title}.{format}',
        'noplaylist': True,
        'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        'progress_hooks': [lambda progress_data: progress_hook(progress_data, request_id)],
    }
    if format == 'wav':
        ydl_opts['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav'
            }
        ]
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['outtmpl'] = f'./media/{title}'
    if format == 'mp3':
        ydl_opts['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320'
            }
        ]
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['outtmpl'] = f'./media/{title}'

    update_status(request_id, "downloading")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


    # 空白カットが選択されていた場合
    if (silence == True) and (format != "mp4"):
        update_status(request_id, "silence_removing")
        filepath = os.path.join(currentpath, "media", f"{title}.{format}")
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
        os.remove(f"media/{title}.{format}")

        # infoファイルを更新する
        update_info(request_id, f"media/cut_{title}.{format}")
        return
    
    # infoファイルを更新する
    update_info(request_id, f"media/{title}.{format}")
    return