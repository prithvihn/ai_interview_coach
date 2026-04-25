import json
import os
from datetime import datetime
from app.config import settings
from app.services.ai_service import generate_session_report
from app.services.session_store import load_session, save_session, list_all_sessions


async def build_report(session_id: str) -> dict | None:
    """
    Assemble the final interview report:
    1. Load the session data.
    2. Call AI for an overall narrative summary.
    3. Compute aggregate scores.
    4. Persist the final report and return it.
    """
    session = load_session(session_id)
    if not session:
        return None

    # Compute aggregate scores from individual answers
    answers = session.get("answers", [])
    if not answers:
        return None

    content_scores = [a["scores"].get("overall_score", 0) for a in answers if "scores" in a]
    delivery_scores = [a.get("delivery_score", {}).get("delivery_score", 0) for a in answers]

    avg_content = round(sum(content_scores) / len(content_scores), 1) if content_scores else 0
    avg_delivery = round(sum(delivery_scores) / len(delivery_scores), 1) if delivery_scores else 0
    overall = round((avg_content + avg_delivery) / 2, 1)

    # AI narrative summary
    ai_summary = await generate_session_report(session_id)

    report = {
        "session_id": session_id,
        "job_role": session.get("job_role"),
        "completed_at": datetime.utcnow().isoformat(),
        "total_questions": len(answers),
        "average_content_score": avg_content,
        "average_delivery_score": avg_delivery,
        "overall_score": overall,
        "ai_summary": ai_summary,
        "answers": answers,
    }

    # Persist report into session
    session["report"] = report
    session["status"] = "completed"
    save_session(session_id, session)

    return report


def list_sessions() -> list:
    """Return summary info for all sessions."""
    sessions = list_all_sessions()
    summaries = []
    for s in sessions:
        summaries.append({
            "session_id": s.get("session_id"),
            "job_role": s.get("job_role"),
            "status": s.get("status", "active"),
            "overall_score": s.get("report", {}).get("overall_score"),
            "completed_at": s.get("report", {}).get("completed_at"),
        })
    return summaries


def get_session(session_id: str) -> dict | None:
    """Return a single session by ID."""
    return load_session(session_id)
