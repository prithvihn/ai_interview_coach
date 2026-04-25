from fastapi import APIRouter, HTTPException
from app.models.schemas import SessionSummary
from app.services.report_builder import list_sessions, get_session
from typing import List

router = APIRouter()


@router.get("/sessions", response_model=List[SessionSummary])
async def get_sessions():
    """Return a list of all past interview sessions."""
    return list_sessions()


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str):
    """Return the full data for a single session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session
