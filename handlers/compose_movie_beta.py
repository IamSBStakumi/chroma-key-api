import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from moviepy import VideoFileClip

from file_operators.save_temp_file import save_temp_file
from file_operators.synthesize_audio_file import synthesize_audio_file
from compositor_beta.process_video_beta import process_video_beta

router = APIRouter()

@router.post("/compose/beta")
async def compose_movie_beta(image: UploadFile = File(...), video: UploadFile = File(...)):
    try:
        print("ベータ版のAPIが呼び出されました")
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = await save_temp_file(image, temp_dir, image.filename)
            video_path = await save_temp_file(video, temp_dir, video.filename)
            print("tempファイル作成")
            try:
                clip_input = VideoFileClip(video_path)
            except OSError as e:
                print(f"動画が開けませんでした: {e}")
                clip_input = None

            print("動画合成開始")
            processed_video_path = process_video_beta(temp_dir, image_path, video_path)

            # 音声トラックを動画に追加
            if clip_input and clip_input.audio:
                try:
                    print("音声合成開始")
                    synthesize_audio_file(clip_input, temp_dir, processed_video_path)

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
        print("エラーが発生")
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
