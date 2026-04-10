import json


def build_prompt_from_json(prompt_path, pilot_json, colreg_json):
    with open(prompt_path, "r", encoding="utf-8") as md_file:
        prompt = md_file.read()

    with open(pilot_json, "r") as file:
        ship_data = json.load(file)

    prompt = prompt.replace("{{SHIP_DATA}}", json.dumps(ship_data, indent=1))

    with open(colreg_json, "r") as file:
        colreg = json.load(file)

    all_rules = colreg.get("rules", [])
    active_rules_ids = ship_data["decision_engine"]["active_colreg"]

    selected_rules = []
    for rule_entry in all_rules:
        if rule_entry["rule"] in active_rules_ids:
            formatted_rule = f"Rule {rule_entry['rule']}: {rule_entry['title']}\n{rule_entry['text']}"
            selected_rules.append(formatted_rule)

    colreg_block = "Active rules:\n" + "\n\n".join(selected_rules)
    prompt = prompt.replace("{{COLREG}}", colreg_block)
    return prompt
