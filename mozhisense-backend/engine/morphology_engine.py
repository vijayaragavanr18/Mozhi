"""
MozhiSense — Morphology Engine
Tamil morphological analysis with 30-rule suffix grammar as hardcoded fallback.
Provides root extraction, inflection generation, and morphological distractors.
"""

# --- Tamil Suffix Grammar (Hardcoded Rules) ---

NOUN_CASE_SUFFIXES = {
    "nominative": "",           # No suffix
    "accusative": "ை",          # -ai
    "dative": "க்கு",           # -kku
    "locative": "ல்",           # -l (in/at)
    "instrumental": "ால்",      # -aal (by/with)
    "ablative": "லிருந்து",      # -liruthu (from)
    "genitive": "ன்",           # -n (of)
    "sociative": "ோடு",         # -odu (with)
}

VERB_FORM_SUFFIXES = {
    "infinitive": "க்க",        # -kka
    "past_masculine": "த்தான்",   # -tthaan
    "past_feminine": "த்தாள்",   # -tthaal
    "past_plural": "த்தார்கள்",  # -tthaargal
    "present_masculine": "க்கிறான்",  # -kkiran
    "present_feminine": "க்கிறாள்",   # -kkiral
    "present_plural": "க்கிறார்கள்",  # -kkirargal
    "future": "ப்பான்",          # -ppaan
    "verbal_noun": "ப்பு",       # -ppu
}

# Common Tamil suffixes to strip for root extraction
COMMON_SUFFIXES = [
    "க்கிறான்", "க்கிறாள்", "க்கிறார்கள்",
    "த்தான்", "த்தாள்", "த்தார்கள்",
    "ப்பான்", "ப்பாள்", "ப்பார்கள்",
    "கிறான்", "கிறாள்", "கிறார்கள்",
    "க்கு", "ால்", "லிருந்து",
    "ோடு", "ன்", "ல்", "ை",
    "க்க", "ப்பு", "த்த",
    "க", "ல்", "லை", "லில்",
]


def get_root(word: str) -> str:
    """
    Extract the root form of a Tamil word.
    Strategy:
      1. Try IndicNLP unsupervised morpher first
      2. If it fails or returns empty, use hardcoded suffix stripping
      3. Fallback to the word itself as root
    """
    try:
        # Attempt IndicNLP morphological analysis
        try:
            from indicnlp.morph import unsupervised_morph
            morphs = unsupervised_morph.UnsupervisedMorphAnalyzer()
            result = morphs.morph_analyze(word)
            if result and len(result) > 0:
                root = result[0] if isinstance(result, list) else str(result)
                if root and root.strip():
                    return root.strip()
        except ImportError:
            print("[MozhiSense Morphology] IndicNLP not available, using fallback.")
        except Exception as e:
            print(f"[MozhiSense Morphology] IndicNLP morph error: {e}")

        # Fallback: hardcoded suffix stripping
        root = word
        for suffix in sorted(COMMON_SUFFIXES, key=len, reverse=True):
            if root.endswith(suffix) and len(root) > len(suffix):
                root = root[:-len(suffix)]
                break

        return root if root else word

    except Exception as e:
        print(f"[MozhiSense Morphology] get_root error: {e}")
        return word


def get_inflected_forms(word: str, pos: str) -> list:
    """
    Generate all inflected forms for a word given its POS.
    Uses root + suffix concatenation from the grammar rules.
    
    Args:
        word: The Tamil word
        pos: "Noun" or "Verb"
    
    Returns:
        Deduplicated list of all inflected forms (no empty strings).
    """
    try:
        root = get_root(word)
        forms = set()

        if pos == "Noun":
            for case_name, suffix in NOUN_CASE_SUFFIXES.items():
                form = root + suffix
                if form:
                    forms.add(form)
        elif pos == "Verb":
            for form_name, suffix in VERB_FORM_SUFFIXES.items():
                form = root + suffix
                if form:
                    forms.add(form)
        else:
            # Unknown POS — apply both noun and verb suffixes
            for suffix in list(NOUN_CASE_SUFFIXES.values()) + list(VERB_FORM_SUFFIXES.values()):
                form = root + suffix
                if form:
                    forms.add(form)

        # Add the original word and root
        forms.add(word)
        forms.add(root)

        # Remove empty strings and deduplicate
        result = [f for f in forms if f and f.strip()]
        return sorted(list(set(result)))

    except Exception as e:
        print(f"[MozhiSense Morphology] get_inflected_forms error: {e}")
        return [word]


def get_morphological_distractors(word: str, pos: str, correct: str) -> list:
    """
    Generate morphological distractors by getting inflected forms
    and filtering out the correct answer.
    
    Returns up to 6 forms that are NOT the correct answer.
    """
    try:
        all_forms = get_inflected_forms(word, pos)
        
        # Filter out the correct answer
        distractors = [f for f in all_forms if f != correct]
        
        # Return up to 6
        return distractors[:6]

    except Exception as e:
        print(f"[MozhiSense Morphology] get_morphological_distractors error: {e}")
        return []
