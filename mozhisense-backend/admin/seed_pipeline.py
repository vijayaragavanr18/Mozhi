"""MozhiSense seed pipeline.

Parses a structured Tamil polysemy JSON dataset, generates morphology-based distractors,
requests context sentences from local Ollama, validates challenge payloads, and stores
results in SQLite.
"""

from __future__ import annotations

import argparse
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


OLLAMA_URL = "http://localhost:11434/api/generate"
PREFERRED_MODEL = "qwen:1.5b"
REQUEST_TIMEOUT_SECONDS = 90
RETRY_DELAY_SECONDS = 0.5

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "db" / "mozhisense.db"
DEFAULT_JSON_PATH = BASE_DIR / "db" / "tamil_polysemy_data.json"

_RESOLVED_MODEL: str | None = None


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
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
    cursor = conn.cursor()

    _ensure_expected_table(conn, "Words", {"id", "word_text"})
    _ensure_expected_table(conn, "Senses", {"id", "word_id", "meaning", "english_translation", "pos"})
    _ensure_expected_table(conn, "Challenges", {"id", "word_id", "sense_id", "sentence_tamil", "correct_answer", "distractors_json"})

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
            meaning TEXT NOT NULL,
            english_translation TEXT NOT NULL,
            pos TEXT NOT NULL,
            UNIQUE(word_id, meaning, english_translation, pos),
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
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(word_id) REFERENCES Words(id) ON DELETE CASCADE,
            FOREIGN KEY(sense_id) REFERENCES Senses(id) ON DELETE CASCADE,
            UNIQUE(word_id, sense_id, sentence_tamil)
        )
        """
    )

    conn.commit()


def upsert_word(conn: sqlite3.Connection, word_text: str) -> int:
    conn.execute("INSERT OR IGNORE INTO Words(word_text) VALUES (?)", (word_text,))
    row = conn.execute("SELECT id FROM Words WHERE word_text = ?", (word_text,)).fetchone()
    if row is None:
        raise RuntimeError(f"Unable to upsert word: {word_text}")
    return int(row["id"])


def upsert_sense(
    conn: sqlite3.Connection,
    word_id: int,
    meaning: str,
    english_translation: str,
    pos: str,
) -> int:
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


def challenge_exists(conn: sqlite3.Connection, word_id: int, sense_id: int) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM Challenges
        WHERE word_id = ? AND sense_id = ?
        LIMIT 1
        """,
        (word_id, sense_id),
    ).fetchone()
    return row is not None


def generate_distractors(base_word: str, morph_rule: str) -> list[str]:
    if morph_rule == "noun_suffix":
        suffixes = ["இல்", "க்கு", "ஆல்"]
    elif morph_rule == "verb_suffix":
        suffixes = ["கிறான்", "கிறது", "தார்"]
    else:
        suffixes = ["இல்", "க்கு", "கிறது"]

    distractors = [f"{base_word}{suffix}" for suffix in suffixes]
    return distractors[:3]


def derive_correct_form(base_word: str, pos: str, morph_rule: str) -> str:
    pos_norm = (pos or "").strip().lower()

    if morph_rule == "verb_suffix" or "verb" in pos_norm:
        return f"{base_word}கிறேன்"
    if morph_rule == "noun_suffix" or "noun" in pos_norm:
        return base_word
    return base_word


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


