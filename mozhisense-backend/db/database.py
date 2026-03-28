"""
MozhiSense — SQLite Database Module
Handles all persistence for challenges and user sessions.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "db/mozhisense.db"


def _get_connection():
    """Get a SQLite connection with row_factory for dict-like access."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"[MozhiSense DB] Connection error: {e}")
        raise


def init_db():
    """
    Initialize the database — creates the challenges and sessions tables
    if they don't already exist.
    """
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                transliteration TEXT NOT NULL,
                pos TEXT NOT NULL,
                meaning_en TEXT NOT NULL,
                meaning_ta TEXT NOT NULL,
                sentence_ta TEXT NOT NULL,
                sentence_en TEXT NOT NULL,
                correct TEXT NOT NULL,
                distractors TEXT NOT NULL,
                explanation TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                word TEXT NOT NULL,
                sense_id TEXT NOT NULL,
                correct INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()
        print("[MozhiSense DB] Database initialized successfully.")
    except Exception as e:
        print(f"[MozhiSense DB] init_db error: {e}")
        raise


def save_challenge(word: str, transliteration: str, sense: dict, challenge_dict: dict):
    """
    Insert one pre-generated challenge into the challenges table.
    
    Args:
        word: The Tamil word
        transliteration: Romanized form
        sense: Sense dict with id, pos, meaning_en, meaning_ta
        challenge_dict: Dict with sentence_ta, sentence_en, correct, distractors, explanation
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        distractors_json = json.dumps(challenge_dict.get("distractors", []), ensure_ascii=False)

        cursor.execute("""
            INSERT INTO challenges 
            (word, transliteration, pos, meaning_en, meaning_ta,
             sentence_ta, sentence_en, correct, distractors, explanation, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            word,
            transliteration,
            sense.get("pos", ""),
            sense.get("meaning_en", ""),
            sense.get("meaning_ta", ""),
            challenge_dict.get("sentence_ta", ""),
            challenge_dict.get("sentence_en", ""),
            challenge_dict.get("correct", ""),
            distractors_json,
            challenge_dict.get("explanation", ""),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()
        print(f"[MozhiSense DB] Saved challenge for '{word}' — sense: {sense.get('id', 'unknown')}")
    except Exception as e:
        print(f"[MozhiSense DB] save_challenge error: {e}")
        raise


def get_challenges_by_word(word: str) -> list:
    """
    Return all challenges for a given word as a list of dicts.
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM challenges WHERE word = ?", (word,))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            row_dict = dict(row)
            # Parse distractors JSON string back to list
            try:
                row_dict["distractors"] = json.loads(row_dict["distractors"])
            except (json.JSONDecodeError, TypeError):
                row_dict["distractors"] = []
            results.append(row_dict)

        return results
    except Exception as e:
        print(f"[MozhiSense DB] get_challenges_by_word error: {e}")
        return []


def get_all_words() -> list:
    """
    Return a list of all unique words in the challenges table.
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT word FROM challenges")
        rows = cursor.fetchall()
        conn.close()
        return [row["word"] for row in rows]
    except Exception as e:
        print(f"[MozhiSense DB] get_all_words error: {e}")
        return []


def get_weakspots(user_id: str) -> list:
    """
    Return list of {word, sense_id, accuracy} where accuracy < 0.6.
    Identifies senses the user struggles with.
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT word, sense_id,
                   CAST(SUM(correct) AS FLOAT) / COUNT(*) as accuracy
            FROM sessions
            WHERE user_id = ?
            GROUP BY word, sense_id
            HAVING accuracy < 0.6
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "word": row["word"],
                "sense_id": row["sense_id"],
                "accuracy": round(row["accuracy"], 3)
            }
            for row in rows
        ]
    except Exception as e:
        print(f"[MozhiSense DB] get_weakspots error: {e}")
        return []


def record_attempt(user_id: str, word: str, sense_id: str, is_correct: bool):
    """
    Insert one session row recording a user's attempt.
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions (user_id, word, sense_id, correct, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            word,
            sense_id,
            1 if is_correct else 0,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()
        print(f"[MozhiSense DB] Recorded attempt — user={user_id}, word={word}, correct={is_correct}")
    except Exception as e:
        print(f"[MozhiSense DB] record_attempt error: {e}")
        raise


def get_session_stats(user_id: str) -> dict:
    """
    Return comprehensive session statistics for a user:
    {total_attempts, correct_count, accuracy, streak, word_mastery: {word: {senses_mastered, total_senses}}}
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # Total attempts and correct count
        cursor.execute("""
            SELECT COUNT(*) as total, SUM(correct) as correct_count
            FROM sessions WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        total_attempts = row["total"] or 0
        correct_count = row["correct_count"] or 0
        accuracy = round(correct_count / total_attempts, 3) if total_attempts > 0 else 0.0

        # Current streak (consecutive correct answers, most recent first)
        cursor.execute("""
            SELECT correct FROM sessions
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
        streak = 0
        for attempt in cursor.fetchall():
            if attempt["correct"] == 1:
                streak += 1
            else:
                break

        # Word mastery: for each word, how many senses are mastered (accuracy >= 0.6)
        cursor.execute("""
            SELECT word, sense_id,
                   CAST(SUM(correct) AS FLOAT) / COUNT(*) as sense_accuracy
            FROM sessions
            WHERE user_id = ?
            GROUP BY word, sense_id
        """, (user_id,))

        word_mastery = {}
        for r in cursor.fetchall():
            w = r["word"]
            if w not in word_mastery:
                word_mastery[w] = {"senses_mastered": 0, "total_senses": 0}
            word_mastery[w]["total_senses"] += 1
            if r["sense_accuracy"] >= 0.6:
                word_mastery[w]["senses_mastered"] += 1

        conn.close()

        return {
            "total_attempts": total_attempts,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "streak": streak,
            "word_mastery": word_mastery
        }
    except Exception as e:
        print(f"[MozhiSense DB] get_session_stats error: {e}")
        return {
            "total_attempts": 0,
            "correct_count": 0,
            "accuracy": 0.0,
            "streak": 0,
            "word_mastery": {}
        }
