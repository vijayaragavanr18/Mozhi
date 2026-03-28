import os
import random
import threading
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from db.database import (
    init_db,
    get_all_words,
    get_challenges_by_word,
    record_attempt,
    get_session_stats,
    get_weakspots
)
from engine.sense_engine import get_senses
from admin.pregenerate import pregenerate_all

# Initialize FastAPI app
app = FastAPI(title="MozhiSense API", version="1.0.0")

# Setup CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize DB on startup."""
    init_db()


# --- Models ---
class AttemptRequest(BaseModel):
    user_id: str
    word: str
    sense_id: str
    correct: bool


# --- Helper ---
def build_challenge_response(row: dict) -> dict:
    """Helper to shuffle correct answer into distractors."""
    try:
        options = list(row.get("distractors", []))
        options.append(row.get("correct", ""))
        # Filter out any empty strings just in case
        options = [opt for opt in options if opt]
        random.shuffle(options)
        
        response = dict(row)
        response["options"] = options
        return response
    except Exception as e:
        print(f"[MozhiSense API] build_challenge_response error: {e}")
        return row


# --- Endpoints ---

@app.get("/")
async def root():
    return {"status": "MozhiSense API running", "version": "1.0.0"}


@app.get("/words")
async def read_words():
    """Returns list of all words that have challenges in DB."""
    try:
        words = get_all_words()
        return {"words": words}
    except Exception as e:
        print(f"[MozhiSense API] /words error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/challenges/{word}")
async def read_challenges(word: str):
    """Returns list of all challenge objects for a given word."""
    try:
        challenges = get_challenges_by_word(word)
        if not challenges:
            raise HTTPException(status_code=404, detail=f"No challenges found for word '{word}'")
            
        return [build_challenge_response(c) for c in challenges]
    except HTTPException:
        raise
    except Exception as e:
        print(f"[MozhiSense API] /challenges/{word} error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/challenges/{word}/{sense_id}")
async def read_challenge(word: str, sense_id: str):
    """Returns a single challenge matching word and sense_id."""
    try:
        challenges = get_challenges_by_word(word)
        
        # WordNet mapping: fetch the sense's Tamil meaning to match against DB challenges
        senses = get_senses(word)
        target_sense = next((s for s in senses if s.get("id") == sense_id), None)
        
        if not target_sense:
            raise HTTPException(status_code=404, detail=f"Sense '{sense_id}' not found for word '{word}'")
            
        meaning_ta = target_sense.get("meaning_ta")
        
        # Find matching challenge by meaning_ta
        for challenge in challenges:
            if challenge.get("meaning_ta") == meaning_ta:
                return build_challenge_response(challenge)
                
        raise HTTPException(status_code=404, detail=f"No challenge generated for sense '{sense_id}'")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[MozhiSense API] /challenges/{word}/{sense_id} error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/graph/{word}")
async def read_graph(word: str):
    """Returns semantic graph data for vis-network."""
    try:
        senses = get_senses(word)
        if not senses:
            raise HTTPException(status_code=404, detail=f"Word '{word}' not found in WordNet")
            
        nodes = [{"id": "root", "label": word, "group": "root", "size": 30}]
        edges = []
        
        for sense in senses:
            sense_id = sense.get("id")
            pos = sense.get("pos")
            meaning_en = sense.get("meaning_en")
            meaning_ta = sense.get("meaning_ta")
            
            nodes.append({
                "id": sense_id,
                "label": meaning_en,
                "group": pos,
                "pos": pos,
                "meaning_ta": meaning_ta
            })
            
            edges.append({
                "from": "root",
                "to": sense_id,
                "label": pos
            })
            
        return {"nodes": nodes, "edges": edges}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[MozhiSense API] /graph/{word} error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/sessions/attempt")
async def create_attempt(attempt: AttemptRequest):
    """Record a user's challenge attempt."""
    try:
        record_attempt(
            user_id=attempt.user_id,
            word=attempt.word,
            sense_id=attempt.sense_id,
            is_correct=attempt.correct
        )
        xp = 10 if attempt.correct else 0
        return {"status": "recorded", "xp_gained": xp}
    except Exception as e:
        print(f"[MozhiSense API] /sessions/attempt error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/sessions/{user_id}/stats")
async def read_session_stats(user_id: str):
    """Get comprehensive session statistics for a user."""
    try:
        return get_session_stats(user_id)
    except Exception as e:
        print(f"[MozhiSense API] /sessions/{user_id}/stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/sessions/{user_id}/weakspots")
async def read_weakspots(user_id: str):
    """Get list of senses the user struggles with."""
    try:
        return get_weakspots(user_id)
    except Exception as e:
        print(f"[MozhiSense API] /sessions/{user_id}/weakspots error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/admin/pregenerate")
async def trigger_pregenerate(background_tasks: BackgroundTasks, x_admin_key: str = Header(None)):
    """Trigger the offline pre-generation pipeline in a background thread."""
    expected_key = os.environ.get("ADMIN_KEY")
    
    if not expected_key or x_admin_key != expected_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    try:
        # Avoid blocking the request
        thread = threading.Thread(target=pregenerate_all)
        thread.daemon = True
        thread.start()
        
        return {"status": "pre-generation started"}
    except Exception as e:
        print(f"[MozhiSense API] /admin/pregenerate error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
