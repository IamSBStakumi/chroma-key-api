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

    # 書き出し用のwriteクラスを作成
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    processed_video_path = f"{temp_dir}/result.mp4"
    writer = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height), True)
    if not writer.isOpened():
        raise IOError("VideoWriterの初期化に失敗しました")

    # 最初のフレームを処理
    output_frame = create_frame(first_frame, back)
    writer.write(output_frame)

    # 残りのフレームを処理
    for frame in frames_iter:
        output_frame = create_frame(frame, back)
        
        # サイズ/カラー調整 (create_frameがRGBA返す場合)
        # create_frame内でastype(np.uint8)とサイズ整合性は保証されているはずだが
        # process_video.pyの元のコードにresize/cvtColorがあったので念の為保持
        if output_frame.shape[:2] != (height, width):
            output_frame = cv2.resize(output_frame, (width, height))

        if output_frame.shape[2] == 4:
            output_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGRA2BGR)
            
        writer.write(output_frame)

    # 書き出し先の動画を開放
    writer.release()

    return processed_video_path
