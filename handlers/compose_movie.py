import os
import tempfile
import subprocess

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()

def iterFile(file_path: str):
    with open(file_path, "rb") as f:
        yield from f        # 少しずつストリーミングを返す

@router.post("/compose")
async def compose_movie(image: UploadFile = File(...), video: UploadFile = File(...)):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
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
                "[1:v][0:v]scale2ref=w=iw:h=ih[bg][fg]"         # 画像を動画のサイズと一致するようリサイズ
                "[fg]chromakey=0x00FF00:0.1:0.2[ck];"           # クロマキー処理
                "[bg][fg]overlay=0:0[out]",                     # 背景中央に画像を配置
                "-map", "[out]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac",
                "-movflags", "+faststart",
                output_path
            ]
            subprocess.run(ffmpeg_cmd, check=True)

            return StreamingResponse(iterFile(output_path),
                                     media_type="video/mp4",
                                     headers={
                                         "Content-Disposition": "attachment; filename=output.mp4",
                                         "Content-Length": str(os.path.getsize(output_path))
                                     })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)