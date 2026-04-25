from fastapi import APIRouter
from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.services.content_analyser import analyse_content
from app.services.delivery_analyser import analyse_delivery
from app.services.improvement_tracker import compute_improvement_trends

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def get_feedback(payload: FeedbackRequest):
    """
    Score a single answer holistically — content AND delivery together.

    1. Run algorithmic delivery analysis (fillers, hedging, confidence, structure)
    2. Pass BOTH the transcript AND delivery data to the AI for content scoring
       so the AI can reference specific delivery issues in its feedback
    3. Compute improvement trends across sessions
    4. Return the combined, moment-specific feedback
    """
    # Step 1: Deep delivery analysis (algorithmic — fast, deterministic)
    delivery = analyse_delivery(payload.transcript, payload.duration_seconds)

    # Step 2: AI content scoring WITH delivery data for holistic feedback
    content = await analyse_content(
        session_id=payload.session_id,
        question=payload.question,
        answer=payload.transcript,
        delivery_data=delivery,
    )

    # Step 3: Compute improvement trends (cross-session)
    trends = compute_improvement_trends(payload.session_id)

    return FeedbackResponse(
        session_id=payload.session_id,
        question_number=payload.question_number,
        content_score=content,
        delivery_score=delivery,
        improvement_trends=trends,
    )
