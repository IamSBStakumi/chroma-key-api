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
    # 利用可能なコーデックを順番に試す
    codecs_to_try = [
        ("X264", "x264"),  # H.264 (最も互換性が高い)
        ("H264", "h264"),  # H.264の別名
        ("mp4v", "mp4v"),  # MPEG-4 (フォールバック)
    ]
    
    writer = None
    used_codec = None
    
    for codec_name, codec_code in codecs_to_try:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec_code)
            writer = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height), True)
            if writer.isOpened():
                used_codec = codec_name
                print(f"使用コーデック: {codec_name}")
                break
            else:
                writer.release()
        except Exception as e:
            print(f"{codec_name}コーデック初期化失敗: {e}")
            continue
    
    if not writer or not writer.isOpened():
        raise IOError("利用可能なVideoWriterコーデックが見つかりません")



    # 最初のフレームを処理
    output_frame = create_frame(first_frame, back)
    writer.write(output_frame)

    # 残りのフレームをバッチ処理で並列化
    from concurrent.futures import ThreadPoolExecutor
    import time
    
    # OpenCVのスレッド数を明示的に設定
    cv2.setNumThreads(0)  # 0 = 自動(全コア使用)
    
    # バッチサイズをfpsに応じて動的に調整
    # 低fpsの動画でも並列処理が効くように、最小30フレームを確保
    BATCH_SIZE = max(30, int(fps * 2))  # 2秒分のフレーム、最小30
    MAX_WORKERS = 16  # スレッド数を増やしてI/O待機時間をカバー
    batch = []
    
    print(f"並列処理設定: バッチサイズ={BATCH_SIZE}, ワーカー数={MAX_WORKERS}, FPS={fps}")
    
    total_frames_processed = 0
    batch_count = 0
    
    def process_batch(frames_batch):
        """バッチ内のフレームを並列処理"""
        batch_start = time.time()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            result = list(executor.map(lambda f: create_frame(f, back), frames_batch))
        batch_time = time.time() - batch_start
        print(f"バッチ処理: {len(frames_batch)}フレーム, {batch_time:.2f}秒, {len(frames_batch)/batch_time:.1f} FPS")
        return result

    # 非同期書き込み用のキューとスレッド
    import queue
    import threading
    
    write_queue = queue.Queue(maxsize=200)  # 最大200フレームをバッファ
    write_complete = threading.Event()
    
    def async_writer():
        """別スレッドでフレームを書き込み"""
        frames_written = 0
        while True:
            try:
                frame = write_queue.get(timeout=1)
                if frame is None:  # 終了シグナル
                    break
                
                # サイズ/カラー調整
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, (width, height))
                
                if frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                writer.write(frame)
                frames_written += 1
                write_queue.task_done()
            except queue.Empty:
                continue
        
        print(f"書き込み完了: {frames_written}フレーム")
        write_complete.set()
    
    # 書き込みスレッドを開始
    writer_thread = threading.Thread(target=async_writer, daemon=True)
    writer_thread.start()
    
    for frame in frames_iter:
        batch.append(frame)
        
        if len(batch) >= BATCH_SIZE:
            # バッチを並列処理
            batch_count += 1
            output_frames = process_batch(batch)
            total_frames_processed += len(batch)
            
            # 処理済みフレームをキューに追加(非同期書き込み)
            for output_frame in output_frames:
                write_queue.put(output_frame)
            
            batch = []
    
    # 残りのフレームを処理
    if batch:
        batch_count += 1
        output_frames = process_batch(batch)
        total_frames_processed += len(batch)
        for output_frame in output_frames:
            write_queue.put(output_frame)

    print(f"並列処理完了: 合計{total_frames_processed}フレーム, {batch_count}バッチ")
    
    # 書き込みスレッドの完了を待つ
    write_queue.put(None)  # 終了シグナル
    write_queue.join()
    write_complete.wait(timeout=60)

    # 書き出し先の動画を開放
    writer.release()

    return processed_video_path
