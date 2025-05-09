import gc
    
import cv2
import numpy as np

# パラメータ設定
contrast_adjustment_value = 1.5  # コントラスト調整値
chroma_key_color = np.uint8([[[0, 255, 0]]])  # クロマキー処理の指定色（緑色）
chroma_key_threshold = 20  # クロマキー処理の閾値

def create_frame(input_frame, back):
    # コントラスト調整
    contrast_image = cv2.convertScaleAbs(input_frame, alpha=contrast_adjustment_value, beta=0)

    # クロマキー処理と二値化
    hsv_chroma_key_color = cv2.cvtColor(chroma_key_color, cv2.COLOR_BGR2HSV)
    target_h = hsv_chroma_key_color[0][0][0]
    lower_h = max(target_h - chroma_key_threshold, 0)
    upper_h = min(target_h + chroma_key_threshold, 179)

    lower_green = np.array([lower_h, 50, 50])
    upper_green = np.array([upper_h, 255, 255])
    
    hsv_image = cv2.cvtColor(contrast_image, cv2.COLOR_BGR2HSV)
    chroma_key_mask = cv2.inRange(hsv_image, lower_green, upper_green)

    # ノイズ除去
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    clean_mask = cv2.morphologyEx(chroma_key_mask, cv2.MORPH_OPEN, kernel)
    clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel)

    # アルファマスクの作成
    alpha_mask = 255 - clean_mask
    alpha_mask = cv2.GaussianBlur(alpha_mask, (5,5), 0)

    # RGBA画像作成
    transparent_image = cv2.cvtColor(contrast_image, cv2.COLOR_BGR2BGRA)
    transparent_image[:, :, 3] = alpha_mask  # アルファチャンネル適用

    # 背景と合成
    alpha = (transparent_image[:, :, 3] / 255.0)[..., None]
    output_frame = (back * (1 - alpha) + transparent_image[:, :, :3] * alpha).astype(np.uint8)

    #メモリ開放
    # del contrast_image, hsv_image, chroma_key_mask, mask_image, transparent_image
    # gc.collect()

    return output_frame
