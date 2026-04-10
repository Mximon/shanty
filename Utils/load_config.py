import yaml


def load_config(path="config.yaml"):

    # charge config.yaml
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return {
        "paths": config["paths"],
        "tokens": config["tokens"],
        "voices": config["voices"],
    }
