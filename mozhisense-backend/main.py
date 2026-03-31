import json
import random
import sqlite3
import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

from engine.morphology_engine import get_morphological_distractors

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db" / "mozhisense.db"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen:1.5b")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "4.5"))
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"


app = FastAPI(title="MozhiSense API", version="1.0.0")

# Dynamic CORS origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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


def _normalize_blank_sentence(word: str, sentence: str) -> str:
    text = (sentence or "").strip()
    if not text:
        return f"______ என்பது இந்த இடத்தில் '{word}' என்ற பொருளைக் குறிக்கிறது."

    for blank in ["____", "_____", "_______", "________"]:
        text = text.replace(blank, "______")

    if "______" in text:
        return text

    if word and word in text:
        return text.replace(word, "______", 1)

    return f"______ {text}"


def _build_generated_distractors(conn: sqlite3.Connection, word: str, pos: str) -> list[str]:
    distractors: list[str] = []

    try:
        morph = get_morphological_distractors(word=word, pos=str(pos or "").title(), correct=word)
        for item in morph:
            value = str(item).strip()
            if value and value != word and value not in distractors:
                distractors.append(value)
            if len(distractors) >= 3:
                break
    except Exception:
        pass

    if len(distractors) < 3:
        rows = conn.execute(
            "SELECT word_text FROM Words WHERE word_text != ? ORDER BY RANDOM() LIMIT 10",
            (word,),
        ).fetchall()
        for row in rows:
            value = str(row["word_text"]).strip()
            if value and value != word and value not in distractors:
                distractors.append(value)
            if len(distractors) >= 3:
                break

    while len(distractors) < 3:
        distractors.append(f"{word}{len(distractors) + 1}")

    return distractors[:3]


def _call_ollama_for_word(word: str) -> dict:
    if not USE_OLLAMA:
        # Return placeholder data when Ollama is disabled
        return {
            "meaning": f"{word} என்பதன் பொருள்",
            "sentence_tamil": f"______ என்பது {word} என்ற பொருளைக் குறிக்கிறது.",
            "explanation": f"இந்த வாக்கியத்தில் '{word}' பயன்படுத்தப்பட்டுள்ளது.",
            "pos": "Noun",
        }
    
    prompt = (
        "You are creating one Tamil vocabulary challenge. "
        f"For the word '{word}', return ONLY valid JSON with keys: "
        "meaning, sentence_tamil, explanation, pos. "
        "Rules: meaning in Tamil, sentence_tamil must contain exactly one '______' blank, "
        "explanation in Tamil, pos one of Noun/Verb/Adjective/Adverb."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "top_p": 0.9, "num_predict": 180},
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT_SECONDS)
    response.raise_for_status()
    outer = response.json()
    raw = str(outer.get("response", "")).strip()
    if not raw:
        raise ValueError("Empty Ollama response")

    parsed = json.loads(raw)
    meaning = str(parsed.get("meaning", "")).strip() or f"{word} என்பதன் பொருள்"
    sentence = _normalize_blank_sentence(word, str(parsed.get("sentence_tamil", "")).strip())
    explanation = str(parsed.get("explanation", "")).strip() or f"இந்த வாக்கியத்தில் '{word}' என்பது '{meaning}' என்பதைக் குறிக்கிறது."
    pos = str(parsed.get("pos", "Noun")).strip().title() or "Noun"

    return {
        "meaning": meaning,
        "sentence_tamil": sentence,
        "explanation": explanation,
        "pos": pos,
    }


def _generate_new_word_data_sync(word: str) -> dict:
    with get_connection() as conn:
        existing = _fetch_random_challenge(conn, "WHERE w.word_text = ?", (word,))
        if existing is not None:
            return _challenge_from_row(existing)

        generated = _call_ollama_for_word(word)
        meaning = generated["meaning"]
        sentence_tamil = generated["sentence_tamil"]
        explanation = generated["explanation"]
        pos = generated["pos"]

        conn.execute("INSERT OR IGNORE INTO Words(word_text) VALUES (?)", (word,))
        word_row = conn.execute("SELECT id FROM Words WHERE word_text = ?", (word,)).fetchone()
        if word_row is None:
            raise RuntimeError(f"Failed to create word '{word}'")
        word_id = int(word_row["id"])

        conn.execute(
            """
            INSERT OR IGNORE INTO Senses(word_id, meaning, english_translation, pos)
            VALUES (?, ?, ?, ?)
            """,
            (word_id, meaning, meaning, pos),
        )
        sense_row = conn.execute(
            """
            SELECT id FROM Senses
            WHERE word_id = ? AND meaning = ? AND english_translation = ? AND pos = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (word_id, meaning, meaning, pos),
        ).fetchone()
        if sense_row is None:
            raise RuntimeError(f"Failed to create sense for '{word}'")
        sense_id = int(sense_row["id"])

        distractors = _build_generated_distractors(conn, word, pos)
        conn.execute(
            """
            INSERT OR IGNORE INTO Challenges(word_id, sense_id, sentence_tamil, correct_answer, distractors_json, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                word_id,
                sense_id,
                sentence_tamil,
                word,
                json.dumps(distractors, ensure_ascii=False),
                explanation,
            ),
        )
        conn.commit()

        created = _fetch_random_challenge(conn, "WHERE w.word_text = ?", (word,))
        if created is None:
            raise RuntimeError(f"Challenge generation completed but fetch failed for '{word}'")
        return _challenge_from_row(created)


async def generate_new_word_data(word: str) -> dict:
    return await asyncio.to_thread(_generate_new_word_data_sync, word)


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
async def get_challenge_by_word(word: str) -> dict:
    try:
        with get_connection() as conn:
            row = _fetch_random_challenge(conn, "WHERE w.word_text = ?", (word,))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if row is not None:
        payload = _challenge_from_row(row)
        payload["generated"] = False
        return payload

    try:
        payload = await generate_new_word_data(word)
        payload["generated"] = True
        return payload
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed for '{word}': {exc}") from exc


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
async def legacy_get_challenges_by_word(word: str) -> list[dict]:
    challenge = await get_challenge_by_word(word)
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
