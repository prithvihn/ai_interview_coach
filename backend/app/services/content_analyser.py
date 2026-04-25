from app.services.ai_service import score_answer_with_ai
from app.services.session_store import load_session, save_session


async def analyse_content(session_id: str, question: str, answer: str) -> dict:
    """
    Score an answer's content using AI and persist it to the session.
    Returns a structured dict with scores and feedback.
    """
    scores = await score_answer_with_ai(session_id, question, answer)

    # Persist the scored Q&A into the session
    session = load_session(session_id)
    if session:
        session.setdefault("answers", []).append({
            "question": question,
            "answer": answer,
            "scores": scores,
        })
        save_session(session_id, session)

    return scores
