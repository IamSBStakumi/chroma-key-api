import os
import queue
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

import cv2

from compositor.create_frame import create_frame
from utils.read_video_frames import read_video_frames_and_fps

# Cloud Run / コンテナ環境の実際のCPU数を取得してワーカー数を決定
_CPU_COUNT = os.cpu_count() or 4
# CPU数の2倍をワーカー数とする（I/Oウェイトを考慮）。上限は16
_MAX_WORKERS = min(_CPU_COUNT * 2, 16)

print(f"[起動] CPU数={_CPU_COUNT}, フレーム処理ワーカー数={_MAX_WORKERS}")


def process_video(temp_dir, image_path, video_path):
    """動画にクロマキー合成を施し、合成済みMP4のパスを返す。"""

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
    back = cv2.resize(back, (width, height))

    processed_video_path = f"{temp_dir}/result.mp4"

    # ========================================
    # ffmpegをパイプモードで起動
    # ========================================
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",                          # 上書き許可
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "bgr24",
        "-r", f"{fps:.2f}",
        "-i", "-",                     # 標準入力から受け取る
        "-c:v", "libx264",
        "-preset", "veryfast",         # Cloud Run向け: 速度優先プリセット
        "-tune", "zerolatency",        # レイテンシ最小化チューニング
        "-crf", "23",                  # 品質（低いほど高品質）
        "-pix_fmt", "yuv420p",         # ブラウザ(HTML5)互換フォーマット
        "-threads", str(_CPU_COUNT),   # ffmpegスレッド数をCPU数に合わせる
        "-movflags", "+faststart",     # moovアトムをファイル先頭に配置（ブラウザ再生必須）
        processed_video_path,
    ]

    try:
        writer_proc = subprocess.Popen(
            ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpegがインストールされていません。システムにffmpegをインストールしてください。"
        )

    # ========================================
    # 非同期3段パイプライン:
    #   reader_thread → read_queue
    #   → ThreadPoolExecutor (create_frame)
    #   → write_queue → writer_thread → ffmpeg stdin
    # ========================================

    # OpenCVの内部スレッドは無効化し、Pythonレベルで並列制御する
    cv2.setNumThreads(0)

    read_queue  = queue.Queue(maxsize=_MAX_WORKERS * 4)
    write_queue = queue.Queue(maxsize=_MAX_WORKERS * 4)

    reading_complete    = threading.Event()
    processing_complete = threading.Event()

    print(f"パイプライン設定: ワーカー数={_MAX_WORKERS}, FPS={fps:.2f}")

    # --- 最初のフレームを同期処理（パイプラインの初期化を帯域外で実施）---
    first_output = create_frame(first_frame, back)
    writer_proc.stdin.write(first_output.tobytes())

    def async_reader():
        """フレームを読み込んで read_queue に積む"""
        frames_read = 0
        try:
            for frame in frames_iter:
                read_queue.put(frame)
                frames_read += 1
        finally:
            print(f"読み込み完了: {frames_read}フレーム")
            reading_complete.set()

    def async_writer():
        """write_queue から取り出してffmpegのstdinに書き込む"""
        frames_written = 0
        while True:
            try:
                frame = write_queue.get(timeout=1)

                # 出力サイズ・チャンネル数の保証
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, (width, height))
                if frame.ndim == 3 and frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                try:
                    writer_proc.stdin.write(frame.tobytes())
                except BrokenPipeError:
                    print("FFmpegのパイプが破損しました。")
                    break

                frames_written += 1
                write_queue.task_done()

            except queue.Empty:
                if processing_complete.is_set() and write_queue.empty():
                    break

        print(f"書き込み完了: {frames_written}フレーム")

    reader_thread = threading.Thread(target=async_reader, daemon=True)
    writer_thread = threading.Thread(target=async_writer, daemon=True)
    reader_thread.start()
    writer_thread.start()

    def frame_generator():
        """read_queue からフレームを取り出すジェネレーター"""
        while True:
            try:
                frame = read_queue.get(timeout=0.1)
                yield frame
                read_queue.task_done()
            except queue.Empty:
                if reading_complete.is_set() and read_queue.empty():
                    break

    # ThreadPoolExecutor.map は入力順序と同じ順序で結果を返す
    total_processed = 0
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        for output_frame in executor.map(
            lambda f: create_frame(f, back), frame_generator()
        ):
            write_queue.put(output_frame)
            total_processed += 1

    print(f"並列処理完了: 合計{total_processed}フレーム")
    processing_complete.set()

    reader_thread.join()
    writer_thread.join()

    # ffmpegへの入力を閉じて終了を待機
    writer_proc.stdin.close()
    writer_proc.wait()

    return processed_video_path
