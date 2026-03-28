"""
MozhiSense — Offline Pre-generation Pipeline
Generates, validates, and stores challenges for all words in the WordNet.
"""

import sys
import os

# Add parent dir to path so we can import from engine/db modules when run as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import init_db, save_challenge
from engine.sense_engine import get_all_words, get_senses, get_transliteration, get_cross_pos_senses
from engine.morphology_engine import get_morphological_distractors
from engine.ai_generator import generate_challenge, generate_ai_distractors, call_ollama, CHALLENGE_SYSTEM_PROMPT
from engine.bias_controller import BiasController
from engine.distractor_selector import select_distractors
from engine.validator import load_stanza_pipeline, validate_challenge

MAX_RETRIES = 5


def pregenerate_word(word: str, bias_controller: BiasController, pipeline):
    """
    Run the pre-generation pipeline for a single word across all its senses.
    """
    senses = get_senses(word)
    transliteration = get_transliteration(word)
    if not senses:
        print(f"[MozhiSense Admin] No senses found for '{word}'. Skipping.")
        return

    print(f"\n--- Generating for '{word}' ({len(senses)} senses) ---")

    for sense in senses:
        sense_id = sense.get("id")
        pos = sense.get("pos")
        
        morphological_pool = []
        cross_sense_pool = []
        
        print(f"  > Sense {sense_id} ({pos}) - max {MAX_RETRIES} retries")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # 1. Prepare morphological forms needed for the generator prompt
                from engine.morphology_engine import get_inflected_forms
                inflected_forms = get_inflected_forms(word, pos)
                
                # Generate base challenge
                challenge = generate_challenge(word, sense, inflected_forms)
                if not challenge:
                    print(f"    [Attempt {attempt}] Generation failed.")
                    continue

                sentence_ta = challenge.get("sentence_ta", "")
                correct = challenge.get("correct", "")

                # 2. Check bias
                if bias_controller.is_too_similar(sentence_ta):
                    print(f"    [Attempt {attempt}] Too similar to previous challenges.")
                    continue

                # 3. Validate base challenge
                if not validate_challenge(challenge, word, sense, senses, pipeline):
                    print(f"    [Attempt {attempt}] Validation failed.")
                    continue

                # 4. Generate distractors
                # Morphological pool relative to correct answer
                morphological_pool = get_morphological_distractors(word, pos, correct)

                # Cross-sense pool strings
                cross_pos_senses = get_cross_pos_senses(word, pos)
                cross_sense_pool = [s.get("meaning_ta") for s in cross_pos_senses if s.get("meaning_ta")]

                # AI distractor pool
                ai_pool = generate_ai_distractors(sentence_ta, correct, word, pos)

                # 5. Select final distractors
                final_distractors = select_distractors(
                    correct=correct,
                    word=word,
                    pos=pos,
                    sentence_ta=sentence_ta,
                    morphological_pool=morphological_pool,
                    cross_sense_pool=cross_sense_pool,
                    ai_pool=ai_pool,
                    n=3
                )

                challenge["distractors"] = final_distractors

                # 6. Save and commit
                save_challenge(word, transliteration, sense, challenge)
                bias_controller.add(sentence_ta)
                print(f"    \033[32m[SUCCESS]\033[0m Generatred challenge for {sense_id}")
                break  # Successful generation, go to next sense

            except Exception as e:
                print(f"    [Attempt {attempt}] Unexpected error: {e}")

        else:
            print(f"    \033[31m[FAILED]\033[0m Exhausted all {MAX_RETRIES} retries for {sense_id}")


def pregenerate_all():
    """
    Main function to run the full pipeline for all words.
    """
    print("\n===========================================")
    print("MozhiSense — Offline Pre-generation Started")
    print("===========================================")

    # Check Ollama status
    test_response = call_ollama("test", "test", max_tokens=10)
    if test_response is None:
        print("\033[31mOllama not running. Start with: ollama serve\033[0m")
        sys.exit(1)

    init_db()
    
    bias_controller = BiasController()
    pipeline = load_stanza_pipeline()
    words = get_all_words()
    
    total_words = len(words)
    print(f"\nFound {total_words} words to process.")

    for i, word in enumerate(words):
        print(f"\nProcessing word {i+1}/{total_words}...")
        pregenerate_word(word, bias_controller, pipeline)

    print("\n===========================================")
    print("MozhiSense — Pre-generation Complete")
    print("===========================================")


if __name__ == "__main__":
    pregenerate_all()
