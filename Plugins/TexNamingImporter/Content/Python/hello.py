from type_define import TextureConfigParams
import config_io


if __name__ == "__main__":
    config_dict = config_io.load_params_map_json("../../Saved/ImportSettings.json")
    print(config_dict)