from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import Optional, Union, Tuple, Dict, List, Tuple
from pathlib import Path
import json

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


AddressPair   = Tuple[AddressMode, AddressMode]
AddressTriple = Tuple[AddressMode, AddressMode, AddressMode]

@dataclass(frozen=True)
class TextureSuffixConfig:
    """
    テクスチャ種別の一覧と、サフィックス → (U,V)/(U,V,W) の対応を保持。
    - texture_type: ["col","msk","nml","mat","cub","flw"] など
    - address_suffix_2d: {"ww": (WRAP, WRAP), "cw": (CLAMP, WRAP), ...}
    - address_suffix_3d: {"ww": (WRAP, WRAP, WRAP), ...}
    """
    texture_type: List[str]
    address_suffix_2d: Dict[str, AddressPair]
    address_suffix_3d: Dict[str, AddressTriple]

    # ---------- 変換ユーティリティ ----------
    @staticmethod
    def _to_addr(x: Union[str, AddressMode]) -> AddressMode:
        if isinstance(x, AddressMode):
            return x
        if isinstance(x, str):
            return AddressMode[x.strip().upper()]
        raise TypeError(f"address element must be str or AddressMode, got: {type(x).__name__}")

    @classmethod
    def _parse_2d(cls, val) -> AddressPair:
        if not isinstance(val, (list, tuple)) or len(val) != 2:
            raise ValueError(f"2D address must be length-2 list/tuple, got: {val!r}")
        return (cls._to_addr(val[0]), cls._to_addr(val[1]))

    @classmethod
    def _parse_3d(cls, val) -> AddressTriple:
        if not isinstance(val, (list, tuple)) or len(val) != 3:
            raise ValueError(f"3D address must be length-3 list/tuple, got: {val!r}")
        return (cls._to_addr(val[0]), cls._to_addr(val[1]), cls._to_addr(val[2]))

    # ---------- dict / JSON I/O ----------
    @classmethod
    def from_dict(cls, data: dict) -> "TextureSuffixConfig":
        if not isinstance(data, dict):
            raise TypeError("root must be a dict")

        # texture_type
        tt = data.get("texture_type")
        if not isinstance(tt, list) or not all(isinstance(x, str) for x in tt):
            raise ValueError("'texture_type' must be a list[str]")

        map2d: Dict[str, AddressPair] = {}
        map3d: Dict[str, AddressTriple] = {}

        # 後方互換: "address_suffix" に 2 or 3 要素が混在していても分類
        raw_mixed = data.get("address_suffix")
        if isinstance(raw_mixed, dict):
            for k, v in raw_mixed.items():
                if isinstance(v, (list, tuple)):
                    if len(v) == 2:
                        map2d[k] = cls._parse_2d(v)
                    elif len(v) == 3:
                        map3d[k] = cls._parse_3d(v)
                    else:
                        raise ValueError(f"address_suffix[{k}] length must be 2 or 3")
                else:
                    raise ValueError(f"address_suffix[{k}] must be list/tuple")

        # 明示セクション形式にも対応: "address_suffix_2d", "address_suffix_3d"
        raw_2d = data.get("address_suffix_2d")
        if isinstance(raw_2d, dict):
            for k, v in raw_2d.items():
                map2d[k] = cls._parse_2d(v)

        raw_3d = data.get("address_suffix_3d")
        if isinstance(raw_3d, dict):
            for k, v in raw_3d.items():
                map3d[k] = cls._parse_3d(v)

        # いずれも無ければエラー
        if not map2d and not map3d:
            raise ValueError("no address suffix mapping found (2D/3D)")

        return cls(texture_type=tt, address_suffix_2d=map2d, address_suffix_3d=map3d)

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "TextureSuffixConfig":
        p = Path(file_path)
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    # 保存は分離形式で人間可読に出力
    def to_dict(self) -> dict:
        out = {
            "texture_type": list(self.texture_type),
        }
        if self.address_suffix_2d:
            out["address_suffix_2d"] = {
                k: [u.name, v.name] for k, (u, v) in self.address_suffix_2d.items()
            }
        if self.address_suffix_3d:
            out["address_suffix_3d"] = {
                k: [u.name, v.name, w.name] for k, (u, v, w) in self.address_suffix_3d.items()
            }
        return out

    def save(self, file_path: Union[str, Path], *, indent: int = 2, ensure_ascii: bool = False) -> None:
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent, ensure_ascii=ensure_ascii)

    # ---------- 利便メソッド ----------
    def has_2d(self, key: str) -> bool:
        return key in self.address_suffix_2d

    def has_3d(self, key: str) -> bool:
        return key in self.address_suffix_3d

    def get_uv(self, key: str) -> AddressPair:
        """
        2Dの(U,V)を返す。3Dしか無いキーに対しては (U,V) を返す（Wは無視）。
        """
        if key in self.address_suffix_2d:
            return self.address_suffix_2d[key]
        if key in self.address_suffix_3d:
            u, v, _ = self.address_suffix_3d[key]
            return (u, v)
        raise KeyError(key)

    def get_uvw(self, key: str) -> AddressTriple:
        """
        3Dの(U,V,W)を返す。2Dしか無いキーに対しては W=V として拡張（慣用的にU/Vを流用）。
        """
        if key in self.address_suffix_3d:
            return self.address_suffix_3d[key]
        if key in self.address_suffix_2d:
            u, v = self.address_suffix_2d[key]
            return (u, v, v)  # 2D→3D拡張の素直なデフォルト
        raise KeyError(key)