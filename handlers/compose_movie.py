import os
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()

def iterFile(file_path: str, temp_dir: str):
    # ジェネレータで少しずつ読み込み。終了後に削除
    try:
        with open(file_path, "rb") as f:
            yield from f
    finally:
        # 一時ファイルを削除
        if os.path.exists(file_path):
            os.remove(file_path)
        # 一時ディレクトリを削除
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@router.post("/compose")
async def compose_movie(background_tasks: BackgroundTasks, image: UploadFile = File(...), video: UploadFile = File(...)):
    try:
        # 一時ディレクトリを手動で作成し、バックグラウンドタスクで削除を予約
        temp_dir = tempfile.mkdtemp()
        background_tasks.add_task(shutil.rmtree, temp_dir)

        try:
            image_path = await save_temp_file(image, temp_dir, image.filename)
            video_path = await save_temp_file(video, temp_dir, video.filename)
            print("tempファイル作成")
            try:
                clip_input = VideoFileClip(video_path)
            except OSError as e:
                print(f"動画が開けませんでした: {e}")
                clip_input = None

            print("動画合成開始")
            processed_video_path = process_video(temp_dir, image_path, video_path)

            # 音声トラックを動画に追加
            if clip_input and clip_input.audio:
                try:
                    print("音声合成開始")
                    synthesize_audio_file(clip_input, temp_dir, processed_video_path)

                    # 音声ありの動画をレスポンスとして返す
                    return StreamingResponse(open(f"{temp_dir}/synthesized_result.mp4", "rb"), media_type="video/mp4")
                except Exception as e:
                    return JSONResponse(content={"error": f"音声追加中にエラーが発生しました: {e}"})

        # 出力ファイルが作成されているか確認
        if not os.path.exists(output_path):
            return JSONResponse(
                content={"error": "Output file was not created"}, status_code=500) 

        return StreamingResponse(iterFile(output_path, temp_dir),
                                    media_type="video/mp4",
                                    headers={
                                        "Content-Disposition": "attachment; filename=output.mp4",
                                        "Content-Length": str(os.path.getsize(output_path))
                                    })

    except Exception as e:
        # エラー発生時は即座に一時ディレクトリを削除（作成されていた場合）
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
        print("エラーが発生")
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
