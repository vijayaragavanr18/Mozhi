"""
MozhiSense — Pipeline Verification Script
Tests the major components and the pipeline without modifying the DB.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import init_db
from engine.sense_engine import get_senses, get_all_words, get_cross_pos_senses
from engine.morphology_engine import get_inflected_forms, get_morphological_distractors
from engine.ai_generator import call_ollama, generate_challenge, generate_ai_distractors
from engine.distractor_selector import select_distractors
from engine.validator import load_stanza_pipeline

def run_verification():
    print("===========================================")
    print("MozhiSense — Pipeline Verification")
    print("===========================================")

    # 1. DB Init Check
    print("\n[1] Checking Database Initialization...")
    try:
        init_db()
        print("    -> Database check passed.")
    except Exception as e:
        print(f"    -> WARNING Database check failed: {e}")

    # 2. WordNet Check
    print("\n[2] Checking Offline WordNet...")
    words = get_all_words()
    print(f"    -> Found words: {words}")
    if not words:
        print("    -> FAIL: No words found.")
        return
    
    test_word = words[0]
    senses = get_senses(test_word)
    print(f"    -> Found {len(senses)} senses for '{test_word}'.")
    if not senses:
        print(f"    -> FAIL: No senses for '{test_word}'.")
        return
    test_sense = senses[0]
    print(f"    -> Sense ID: {test_sense.get('id')} - Meaning: {test_sense.get('meaning_en')}")

    # 3. Morphology Check
    print("\n[3] Checking Morphology Engine...")
    pos = test_sense.get("pos", "Noun")
    forms = get_inflected_forms(test_word, pos)
    print(f"    -> Inflected forms for '{test_word}' ({pos}): {forms}")

    # 4. Prompt Generation Check
    print("\n[4] Checking AI Distractor and Generator Pipeline...")
    
    # Try calling Ollama simply
    ollama_test = call_ollama("test", "test", max_tokens=10)
    
    if ollama_test is None:
        print("    -> ERROR: Ollama is not running or Qwen model not found.")
        print("    -> Cannot test actual full generation pipeline. Mocking a response to test Selector logic...")
        
        # Mocking generation
        challenge = {
            "sentence_ta": f"இது ஒரு ______.",
            "sentence_en": "This is a ______.",
            "correct": forms[0] if forms else test_word,
            "explanation": "Mock explanation."
        }
        sentence_ta = challenge["sentence_ta"]
        correct = challenge["correct"]
        
        # Mocking distractors
        morph_pool = get_morphological_distractors(test_word, pos, correct)
        cross_sense_pool = [s.get("meaning_ta") for s in get_cross_pos_senses(test_word, pos)]
        ai_pool = ["தவறானவிடை1", "தவறானவிடை2"]
        
        print(f"    -> Mock Sentence: {sentence_ta}")
        print(f"    -> Correct: {correct}")
        
        final_distractors = select_distractors(
            correct, test_word, pos, sentence_ta, morph_pool, cross_sense_pool, ai_pool, n=3
        )
        print(f"    -> Selected Distractors: {final_distractors}")
        if len(final_distractors) > 0:
            print("    -> Distractor Selector logic passed.")
        else:
            print("    -> Distractor Selector logic failed.")

    else:
        print("    -> Ollama is running. Testing actual challenge generation.")
        try:
            challenge = generate_challenge(test_word, test_sense, forms)
            if challenge:
                print(f"    -> Generated Sentence: {challenge.get('sentence_ta')}")
                print(f"    -> Correct Answer: {challenge.get('correct')}")
                print(f"    -> Explanation: {challenge.get('explanation')}")
                
                print("    -> Generating Distractors...")
                morph_pool = get_morphological_distractors(test_word, pos, challenge.get('correct'))
                cross_sense_pool = [s.get("meaning_ta") for s in get_cross_pos_senses(test_word, pos)]
                ai_pool = generate_ai_distractors(challenge.get('sentence_ta'), challenge.get('correct'), test_word, pos)
                
                final_distractors = select_distractors(
                    challenge.get('correct'), test_word, pos, challenge.get('sentence_ta'),
                    morph_pool, cross_sense_pool, ai_pool, n=3
                )
                print(f"    -> Options for Answer (Correct + 3 Distractors):")
                print(f"       Correct: {challenge.get('correct')}")
                print(f"       Distractors: {final_distractors}")
            else:
                print("    -> ERROR: Failed to generate challenge via Ollama.")
        except Exception as e:
            print(f"    -> ERROR in AI generation: {e}")

    # 5. Stanza Validator Check
    print("\n[5] Checking Stanza Validator Pipeline...")
    try:
        pipeline = load_stanza_pipeline()
        if pipeline:
            print("    -> Stanza loaded from models/stanza successfully.")
        else:
            print("    -> WARNING: Stanza pipeline failed to load. (Did you run setup.sh first?)")
    except Exception as e:
        print(f"    -> ERROR loading stanza: {e}")

    print("\n===========================================")
    print("Verification Script Finished.")
    print("Run `bash scripts/setup.sh` to initialize everything and pregenerate.")
    print("===========================================")

if __name__ == "__main__":
    run_verification()
