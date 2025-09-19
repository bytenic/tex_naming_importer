import texture_config
import suffix_config


if __name__ == "__main__":
    tex_settings = texture_config.load_params_map_json("../../Saved/ImportSettings.json")
    print(tex_settings)
    suffix_settings = suffix_config.load_texture_suffix_config("../../Saved/SuffixSettings.json")
    print(suffix_settings)