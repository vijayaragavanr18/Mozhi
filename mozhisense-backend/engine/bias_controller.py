"""
MozhiSense — Bias Controller
Session-level deduplication controller using TF-IDF cosine similarity
to prevent repetitive challenge sentences.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class BiasController:
    """
    Prevents generation of overly similar sentences within a pre-generation session.
    Uses character-level TF-IDF with n-grams for Tamil text similarity detection.
    """

    def __init__(self, threshold: float = 0.85):
        """
        Args:
            threshold: Cosine similarity threshold above which sentences are
                       considered too similar (default: 0.85)
        """
        self.seen_sentences: list[str] = []
        self.threshold = threshold

    def is_too_similar(self, new_sentence: str) -> bool:
        """
        Check if a new sentence is too similar to any previously seen sentence.
        
        Args:
            new_sentence: The sentence to check
        
        Returns:
            True if max similarity >= threshold, False otherwise.
        """
        if not self.seen_sentences:
            return False

        try:
            # Combine seen sentences with the new one for TF-IDF
            corpus = self.seen_sentences + [new_sentence]

            vectorizer = TfidfVectorizer(
                analyzer='char',
                ngram_range=(1, 3)
            )
            tfidf_matrix = vectorizer.fit_transform(corpus)

            # Compare new sentence (last row) against all seen sentences
            new_vector = tfidf_matrix[-1]
            seen_vectors = tfidf_matrix[:-1]

            similarities = cosine_similarity(new_vector, seen_vectors).flatten()
            max_similarity = similarities.max()

            if max_similarity >= self.threshold:
                print(f"[MozhiSense Bias] Sentence too similar (score: {max_similarity:.3f})")
                return True

            return False

        except Exception as e:
            print(f"[MozhiSense Bias] Similarity check error: {e}")
            return False

    def add(self, sentence: str):
        """
        Add a sentence to the seen list.
        
        Args:
            sentence: The sentence to track
        """
        self.seen_sentences.append(sentence)

    def reset(self):
        """Clear all seen sentences."""
        self.seen_sentences = []
        print("[MozhiSense Bias] Controller reset.")
