import os
from concurrent.futures import ProcessPoolExecutor

import cv2

from compositor.create_frame import create_frame
from utils.read_video_frames import read_video_frames_and_fps

def process_frame(args):
    i, frame, back = args

    return i, create_frame(frame, back)

def process_video(temp_dir, image_path, video_path):
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

    results = []
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        args_list = [(i, frame, back) for i, frame in enumerate(frames)]
        results = list(executor.map(process_frame, args_list))
        
    for i, output_frame in sorted(results, key=lambda x: x[0]):
        writer.write(output_frame)

    # 書き出し先の動画を開放
    writer.release()

    return processed_video_path
