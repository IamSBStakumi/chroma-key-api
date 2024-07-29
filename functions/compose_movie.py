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
            # try:
            #     clip_input = mpe.VideoFileClip(video_path)
            # except OSError as e:
            #     clip_input = None

            loop = asyncio.get_running_loop()
            processed_video_path = await loop.run_in_executor(executor, pv.process_video, temp_dir, image_path, video_path)

            # 音声トラックを動画に追加
            # if clip_input and clip_input.audio:
            #     try:    
            #         synthesized_sound_video = f"{temp_dir}/result.mp4"
            #         clip_input.audio.write_audiofile(f'{temp_dir}/audio.mp3')
            #         clip = mpe.VideoFileClip(processed_video_path)
            #         clip = clip.set_audio(mpe.AudioFileClip(f'{temp_dir}/audio.mp3'))
            #         clip.write_videofile(synthesized_sound_video)
            #     except Exception as e:
            #         print(f"An error occurred: {e}")

            # 画像と動画をレスポンスとして返す
            # if os.path.exists(synthesized_sound_video):
            #     return StreamingResponse(open(synthesized_sound_video, 'rb'), media_type="video/mp4")
            # elif os.path.exists(processed_video_path):
            if os.path.exists(processed_video_path):
                return StreamingResponse(open(processed_video_path, 'rb'), media_type="video/mp4")
            else:
                return JSONResponse(content={"error": "video file not found"})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
