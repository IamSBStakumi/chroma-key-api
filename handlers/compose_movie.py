import os
import tempfile
import subprocess

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()

@router.post("/compose")
async def compose_movie(image: UploadFile = File(...), video: UploadFile = File(...)):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, image.filename)
            video_path = os.path.join(temp_dir, video.filename)
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
                "-filter_complex", "[0:v]chromakey=0x00FF00:0.1:0.2[fg];[1:v][fg]overlay=0:0[out]",
                "-map", "[out]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac",
                "-movflags", "+faststart",
                output_path
            ]
            subprocess.run(ffmpeg_cmd, check=True)

            file_size = os.path.getsize(output_path)

            return StreamingResponse(open(output_path, "rb"),
                                     media_type="video/mp4",
                                     headers={
                                         "Content-Disposition": "attachment; filename=output.mp4",
                                         "Content-Length": str(file_size)
                                     })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)