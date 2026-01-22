import cv2
import numpy as np
import os

def create_dummy_assets():
    assets_dir = "tests/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    # Create dummy image (100x100 green background)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:] = (0, 255, 0) # Green
    cv2.imwrite(f"{assets_dir}/back.png", img)
    print("Created back.png")

    # Create dummy video (100x100, 30 frames, red circle moving)
    height, width = 100, 100
    fps = 10
    duration_sec = 1
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_path = f"{assets_dir}/input.mp4"
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    for i in range(fps * duration_sec):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Blue background
        frame[:] = (255, 0, 0)
        # Moving red circle
        cv2.circle(frame, (i * 3, 50), 10, (0, 0, 255), -1)
        out.write(frame)

    out.release()
    print("Created input.mp4")

if __name__ == "__main__":
    create_dummy_assets()
