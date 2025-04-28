import os

import aiofiles
from fastapi import UploadFile
from moviepy import AudioFileClip, VideoFileClip

class file_operators:
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    async def save_temp_file(self, upload_file: UploadFile, filename: str):
        destination_path = os.path.join(self.temp_dir, filename)

        async with aiofiles.open(destination_path, "wb") as out_file:
            while content := await upload_file.read(1024):
                await out_file.write(content)

        return destination_path
    
    def synthesize_audio_file(self, clip_input: VideoFileClip, processed_video_path: str):
        # 音声ファイルを抽出
        clip_input.audio.write_audiofile(f"{self.temp_dir}/audio.mp3")
        audio_clip = AudioFileClip(f"{self.temp_dir}/audio.mp3")

        # 処理済みの動画に音声を追加
        video_clip = VideoFileClip(processed_video_path)
        video_clip = video_clip.set_audio(audio_clip)
        video_clip.write_videofile(f"{self.temp_dir}/synthesized_result.mp4", codec="mpeg4", bitrate="3000k", audio_codec="aac",fps=clip_input.fps)

