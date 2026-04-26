from fastapi import APIRouter
from app.models.schemas import FeedbackRequest, FeedbackResponse, InterviewerReaction
from app.services.content_analyser import analyse_content
from app.services.delivery_analyser import analyse_delivery
from app.services.improvement_tracker import compute_improvement_trends
from app.services.ai_service import generate_interviewer_reaction
from app.services.session_store import load_session

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def get_feedback(payload: FeedbackRequest):
    """
    Score a single answer holistically — content AND delivery together.
    Also generates a natural verbal reaction from the AI interviewer.

    Pipeline:
    1. Run algorithmic delivery analysis (fillers, hedging, confidence, structure)
    2. Pass BOTH the transcript AND delivery data to the AI for content scoring
    3. Compute improvement trends across sessions
    4. Generate a natural HR interviewer verbal reaction
    5. Return the combined, moment-specific feedback + verbal reaction
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

    # Step 4: Generate interviewer verbal reaction
    # Get job_role from session for context
    session = load_session(payload.session_id)
    job_role = session.get("job_role", "") if session else ""

    try:
        reaction_data = await generate_interviewer_reaction(
            question=payload.question,
            transcript=payload.transcript,
            content_score=content if isinstance(content, dict) else content.dict() if hasattr(content, 'dict') else {},
            delivery_data=delivery if isinstance(delivery, dict) else delivery.dict() if hasattr(delivery, 'dict') else {},
            job_role=job_role,
        )
        reaction = InterviewerReaction(
            reaction=reaction_data.get("reaction", ""),
            tone=reaction_data.get("tone", "neutral"),
        )
    except Exception as e:
        # If reaction generation fails, don't block the whole response
        print(f"Interviewer reaction generation failed: {e}")
        reaction = None

    return FeedbackResponse(
        session_id=payload.session_id,
        question_number=payload.question_number,
        content_score=content,
        delivery_score=delivery,
        improvement_trends=trends,
        interviewer_reaction=reaction,
    )
