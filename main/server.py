from fastapi import FastAPI, Request, UploadFile, File, status
import cv2
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from variables import *

server = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:*",
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

@server.post("/compose")
async def compose_movie(image: UploadFile=File(...), video: UploadFile=File(...)):
    print("heeee", image.filename)
    # 画像ファイルの内容を読み取る
    image_content = await image.read()
    # 動画ファイルの内容を読み取る
    video_content = await video.read()

    return JSONResponse(content={"message": "hello"}, status_code=200)

@server.exception_handler(RequestValidationError)
async def handler(request: Request, exc:RequestValidationError):
    print(exc)
    return JSONResponse(content={}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


if __name__=="__main__":
    import uvicorn
    uvicorn.run(server, host="0.0.0.0", port=8080)