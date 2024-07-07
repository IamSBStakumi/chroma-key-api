from fastapi import FastAPI, UploadFile
import cv2
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from variables import *

server = FastAPI()

origins = [
    "http://localhost:3000",
    "https://chroma-key-front-spbb34bsma-dt.a.run.app",
]

server.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["get", "post"],
    allow_headers=["*"]
)

# リクエストボディの型定義
class Param(BaseModel):
    contrast_adjustment_value: float
    chroma_key_color: list[int]
    chroma_key_threshold: int
    noise_removal_iterations: int

@server.get("/")
async def root():
    return {"message": "Hello World"}

@server.post("/create")
async def create_movie(image: UploadFile, video: UploadFile):
    # 画像ファイルの内容を読み取る
    image_content = await image.read()
    # 動画ファイルの内容を読み取る
    video_content = await video.read()

    return {"message", f'{image.filename}{video.filename}'}


if __name__=="__main__":
    import uvicorn
    uvicorn.run(server, host="0.0.0.0", port=8080)