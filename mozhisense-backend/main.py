import json
import random
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db" / "mozhisense.db"


app = FastAPI(title="MozhiSense API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _load_distractors(raw: str) -> list[str]:
    try:
        parsed = json.loads(raw) if raw else []
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        pass
    return []


def _build_options(correct_answer: str, distractors: list[str]) -> list[str]:
    merged = [correct_answer] + distractors
    seen: set[str] = set()
    options: list[str] = []

    for item in merged:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        options.append(value)

    random.shuffle(options)
    return options


def _challenge_from_row(row: sqlite3.Row) -> dict:
    distractors = _load_distractors(str(row["distractors_json"]))
    correct_answer = str(row["correct_answer"])
    options = _build_options(correct_answer, distractors)

    return {
        "challenge_id": int(row["challenge_id"]),
        "word": str(row["word"]),
        "sense_id": int(row["sense_id"]),
        "meaning": str(row["meaning"]),
        "english_translation": str(row["english_translation"]),
        "pos": str(row["pos"]),
        "sentence_tamil": str(row["sentence_tamil"]),
        "correct_answer": correct_answer,
        "options": options,
        "explanation": str(row["explanation"]),
    }


def _fetch_random_challenge(conn: sqlite3.Connection, where_clause: str = "", params: tuple = ()) -> sqlite3.Row | None:
    query = f"""
        SELECT
            c.id AS challenge_id,
            w.word_text AS word,
            s.id AS sense_id,
            s.meaning AS meaning,
            s.english_translation AS english_translation,
            s.pos AS pos,
            c.sentence_tamil AS sentence_tamil,
            c.correct_answer AS correct_answer,
            c.distractors_json AS distractors_json,
            c.explanation AS explanation
        FROM Challenges c
        JOIN Words w ON w.id = c.word_id
        JOIN Senses s ON s.id = c.sense_id
        {where_clause}
        ORDER BY RANDOM()
        LIMIT 1
    """
    return conn.execute(query, params).fetchone()


def _fetch_senses_by_word(conn: sqlite3.Connection, word: str) -> list[sqlite3.Row]:
    query = """
        SELECT
            s.id AS sense_id,
            w.word_text AS word,
            s.meaning AS meaning,
            s.english_translation AS english_translation,
            s.pos AS pos
        FROM Senses s
        JOIN Words w ON w.id = s.word_id
        WHERE w.word_text = ?
        ORDER BY s.id
    """
    return conn.execute(query, (word,)).fetchall()


class AttemptRequest(BaseModel):
    user_id: str
    word: str
    sense_id: str
    correct: bool


@app.get("/")
def health() -> dict:
    return {"status": "ok", "service": "MozhiSense API"}


@app.get("/api/words")
def get_words() -> list[dict]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, word_text
                FROM Words
                ORDER BY word_text COLLATE NOCASE
                """
            ).fetchall()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return [{"id": int(row["id"]), "word": str(row["word_text"])} for row in rows]


@app.get("/api/challenge/{word}")
def get_challenge_by_word(word: str) -> dict:
    try:
        with get_connection() as conn:
            row = _fetch_random_challenge(conn, "WHERE w.word_text = ?", (word,))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if row is None:
        raise HTTPException(status_code=404, detail=f"No challenge found for word '{word}'")

    return _challenge_from_row(row)


@app.get("/api/word/{word}/senses")
def get_senses_by_word(word: str) -> list[dict]:
    try:
        with get_connection() as conn:
            rows = _fetch_senses_by_word(conn, word)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if not rows:
        raise HTTPException(status_code=404, detail=f"No senses found for word '{word}'")

    return [
        {
            "id": int(row["sense_id"]),
            "word": str(row["word"]),
            "meaning_ta": str(row["meaning"]),
            "meaning_en": str(row["english_translation"]),
            "pos": str(row["pos"]),
        }
        for row in rows
    ]


@app.get("/api/graph/{word}")
def get_graph_by_word(word: str) -> dict:
    senses = get_senses_by_word(word)
    root_id = f"root:{word}"
    return {
        "nodes": [
            {"id": root_id, "label": word, "group": "root", "size": 30},
            *[
                {
                    "id": sense["id"],
                    "label": sense["meaning_en"] or sense["meaning_ta"],
                    "group": sense["pos"],
                    "pos": sense["pos"],
                    "meaning_ta": sense["meaning_ta"],
                }
                for sense in senses
            ],
        ],
        "edges": [{"from": root_id, "to": sense["id"], "label": sense["pos"]} for sense in senses],
    }


@app.get("/api/random-challenge")
def get_random_challenge() -> dict:
    try:
        with get_connection() as conn:
            row = _fetch_random_challenge(conn)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if row is None:
        raise HTTPException(status_code=404, detail="No challenges available")

    return _challenge_from_row(row)


@app.get("/words")
def legacy_get_words() -> dict:
    items = get_words()
    return {"words": [item["word"] for item in items]}


@app.get("/challenges/{word}")
def legacy_get_challenges_by_word(word: str) -> list[dict]:
    challenge = get_challenge_by_word(word)
    return [challenge]


@app.get("/graph/{word}")
def legacy_get_graph(word: str) -> dict:
    return get_graph_by_word(word)


@app.post("/sessions/attempt")
def legacy_record_attempt(payload: AttemptRequest) -> dict:
    return {
        "status": "recorded",
        "xp_gained": 10 if payload.correct else 0,
        "user_id": payload.user_id,
        "word": payload.word,
        "sense_id": payload.sense_id,
        "correct": payload.correct,
    }
