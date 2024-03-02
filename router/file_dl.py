from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get('/file_dl/{filename}')
def file_response(filename: str):
    path = os.path.join("file", filename)
    return FileResponse(path, filename=filename)