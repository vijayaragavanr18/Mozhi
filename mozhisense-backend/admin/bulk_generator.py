"""MozhiSense bulk challenge generator.

Generates challenges for 50 seed words and stores them in SQLite with strong
resiliency (skip/resume, timeout-safe Ollama calls, immediate commits).
"""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

try:
    from tqdm import tqdm
except Exception:
    tqdm = None


SEED_WORDS = [
    "படி", "ஆறு", "திங்கள்", "மாலை", "கலை", "கல்", "பார்", "அடி", "கால்", "பால்",
    "மலர்", "தலை", "மழை", "காடு", "நாடு", "வீடு", "ஆடு", "மாடு", "காசு", "பாதி",
    "வில்", "சொல்", "நில்", "செல்", "புல்", "பல்", "கல்வி", "கண்", "பெண்", "மண்",
    "விண்", "பண்", "எண்", "உண்", "தண்", "நண்பு", "பண்பு", "அன்பு", "துன்பு", "இன்பு",
    "கை", "தை", "பை", "மை", "வை", "நை", "கொடு", "சுடு", "படு", "விடு",
]

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "mozhisense.db"
WORDNET_PATH = BASE_DIR / "db" / "wordnet.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
PREFERRED_MODEL = "qwen:1.5b"
REQUEST_TIMEOUT_SECONDS = 30
RETRY_DELAY_SECONDS = 0.4

TARGET_CHALLENGES_PER_WORD = 2
MAX_GENERATION_TRIES_PER_SENSE = 5

_RESOLVED_MODEL: str | None = None


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _find_table_name_ci(conn: sqlite3.Connection, table_name: str) -> str | None:
    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND lower(name) = lower(?)
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return str(row["name"]) if row else None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _ensure_expected_table(conn: sqlite3.Connection, table_name: str, required_columns: set[str]) -> None:
    existing_name = _find_table_name_ci(conn, table_name)
    if not existing_name:
        return

    existing_columns = _table_columns(conn, existing_name)
    if required_columns.issubset(existing_columns):
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    legacy_name = f"{table_name}_legacy_{stamp}"
    conn.execute(f"ALTER TABLE {existing_name} RENAME TO {legacy_name}")
    print(f"[INFO] Renamed incompatible table '{existing_name}' -> '{legacy_name}'")


def initialize_database(conn: sqlite3.Connection) -> None:
    _ensure_expected_table(conn, "Words", {"id", "word_text"})
    _ensure_expected_table(conn, "Senses", {"id", "word_id", "meaning", "english_translation", "pos"})
    _ensure_expected_table(conn, "Challenges", {"id", "word_id", "sense_id", "sentence_tamil", "correct_answer", "distractors_json"})

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_text TEXT NOT NULL UNIQUE
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Senses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            meaning TEXT NOT NULL,
            english_translation TEXT NOT NULL,
            pos TEXT NOT NULL,
            UNIQUE(word_id, meaning, english_translation, pos),
            FOREIGN KEY(word_id) REFERENCES Words(id) ON DELETE CASCADE
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            sense_id INTEGER NOT NULL,
            sentence_tamil TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            distractors_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(word_id) REFERENCES Words(id) ON DELETE CASCADE,
            FOREIGN KEY(sense_id) REFERENCES Senses(id) ON DELETE CASCADE,
            UNIQUE(word_id, sense_id, sentence_tamil)
        )
        """
    )
    conn.commit()


def load_wordnet() -> dict[str, Any]:
    if not WORDNET_PATH.exists():
        return {}
    with WORDNET_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def upsert_word(conn: sqlite3.Connection, word: str) -> int:
    conn.execute("INSERT OR IGNORE INTO Words(word_text) VALUES (?)", (word,))
    row = conn.execute("SELECT id FROM Words WHERE word_text = ?", (word,)).fetchone()
    if row is None:
        raise RuntimeError(f"Unable to upsert word: {word}")
    return int(row["id"])


def upsert_sense(conn: sqlite3.Connection, word_id: int, meaning: str, english_translation: str, pos: str) -> int:
    conn.execute(
        """
        INSERT OR IGNORE INTO Senses(word_id, meaning, english_translation, pos)
        VALUES (?, ?, ?, ?)
        """,
        (word_id, meaning, english_translation, pos),
    )
    row = conn.execute(
        """
        SELECT id FROM Senses
        WHERE word_id = ? AND meaning = ? AND english_translation = ? AND pos = ?
        """,
        (word_id, meaning, english_translation, pos),
    ).fetchone()
    if row is None:
        raise RuntimeError("Unable to upsert sense")
    return int(row["id"])


def count_challenges_for_word(conn: sqlite3.Connection, word: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM Challenges c
        JOIN Words w ON c.word_id = w.id
        WHERE w.word_text = ?
        """,
        (word,),
    ).fetchone()
    return int(row["c"] if row else 0)


