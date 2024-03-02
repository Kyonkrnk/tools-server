from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

import os
import io
import uuid
import pjsekai.scores
import pjsekai.scores.line


router = APIRouter()

@router.get('/sus2svg')
def sus2svg():
    path = os.path.join("templates/sus2svg.html")
    return FileResponse(path) 

@router.post('/sus2svg')
async def generate(fileInput: UploadFile = File(...)):
    # データを読み込む
    data = await fileInput.read()
    sus_data = io.TextIOWrapper(io.BytesIO(data))

    # 描画する
    self = pjsekai.scores.Score()
    self._init_by_lines([pjsekai.scores.line.Line(line) for line in sus_data.readlines()])
    drawing = pjsekai.scores.Drawing(score=self)

    # 保存する
    name = str(uuid.uuid4())
    drawing.svg().saveas(f"file/{name}.svg")
    
    # 送る
    return FileResponse(f"file/{name}.svg")