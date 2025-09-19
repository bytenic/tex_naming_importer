from type_define import TextureConfigParams
import config_io


if __name__ == "__main__":
    texture_config = config_io.load_params_map_json("../../Saved/ImportSettings.json")
    print(texture_config)
    suffix_config = config_io.load_texture_suffix_config("../../Saved/SuffixSettings.json")
    print(suffix_config)