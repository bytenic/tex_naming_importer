from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from suffix_config import TextureSuffixConfig


@dataclass
class ValidationResult:
    ok: bool
    # 行インデックス → 実際に一致したサフィックス（元の大小保持）
    matches_by_row: List[Optional[str]] = None
    # 失敗時の情報
    error: Optional[str] = None
    # 失敗した行（カテゴリ）インデックス。0 が先頭行（＝ suffix_index の先頭）
    failed_row_index: Optional[int] = None
    # 解析に使った元配列
    suffix_list: Optional[List[str]] = None

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

def validate_suffixes(
    suffix_list: List[str],
    suffix_grid: List[List[str]],
) -> ValidationResult:
    """
    Suffix命名規則の検証を行う:
      - suffix_list はサフィックスのみ（テクスチャ名等は含まれない）
      - 行数（=カテゴリ数）とサフィックス数が一致しない場合は即エラー
      - 行 i の許容キー群 (suffix_grid[i]) に対して suffix_list[i] を大小無視で照合
      - すべて一致で OK、どこか1つでも不一致なら即 NG
    """
    # 行数（カテゴリ数）とサフィックス数の厳密一致を要求
    if len(suffix_list) != len(suffix_grid):
        return ValidationResult(
            ok=False,
            error=f"サフィックス数と規則行数が一致しません。expected={len(suffix_grid)}, actual={len(suffix_list)}",
            failed_row_index=None,
            suffix_list=suffix_list,
        )

    # 各行 i について、suffix_list[i] が suffix_grid[i] の許容キーに含まれるか検証
    for i, (token_orig, allowed_row) in enumerate(zip(suffix_list, suffix_grid)):
        token_l = token_orig.lower()
        allowed_lower = {k.lower() for k in allowed_row or []}
        if token_l not in allowed_lower:
            preview = ", ".join(list(allowed_lower)[:8]) + ("..." if len(allowed_lower) > 8 else "")
            return ValidationResult(
                ok=False,
                error=f"行 {i} のサフィックス '{token_orig}' は許容値に含まれていません。許容例: [{preview}]",
                failed_row_index=i,
                suffix_list=suffix_list,
            )

    # すべて一致
    return ValidationResult(
        ok=True,
        matches_by_row=list(suffix_list),
        suffix_list=suffix_list,
    )