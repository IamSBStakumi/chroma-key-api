import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import cv2

from compositor.create_frame import create_frame

def read_video_frames_generator(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"動画を読み込めません: {video_path}")
    
    index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        yield index, frame
        index += 1

    cap.release()
    return

def process_single_frame(i, frame, back):
    result = create_frame(frame, back)

    return i, result

def process_video(temp_dir, image_path, video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("動画を開けません")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30
    
    ret, sample_frame = cap.read()
    cap.release()
    if not ret:
        raise ValueError("動画からフレームを取得できません")
    
    height, width = sample_frame.shape[:2]

    back = cv2.imread(image_path)
    if back is None:
        raise ValueError(f"背景画像が読み込めません: {image_path}")
    back= cv2.resize(back, (width, height))

    # 書き出し用のwriteクラスを作成
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    processed_video_path = f"{temp_dir}/result.mp4"
    writer = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height), True)
    if not writer.isOpened():
        raise IOError("VideoWriterの初期化に失敗しました")

    futures = {}
    # with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
    with ProcessPoolExecutor(max_workers=1) as executor:
        for i, frame in read_video_frames_generator(video_path):
            futures[executor.submit(process_single_frame, i, frame, back)] = i
        
        # 書き出し順保持のための一時バッファ
        buffer = {}
        next_index = 0

        for future in as_completed(futures):
            i, output_frame = future.result()
            if output_frame.shape[:2] != (height, width):
                output_frame = cv2.resize(output_frame, (width, height))

            if output_frame.shape[2] == 4:
                output_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGRA2BGR)

            buffer[i] = output_frame

            # 順序通り書き込む（アウト・オブ・オーダー防止）
            while next_index in buffer:
                writer.write(buffer.pop(next_index))
                next_index += 1

    # 書き出し先の動画を開放
    writer.release()

    return processed_video_path
