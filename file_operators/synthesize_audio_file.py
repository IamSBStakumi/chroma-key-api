from moviepy.editor import AudioFileClip, VideoFileClip

def synthesize_audio_file(clip_input: VideoFileClip, temp_dir: str, processed_video_path: str):
    # 音声ファイルを抽出
    clip_input.audio.write_audiofile(f"{temp_dir}/audio.mp3")
    audio_clip = AudioFileClip(f"{temp_dir}/audio.mp3")

    # 処理済みの動画に音声を追加
    video_clip = VideoFileClip(processed_video_path)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(f"{temp_dir}/synthesized_result.mp4", codec="mpeg4", bitrate="3000k", audio_codec="aac",fps=clip_input.fps)
