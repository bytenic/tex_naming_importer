from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from suffix_config import TextureSuffixConfig

def build_suffix_grid(cfg: TextureSuffixConfig) -> List[List[str]]:
    """
    suffix_index の順で各カテゴリの許容キー一覧を収集し、二次元配列として返す。
    行 = suffix_index の順
    列 = その行（カテゴリ）の候補キー
    """
    grid: List[List[str]] = []
    for cat in cfg.suffix_index:
        grid.append(cfg.allowed_keys(cat))
    return grid