import gc
    
import cv2
import numpy as np

# パラメータ設定
contrast_adjustment_value = 1.5  # コントラスト調整値
chroma_key_color = np.uint8([[[0, 255, 0]]])  # クロマキー処理の指定色（緑色）
chroma_key_threshold = 20  # クロマキー処理の閾値
noise_removal_iterations = 50  # ノイズ除去の繰り返し回数

def create_frame(input_frame, back):
    # コントラスト調整
    contrast_image = cv2.convertScaleAbs(input_frame, alpha=contrast_adjustment_value, beta=0)

    # クロマキー処理と二値化
    hsv_chroma_key_color = cv2.cvtColor(chroma_key_color, cv2.COLOR_BGR2HSV)
    lower_green = np.array([hsv_chroma_key_color[0][0][0] - chroma_key_threshold, 50, 50])
    upper_green = np.array([hsv_chroma_key_color[0][0][0] + chroma_key_threshold, 255, 255])
    hsv_image = cv2.cvtColor(contrast_image, cv2.COLOR_BGR2HSV)
    chroma_key_image = cv2.inRange(hsv_image, lower_green, upper_green)
    mask_image = cv2.bitwise_not(chroma_key_image)

    # ノイズ除去
    transparent_image = cv2.cvtColor(input_frame, cv2.COLOR_BGR2BGRA)  # RGBA形式に変換
    transparent_image[:, :, 3] = mask_image  # アルファチャンネルにマスク画像を設定

    output_frame = cv2.convertScaleAbs(
        back * (1 - (transparent_image[:, :, 3:] / 255.0)) + transparent_image[:, :, :3] * (transparent_image[:, :, 3:] / 255.0)
    )

    # 明示的に不要なデータを開放
    del contrast_image, hsv_image, chroma_key_image, mask_image, transparent_image
    # ガベージコレクション実行
    gc.collect()

    return output_frame
