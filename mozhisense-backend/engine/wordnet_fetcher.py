import json
from pathlib import Path
from typing import Any, Dict


def get_wordnet_path() -> Path:
    return Path(__file__).resolve().parent.parent / "db" / "wordnet.json"


def load_wordnet() -> Dict[str, Any]:
    path = get_wordnet_path()
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
