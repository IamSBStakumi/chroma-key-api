import os
from concurrent.futures import ThreadPoolExecutor

import cv2

from compositor_beta.create_frame_beta import create_frame_beta

executor = ThreadPoolExecutor(max_workers=os.cpu_count())

def process_video_beta(temp_dir, image_path, video_path):
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

    # 背景差分を計算するモデル
    model = cv2.createBackgroundSubtractorMOG2()

    # フレーム処理を並行して行う
    def process_and_write_frame(i, movie_frame):
        output_frame = create_frame_beta(movie_frame, back, model)
        return i, output_frame

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
        # _, output_frame = process_and_write_frame(i, movie_frame)
        # フレームをエンコーダに送信
        writer.write(output_frame)

    # 読み込んだ動画と書き出し先の動画を開放
    video.release()
    writer.release()

    return processed_video_path