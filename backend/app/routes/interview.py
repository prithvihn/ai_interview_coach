from fastapi import APIRouter, HTTPException
from app.models.schemas import NextQuestionRequest, NextQuestionResponse
from app.services.ai_service import generate_next_question
from app.services.delivery_analyser import analyse_delivery

router = APIRouter()


@router.post("/next-question", response_model=NextQuestionResponse)
async def next_question(payload: NextQuestionRequest):
    """
    Given the current session state and (optionally) the candidate's
    last answer transcript, return the next interview question.
    Also runs delivery analysis on the previous answer if provided.
    """
    delivery_metrics = None
    if payload.last_answer_transcript:
        delivery_metrics = analyse_delivery(
            payload.last_answer_transcript,
            payload.duration_seconds,
        )

    question = await generate_next_question(
        session_id=payload.session_id,
        question_number=payload.question_number,
        delivery_metrics=delivery_metrics,
    )

    if not question:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{payload.session_id}' not found. Upload a resume first via /api/analyse.",
        )

    return question
