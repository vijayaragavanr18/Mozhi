from typing import Any, Dict, List

from .wordnet_fetcher import load_wordnet


def expand_word_entries(word: str) -> Dict[str, Any]:
    wordnet = load_wordnet()
    return wordnet.get(word, {})


def list_all_words() -> List[str]:
    wordnet = load_wordnet()
    return sorted(wordnet.keys())
