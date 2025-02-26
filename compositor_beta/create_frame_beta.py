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

    # RGBA画像作成
    transparent_image = cv2.cvtColor(input_frame, cv2.COLOR_BGR2BGRA)  # RGBA形式に変換
    transparent_image[:, :, 3] = mask_image  # アルファチャンネルにマスク画像を設定
    
    # 背景と合成
    alpha = (transparent_image[:, :, 3] / 255.0)[..., None]
    output_frame = (back * (1 - alpha) + transparent_image[:, :, :3] * alpha).astype(np.uint8)

    # メモリ開放
    del contrast_image, hsv_image, mask_image, transparent_image
    gc.collect()

    return output_frame
