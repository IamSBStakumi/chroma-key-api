import gc
import os
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

executor = ThreadPoolExecutor(max_workers=os.cpu_count())

# パラメータ設定
contrast_adjustment_value = 1.5  # コントラスト調整値
chroma_key_color = np.uint8([[[0, 255, 0]]])  # クロマキー処理の指定色（緑色）
chroma_key_threshold = 20  # クロマキー処理の閾値
noise_removal_iterations = 50  # ノイズ除去の繰り返し回数


def process_video(temp_dir, image_path, video_path):
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
    processed_video_path = f"{temp_dir}/result.mp4"
    writer = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height), 1)

    # フレーム処理を並行して行う
    def process_and_write_frame(i, movie_frame):
        output_frame = create_frame(movie_frame)
        return i, output_frame

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
        transparent_image = cv2.cvtColor(input_frame, cv2.COLOR_BGR2BGRA)  # RGBA形式に変換
        transparent_image[:, :, 3] = mask_image  # アルファチャンネルにマスク画像を設定

        # 背景画像に重ねる
        # foreground = transparent_image[:, :, :3]
        # alpha = transparent_image[:, :, 3:] / 255.0
        # background = back.copy()

        # output_frame = cv2.convertScaleAbs(background * (1 - alpha) + foreground * alpha)
        output_frame = cv2.convertScaleAbs(
            back * (1 - (transparent_image[:, :, 3:] / 255.0)) + transparent_image[:, :, :3] * (transparent_image[:, :, 3:] / 255.0)
        )

        # 明示的に不要なデータを開放
        del contrast_image, hsv_image, chroma_key_image, mask_image, transparent_image
        # ガベージコレクション実行
        gc.collect()

        return output_frame

    futures = []
    for i in range(frame_count):
        success, movie_frame = video.read()
        if not success:
            break

        # frameごとの処理をsubmit
        futures.append(executor.submit(process_and_write_frame, i, movie_frame))

    # すべての処理が終わるのを待つ
    for future in futures:
        i, output_frame = future.result()
        # フレームをエンコーダに送信
        writer.write(output_frame)

    # 読み込んだ動画と書き出し先の動画を開放
    video.release()
    writer.release()

    return processed_video_path
