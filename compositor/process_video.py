import os

import cv2

from compositor.create_frame import create_frame
from utils.read_video_frames import read_video_frames_and_fps

def process_video(temp_dir, image_path, video_path):
    frames_iter, fps = read_video_frames_and_fps(video_path)
    if fps <= 0:
        fps = 30

    try:
        first_frame = next(frames_iter)
    except StopIteration:
        raise ValueError("動画からフレームを取得できません")
    
    height, width = first_frame.shape[:2]

    back = cv2.imread(image_path)
    if back is None:
        raise ValueError(f"背景画像が読み込めません: {image_path}")
    back= cv2.resize(back, (width, height))

    processed_video_path = f"{temp_dir}/result.mp4"


    # 書き出し用のwriteクラスを作成
    # H.264コーデック(avc1)を優先、利用できない場合はmp4vにフォールバック
    try:
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        writer = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height), True)
        if not writer.isOpened():
            raise IOError("avc1 codec not available")
    except (IOError, cv2.error):
        print("avc1コーデックが利用できないため、mp4vを使用します")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height), True)
        if not writer.isOpened():
            raise IOError("VideoWriterの初期化に失敗しました")



    # 最初のフレームを処理
    output_frame = create_frame(first_frame, back)
    writer.write(output_frame)

    # 残りのフレームをバッチ処理で並列化
    from concurrent.futures import ThreadPoolExecutor
    
    BATCH_SIZE = 30  # 1秒分のフレーム(30fps想定)をバッチ処理
    batch = []
    
    def process_batch(frames_batch):
        """バッチ内のフレームを並列処理"""
        with ThreadPoolExecutor(max_workers=8) as executor:
            return list(executor.map(lambda f: create_frame(f, back), frames_batch))
    
    for frame in frames_iter:
        batch.append(frame)
        
        if len(batch) >= BATCH_SIZE:
            # バッチを並列処理
            output_frames = process_batch(batch)
            
            # 処理済みフレームを書き込み
            for output_frame in output_frames:
                # サイズ/カラー調整
                if output_frame.shape[:2] != (height, width):
                    output_frame = cv2.resize(output_frame, (width, height))
                
                if output_frame.shape[2] == 4:
                    output_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGRA2BGR)
                
                writer.write(output_frame)
            
            batch = []
    
    # 残りのフレームを処理
    if batch:
        output_frames = process_batch(batch)
        for output_frame in output_frames:
            if output_frame.shape[:2] != (height, width):
                output_frame = cv2.resize(output_frame, (width, height))
            
            if output_frame.shape[2] == 4:
                output_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGRA2BGR)
            
            writer.write(output_frame)

    # 書き出し先の動画を開放
    writer.release()

    return processed_video_path