def _resolve_model(preferred_model: str = PREFERRED_MODEL) -> str:
    global _RESOLVED_MODEL
    if _RESOLVED_MODEL:
        return _RESOLVED_MODEL

    tags_url = OLLAMA_URL.replace("/api/generate", "/api/tags")
    try:
        resp = requests.get(tags_url, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        installed = [m.get("name", "") for m in payload.get("models", []) if isinstance(m, dict)]
    except Exception:
        _RESOLVED_MODEL = preferred_model
        return _RESOLVED_MODEL

    if preferred_model in installed:
        _RESOLVED_MODEL = preferred_model
        return _RESOLVED_MODEL

    fallback_order = ["qwen2:1.5b", "qwen:1.5b", "qwen2:latest", "qwen:latest"]
    for candidate in fallback_order:
        if candidate in installed:
            print(f"[WARN] Model '{preferred_model}' unavailable. Using '{candidate}'.")
            _RESOLVED_MODEL = candidate
            return _RESOLVED_MODEL

    if installed:
        print(f"[WARN] Model '{preferred_model}' unavailable. Using '{installed[0]}'.")
        _RESOLVED_MODEL = installed[0]
        return _RESOLVED_MODEL

    _RESOLVED_MODEL = preferred_model
    return _RESOLVED_MODEL


def generate_sentence(word: str, sense_data: dict[str, Any], correct_form: str) -> tuple[str, str] | tuple[None, None]:
    meaning = str(sense_data.get("meaning", "")).strip()
    english_translation = str(sense_data.get("english_translation", "")).strip()
    pos = str(sense_data.get("pos", "")).strip()

    prompt = (
        "Generate one natural Tamil sentence for a language-learning quiz. "
        "The sentence must reflect this sense exactly. "
        f"Word: '{word}'. Correct form: '{correct_form}'. POS: '{pos}'. "
        f"Sense meaning: '{meaning}'. English translation: '{english_translation}'. "
        "Return ONLY JSON with keys: sentence_with_blank, explanation. "
        "Replace the target word position with exactly '______' (six underscores). "
        "Do not include markdown or extra keys."
    )

    payload = {
        "model": _resolve_model(PREFERRED_MODEL),
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.4,
            "top_p": 0.9,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        outer = response.json()

        raw_response = outer.get("response")
        if not raw_response:
            raise ValueError("Missing 'response' field in Ollama output")

        data = _extract_json_from_text(raw_response)
        sentence = str(data.get("sentence_with_blank", "")).strip()
        explanation = str(data.get("explanation", "")).strip()

        if not sentence:
            raise ValueError("Ollama response missing 'sentence_with_blank'")

        return sentence, explanation
    except requests.RequestException as exc:
        print(f"[ERROR] Ollama request failed for '{word}': {exc}")
        return None, None
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"[ERROR] Ollama JSON parse failed for '{word}': {exc}")
        return None, None


def validate_challenge(sentence: str, correct_answer: str, distractors: list[str]) -> bool:
    if not sentence or "______" not in sentence:
        return False
    if sentence.count("______") != 1:
        return False
    if not correct_answer:
        return False
    if len(distractors) != 3:
        return False

    # TODO: Add Stanza POS validation check for sentence/correct_answer alignment.
    # TODO: Add iNLTK perplexity check to reject low-fluency generated sentences.
    return True


def save_challenge(
    conn: sqlite3.Connection,
    word_id: int,
    sense_id: int,
    sentence_tamil: str,
    correct_answer: str,
    distractors: list[str],
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO Challenges(
            word_id,
            sense_id,
            sentence_tamil,
            correct_answer,
            distractors_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            word_id,
            sense_id,
            sentence_tamil,
            correct_answer,
            json.dumps(distractors, ensure_ascii=False),
        ),
    )
    conn.commit()


def load_json_data(json_path: Path) -> list[dict[str, Any]]:
    with json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise ValueError("Input JSON root must be a list")
    return payload


def process_dataset(conn: sqlite3.Connection, dataset: list[dict[str, Any]]) -> None:
    items = tqdm(dataset, desc="Processing words", unit="word") if tqdm else dataset

    generated = 0
    skipped = 0
    failed = 0

    for entry in items:
        word = str(entry.get("word", "")).strip()
        senses = entry.get("senses", [])

        if not word or not isinstance(senses, list) or not senses:
            print(f"[WARN] Invalid entry skipped: {entry}")
            failed += 1
            continue

        word_id = upsert_word(conn, word)

        for sense in senses:
            meaning = str(sense.get("meaning", "")).strip()
            english_translation = str(sense.get("english_translation", "")).strip()
            pos = str(sense.get("pos", "")).strip()
            morph_rule = str(sense.get("morph_rule", "")).strip()

            if not meaning or not english_translation or not pos:
                print(f"[WARN] Incomplete sense skipped for word '{word}'.")
                failed += 1
                continue

            sense_id = upsert_sense(
                conn=conn,
                word_id=word_id,
                meaning=meaning,
                english_translation=english_translation,
                pos=pos,
            )

            if challenge_exists(conn, word_id, sense_id):
                skipped += 1
                continue

            correct_form = derive_correct_form(word, pos, morph_rule)
            distractors = generate_distractors(word, morph_rule)
            distractors = [d for d in distractors if d != correct_form][:3]
            while len(distractors) < 3:
                distractors.append(f"{word}{len(distractors) + 1}")

            sentence, _explanation = generate_sentence(word, sense, correct_form)
            if sentence is None:
                failed += 1
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            try:
                if validate_challenge(sentence, correct_form, distractors):
                    save_challenge(
                        conn=conn,
                        word_id=word_id,
                        sense_id=sense_id,
                        sentence_tamil=sentence,
                        correct_answer=correct_form,
                        distractors=distractors,
                    )
                    generated += 1
                else:
                    failed += 1
            except Exception as exc:
                print(f"[ERROR] Failed to save challenge for '{word}': {exc}")
                failed += 1

            time.sleep(RETRY_DELAY_SECONDS)

    print("\nPipeline complete")
    print(f"Generated: {generated}")
    print(f"Skipped  : {skipped}")
    print(f"Failed   : {failed}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MozhiSense seed pipeline")
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON_PATH,
        help="Path to tamil_polysemy_data.json",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to SQLite database",
    )
    args = parser.parse_args()

    if not args.json.exists():
        raise FileNotFoundError(f"Input JSON not found: {args.json}")

    with get_connection(args.db) as conn:
        initialize_database(conn)
        dataset = load_json_data(args.json)
        process_dataset(conn, dataset)


if __name__ == "__main__":
    main()