def generate_distractors(base_word: str, pos: str) -> list[str]:
    pos_norm = (pos or "").strip().lower()

    if pos_norm == "noun":
        suffixes = ["இல்", "ஐ", "க்கு"]
    elif pos_norm == "verb":
        suffixes = ["கிறான்", "கிறது", "தார்"]
    else:
        suffixes = ["இல்", "க்கு", "கிறது"]

    distractors = [f"{base_word}{s}" for s in suffixes]
    unique: list[str] = []
    for item in distractors:
        if item not in unique:
            unique.append(item)
    return unique[:3]


def _extract_json_from_text(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _resolve_model() -> str:
    global _RESOLVED_MODEL
    if _RESOLVED_MODEL:
        return _RESOLVED_MODEL

    tags_url = OLLAMA_URL.replace("/api/generate", "/api/tags")
    try:
        response = requests.get(tags_url, timeout=10)
        response.raise_for_status()
        payload = response.json()
        installed = [m.get("name", "") for m in payload.get("models", []) if isinstance(m, dict)]
    except Exception:
        _RESOLVED_MODEL = PREFERRED_MODEL
        return _RESOLVED_MODEL

    if PREFERRED_MODEL in installed:
        _RESOLVED_MODEL = PREFERRED_MODEL
        return _RESOLVED_MODEL

    fallback = ["qwen2:1.5b", "qwen:1.5b", "qwen2:latest", "qwen:latest"]
    for candidate in fallback:
        if candidate in installed:
            print(f"[WARN] Model '{PREFERRED_MODEL}' unavailable. Using '{candidate}'.")
            _RESOLVED_MODEL = candidate
            return _RESOLVED_MODEL

    _RESOLVED_MODEL = installed[0] if installed else PREFERRED_MODEL
    return _RESOLVED_MODEL


def _normalize_sentence_with_blank(sentence: str, word: str, correct_answer: str) -> str | None:
    text = (sentence or "").strip()
    if not text:
        return None

    # Normalize alternative blank styles into the required token
    text = text.replace("_____", "______")
    text = text.replace("_______", "______")
    text = text.replace("________", "______")

    # If blank not present, try replacing answer tokens with blank
    if "______" not in text:
        for token in [correct_answer, word]:
            token = (token or "").strip()
            if token and token in text:
                text = text.replace(token, "______", 1)
                break

    # Ensure exactly one blank token
    if "______" not in text:
        return None

    if text.count("______") > 1:
        first = text.replace("______", "<<BLANK>>", 1)
        text = first.replace("______", "").replace("<<BLANK>>", "______")

    return text if text.count("______") == 1 else None


def generate_sentence(word: str, sense: dict[str, str], correct_answer: str) -> tuple[str | None, str | None]:
    prompt = (
        "Create one natural Tamil fill-in-the-blank sentence for language learning. "
        f"Target word: '{word}'. Intended meaning: '{sense['meaning']}' ({sense['english_translation']}). "
        f"POS: {sense['pos']}. Correct answer form: '{correct_answer}'. "
        "Return ONLY valid JSON with keys: sentence_with_blank, explanation. "
        "Sentence must contain exactly one '______' blank in place of the target."
    )

    payload = {
        "model": _resolve_model(),
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.4, "top_p": 0.9},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        outer = response.json()
        raw = outer.get("response")
        if not raw:
            return None, "Ollama response missing 'response'"

        parsed = _extract_json_from_text(raw)
        sentence = str(
            parsed.get("sentence_with_blank")
            or parsed.get("sentence")
            or parsed.get("sentence_tamil")
            or ""
        ).strip()
        if not sentence:
            return None, "Missing sentence_with_blank"

        normalized = _normalize_sentence_with_blank(sentence, word, correct_answer)
        if not normalized:
            return None, "Sentence must contain exactly one blank token"
        return normalized, None
    except requests.RequestException as exc:
        return None, f"API error: {exc}"
    except (json.JSONDecodeError, ValueError) as exc:
        return None, f"JSON parse error: {exc}"
    except Exception as exc:
        return None, f"Unexpected error: {exc}"


def choose_two_senses(word: str, wordnet: dict[str, Any]) -> list[dict[str, str]]:
    if word in wordnet and isinstance(wordnet[word], dict):
        senses = wordnet[word].get("senses", [])
        normalized: list[dict[str, str]] = []
        for item in senses:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "meaning": str(item.get("meaning_ta") or item.get("meaning_en") or "அர்த்தம்").strip(),
                    "english_translation": str(item.get("meaning_en") or "meaning").strip(),
                    "pos": str(item.get("pos") or "Noun").strip().title(),
                }
            )
        if len(normalized) >= 2:
            return normalized[:2]

    return [
        {
            "meaning": f"{word} (பெயர்ச்சொல் பயன்பாடு)",
            "english_translation": f"{word} as noun",
            "pos": "Noun",
        },
        {
            "meaning": f"{word} (வினைச்சொல் பயன்பாடு)",
            "english_translation": f"{word} as verb",
            "pos": "Verb",
        },
    ]


