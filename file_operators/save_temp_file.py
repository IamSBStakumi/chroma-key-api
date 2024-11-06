import os

import aiofiles
from fastapi import UploadFile

async def save_temp_file(upload_file: UploadFile, temp_dir: str, filename: str):
    destination_path = os.path.join(temp_dir, filename)

    async with aiofiles.open(destination_path, "wb") as out_file:
        while content := await upload_file.read(1024):
            await out_file.write(content)
    
    return destination_path