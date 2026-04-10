import json


class HotwordExtractor:
    def __init__(self):
        # Your static list stays in memory
        self.static_hotwords = [
            "Mayday",
            "Pan-Pan",
            "Sécurité",
            "MMSI",
            "VTS",
            "UTC",
            "ETA",
            "Over",
            "Out",
            "Roger",
            "Copy",
            "Standing by",
            "Correction",
            "Say again",
            "Sinking",
            "Grounding",
            "Collision",
            "Assistance",
            "Starboard",
            "Portside",
            "Midships",
            "Steady as she goes",
            "Hard-a-port",
            "Hard-a-starboard",
            "Underway",
            "Making way",
            "At anchor",
            "Moored",
            "Draft",
            "Knot",
            "Knots",
            "Hull",
            "Keel",
            "Bulwark",
            "Windlass",
            "Winch",
            "Aft",
            "Forward",
            "Bridge",
            "Galley",
            "EPIRB",
            "SART",
            "AIS",
            "Radar",
            "ECDIS",
        ]

    def extract_hotwords(self, ship_data):

        # Handle input type
        data = json.loads(ship_data) if isinstance(ship_data, str) else ship_data

        dynamic_set = set()

        # 1. Extract Identity
        dynamic_set.add(data.get("header", {}).get("vessel_id"))
        manifest = data.get("voyage_manifest", {})
        dynamic_set.add(manifest.get("call_sign"))
        dynamic_set.add(manifest.get("destination"))

        # 2. Extract Traffic (AIS Targets)
        traffic = data.get("traffic_analysis", {})
        for target in traffic.get("targets", []):
            dynamic_set.add(target.get("name"))

        # 3. Extract Hazards
        env = data.get("environment", {})
        for hazard in env.get("geographic_hazards", []):
            dynamic_set.add(hazard.get("label"))

        # 4. Clean and Combine
        dynamic_words = [str(k).replace("_", " ") for k in dynamic_set if k]

        # Combine lists and return as single string
        return ", ".join(self.static_hotwords + dynamic_words)
