import cv2
import numpy as np

# ========================================================
# モジュールロード時に1回だけ計算する定数（全フレーム共通）
# ========================================================

# コントラスト調整値
_CONTRAST_ALPHA = 1.5

# クロマキー色（緑）をHSVに変換してH値を取得
_CHROMA_KEY_COLOR_BGR = np.uint8([[[0, 255, 0]]])
_CHROMA_KEY_THRESHOLD = 20
_hsv_tmp = cv2.cvtColor(_CHROMA_KEY_COLOR_BGR, cv2.COLOR_BGR2HSV)
_TARGET_H = int(_hsv_tmp[0][0][0])

# HSV閾値の上下限（全フレーム同一値）
_LOWER_GREEN = np.array([max(_TARGET_H - _CHROMA_KEY_THRESHOLD, 0),   50,  50], dtype=np.uint8)
_UPPER_GREEN = np.array([min(_TARGET_H + _CHROMA_KEY_THRESHOLD, 179), 255, 255], dtype=np.uint8)

# モルフォロジーカーネル（全フレーム同一）
_MORPH_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))


def create_frame(input_frame, back):
    """1フレームのクロマキー合成を行う。定数は事前計算済みのモジュール変数を使用。"""

    # コントラスト調整
    contrast_image = cv2.convertScaleAbs(input_frame, alpha=_CONTRAST_ALPHA, beta=0)

    # HSV変換 → クロマキーマスク生成
    hsv_image = cv2.cvtColor(contrast_image, cv2.COLOR_BGR2HSV)
    chroma_key_mask = cv2.inRange(hsv_image, _LOWER_GREEN, _UPPER_GREEN)

    # ノイズ除去（事前計算済みカーネルを使用）
    clean_mask = cv2.morphologyEx(chroma_key_mask, cv2.MORPH_OPEN,  _MORPH_KERNEL)
    clean_mask = cv2.morphologyEx(clean_mask,      cv2.MORPH_CLOSE, _MORPH_KERNEL)

    # アルファマスク（0=背景, 255=前景）+ エッジをぼかす
    alpha_mask = cv2.GaussianBlur(255 - clean_mask, (5, 5), 0)

    # uint16 整数演算でアルファブレンド（float64より高速）
    alpha    = alpha_mask[..., None].astype(np.uint16)
    bg_alpha = np.uint16(255) - alpha

    output_16 = (contrast_image.astype(np.uint16) * alpha
                 + back.astype(np.uint16) * bg_alpha) // 255

    return output_16.astype(np.uint8)

