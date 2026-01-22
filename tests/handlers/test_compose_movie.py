import os
import shutil
import pytest
from httpx import AsyncClient, ASGITransport
from main.server import server

# テスト用アセットのパス
ASSETS_DIR = "tests/assets"
IMAGE_PATH = os.path.join(ASSETS_DIR, "back.png")
VIDEO_PATH = os.path.join(ASSETS_DIR, "input.mp4")

@pytest.mark.asyncio
async def test_compose_movie_success():
    """正常系: 動画と画像をアップロードして処理された動画が返ってくるかテスト"""
    if not os.path.exists(IMAGE_PATH) or not os.path.exists(VIDEO_PATH):
        pytest.skip("Test assets not found. Run create_assets.py first.")

    transport = ASGITransport(app=server)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {
            "image": ("back.png", open(IMAGE_PATH, "rb"), "image/png"),
            "video": ("input.mp4", open(VIDEO_PATH, "rb"), "video/mp4"),
        }
        
        # ストリーミングレスポンスをテスト
        async with ac.stream("POST", "/compose", files=files) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "video/mp4"
            
            # コンテンツを全て読み切る（ここで途切れたりエラーが出ないか確認）
            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk
            
            assert len(content) > 0
            # MP4ヘッダー(ftyp)が含まれているか簡易チェック
            # assert b"ftyp" in content[:20] 

@pytest.mark.asyncio
async def test_compose_movie_beta_success():
    """Beta版正常系"""
    if not os.path.exists(IMAGE_PATH) or not os.path.exists(VIDEO_PATH):
        pytest.skip("Test assets not found.")

    transport = ASGITransport(app=server)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {
            "image": ("back.png", open(IMAGE_PATH, "rb"), "image/png"),
            "video": ("input.mp4", open(VIDEO_PATH, "rb"), "video/mp4"),
        }
        
        async with ac.stream("POST", "/compose/beta", files=files) as response:
            assert response.status_code == 200
            
            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk
            
            assert len(content) > 0

