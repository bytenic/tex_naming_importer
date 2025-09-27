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

def main(texture_list: List[str]):
    tex_settings, suffix_settings = settings_importer.load_settings(
        "E:/dev_e/tex_naming_importer/TexImporterProject/Saved/ImportSettings.json",
        "E:/dev_e/tex_naming_importer/TexImporterProject/Saved/SuffixSettings.json"
    )
    #print(tex_settings)
    #print(suffix_settings)
    suffix_grid = validator.build_suffix_grid(suffix_settings)
    print(suffix_grid)
    return 0
    


if __name__ == "__main__":
    texture_path = sys.argv[1]
    sys.exit(main([texture_path]))
