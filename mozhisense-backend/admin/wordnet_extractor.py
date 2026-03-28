"""MozhiSense Tamil WordNet extractor.

Extracts senses and examples for seed words using pyiwn, stores them in SQLite,
using deterministic template-based challenge generation (no LLM dependency).
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from tqdm import tqdm
except Exception:
    tqdm = None

try:
    import pyiwn
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "pyiwn is not installed. Install with: pip install pyiwn"
    ) from exc


SEED_WORDS = [
    "படி", "ஆறு", "திங்கள்", "மாலை", "கலை", "கல்", "பார்", "அடி", "கால்", "பால்",
    "மலர்", "தலை", "மழை", "காடு", "நாடு", "வீடு", "ஆடு", "மாடு", "காசு", "பாதி",
    "வில்", "சொல்", "நில்", "செல்", "புல்", "பல்", "கல்வி", "கண்", "பெண்", "மண்",
    "விண்", "பண்", "எண்", "உண்", "தண்", "நண்பு", "பண்பு", "அன்பு", "துன்பு", "இன்பு",
    "கை", "தை", "பை", "மை", "வை", "நை", "கொடு", "சுடு", "படு", "விடு",
]

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "mozhisense.db"
BACKFILL_START_SENSE_ID = 235
COMMIT_BATCH_SIZE = 10

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


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
        WHERE type='table' AND lower(name)=lower(?)
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

    if required_columns.issubset(_table_columns(conn, existing_name)):
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


def upsert_word(conn: sqlite3.Connection, word_text: str) -> int:
    conn.execute("INSERT OR IGNORE INTO Words(word_text) VALUES (?)", (word_text,))
    row = conn.execute("SELECT id FROM Words WHERE word_text = ?", (word_text,)).fetchone()
    if row is None:
        raise RuntimeError(f"Failed to upsert word: {word_text}")
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
        raise RuntimeError("Failed to upsert sense")
    return int(row["id"])


def challenge_exists(conn: sqlite3.Connection, word_id: int, sense_id: int) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM Challenges
        WHERE word_id = ? AND sense_id = ?
        LIMIT 1
        """,
        (word_id, sense_id),
    ).fetchone()
    return row is not None


def _safe_attr(obj: Any, candidates: list[str], default: Any = "") -> Any:
    for name in candidates:
        if not hasattr(obj, name):
            continue
        value = getattr(obj, name)
        try:
            value = value() if callable(value) else value
        except Exception:
            continue
        if value is not None and value != "":
            return value
    return default


def extract_pos(synset: Any) -> str:
    pos = _safe_attr(synset, ["pos", "part_of_speech", "lexical_category"], default="Noun")
    return str(pos).strip().title() or "Noun"


def extract_gloss(synset: Any) -> str:
    gloss = _safe_attr(synset, ["gloss", "definition", "meaning"], default="")
    if isinstance(gloss, (list, tuple)):
        gloss = " ; ".join(str(x) for x in gloss if x)
    return str(gloss).strip() or "அர்த்தம் இல்லை"


def extract_examples(synset: Any) -> list[str]:
    raw = _safe_attr(synset, ["examples", "example_sentences", "example"], default=[])
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if isinstance(raw, (list, tuple, set)):
        out: list[str] = []
        for item in raw:
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    return []


def generate_distractors(conn: sqlite3.Connection | None, word: str, pos: str) -> list[str]:
    """Generate 3 distractors using morphology engine, fallback to random words."""
    distractors: list[str] = []

    try:
        from engine.morphology_engine import get_morphological_distractors

        morph_candidates = get_morphological_distractors(
            word=word,
            pos=str(pos or "").title(),
            correct=word,
        )
        for item in morph_candidates:
            value = str(item).strip()
            if value and value != word and value not in distractors:
                distractors.append(value)
                if len(distractors) >= 3:
                    break
    except Exception:
        pass

    if len(distractors) < 3:
        pos_norm = (pos or "").strip().lower()
        if pos_norm == "noun":
            suffixes = ["இல்", "ஐ", "க்கு"]
        elif pos_norm == "verb":
            suffixes = ["கிறான்", "கிறது", "தார்"]
        else:
            suffixes = ["இல்", "க்கு", "கிறது"]
        for suffix in suffixes:
            candidate = f"{word}{suffix}"
            if candidate != word and candidate not in distractors:
                distractors.append(candidate)
                if len(distractors) >= 3:
                    break

    if conn and len(distractors) < 3:
        try:
            random_words_rows = conn.execute(
                "SELECT word_text FROM Words WHERE word_text != ? ORDER BY RANDOM() LIMIT 20",
                (word,),
            ).fetchall()
            for row in random_words_rows:
                value = str(row[0]).strip()
                if value and value != word and value not in distractors:
                    distractors.append(value)
                    if len(distractors) >= 3:
                        break
        except Exception:
            pass

    while len(distractors) < 3:
        distractors.append(f"{word}{len(distractors) + 1}")

    return distractors[:3]


