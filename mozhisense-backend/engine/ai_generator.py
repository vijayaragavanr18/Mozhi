"""
MozhiSense — AI Generator
Integrates with Ollama/Qwen for challenge and distractor generation.
"""

import json
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2:1.5b"

CHALLENGE_SYSTEM_PROMPT = """You are a Tamil linguistics expert specializing in polysemous (multi-meaning) Tamil words.

Your task: Generate a fill-in-the-blank Tamil sentence that uses the given Tamil word in a SPECIFIC sense/meaning.

STRICT RULES:
1. The sentence MUST be in Tamil script.
2. The blank in sentence_ta MUST be exactly "______" (6 underscores).
3. The correct answer MUST be a real Tamil word form that fits the given sense.
4. The sentence must clearly and unambiguously point to the given sense (not any other sense of the word).
5. The explanation must be in English, explaining why the correct answer fits this specific sense.
6. Return ONLY valid JSON. No markdown, no explanation, no preamble, no code fences.

JSON format (EXACTLY this structure):
{"sentence_ta": "Tamil sentence with ______ as blank", "sentence_en": "English translation with ______ as blank", "correct": "correct Tamil word form", "explanation": "English explanation of why this is correct for this sense"}"""

DISTRACTOR_SYSTEM_PROMPT = """You are a Tamil linguistics expert.

Your task: Generate 4 plausible but WRONG Tamil word options for a fill-in-the-blank sentence.

STRICT RULES:
1. Each distractor must be a grammatically valid Tamil word.
2. Each distractor must be semantically WRONG for the given sentence context.
3. Distractors should be plausible (related to the word or topic) but clearly incorrect.
4. Return ONLY a JSON array. No markdown, no explanation, no preamble, no code fences.

JSON format (EXACTLY this):
["word1", "word2", "word3", "word4"]"""


def call_ollama(prompt: str, system: str, max_tokens: int = 400) -> str | None:
    """
    Make a POST request to the Ollama API.
    
    Args:
        prompt: The user prompt
        system: The system prompt
        max_tokens: Maximum tokens in response
    
    Returns:
        The response text, or None if Ollama is not running or errors occur.
    """
    try:
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        text = result.get("response", "")

        # Strip markdown fences if present
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()

        return text

    except requests.exceptions.ConnectionError:
        print("[MozhiSense AI] Ollama not running. Start with: ollama serve")
        return None
    except requests.exceptions.Timeout:
        print("[MozhiSense AI] Ollama request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[MozhiSense AI] Ollama request error: {e}")
        return None
    except Exception as e:
        print(f"[MozhiSense AI] Unexpected error calling Ollama: {e}")
        return None


def generate_challenge(word: str, sense: dict, morphological_forms: list) -> dict | None:
    """
    Generate a fill-in-the-blank challenge for a word in a specific sense.
    
    Args:
        word: The Tamil word
        sense: Sense dict with id, pos, meaning_en, meaning_ta, example_en
        morphological_forms: List of available morphological forms
    
    Returns:
        Dict with sentence_ta, sentence_en, correct, explanation — or None on failure.
    """
    try:
        prompt = f"""Generate a fill-in-the-blank Tamil sentence for the word "{word}".

Word: {word}
Sense ID: {sense.get('id', '')}
Part of Speech: {sense.get('pos', '')}
Meaning (English): {sense.get('meaning_en', '')}
Meaning (Tamil): {sense.get('meaning_ta', '')}
Example: {sense.get('example_en', '')}

Available morphological forms: {', '.join(morphological_forms[:8])}

The sentence MUST use this word specifically in the sense of "{sense.get('meaning_en', '')}".
The blank (______) should be where the correct answer goes.
Return ONLY valid JSON."""

        response_text = call_ollama(prompt, CHALLENGE_SYSTEM_PROMPT)
        if response_text is None:
            return None

        # Parse JSON
        challenge = json.loads(response_text)

        # Validate required keys
        required_keys = ["sentence_ta", "sentence_en", "correct", "explanation"]
        for key in required_keys:
            if key not in challenge or not challenge[key]:
                print(f"[MozhiSense AI] Missing key '{key}' in challenge response.")
                return None

        return {
            "sentence_ta": challenge["sentence_ta"],
            "sentence_en": challenge["sentence_en"],
            "correct": challenge["correct"],
            "explanation": challenge["explanation"]
        }

    except json.JSONDecodeError as e:
        print(f"[MozhiSense AI] JSON parse error in generate_challenge: {e}")
        return None
    except Exception as e:
        print(f"[MozhiSense AI] generate_challenge error: {e}")
        return None


def generate_ai_distractors(sentence_ta: str, correct: str, word: str, pos: str) -> list:
    """
    Generate AI-powered distractors for a given challenge.
    
    Args:
        sentence_ta: The Tamil sentence with blank
        correct: The correct answer
        word: The word being tested
        pos: Part of speech
    
    Returns:
        List of distractor strings, or empty list on failure.
    """
    try:
        prompt = f"""Generate 4 plausible but WRONG Tamil word options for this sentence:

Sentence: {sentence_ta}
Correct answer: {correct}
Word being tested: {word}
Part of Speech: {pos}

The distractors should be:
- Grammatically valid Tamil words
- Related to the word or context but semantically wrong
- Plausible enough to trick a learner

Return ONLY a JSON array of 4 Tamil words."""

        response_text = call_ollama(prompt, DISTRACTOR_SYSTEM_PROMPT)
        if response_text is None:
            return []

        # Parse JSON array
        distractors = json.loads(response_text)

        if isinstance(distractors, list):
            # Filter to valid non-empty strings
            return [d for d in distractors if isinstance(d, str) and d.strip()]
        else:
            print("[MozhiSense AI] Distractor response is not a list.")
            return []

    except json.JSONDecodeError as e:
        print(f"[MozhiSense AI] JSON parse error in generate_ai_distractors: {e}")
        return []
    except Exception as e:
        print(f"[MozhiSense AI] generate_ai_distractors error: {e}")
        return []
