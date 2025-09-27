
from typing import Optional, Union, Tuple, Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass
import json
from type_define import AddressMode



AddressPair   = Tuple[AddressMode, AddressMode]
AddressTriple = Tuple[AddressMode, AddressMode, AddressMode]

@dataclass(frozen=True)
class TextureSuffixConfig:
    """
    テクスチャ種別の一覧と、サフィックス → (U,V)/(U,V,W) の対応を保持。
    - texture_type: ["col","msk","nml","mat","cub","flw"] など
    - address_suffix_2d: {"ww": (WRAP, WRAP), "cw": (CLAMP, WRAP), ...}
    - address_suffix_3d: {"ww": (WRAP, WRAP, WRAP), ...}
    - suffix_index: ["texture_type", "address_suffix_2d"] など、サフィックスの優先探索順序
    """
    texture_type: List[str]
    address_suffix_2d: Dict[str, AddressPair]
    address_suffix_3d: Dict[str, AddressTriple]
    suffix_index: List[str]
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
        
        suf_index = data.get("suffix_index")
        if not isinstance(suf_index, list) or not all(isinstance(x, str) for x in v):
            raise ValueError("'suffix_index' must be a list[str]")

        return cls(texture_type=tt, address_suffix_2d=map2d, address_suffix_3d=map3d, suffix_index=suf_index)

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
    
    
def load_texture_suffix_config(file_path: Union[str, Path]) -> TextureSuffixConfig:
    """独立ユーティリティ：JSONファイルから TextureSuffixConfig を読み込む。"""
    p = Path(file_path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    try:
        return TextureSuffixConfig.from_dict(data)
    except Exception as e:
        # ファイル名を含むエラーで原因が追いやすいように
        raise ValueError(f"failed to load TextureSuffixConfig from '{p}': {e}") from e

def save_texture_suffix_config(cfg: TextureSuffixConfig, file_path: Union[str, Path], *,
                               indent: int = 2, ensure_ascii: bool = False) -> None:
    """独立ユーティリティ：TextureSuffixConfig を JSON へ保存。"""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(cfg.to_dict(), f, indent=indent, ensure_ascii=ensure_ascii)