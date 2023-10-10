import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

from router import media_dl, media_dl_download

app = FastAPI()
app.include_router(media_dl.router)
app.include_router(media_dl_download.router)

@app.get('/')
def index():
    return {"message": "Hello, World!"}

@app.get('/favicon.ico', include_in_schema=False)
def icon():
    return FileResponse("favicon.ico")

if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, host="0.0.0.0", reload=True)