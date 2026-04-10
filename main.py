from Engines.LRL_engine_V4 import LRL_v4_MaritimeEngine
from Utils.prompt import build_prompt_from_json
from Utils.load_config import load_config
from Utils.hotwords_extractor import HotwordExtractor
from Utils.bilingual_formatter import MessageFormatter
from interface_V02 import EngineInterface

if __name__ == "__main__":

    config = load_config("config.yaml")
    formatter = MessageFormatter()
    engine = LRL_v4_MaritimeEngine(config, formatter)
    system_prompt = build_prompt_from_json(
        config["paths"]["prompt"],
        config["paths"]["master_schema"],
        config["paths"]["colreg"],
    )
    hotword_extractor = HotwordExtractor()
    app = EngineInterface(config, engine, system_prompt, hotword_extractor)
    app.launch()
