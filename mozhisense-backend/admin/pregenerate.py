"""MozhiSense offline pre-generation pipeline.

This script pre-generates Tamil fill-in-the-blank challenges using a local
Ollama model and stores them in SQLite. It is resumable and safe to re-run.
"""

from __future__ import annotations

import json
import random
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

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen:1.5b"
TARGET_CHALLENGES_PER_WORD = 2
MAX_ATTEMPTS_PER_WORD = 12
REQUEST_TIMEOUT_SECONDS = 90
RETRY_DELAY_SECONDS = 0.75

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "mozhisense.db"

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


def _ensure_expected_table(
    conn: sqlite3.Connection,
    table_name: str,
    required_columns: set[str],
) -> None:
    existing_name = _find_table_name_ci(conn, table_name)
    if not existing_name:
        return

    existing_columns = _table_columns(conn, existing_name)
    if required_columns.issubset(existing_columns):
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    legacy_name = f"{table_name}_legacy_{stamp}"
    conn.execute(f"ALTER TABLE {existing_name} RENAME TO {legacy_name}")
    print(
        f"[INFO] Renamed incompatible table '{existing_name}' -> '{legacy_name}' "
        "to preserve old data."
    )


def initialize_database() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_expected_table(conn, "Words", {"id", "word_text"})
        _ensure_expected_table(conn, "Senses", {"id", "word_id", "pos_tag", "meaning_english"})
        _ensure_expected_table(
            conn,
            "Challenges",
            {"id", "word_id", "sense_id", "sentence_tamil", "correct_answer", "distractors_json", "explanation"},
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_text TEXT NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Senses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                pos_tag TEXT NOT NULL,
                meaning_english TEXT NOT NULL,
                UNIQUE(word_id, pos_tag, meaning_english),
                FOREIGN KEY(word_id) REFERENCES Words(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                sense_id INTEGER NOT NULL,
                sentence_tamil TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                distractors_json TEXT NOT NULL,
                explanation TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(word_id) REFERENCES Words(id) ON DELETE CASCADE,
                FOREIGN KEY(sense_id) REFERENCES Senses(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()


def upsert_word(conn: sqlite3.Connection, word: str) -> int:
    conn.execute("INSERT OR IGNORE INTO Words(word_text) VALUES (?)", (word,))
    row = conn.execute("SELECT id FROM Words WHERE word_text = ?", (word,)).fetchone()
    if row is None:
        raise RuntimeError(f"Unable to upsert word: {word}")
    return int(row["id"])


def upsert_sense(conn: sqlite3.Connection, word_id: int, pos_tag: str, meaning_english: str) -> int:
    conn.execute(
        """
        INSERT OR IGNORE INTO Senses(word_id, pos_tag, meaning_english)
        VALUES (?, ?, ?)
        """,
        (word_id, pos_tag, meaning_english),
    )
    row = conn.execute(
        """
        SELECT id FROM Senses
        WHERE word_id = ? AND pos_tag = ? AND meaning_english = ?
        """,
        (word_id, pos_tag, meaning_english),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"Unable to upsert sense for word_id={word_id}")
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


def challenge_sentence_exists(conn: sqlite3.Connection, word_id: int, sentence_tamil: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM Challenges
        WHERE word_id = ? AND sentence_tamil = ?
        LIMIT 1
        """,
        (word_id, sentence_tamil),
    ).fetchone()
    return row is not None


def extract_json_from_text(raw: str) -> dict[str, Any]:
    stripped = raw.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


def _build_prompt(word: str) -> str:
    return (
        "You are generating Tamil vocabulary game data. "
        "Return only one valid JSON object with these keys exactly: "
        "sentence_tamil, correct_answer, distractors, explanation, pos_tag, meaning_english. "
        "Rules: "
        "1) sentence_tamil must contain exactly one blank token '______'. "
        "2) correct_answer must be exactly this target word: "
        f"'{word}'. "
        "3) distractors must be an array of exactly 3 Tamil words, grammatically plausible "
        "in the sentence but semantically wrong for that context. "
        "4) explanation must be short English text (1-2 sentences). "
        "5) pos_tag can be one of N/V/ADJ/ADV/PRON/OTHER. "
        "6) meaning_english is short gloss for the intended sense. "
        "Do not include markdown, code fences, or extra keys."
    )


def resolve_ollama_model(preferred_model: str) -> str:
    global _RESOLVED_MODEL
    if _RESOLVED_MODEL:
        return _RESOLVED_MODEL

    try:
        tags_url = OLLAMA_URL.replace("/api/generate", "/api/tags")
        resp = requests.get(tags_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        models = [m.get("name", "") for m in data.get("models", []) if isinstance(m, dict)]
    except Exception as exc:
        print(f"[WARN] Could not fetch Ollama model list: {exc}. Using '{preferred_model}'.")
        _RESOLVED_MODEL = preferred_model
        return _RESOLVED_MODEL

    if preferred_model in models:
        _RESOLVED_MODEL = preferred_model
        return _RESOLVED_MODEL

    fallback_candidates = ["qwen2:1.5b", "qwen:1.5b", "qwen2:latest", "qwen:latest"]
    for candidate in fallback_candidates:
        if candidate in models:
            print(f"[WARN] Preferred model '{preferred_model}' not found. Using '{candidate}' instead.")
            _RESOLVED_MODEL = candidate
            return _RESOLVED_MODEL

    if models:
        print(f"[WARN] Preferred model '{preferred_model}' not found. Using '{models[0]}' instead.")
        _RESOLVED_MODEL = models[0]
        return _RESOLVED_MODEL

    _RESOLVED_MODEL = preferred_model
    return _RESOLVED_MODEL


def generate_challenge(word: str) -> dict[str, Any] | None:
    model_name = resolve_ollama_model(OLLAMA_MODEL)
    payload = {
        "model": model_name,
        "prompt": _build_prompt(word),
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.5,
            "top_p": 0.9,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        outer = response.json()

        raw_model_output = outer.get("response")
        if not raw_model_output:
            raise ValueError("Ollama response missing 'response' field")

        candidate = extract_json_from_text(raw_model_output)

        normalized = {
            "sentence_tamil": str(candidate.get("sentence_tamil", "")).strip(),
            "correct_answer": str(candidate.get("correct_answer", "")).strip(),
            "distractors": candidate.get("distractors", []),
            "explanation": str(candidate.get("explanation", "")).strip(),
            "pos_tag": str(candidate.get("pos_tag", "OTHER")).strip() or "OTHER",
            "meaning_english": str(candidate.get("meaning_english", "Unknown sense")).strip() or "Unknown sense",
        }
        return normalized
    except requests.RequestException as exc:
        print(f"[ERROR] Ollama request failed for '{word}': {exc}")
        return None
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"[ERROR] Broken JSON from Ollama for '{word}': {exc}")
        return None


def layer1_wordnet_anchor_check(challenge_dict: dict[str, Any]) -> bool:
    _ = challenge_dict
    return True


def layer2_stanza_pos_check(challenge_dict: dict[str, Any]) -> bool:
    _ = challenge_dict
    return True


def layer3_inltk_perplexity_check(challenge_dict: dict[str, Any]) -> bool:
    _ = challenge_dict
    return True


def validate_challenge(challenge_dict: dict[str, Any]) -> bool:
    sentence_tamil = challenge_dict.get("sentence_tamil", "")
    correct_answer = challenge_dict.get("correct_answer", "")
    distractors = challenge_dict.get("distractors", [])
    explanation = challenge_dict.get("explanation", "")

    if not sentence_tamil or "______" not in sentence_tamil:
        return False
    if sentence_tamil.count("______") != 1:
        return False
    if not correct_answer:
        return False
    if not isinstance(distractors, list) or len(distractors) != 3:
        return False
    if any(not isinstance(item, str) or not item.strip() for item in distractors):
        return False
    if correct_answer in distractors:
        return False
    if not explanation:
        return False

    if not layer1_wordnet_anchor_check(challenge_dict):
        return False
    if not layer2_stanza_pos_check(challenge_dict):
        return False
    if not layer3_inltk_perplexity_check(challenge_dict):
        return False
    return True


def save_challenge(conn: sqlite3.Connection, word: str, challenge: dict[str, Any]) -> bool:
    word_id = upsert_word(conn, word)
    sentence_tamil = challenge["sentence_tamil"]

    if challenge_sentence_exists(conn, word_id, sentence_tamil):
        return False

    sense_id = upsert_sense(
        conn,
        word_id=word_id,
        pos_tag=challenge.get("pos_tag", "OTHER"),
        meaning_english=challenge.get("meaning_english", "Unknown sense"),
    )

    conn.execute(
        """
        INSERT INTO Challenges(
            word_id,
            sense_id,
            sentence_tamil,
            correct_answer,
            distractors_json,
            explanation
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            word_id,
            sense_id,
            challenge["sentence_tamil"],
            challenge["correct_answer"],
            json.dumps(challenge["distractors"], ensure_ascii=False),
            challenge["explanation"],
        ),
    )
    conn.commit()
    return True


def process_word(conn: sqlite3.Connection, word: str) -> tuple[int, int]:
    existing = count_challenges_for_word(conn, word)
    if existing >= TARGET_CHALLENGES_PER_WORD:
        print(f"[SKIP] '{word}' already has {existing} challenges")
        return 0, 0

    needed = TARGET_CHALLENGES_PER_WORD - existing
    saved_count = 0
    failed_count = 0
    attempts = 0

    while saved_count < needed and attempts < MAX_ATTEMPTS_PER_WORD:
        attempts += 1
        challenge = generate_challenge(word)
        if challenge is None:
            failed_count += 1
            time.sleep(RETRY_DELAY_SECONDS)
            continue

        if challenge.get("correct_answer") != word:
            failed_count += 1
            time.sleep(RETRY_DELAY_SECONDS)
            continue

        if not validate_challenge(challenge):
            failed_count += 1
            time.sleep(RETRY_DELAY_SECONDS)
            continue

        try:
            inserted = save_challenge(conn, word, challenge)
            if inserted:
                saved_count += 1
                print(f"[OK] '{word}' challenge saved ({saved_count}/{needed})")
            else:
                failed_count += 1
        except sqlite3.DatabaseError as exc:
            failed_count += 1
            print(f"[ERROR] DB insert failed for '{word}': {exc}")

        time.sleep(RETRY_DELAY_SECONDS)

    return saved_count, failed_count


def verify_database(conn: sqlite3.Connection) -> None:
    total = conn.execute("SELECT COUNT(*) AS c FROM Challenges").fetchone()["c"]
    print("\n" + "=" * 72)
    print(f"Total challenges generated: {total}")

    sample = conn.execute(
        """
        SELECT
            c.id,
            w.word_text,
            s.pos_tag,
            s.meaning_english,
            c.sentence_tamil,
            c.correct_answer,
            c.distractors_json,
            c.explanation,
            c.created_at
        FROM Challenges c
        JOIN Words w ON c.word_id = w.id
        JOIN Senses s ON c.sense_id = s.id
        ORDER BY RANDOM()
        LIMIT 1
        """
    ).fetchone()

    if sample is None:
        print("No challenges available yet.")
        print("=" * 72)
        return

    distractors = json.loads(sample["distractors_json"])
    print("Sample Challenge")
    print("-" * 72)
    print(f"ID           : {sample['id']}")
    print(f"Word         : {sample['word_text']}")
    print(f"POS          : {sample['pos_tag']}")
    print(f"Meaning (EN) : {sample['meaning_english']}")
    print(f"Sentence     : {sample['sentence_tamil']}")
    print(f"Correct      : {sample['correct_answer']}")
    print(f"Distractors  : {', '.join(distractors)}")
    print(f"Explanation  : {sample['explanation']}")
    print(f"Created At   : {sample['created_at']}")
    print("=" * 72)


def run() -> None:
    print("Initializing MozhiSense pre-generation pipeline...")
    initialize_database()

    with get_connection() as conn:
        words_iterable = tqdm(SEED_WORDS, desc="Pregenerating", unit="word") if tqdm else SEED_WORDS
        total_saved = 0
        total_failed = 0

        for word in words_iterable:
            saved, failed = process_word(conn, word)
            total_saved += saved
            total_failed += failed
            if not tqdm:
                print(f"[PROGRESS] word='{word}' saved={saved} failed={failed}")

        print("\nGeneration finished.")
        print(f"Saved this run : {total_saved}")
        print(f"Failed attempts: {total_failed}")

        verify_database(conn)


if __name__ == "__main__":
    run()
