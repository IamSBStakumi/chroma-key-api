import cv2

def read_video_frames_and_fps(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"動画を読み込めません: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    
    def frame_generator():
        try:
            while True:
                success, frame = cap.read()
                if not success:
                    break
                yield frame
        finally:
            cap.release()

    return frame_generator(), fps