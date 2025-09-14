from type_define import AddressMode


SUFFIX_TO_TEX2D_ADDRESS_MAP = {
    "cc": (AddressMode.CLAMP, AddressMode.CLAMP),
    "cw": (AddressMode.CLAMP, AddressMode.WRAP),
    "cm": (AddressMode.CLAMP, AddressMode.MIRROR),
    "wc": (AddressMode.WRAP, AddressMode.CLAMP),
    "ww": (AddressMode.WRAP, AddressMode.WRAP),
    "wm": (AddressMode.WRAP, AddressMode.MIRROR),
    "mc": (AddressMode.MIRROR, AddressMode.CLAMP),
    "mw": (AddressMode.MIRROR, AddressMode.WRAP),
    "mm": (AddressMode.MIRROR, AddressMode.CLAMP),
}

TEXTURE_TYPE_SUFFIXES = ["col", "msk", "nml", "mat", "cub", "flw"]
