import asyncio
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

import aiofiles
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from moviepy.editor import AudioFileClip, VideoFileClip

from functions import init_progress as ip
from functions import process_video as pv

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)


async def save_temp_file(upload_file: UploadFile, destination_path: str):
    async with aiofiles.open(destination_path, "wb") as out_file:
        while content := await upload_file.read(1024):
            await out_file.write(content)


@router.post("/compose")
async def compose_movie(image: UploadFile = File(...), video: UploadFile = File(...)):
    ip.init_progress()
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, image.filename)
            video_path = os.path.join(temp_dir, video.filename)

            await save_temp_file(image, image_path)
            await save_temp_file(video, video_path)
            try:
                clip_input = VideoFileClip(video_path)
            except OSError as e:
                print(f"動画が開けませんでした: {e}")
                clip_input = None

            loop = asyncio.get_running_loop()
            processed_video_path = await loop.run_in_executor(
                executor, pv.process_video, temp_dir, image_path, video_path
            )

            # 音声トラックを動画に追加
            if clip_input and clip_input.audio:
                try:
                    # 音声ファイルを抽出
                    clip_input.audio.write_audiofile(f"{temp_dir}/audio.mp3")
                    audio_clip = AudioFileClip(f"{temp_dir}/audio.mp3")
                    # 処理済みの動画に音声を追加
                    video_clip = VideoFileClip(processed_video_path)
                    video_clip = video_clip.set_audio(audio_clip)
                    video_clip.write_videofile(f"{temp_dir}/synthesized_result.mp4")

                    # 音声ありの動画をレスポンスとして返す
                    return StreamingResponse(open(f"{temp_dir}/synthesized_result.mp4", "rb"), media_type="video/mp4")
                except Exception as e:
                    return JSONResponse(content={"error": f"音声追加中にエラーが発生しました: {e}"})

            # 音声なしの動画をレスポンスとして返す
            if os.path.exists(processed_video_path):
                return StreamingResponse(open(processed_video_path, "rb"), media_type="video/mp4")
            else:
                return JSONResponse(content={"error": "video file not found"})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
