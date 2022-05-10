from pathlib import Path
from typing import Optional
import traceback
import json

from fastapi import FastAPI, WebSocket, File, UploadFile
from fastapi.responses import FileResponse

from parser import parse

app = FastAPI()

jsons = Path('.')
frontend = Path('dist/')

@app.get("/")
async def root():
    return FileResponse(frontend / 'index.html')


@app.get("/main.js")
async def js():
    return FileResponse(frontend / 'main.js')

@app.get("/main.css")
async def css():
    return FileResponse(frontend / 'main.css')

@app.post("/upload")
async def upload_data(file: UploadFile = File(...)):
    code = b''
    while content := await file.read(1024):  # async read chunk
        code += content  # async write chunk

    # print(code.decode('utf-8'))
    nodes, edges = parse(code.decode('utf-8'))
    return {
        "type": "graph",
        "error": None,
        "values": {
            "code": code.decode('utf-8'),
            "nodes": nodes,
            "edges": edges,
        }
    }
