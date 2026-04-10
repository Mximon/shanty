import re


class MessageFormatter:
    def __init__(self, call_sign="PATHFINDER"):
        self.call_sign = call_sign.upper()

        # Multilingual Phonetic Mapping
        self.locales = {
            "en": {
                "phonetics": {
                    "0": "ZERO",
                    "1": "ONE",
                    "2": "TWO",
                    "3": "THREE",
                    "4": "FOUR",
                    "5": "FIVE",
                    "6": "SIX",
                    "7": "SEVEN",
                    "8": "EIGHT",
                    "9": "NINE",
                    ".": "POINT",
                    ",": "STOP",
                },
                "corrections": {
                    r"\brepeat\b": "SAY AGAIN",
                    r"\bokay\b": "ROGER",
                    r"\byes\b": "AFFIRMATIVE",
                    r"\bno\b": "NEGATIVE",
                    r"\bcan i\b": "MAY I",
                    r"\bhelp\b": "ASSISTANCE",
                    r"\bnm\b": "NAUTICAL MILES",
                },
            },
            "de": {
                "phonetics": {
                    "0": "NULL",
                    "1": "EINS",
                    "2": "ZWO",
                    "3": "DREI",
                    "4": "VIER",
                    "5": "FÜNF",
                    "6": "SECHS",
                    "7": "SIEBEN",
                    "8": "ACHT",
                    "9": "NEUN",
                    ".": "KOMMA",
                    ",": "STOPP",
                },
                "corrections": {
                    r"\bwiederholen\b": "ICH WIEDERHOLE",
                    r"\bokay\b": "VERSTANDEN",
                    r"\bja\b": "POSITIV",
                    r"\bnein\b": "NEGATIV",
                },
            },
        }

    def _phoneticize_numbers(self, text, lang):
        phonetic_map = self.locales[lang]["phonetics"]

        def replace_digit(match):
            return (
                " "
                + " ".join(phonetic_map.get(char, char) for char in match.group())
                + " "
            )

        return re.sub(r"\d+\.\d+|\d+", replace_digit, text)

    def format_for_radio(self, llm_text, lang="en"):
        lang = lang.lower() if lang in self.locales else "en"
        config = self.locales[lang]

        formatted = llm_text.upper().strip()

        for pattern, replacement in config["corrections"].items():
            formatted = re.sub(pattern, replacement, formatted, flags=re.IGNORECASE)

        formatted = self._phoneticize_numbers(formatted, lang)

        # 5. Clean up extra whitespaces
        formatted = " ".join(formatted.split())

        return formatted
