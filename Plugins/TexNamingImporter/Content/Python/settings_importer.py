import sys
from pathlib import Path
from typing import List, Dict, Tuple

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from texture_config import TextureConfigParams, load_params_map_json
from suffix_config import TextureSuffixConfig, load_texture_suffix_config

def  load_settings(tex_settings_path: str, suffix_settings_path: str)-> ( Dict[str, TextureConfigParams], TextureSuffixConfig):
    tex_settings = load_params_map_json(tex_settings_path)
    suffix_settings = load_texture_suffix_config(suffix_settings_path)
    return tex_settings, suffix_settings