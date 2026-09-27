import re

# Explicit Bengali block so vowel signs (combining marks) don't split words.
_TOKEN = re.compile(r"[\w\u0980-\u09FF]+")


def tokenize(text: str) -> list[str]:
    return sorted({t for t in _TOKEN.findall(text.lower()) if len(t) >= 2})
