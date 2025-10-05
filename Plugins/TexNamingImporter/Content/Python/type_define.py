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


class MipGenKind(Enum):
    FROM_TEXTURE_GROUP = 0
    NO_MIPMAPS = 1
    SIMPLE_AVERAGE = 2
    SHARPEN0 = 10
    SHARPEN1 = 11
    SHARPEN2 = 12
    SHARPEN3 = 13
    SHARPEN4 = 14
    SHARPEN5 = 15
    SHARPEN6 = 16
    SHARPEN7 = 17
    SHARPEN8 = 18
    # 必要になったら随時追加（Blur 系などの派生があるエンジンもあります）


class TextureGroupKind(Enum):
    WORLD = 0
    WORLD_NORMAL_MAP = 1
    WORLD_SPECULAR = 2
    CHARACTER = 3
    CHARACTER_NORMAL_MAP = 4
    CHARACTER_SPECULAR = 5
    UI = 6
    LIGHTMAP = 7
    SHADOWMAP = 8
    SKYBOX = 9
    VEHICLE = 10
    CINEMATIC = 11
    EFFECTS = 12
    MEDIA = 13
