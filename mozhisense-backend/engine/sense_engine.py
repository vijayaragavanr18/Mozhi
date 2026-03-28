"""
MozhiSense — Sense Engine
Loads the offline Tamil WordNet and exposes sense lookup functions.
"""

import json
import os

# Module-level wordnet storage
_WORDNET = None
_WORDNET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "wordnet.json")


def load_wordnet() -> dict:
    """
    Load the WordNet JSON file once into memory at module level.
    Returns the parsed dictionary.
    """
    global _WORDNET
    if _WORDNET is not None:
        return _WORDNET

    try:
        with open(_WORDNET_PATH, "r", encoding="utf-8") as f:
            _WORDNET = json.load(f)
        print(f"[MozhiSense SenseEngine] Loaded WordNet with {len(_WORDNET)} words.")
        return _WORDNET
    except FileNotFoundError:
        print(f"[MozhiSense SenseEngine] WordNet file not found at {_WORDNET_PATH}")
        _WORDNET = {}
        return _WORDNET
    except json.JSONDecodeError as e:
        print(f"[MozhiSense SenseEngine] WordNet JSON parse error: {e}")
        _WORDNET = {}
        return _WORDNET
    except Exception as e:
        print(f"[MozhiSense SenseEngine] Unexpected error loading WordNet: {e}")
        _WORDNET = {}
        return _WORDNET


def get_senses(word: str) -> list:
    """
    Look up a word in the WordNet.
    Returns list of sense dicts with: id, pos, meaning_en, meaning_ta, example_en
    Returns empty list if word not found.
    """
    try:
        wordnet = load_wordnet()
        if word not in wordnet:
            print(f"[MozhiSense SenseEngine] Word '{word}' not found in WordNet.")
            return []

        senses = wordnet[word].get("senses", [])
        return [
            {
                "id": s.get("id", ""),
                "pos": s.get("pos", ""),
                "meaning_en": s.get("meaning_en", ""),
                "meaning_ta": s.get("meaning_ta", ""),
                "example_en": s.get("example_en", "")
            }
            for s in senses
        ]
    except Exception as e:
        print(f"[MozhiSense SenseEngine] get_senses error: {e}")
        return []


def get_transliteration(word: str) -> str:
    """
    Get the transliteration for a word.
    """
    try:
        wordnet = load_wordnet()
        if word in wordnet:
            return wordnet[word].get("transliteration", "")
        return ""
    except Exception as e:
        print(f"[MozhiSense SenseEngine] get_transliteration error: {e}")
        return ""


def get_all_words() -> list:
    """
    Return all word keys from the WordNet.
    """
    try:
        wordnet = load_wordnet()
        return list(wordnet.keys())
    except Exception as e:
        print(f"[MozhiSense SenseEngine] get_all_words error: {e}")
        return []


def get_cross_pos_senses(word: str, current_pos: str) -> list:
    """
    Return senses of a word where pos != current_pos.
    Used for cross-sense distractor generation.
    """
    try:
        all_senses = get_senses(word)
        cross_senses = [s for s in all_senses if s.get("pos", "") != current_pos]
        return cross_senses
    except Exception as e:
        print(f"[MozhiSense SenseEngine] get_cross_pos_senses error: {e}")
        return []


# Auto-load on import
load_wordnet()