def generate_sentence_tamil(word: str, meaning: str) -> str:
    """Generate Tamil sentence using deterministic template format.
    
    Template: "______ என்பது இந்த இடத்தில் '{meaning}' என்ற பொருளைக் குறிக்கிறது."
    (Translation: "______ means '{meaning}' in this place.")
    """
    return f"______ என்பது இந்த இடத்தில் '{meaning}' என்ற பொருளைக் குறிக்கிறது."


def inject_blank(sentence: str, word: str) -> str:
    text = (sentence or "").strip()
    if not text:
        return ""

    for blank in ["_____", "_______", "________", "____", "___"]:
        text = text.replace(blank, "______")

    if "______" in text:
        if text.count("______") > 1:
            text = text.replace("______", "<<BLANK>>", 1)
            text = text.replace("______", "")
            text = text.replace("<<BLANK>>", "______")
        return text

    if word in text:
        return text.replace(word, "______", 1)

    return f"{text.rstrip(' .')} ______."


def save_challenge(
    conn: sqlite3.Connection,
    word_id: int,
    sense_id: int,
    sentence_tamil: str,
    correct_answer: str,
    distractors: list[str],
    explanation: str,
) -> bool:
    """Insert challenge without auto-commit (for batch processing)."""
    safe_explanation = (explanation or "").strip()
    if not safe_explanation:
        safe_explanation = "இந்த வாக்கியத்தில் வார்த்தை பயன்படுத்தப்படுகிறது."

    try:
        conn.execute(
            """
            INSERT INTO Challenges(word_id, sense_id, sentence_tamil, correct_answer, distractors_json, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                word_id,
                sense_id,
                sentence_tamil,
                correct_answer,
                json.dumps(distractors, ensure_ascii=False),
                safe_explanation,
            ),
        )
        return True
    except sqlite3.IntegrityError:
        return False


def fetch_senses_without_challenge(conn: sqlite3.Connection, start_sense_id: int = BACKFILL_START_SENSE_ID) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            s.id AS sense_id,
            s.meaning,
            s.english_translation,
            s.pos,
            w.id AS word_id,
            w.word_text
        FROM Senses s
        JOIN Words w ON w.id = s.word_id
        LEFT JOIN Challenges c ON c.sense_id = s.id
        WHERE c.id IS NULL AND s.id >= ?
        ORDER BY s.id
        """,
        (start_sense_id,),
    ).fetchall()