def build_correct_answer(word: str, pos: str) -> str:
    if (pos or "").strip().lower() == "verb":
        return f"{word}கிறான்"
    return word


def build_fallback_sentence(word: str, sense: dict[str, str]) -> str:
    pos = (sense.get("pos") or "").strip().lower()
    meaning = (sense.get("meaning") or "").strip()

    if pos == "verb":
        return f"இந்த செயலை விவரிக்க சரியான சொல் ______; இதன் அர்த்தம்: {meaning}."
    return f"இந்த சூழலில் பொருத்தமான சொல் ______; இது '{word}' என்பதின் அர்த்தம்: {meaning}."


def save_challenge(
    conn: sqlite3.Connection,
    word_id: int,
    sense_id: int,
    sentence_tamil: str,
    correct_answer: str,
    distractors: list[str],
) -> bool:
    try:
        conn.execute(
            """
            INSERT INTO Challenges(word_id, sense_id, sentence_tamil, correct_answer, distractors_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (word_id, sense_id, sentence_tamil, correct_answer, json.dumps(distractors, ensure_ascii=False)),
        )
        conn.commit()  # immediate commit per requirement
        return True
    except sqlite3.IntegrityError:
        return False


def run_bulk_generation() -> None:
    wordnet = load_wordnet()
    new_challenges = 0
    failed_calls = 0

    with get_connection() as conn:
        initialize_database(conn)

        iterator = tqdm(SEED_WORDS, desc="Generating", unit="word") if tqdm else SEED_WORDS

        for word in iterator:
            existing_count = count_challenges_for_word(conn, word)
            if existing_count >= TARGET_CHALLENGES_PER_WORD:
                print(f"Skipping {word} - already generated")
                continue

            word_id = upsert_word(conn, word)
            senses = choose_two_senses(word, wordnet)

            for sense in senses:
                current_count = count_challenges_for_word(conn, word)
                if current_count >= TARGET_CHALLENGES_PER_WORD:
                    break

                sense_id = upsert_sense(
                    conn,
                    word_id=word_id,
                    meaning=sense["meaning"],
                    english_translation=sense["english_translation"],
                    pos=sense["pos"],
                )

                correct_answer = build_correct_answer(word, sense["pos"])
                distractors = [d for d in generate_distractors(word, sense["pos"]) if d != correct_answer]
                while len(distractors) < 3:
                    distractors.append(f"{word}{len(distractors) + 1}")
                distractors = distractors[:3]

                generated = False
                for _ in range(MAX_GENERATION_TRIES_PER_SENSE):
                    sentence, error = generate_sentence(word, sense, correct_answer)
                    if sentence is None:
                        failed_calls += 1
                        if error:
                            print(f"[ERROR] {word} ({sense['pos']}): {error}")
                        time.sleep(RETRY_DELAY_SECONDS)
                        continue

                    inserted = save_challenge(
                        conn,
                        word_id=word_id,
                        sense_id=sense_id,
                        sentence_tamil=sentence,
                        correct_answer=correct_answer,
                        distractors=distractors,
                    )
                    if inserted:
                        new_challenges += 1
                        generated = True
                        break

                    time.sleep(RETRY_DELAY_SECONDS)

                if not generated:
                    fallback_sentence = build_fallback_sentence(word, sense)
                    inserted = save_challenge(
                        conn,
                        word_id=word_id,
                        sense_id=sense_id,
                        sentence_tamil=fallback_sentence,
                        correct_answer=correct_answer,
                        distractors=distractors,
                    )
                    if inserted:
                        new_challenges += 1
                        print(f"[WARN] Used fallback sentence for {word} ({sense['pos']})")
                    else:
                        print(f"[WARN] Could not generate valid challenge for {word} ({sense['pos']})")

    print("\n========================================")
    print(f"Total new challenges added: {new_challenges}")
    print(f"Total failed LLM calls: {failed_calls}")
    print("========================================")


if __name__ == "__main__":
    run_bulk_generation()
