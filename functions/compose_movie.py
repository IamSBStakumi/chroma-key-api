from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from concurrent.futures import ThreadPoolExecutor
from functions import process_video as pv
import tempfile
import os
import asyncio
import aiofiles

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)

async def save_temp_file(upload_file: UploadFile, destination_path: str):
    async with aiofiles.open(destination_path, "wb") as out_file:
        while content := await upload_file.read(1024):
            await out_file.write(content)

@router.post("/compose")
async def compose_movie(image: UploadFile=File(...), video: UploadFile=File(...)):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, image.filename)
            video_path=os.path.join(temp_dir, video.filename)

            await save_temp_file(image, image_path)
            await save_temp_file(video, video_path)

            loop= asyncio.get_event_loop()
            processed_video_path = await loop.run_in_executor(executor, pv.process_video, temp_dir, image_path, video_path)

            # 音声トラックを動画に追加
            # clip = mpe.VideoFileClip("outputs/chroma.mp4").subclip()
            # clip.write_videofile("outputs/result.mp4", audio="outputs/audio.mp3")

            # 画像と動画をレスポンスとして返す
            return StreamingResponse(open(processed_video_path, 'rb'), media_type="video/mp4")

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
