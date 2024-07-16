from fastapi import FastAPI, Request, UploadFile, File, status
import cv2
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
import tempfile
import os
import shutil

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

# パラメータ設定
contrast_adjustment_value = 1.5  # コントラスト調整値
chroma_key_color = np.uint8([[[0, 255, 0]]])  # クロマキー処理の指定色（緑色）
chroma_key_threshold = 20  # クロマキー処理の閾値
noise_removal_iterations = 50  # ノイズ除去の繰り返し回数

@server.get("/")
async def root():
    return {"message": "Hello World"}

@server.post("/compose")
async def compose_movie(image: UploadFile=File(...), video: UploadFile=File(...)):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 画像ファイルを一時ディレクトリに保存
            image_path = os.path.join(temp_dir, image.filename)
            with open(image_path, "wb") as image_file:
                shutil.copyfileobj(image.file, image_file)

            # 動画ファイルを一時ディレクトリに保存
            video_path=os.path.join(temp_dir, video.filename)
            with open(video_path, "wb") as video_file:
                shutil.copyfileobj(video.file,video_file)

            video = cv2.VideoCapture(video_path)
            width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            back = cv2.imread(image_path)
            back = cv2.resize(back, (width, height))

            # 動画の総フレーム数を取得
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

            # 書き出し用のwriteクラスを作成
            fps = video.get(cv2.CAP_PROP_FPS)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            processed_video_path=f'{temp_dir}/result.mp4'
            writer = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height), 1)

            # 音声トラック書き出し
            # clip_input = mpe.VideoFileClip(path)
            # clip_input.audio.write_audiofile(f'{temp_dir}/result.mp4')
            # print("音声トラック読み込み")
            def create_frame(input_frame):
                # コントラスト調整
                contrast_image = cv2.convertScaleAbs(input_frame, alpha=contrast_adjustment_value, beta=0)

                # クロマキー処理と二値化
                hsv_chroma_key_color = cv2.cvtColor(chroma_key_color, cv2.COLOR_BGR2HSV)
                lower_green = np.array([hsv_chroma_key_color[0][0][0] - chroma_key_threshold, 50, 50])
                upper_green = np.array([hsv_chroma_key_color[0][0][0] + chroma_key_threshold, 255, 255])
                hsv_image = cv2.cvtColor(contrast_image, cv2.COLOR_BGR2HSV)
                chroma_key_image = cv2.inRange(hsv_image, lower_green, upper_green)
                mask_image = cv2.bitwise_not(chroma_key_image)

                # ノイズ除去
                transparent_image = cv2.cvtColor(input_frame, cv2.COLOR_BGR2BGRA) # RGBA形式に変換
                transparent_image[:, :, 3] = mask_image # アルファチャンネルにマスク画像を設定
                
                # 背景画像に重ねる
                foreground = transparent_image[:, :, :3]
                alpha = transparent_image[:, :, 3:] / 255.0
                background = back.copy()

                output_frame = cv2.convertScaleAbs(background * (1 - alpha) + foreground * alpha)

                return output_frame

            for i in range(frame_count):
                success, movie_frame = video.read()

                if not success:
                    break
                
                chroma_frame = create_frame(movie_frame)

                # 画像を動画へ書き出し
                writer.write(chroma_frame)

            # 読み込んだ動画と書き出し先の動画を開放
            video.release()
            writer.release()

            # 音声トラックを動画に追加
            # clip = mpe.VideoFileClip("outputs/chroma.mp4").subclip()
            # clip.write_videofile("outputs/result.mp4", audio="outputs/audio.mp3")

            # 画像と動画をレスポンスとして返す
            return StreamingResponse(open(processed_video_path, 'rb'), media_type="video/mp4")

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@server.exception_handler(RequestValidationError)
async def handler(request: Request, exc:RequestValidationError):
    print(exc)
    return JSONResponse(content={}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


# if __name__=="__main__":
#     import uvicorn
#     uvicorn.run(server, host="0.0.0.0", port=8080)