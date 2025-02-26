import cv2

def read_video_frames_and_fps(video_path):
    video = cv2.VideoCapture(video_path)
    frames = []

    while True:
        success, frame = video.read()
        if not success:
            break
        frames.append(frame)
    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()

    return frames, fps