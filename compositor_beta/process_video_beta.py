import os
from concurrent.futures import ProcessPoolExecutor

import cv2

from compositor_beta.create_frame_beta import create_frame_beta
from utils.read_video_frames import read_video_frames_and_fps

def process_frame(args):
    i, frame, back, model = args

    return i, create_frame_beta(frame, back, model)

def process_video_beta(temp_dir, image_path, video_path):
    frames, fps = read_video_frames_and_fps(video_path)
    if not frames:
        raise ValueError("動画を読み込めません")
    
    height, width = frames[0].shape[:2]
    back = cv2.imread(image_path)
    back = cv2.resize(back, (width, height))

    # 書き出し用のwriteクラスを作成
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    processed_video_path = f"{temp_dir}/result.mp4"
    writer = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height), 1)

    # 背景差分を計算するモデル
    model = cv2.createBackgroundSubtractorMOG2()

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        args_list = [(i, frame, back, model) for i, frame in enumerate(frames)]
        for i, output_frame in executor.map(process_video_beta, args_list):
            writer.write(output_frame)

    # 読み込んだ動画と書き出し先の動画を開放
    writer.release()

    return processed_video_path
