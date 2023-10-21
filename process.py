#サーバーがダウン(？)した場合に自動的にプロセスを再起動させるスクリプト
import time
import psutil
import requests
import subprocess


def restart_process():
    flg = 0
    for process in psutil.process_iter():
        try:
            cmd_line = process.cmdline()
            p_id = process.pid
            if ("python3" in cmd_line) and ("main.py" in cmd_line):
                flg += 1
                subprocess.run(["kill", p_id]) #プロセスをキルする
                time.sleep(5)
                subprocess.run(["nohup", "python3", "main.py"]) #プロセスを起動する
        except: #プロセスへのアクセス権がない場合
            pass

    if flg == 0:
        subprocess.run(["nohup", "python3", "main.py"]) #プロセスを起動する


while True:
    try:
        resp = requests.get("http://localhost:5000/media_dl", timeout=(15.0, 15.0))
        if resp.status_code != 200:
            restart_process()
    except:
        restart_process()
    time.sleep(20)