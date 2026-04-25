from fastapi import APIRouter, HTTPException
from app.models.schemas import ReportRequest, ReportResponse
from app.services.report_builder import build_report

router = APIRouter()


@router.post("/report", response_model=ReportResponse)
async def generate_report(payload: ReportRequest):
    """
    Assemble the final interview report for a completed session.
    Reads persisted Q&A data and generates an AI summary.
    """
    report = await build_report(payload.session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Session not found or incomplete.")
    return report
