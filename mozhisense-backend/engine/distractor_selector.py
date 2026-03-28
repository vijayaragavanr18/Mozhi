"""
MozhiSense — Distractor Selector
3-strategy distractor selection with diversity enforcement and quality filtering.
"""

import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _is_too_similar_to_correct(candidate: str, correct: str, threshold: float = 0.85) -> bool:
    """
    Check if a candidate distractor is too similar to the correct answer
    using TF-IDF character n-gram cosine similarity.
    
    Returns True if similarity >= threshold.
    """
    try:
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3))
        tfidf = vectorizer.fit_transform([correct, candidate])
        sim = cosine_similarity(tfidf[0], tfidf[1]).flatten()[0]
        return sim >= threshold
    except Exception:
        # On error, allow the candidate (don't reject)
        return False


def select_distractors(
    correct: str,
    word: str,
    pos: str,
    sentence_ta: str,
    morphological_pool: list,
    cross_sense_pool: list,
    ai_pool: list,
    n: int = 3
) -> list:
    """
    Select exactly n distractors from 3 strategy pools with diversity guarantees.
    
    Strategy:
    1. Merge and deduplicate all pools
    2. Remove the correct answer and empty strings
    3. Filter out candidates too similar to correct (cosine sim >= 0.85)
    4. Pick 1 from each pool for diversity
    5. Fill remaining slots with any filtered candidates
    6. Pad with morphological forms if needed
    
    Args:
        correct: The correct answer
        word: The Tamil word
        pos: Part of speech
        sentence_ta: The Tamil sentence
        morphological_pool: Distractors from morphological engine
        cross_sense_pool: Distractors from cross-sense lookup
        ai_pool: Distractors from AI generator
        n: Number of distractors to return (default 3)
    
    Returns:
        List of exactly n distractors (or as many as available).
    """
    try:
        # --- Step 1-3: Filter each pool individually ---
        def filter_pool(pool: list) -> list:
            """Remove correct answer, empties, and too-similar candidates."""
            filtered = []
            for c in pool:
                if not c or not c.strip():
                    continue
                if c == correct:
                    continue
                if _is_too_similar_to_correct(c, correct):
                    continue
                if c not in filtered:
                    filtered.append(c)
            return filtered

        filtered_morph = filter_pool(morphological_pool)
        filtered_cross = filter_pool(cross_sense_pool)
        filtered_ai = filter_pool(ai_pool)

        selected = []
        used = set()

        # --- Step 4: Pick 1 from each pool for diversity ---
        for pool in [filtered_morph, filtered_cross, filtered_ai]:
            if len(selected) >= n:
                break
            for candidate in pool:
                if candidate not in used:
                    selected.append(candidate)
                    used.add(candidate)
                    break

        # --- Step 5: Fill remaining with any filtered candidates ---
        if len(selected) < n:
            all_filtered = filtered_morph + filtered_cross + filtered_ai
            for candidate in all_filtered:
                if len(selected) >= n:
                    break
                if candidate not in used:
                    selected.append(candidate)
                    used.add(candidate)

        # --- Step 6: Pad with morphological forms without filtering ---
        if len(selected) < n:
            for candidate in morphological_pool:
                if len(selected) >= n:
                    break
                if candidate and candidate != correct and candidate not in used:
                    selected.append(candidate)
                    used.add(candidate)

        # Shuffle for randomness
        random.shuffle(selected)

        return selected[:n]

    except Exception as e:
        print(f"[MozhiSense Distractor] select_distractors error: {e}")
        # Emergency fallback: return what we can from morphological pool
        fallback = [c for c in morphological_pool if c and c != correct]
        return fallback[:n]
