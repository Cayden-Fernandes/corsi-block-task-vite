# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from uuid import uuid4

from corsi_engine import CorsiEngine
from database_manager import DatabaseManager


app = FastAPI(
    title="Corsi Block Tapping Task API",
    description="Backend API for web-based Corsi task",
    version="1.0.0",
)

# CORS – allow your React dev server
origins = [
    "http://localhost:5173",  # Vite dev
    "http://localhost:3000",  # CRA, if ever used
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: session_id -> CorsiEngine
SESSIONS: Dict[str, CorsiEngine] = {}
db = DatabaseManager()


class CandidateInfo(BaseModel):
    examiner_name: str
    candidate_name: str
    candidate_id: str
    age: str | None = None
    gender: str | None = None
    session: int = 1
    additional_notes: str | None = None


class TrialSubmission(BaseModel):
    session_id: str
    sequence: List[int]
    response: List[int]


@app.get("/")
def root():
    return {"message": "Corsi API is running. See /docs for documentation."}


@app.post("/api/start-session")
def start_session(candidate: CandidateInfo):
    """Create a new engine for this candidate and return session_id + initial state."""
    session_id = str(uuid4())
    engine = CorsiEngine(candidate.dict())
    SESSIONS[session_id] = engine
    state = engine.start_session()
    return {"session_id": session_id, "state": state}


@app.get("/api/sequence/{session_id}")
def get_sequence(session_id: str):
    """Get a new sequence for the current span of this session."""
    engine = SESSIONS.get(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Session not found")

    seq = engine.new_sequence()
    state = engine._state()
    return {"sequence": seq, "state": state}


@app.post("/api/submit-trial")
def submit_trial(sub: TrialSubmission):
    """Submit a response and return correctness + next state + summary if finished."""
    engine = SESSIONS.get(sub.session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Session not found")

    result = engine.submit_trial(sub.sequence, sub.response)
    summary = engine.save_session() if result["finished"] else None
    return {"trial_result": result, "summary": summary}


@app.get("/api/stats")
def database_stats():
    """Database statistics for UI."""
    stats = db.get_stats()
    if not stats:
        raise HTTPException(status_code=500, detail="Database error")

    formatted_recent = [
        {
            "candidate_name": row[0],
            "session_number": row[1],
            "corsi_span": row[2],
            "test_date": row[3],
        }
        for row in stats["recent_sessions"]
    ]

    return {
        "candidate_count": stats["candidate_count"],
        "session_count": stats["session_count"],
        "recent_sessions": formatted_recent,
    }
