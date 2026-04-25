from fastapi import APIRouter
from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.services.content_analyser import analyse_content
from app.services.delivery_analyser import analyse_delivery

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def get_feedback(payload: FeedbackRequest):
    """
    Score a single answer for content (STAR, relevance, depth)
    and delivery (filler words, WPM, clarity).
    """
    delivery = analyse_delivery(payload.transcript, payload.duration_seconds)
    content = await analyse_content(
        session_id=payload.session_id,
        question=payload.question,
        answer=payload.transcript,
    )
    return FeedbackResponse(
        session_id=payload.session_id,
        question_number=payload.question_number,
        content_score=content,
        delivery_score=delivery,
    )
