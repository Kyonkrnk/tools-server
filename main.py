import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from router import media_dl, media_dl_download, media_dl_api, media_dl_adm
from router import sus2svg
from router import chart_dl
from router import file_dl

import json
with open("config.json", encoding="utf-8") as f:
    conf = json.load(f)
    host = conf["Host"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[host],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(media_dl.router)
app.include_router(media_dl_download.router)
app.include_router(media_dl_api.router)
app.include_router(media_dl_adm.router)
app.include_router(sus2svg.router)
app.include_router(chart_dl.router)
app.include_router(file_dl.router)


@app.get('/')
def index():
    return FileResponse("templates/index.html")

@app.get('/favicon.ico', include_in_schema=False)
def icon():
    return FileResponse("favicon.ico")

@app.exception_handler(404)
def not_found(request, exc):
    return RedirectResponse('https://www.youtube.com/@kyonchan_net')


if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, host="0.0.0.0", reload=True)