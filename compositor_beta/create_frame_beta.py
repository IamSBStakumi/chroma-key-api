import gc
    
import cv2
import numpy as np

# パラメータ設定
contrast_adjustment_value = 1.5  # コントラスト調整値

def create_frame_beta(input_frame, back, model):
    # コントラスト調整
    contrast_image = cv2.convertScaleAbs(input_frame, alpha=contrast_adjustment_value, beta=0)

    # HSVイメージに変換後、前景領域のマスクを作成
    hsv_image = cv2.cvtColor(contrast_image, cv2.COLOR_BGR2HSV)
    mask_image = model.apply(hsv_image)

    transparent_image = cv2.cvtColor(input_frame, cv2.COLOR_BGR2BGRA)  # RGBA形式に変換
    transparent_image[:, :, 3] = mask_image  # アルファチャンネルにマスク画像を設定

    output_frame = cv2.convertScaleAbs(
        back * (1 - (transparent_image[:, :, 3:] / 255.0)) + transparent_image[:, :, :3] * (transparent_image[:, :, 3:] / 255.0)
    )

    # 明示的に不要なデータを開放
    del contrast_image, hsv_image, mask_image, transparent_image
    # ガベージコレクション実行
    gc.collect()

    return output_frame
