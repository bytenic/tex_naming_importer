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
    valid_directory = ["/Game/VFX/", "/Game/Debug"]
    suffix_grid = validator.build_suffix_grid(suffix_settings)
    all_suffixes = [suf for row in suffix_grid for suf in row]
    
    for tex_path in texture_list:
        print(f"---import start  {tex_path} ---")
        suffixes = collect_suffixes_from_path(tex_path, all_suffixes)
        suffix_result = validator.validate_suffixes(suffixes, suffix_grid)
        print(suffix_result)  
        if suffix_result.ok:
            print("Suffix OK")
        else:
            print(f"Suffix Error: {suffix_result.error}")
            continue  # サフィックスエラーならインポートしない

        is_valid_dir = validator.validate_directory(tex_path, valid_directory)
        if is_valid_dir:
            print("Valid Directory")
        else:
            print("Invalid Directory")
            print(f"---import end  {tex_path} ---")
            continue
        
        print(f"---import end  {tex_path} ---")

    return 0
    

if __name__ == "__main__":
    texture_path = sys.argv[1]
    sys.exit(main([texture_path]))
