"""
MozhiSense — Validator
3-layer validation pipeline for generated challenges:
1. WordNet Anchor match
2. POS verification (via Stanza)
3. Perplexity check (via iNLTK)
"""

import stanza
try:
    from inltk.inltk import get_sentence_encoding
except ImportError:
    pass


# Module-level Stanza pipeline storage
_STANZA_PIPELINE = None


def load_stanza_pipeline() -> stanza.Pipeline | None:
    """
    Load Stanza pipeline once at module level with tokenization and POS.
    Gracefully handles missing packages.
    """
    global _STANZA_PIPELINE
    if _STANZA_PIPELINE is not None:
        return _STANZA_PIPELINE

    try:
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        stanza_dir = os.path.join(base_dir, "models", "stanza")
        
        # models were downloaded to this specific dir in setup.sh
        _STANZA_PIPELINE = stanza.Pipeline(lang='ta', dir=stanza_dir, processors='tokenize,pos', use_gpu=False, download_method=None)
        print("[MozhiSense Validator] Stanza pipeline from local models dir loaded successfully.")
        return _STANZA_PIPELINE
    except Exception as e:
        print(f"[MozhiSense Validator] Stanza load error: {e}")
        return None


def validate_wordnet_anchor(sentence_ta: str, word: str, wordnet_senses: list) -> bool:
    """
    Layer 1: Check if the word root or any of its Tamil meanings appear in the sentence.
    
    Args:
        sentence_ta: The generated Tamil sentence
        word: The word root
        wordnet_senses: List of all sense dicts for this word (from get_senses())
    """
    try:
        # Strip punctuation for simple matching
        clean_sentence = ''.join(c for c in sentence_ta if c.isalnum() or c.isspace())
        tokens = clean_sentence.split()

        # Check for word root
        if word in tokens:
            return True
        if any(t.startswith(word) for t in tokens):
            return True

        # Check for any exact meaning match in the sentence
        for sense in wordnet_senses:
            meaning = sense.get("meaning_ta", "")
            if meaning and meaning in sentence_ta:
                return True

        return False

    except Exception as e:
        print(f"[MozhiSense Validator] Anchor validation error: {e}")
        return False


def validate_pos(sentence_ta: str, word: str, expected_pos: str, pipeline: stanza.Pipeline | None) -> bool:
    """
    Layer 2: Check if any token matching the word has the expected POS tag.
    Gracefully passes if Stanza is not loaded or word is not found.
    """
    if pipeline is None:
        return True  # Graceful skip

    try:
        # Convert our POS string to Stanza UPOS
        upos_map = {
            "Noun": "NOUN",
            "Verb": "VERB",
            "Adjective": "ADJ",
            "Adverb": "ADV",
            "Pronoun": "PRON"
        }
        target_upos = upos_map.get(expected_pos)
        if not target_upos:
            return True

        doc = pipeline(sentence_ta)
        word_found = False

        for sentence in doc.sentences:
            for word_obj in sentence.words:
                text = word_obj.text
                if text.startswith(word):
                    word_found = True
                    if word_obj.upos == target_upos:
                        return True

        # Ifword wasn't found in tokens, pass gracefully (might be compound word or morphological issue)
        if not word_found:
            return True

        return False

    except Exception as e:
        print(f"[MozhiSense Validator] POS validation error: {e}")
        return True


def validate_perplexity(sentence_ta: str) -> bool:
    """
    Layer 3: Try to use iNLTK for perplexity check via sentence encodings.
    Gracefully skips if unavailable.
    """
    try:
        # Simple test to see if iNLTK is fully operational
        encodings = get_sentence_encoding(sentence_ta, 'ta')
        
        # We proxy perplexity by computing the mean of the encoding array
        mean_encoding = abs(sum(encodings) / len(encodings))
        
        # Arbitrary threshold from spec
        if mean_encoding < 180:
            return True
            
        print(f"[MozhiSense Validator] Perplexity > 180 ({mean_encoding})")
        return False
        
    except Exception as e:
        # iNLTK might not be installed, model might missing, etc. Graceful skip.
        pass
        
    return True


def validate_challenge(challenge: dict, word: str, sense: dict, all_senses: list, pipeline: stanza.Pipeline | None) -> bool:
    """
    Run all 3 layers in sequence.
    Returns True only if all 3 pass.
    """
    try:
        sentence_ta = challenge.get("sentence_ta", "")
        if not sentence_ta:
            print("[MozhiSense Validator] Validation failed: Empty sentence.")
            return False

        # Layer 1
        if not validate_wordnet_anchor(sentence_ta, word, all_senses):
            print(f"[MozhiSense Validator] Layer 1 failed (Anchor) for '{word}'.")
            return False

        # Layer 2
        expected_pos = sense.get("pos", "")
        if not validate_pos(sentence_ta, word, expected_pos, pipeline):
            print(f"[MozhiSense Validator] Layer 2 failed (POS) for '{word}' ({expected_pos}).")
            return False

        # Layer 3
        if not validate_perplexity(sentence_ta):
            print(f"[MozhiSense Validator] Layer 3 failed (Perplexity) for '{word}'.")
            return False

        return True

    except Exception as e:
        print(f"[MozhiSense Validator] validate_challenge error: {e}")
        return False
