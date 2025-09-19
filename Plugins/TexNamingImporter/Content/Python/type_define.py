from enum import Enum, IntEnum
from dataclasses import dataclass

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

