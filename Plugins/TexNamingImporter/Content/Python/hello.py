import os, sys

import sys
from pathlib import Path
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import texture_config, suffix_config


if __name__ == "__main__":
    tex_settings = texture_config.load_params_map_json("E:/dev_e/tex_naming_importer/TexImporterProject/Saved/ImportSettings.json")
    print(tex_settings)
    suffix_settings = suffix_config.load_texture_suffix_config("E:/dev_e/tex_naming_importer/TexImporterProject/Saved/SuffixSettings.json")
    print(suffix_settings)
    texture_path = sys.argv[1]
    print(texture_path)
