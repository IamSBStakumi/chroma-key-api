import time
import cv2
import os
import sys
import tempfile
import shutil

# Add project root to path
sys.path.append(os.getcwd())

from compositor.process_video import process_video

def benchmark():
    """通常版(/compose)のprocess_videoをベンチマーク"""
    
    # 環境変数を設定
    os.environ['OPENCV_THREAD_NUM'] = '8'
    os.environ['OMP_NUM_THREADS'] = '8'
    os.environ['OPENBLAS_NUM_THREADS'] = '8'
    os.environ['MKL_NUM_THREADS'] = '8'
    
    print(f"OpenCV version: {cv2.__version__}")
    print(f"OpenCV threads: {cv2.getNumThreads()}")
    print(f"OpenCV parallel framework: {cv2.getBuildInformation().split('Parallel framework:')[1].split()[0] if 'Parallel framework:' in cv2.getBuildInformation() else 'Unknown'}")
    print()
    
    # テストアセット
    image_path = "tests/assets/back.png"
    video_path = "tests/assets/input.mp4"
    
    if not os.path.exists(image_path) or not os.path.exists(video_path):
        print("テストアセットが見つかりません")
        return
    
    # 動画情報を取得
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    print(f"動画情報:")
    print(f"  解像度: {width}x{height}")
    print(f"  FPS: {fps}")
    print(f"  フレーム数: {frame_count}")
    print(f"  長さ: {frame_count/fps:.2f}秒")
    print()
    
    # ベンチマーク実行
    temp_dir = tempfile.mkdtemp()
    try:
        print("処理開始...")
        start = time.time()
        
        result_path = process_video(temp_dir, image_path, video_path)
        
        end = time.time()
        elapsed = end - start
        
        print(f"処理完了!")
        print(f"処理時間: {elapsed:.2f}秒")
        print(f"処理速度: {frame_count/elapsed:.2f} FPS")
        print(f"リアルタイム比: {(frame_count/fps)/elapsed:.2f}x")
        print(f"出力ファイル: {result_path}")
        
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path) / (1024 * 1024)
            print(f"ファイルサイズ: {file_size:.2f} MB")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    benchmark()
