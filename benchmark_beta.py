
import time
import cv2
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from compositor_beta.create_frame_beta import create_frame_beta

def benchmark():
    # Mock MOG2
    model = cv2.createBackgroundSubtractorMOG2()
    back = cv2.imread("tests/assets/back.png")
    # Simulate a frame
    input_frame = cv2.imread("tests/assets/back.png") 
    
    if back is None:
        print("Back image not found")
        return
    if input_frame is None:
         # Create a dummy frame if video not easy to read frame from
         input_frame = back.copy()

    # Resize to match 1080p for realistic load
    height, width = 1080, 1920
    input_frame = cv2.resize(input_frame, (width, height))
    back = cv2.resize(back, (width, height))

    print("Starting benchmark for 30 frames...")
    start = time.time()
    for _ in range(30): # Simulate 30 frames
        create_frame_beta(input_frame, back, model)
    end = time.time()

    print(f"Time for 30 frames: {end - start:.4f}s")
    print(f"FPS: {30 / (end - start):.2f}")

if __name__ == "__main__":
    benchmark()
