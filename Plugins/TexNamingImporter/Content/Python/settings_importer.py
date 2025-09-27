import sys
from pathlib import Path
from typing import List

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import texture_config, suffix_config

def  load_settings(tex_settings_path: str, suffix_settings_path: str)-> (dict, dict):
    tex_settings = texture_config.load_params_map_json(tex_settings_path)
    suffix_settings = suffix_config.load_texture_suffix_config(suffix_settings_path)
    return tex_settings, suffix_settings