def fetch_all_missing_senses(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM Senses
        WHERE id NOT IN (SELECT sense_id FROM Challenges)
        ORDER BY id
        """
    ).fetchall()


def backfill_missing_challenges(conn: sqlite3.Connection, iwn: Any) -> tuple[int, int]:
    """Backfill missing challenges using deterministic template-based generation.
    
    Commits in batches of COMMIT_BATCH_SIZE (10) rows for performance.
    No LLM dependency - uses template: "______ என்பது இந்த இடத்தில் '{meaning}' என்ற பொருளைக் குறிக்கிறது."
    """
    rows = fetch_senses_without_challenge(conn, start_sense_id=BACKFILL_START_SENSE_ID)
    if not rows:
        return 0, 0

    inserted = 0
    failed = 0
    batch_count = 0
    iterator = tqdm(rows, desc="Backfilling challenges", unit="sense") if tqdm else rows

    for row in iterator:
        word = str(row["word_text"]).strip()
        meaning = str(row["meaning"]).strip()
        pos = str(row["pos"]).strip()
        sense_id = int(row["sense_id"])
        word_id = int(row["word_id"])

        # Use deterministic template-based sentence generation (no LLM calls)
        sentence = generate_sentence_tamil(word, meaning)
        
        # Generate distractors using morphology engine with DB fallback
        distractors = generate_distractors(conn, word, pos)
        distractors = [d for d in distractors if d != word][:3]
        
        # Pad with generic variants if needed
        while len(distractors) < 3:
            distractors.append(f"{word}{len(distractors)+1}")

        # Use Tamil explanation template
        explanation = f"இந்த வாக்கியத்தில் '{word}' என்பது '{meaning}' என்பதைக் குறிக்கப் பயன்படுத்தப்படுகிறது."

        try:
            created = save_challenge(
                conn,
                word_id=word_id,
                sense_id=sense_id,
                sentence_tamil=sentence,
                correct_answer=word,
                distractors=distractors,
                explanation=explanation,
            )
            if created:
                inserted += 1
                batch_count += 1
            else:
                failed += 1
        except Exception as exc:
            failed += 1
            print(f"[ERROR] Failed for word='{word}' sense_id={sense_id}: {exc}")

        # Batch commit every COMMIT_BATCH_SIZE rows
        if batch_count >= COMMIT_BATCH_SIZE:
            try:
                conn.commit()
                batch_count = 0
            except Exception as exc:
                print(f"[ERROR] Batch commit failed: {exc}")

    # Final commit for remaining rows
    try:
        conn.commit()
    except Exception as exc:
        print(f"[ERROR] Final commit failed: {exc}")

    return inserted, failed


def final_completion_sweep(conn: sqlite3.Connection) -> tuple[int, int]:
    """Final sweep to complete all missing challenges for all senses.

    Targets: SELECT * FROM Senses WHERE id NOT IN (SELECT sense_id FROM Challenges)
    """
    rows = fetch_all_missing_senses(conn)
    if not rows:
        final_count = conn.execute("SELECT COUNT(*) FROM Challenges").fetchone()[0]
        print(f"Final Total Challenges: {final_count}")
        return 0, 0

    inserted = 0
    failed = 0
    processed = 0
    batch_count = 0

    for row in rows:
        processed += 1
        sense_id = int(row["id"])
        word_id = int(row["word_id"])
        meaning = str(row["meaning"]).strip()
        pos = str(row["pos"]).strip()

        word_row = conn.execute(
            "SELECT id, word_text FROM Words WHERE id = ?",
            (word_id,),
        ).fetchone()
        if word_row is None:
            failed += 1
            continue

        linked_sense = conn.execute(
            "SELECT 1 FROM Senses WHERE id = ? AND word_id = ? LIMIT 1",
            (sense_id, word_id),
        ).fetchone()
        if linked_sense is None:
            failed += 1
            continue

        word = str(word_row["word_text"]).strip()
        sentence = generate_sentence_tamil(word, meaning)
        explanation = f"இந்த வாக்கியத்தில் '{word}' என்பது '{meaning}' என்பதைக் குறிக்கப் பயன்படுத்தப்படுகிறது."
        distractors = generate_distractors(conn, word, pos)

        created = save_challenge(
            conn,
            word_id=word_id,
            sense_id=sense_id,
            sentence_tamil=sentence,
            correct_answer=word,
            distractors=distractors,
            explanation=explanation,
        )

        if created:
            inserted += 1
            batch_count += 1
        else:
            failed += 1

        if batch_count >= COMMIT_BATCH_SIZE:
            conn.commit()
            batch_count = 0

        if processed % 50 == 0:
            print(f"[Progress] Processed {processed}/{len(rows)} | Inserted: {inserted} | Failed: {failed}")

    if batch_count > 0:
        conn.commit()

    final_count = conn.execute("SELECT COUNT(*) FROM Challenges").fetchone()[0]
    print(f"Final Total Challenges: {final_count}")
    return inserted, failed


def extract_and_seed() -> None:
    iwn = pyiwn.IndoWordNet(pyiwn.Language.TAMIL)

    missing_words: list[str] = []
    inserted_senses = 0
    inserted_challenges = 0

    with get_connection(DB_PATH) as conn:
        initialize_database(conn)

        for word in SEED_WORDS:
            try:
                # Preferred word-level lookup for current pyiwn versions.
                synsets = list(iwn.synsets(word))
            except Exception as exc:
                # Compatibility fallback if environment has a variant API.
                try:
                    all_items = list(iwn.all_synsets())
                    synsets = [s for s in all_items if word in str(_safe_attr(s, ["head_word", "lemma", "lemmas"], default=""))]
                except Exception:
                    print(f"[WARN] Failed to fetch synsets for '{word}': {exc}")
                    continue

            if not synsets:
                print(f"[WARN] No synsets found for: {word}")
                missing_words.append(word)
                continue

            try:
                word_id = upsert_word(conn, word)
            except Exception as exc:
                print(f"[ERROR] DB insert failed for word '{word}': {exc}")
                continue

            for synset in synsets:
                meaning = extract_gloss(synset)
                pos = extract_pos(synset)
                examples = extract_examples(synset)

                try:
                    sense_id = upsert_sense(
                        conn,
                        word_id=word_id,
                        meaning=meaning,
                        english_translation=meaning,
                        pos=pos,
                    )
                    inserted_senses += 1
                except Exception as exc:
                    print(f"[ERROR] DB insert failed for sense '{word}': {exc}")
                    continue

                # Challenge creation is handled in a dedicated backfill pass below.
                _ = examples

        backfill_inserted, backfill_failed = backfill_missing_challenges(conn, iwn)
        inserted_challenges += backfill_inserted

    print("\n========================================")
    print(f"Words with no WordNet synsets: {len(missing_words)}")
    if missing_words:
        print("Missing:", ", ".join(missing_words))
    print(f"Senses processed/inserted     : {inserted_senses}")
    print(f"Challenges inserted           : {inserted_challenges}")
    print(f"Challenges failed             : {backfill_failed}")
    print("========================================")


if __name__ == "__main__":
    with get_connection(DB_PATH) as connection:
        initialize_database(connection)
        inserted_count, failed_count = final_completion_sweep(connection)
    print(f"Final Sweep Inserted: {inserted_count}")
    print(f"Final Sweep Failed  : {failed_count}")
