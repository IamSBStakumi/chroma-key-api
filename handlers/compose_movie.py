import os
import tempfile
import subprocess
import shutil

from fastapi import APIRouter, File, UploadFile
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
async def compose_movie(image: UploadFile = File(...), video: UploadFile = File(...)):
    temp_dir = tempfile.mkdtemp()  # 一時ディレクトリを作成
    try:
        image_ext = os.path.splitext(image.filename)[1]         # 画像ファイルの拡張子を取得
        video_ext = os.path.splitext(video.filename)[1]         # 動画ファイルの拡張子を取得

        image_path = os.path.join(temp_dir, f"background{image_ext}")
        video_path = os.path.join(temp_dir, f"input{video_ext}")
        output_path = os.path.join(temp_dir, "output.mp4")

        # 一時保存
        with open(image_path, "wb") as f:
            f.write(await image.read())
        with open(video_path, "wb") as f:
            f.write(await video.read())

        # ffmpegコマンドでクロマキー合成
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", video_path, "-i", image_path,
            "-filter_complex", 
            "[1:v][0:v]scale2ref=iw:ih[bg][fg];"
            "[fg]chromakey=0x00FF00:0.1:0.2[ck];"
            "[bg][ck]overlay=0:0[out]",
            "-map", "[out]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac",
            "-movflags", "+faststart",
            output_path
        ]

        ## ffmpegを実行(標準出力と標準エラーをログ出力)
        try:
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            print("stdout: e.stdout")
            print("stderr: e.stderr")
            return JSONResponse(content={"error": f"FFmpeg error: {e.stderr}"}, status_code=500)

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
        return JSONResponse(content={"error": str(e)}, status_code=500)