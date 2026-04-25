from app.services.ai_service import score_answer_with_ai
from app.services.session_store import load_session, save_session


async def analyse_content(
    session_id: str,
    question: str,
    answer: str,
    delivery_data: dict | None = None,
) -> dict:
    """
    Score an answer's content using AI — with delivery data for holistic feedback.

    The AI receives both the transcript AND the algorithmic delivery analysis
    so it can tie content feedback to delivery observations (e.g., "when you said
    'I think I maybe helped,' the hedging undermines your actual contribution").

    Persists the scored Q&A into the session for improvement tracking.
    """
    scores = await score_answer_with_ai(
        session_id=session_id,
        question=question,
        answer=answer,
        delivery_data=delivery_data,
    )

    # Persist the scored Q&A into the session (with both content + delivery)
    session = load_session(session_id)
    if session:
        session.setdefault("answers", []).append({
            "question": question,
            "answer": answer,
            "scores": scores,
            "delivery_metrics": delivery_data or {},
        })
        save_session(session_id, session)

    return scores
