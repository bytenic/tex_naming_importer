import sys
from pathlib import Path
from typing import List

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import settings_importer
import validator
from texture_config import TextureConfigParams
from suffix_config import TextureSuffixConfig
from path_utils.path_functions import *

def main(texture_list: List[str]):
    tex_settings, suffix_settings = settings_importer.load_settings(
        "E:/dev_e/tex_naming_importer/TexImporterProject/Saved/ImportSettings.json",
        "E:/dev_e/tex_naming_importer/TexImporterProject/Saved/SuffixSettings.json"
    )
    suffix_grid = validator.build_suffix_grid(suffix_settings)
    print(suffix_grid)
    all_suffixes = [suf for row in suffix_grid for suf in row]
    print(all_suffixes)
    for tex_path in texture_list:
        suffixes = collect_suffixes_from_path(tex_path, all_suffixes)
        if len(suffixes) == 0:
            print(f"{tex_path} -> <no suffix>")
            continue
        print(f"{tex_path} -> {suffixes}")  
        result = validator.validate_suffixes(suffixes, suffix_grid)      
        if result.ok:
            print("  OK")
        else:
            print(f"  NG: {result.error}")

    return 0
    


if __name__ == "__main__":
    texture_path = sys.argv[1]
    sys.exit(main([texture_path]))
