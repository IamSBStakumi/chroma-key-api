import os
import tempfile
import shutil
import asyncio
from typing import Generator

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from moviepy import VideoFileClip

from file_operators.save_temp_file import save_temp_file
from file_operators.synthesize_audio_file import synthesize_audio_file
from compositor.process_video import process_video

router = APIRouter()

# チャンクサイズ（1MB）
CHUNK_SIZE = 1024 * 1024


def _stream_file_then_cleanup(file_path: str, temp_dir: str) -> Generator[bytes, None, None]:
    """
    ファイルをチャンク単位でストリーミングし、
    全データ送信完了後に一時ディレクトリを削除するジェネレーター。
    StreamingResponse の background_tasks との競合を防ぐ。
    """
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
    finally:
        # ストリーミングが正常終了・例外発生のどちらでも必ず削除
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"一時ディレクトリを削除しました: {temp_dir}")


@router.post("/compose")
async def compose_movie(image: UploadFile = File(...), video: UploadFile = File(...)):
    temp_dir = None
    try:
        # 一時ディレクトリを作成（削除は _stream_file_then_cleanup 内で行う）
        temp_dir = tempfile.mkdtemp()

        image_path = await save_temp_file(image, temp_dir, image.filename)
        video_path = await save_temp_file(video, temp_dir, video.filename)
        print("tempファイル作成")

        try:
            clip_input = VideoFileClip(video_path)
        except OSError as e:
            print(f"動画が開けませんでした: {e}")
            clip_input = None

        print("動画合成開始")
        # 重い処理を別スレッドで実行（イベントループのブロックを回避）
        loop = asyncio.get_event_loop()
        processed_video_path = await loop.run_in_executor(
            None, process_video, temp_dir, image_path, video_path
        )

        # 音声トラックを動画に追加
        if clip_input and clip_input.audio:
            try:
                print("音声合成開始")
                synthesize_audio_file(clip_input, temp_dir, processed_video_path)
                output_path = f"{temp_dir}/synthesized_result.mp4"
            except Exception as e:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                return JSONResponse(content={"error": f"音声追加中にエラーが発生しました: {e}"})
        else:
            output_path = processed_video_path

        # 出力ファイルが作成されているか確認
        if not os.path.exists(output_path):
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return JSONResponse(
                content={"error": "Output file was not created"}, status_code=500
            )

        file_size = os.path.getsize(output_path)
        print(f"ストリーミング開始: {output_path} ({file_size} bytes)")

        # ジェネレーターでストリーミング → 完了後に一時ディレクトリを削除
        return StreamingResponse(
            _stream_file_then_cleanup(output_path, temp_dir),
            media_type="video/mp4",
            headers={
                "Content-Disposition": "attachment; filename=output.mp4",
                "Content-Length": str(file_size),
            },
        )

    except Exception as e:
        # エラー発生時は即座に一時ディレクトリを削除
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

        print("エラーが発生")
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
