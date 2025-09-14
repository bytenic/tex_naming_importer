from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import Optional, Union

class AddressMode(Enum):
    WRAP = 0
    CLAMP = 1
    MIRROR = 2

class CompressionKind(Enum):
    DEFAULT = 0
    NORMAL_MAP = 1
    MASKS = 2
    GRAYSCALE = 3
    HDR = 4
    ALPHA = 5
    EDITOR_ICON = 6
    DISTANCE_FIELD_FONT = 7
    BC7 = 8

class SRGBMode(Enum):
    ON = 1
    OFF = 0
    AUTO = -1  # 圧縮設定や用途から推定

class SizePreset(IntEnum):
    AUTO = 0
    P256 = 256
    P512 = 512
    P1024 = 1024
    P2048 = 2048
    P4096 = 4096

NumericSize = Union[int, SizePreset]

# =========================
# 設定値コンテナ（専用dataclass）
# =========================
@dataclass
class TextureConfigParams:
    # アドレスモード（U/V はセットで使うのが自然。Zは3D/Cube等で任意）
    address_u: Optional[AddressMode] = None
    address_v: Optional[AddressMode] = None
    address_z: Optional[AddressMode] = None

    # ゲーム中最大サイズ（0 or SizePreset.AUTO で無制限）
    max_in_game: Optional[NumericSize] = None
    enforce_pow2: bool = False

    # 圧縮設定 & sRGB
    compression: Optional[CompressionKind] = None
    srgb: Optional[SRGBMode] = None

    # 共通動作
    save: bool = True
    silent: bool = False


def overwrite_address_uv(params: TextureConfigParams, u: AddressMode, v: AddressMode) -> TextureConfigParams:
    """
    TextureConfigParams の address_u / address_v を“破壊的（in-place）”に上書きします。
    clear_z=True の場合、address_z を None にクリアします（3D/Cube等でU/Vのみ使いたいときに便利）。
    戻り値は同じインスタンス（チェーン用に返すだけ）。
    """
    if not isinstance(params, TextureConfigParams):
        raise TypeError("params must be TextureConfigParams")
    if not isinstance(u, AddressMode) or not isinstance(v, AddressMode):
        raise TypeError("u, v must be AddressMode")

    params.address_u = u
    params.address_v = v
    return params

def _normalize_max_size(v: NumericSize, *, clamp_range: bool = True) -> int:
    """
    SizePreset/int -> int に正規化。0 は無制限。
    clamp_range=True の場合、Unreal想定に合わせて 0 or [16, 4096] にクランプ。
    """
    if isinstance(v, SizePreset):
        px = int(v)
    elif isinstance(v, int):
        px = max(0, v)
    else:
        raise TypeError("max_size must be int or SizePreset")
    if clamp_range and px > 0:
        px = max(16, min(px, 4096))
    return px

def overwrite_max_in_game(
    params: TextureConfigParams,
    max_size: NumericSize,
    *,
    enforce_pow2: Optional[bool] = None,
    clamp_range: bool = True
) -> TextureConfigParams:
    """
    読み込んだ TextureConfigParams の max_in_game を“破壊的”に上書きします。
    - max_size: SizePreset か int（0 は無制限）
    - enforce_pow2: None の場合は既存値を維持。True/False で同時更新。
    - clamp_range: True なら 0 or [16, 16384] にクランプ
    戻り値は同じインスタンス（チェーン用）。
    """
    if not isinstance(params, TextureConfigParams):
        raise TypeError("params must be TextureConfigParams")

    params.max_in_game = _normalize_max_size(max_size, clamp_range=clamp_range)
    if enforce_pow2 is not None:
        params.enforce_pow2 = bool(enforce_pow2)
    return params
