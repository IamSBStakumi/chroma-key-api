import subprocess
from moviepy import AudioFileClip, VideoFileClip

def synthesize_audio_file(clip_input: VideoFileClip, temp_dir: str, processed_video_path: str):
    # 音声ファイルを抽出
    audio_path = f"{temp_dir}/audio.mp3"
    clip_input.audio.write_audiofile(audio_path)
    # audio_clip = AudioFileClip(audio_path)

    # 処理済みの動画に音声を追加
    # video_clip = VideoFileClip(processed_video_path)
    # video_clip = video_clip.set_audio(audio_clip)
    # video_clip.write_videofile(f"{temp_dir}/synthesized_result.mp4", codec="mpeg4", bitrate="3000k", audio_codec="aac",fps=clip_input.fps)

    command = [
        "ffmpeg",
        "-y",
        "-i", processed_video_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        "-movflags", "+faststart",  # moovアトムをファイル先頭に配置（ブラウザ再生必須）
        f"{temp_dir}/synthesized_result.mp4"
    ]

    subprocess.run(command, check=True)
