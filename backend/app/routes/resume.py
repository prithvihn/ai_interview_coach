from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.resume_parser import parse_resume
from app.services.ai_service import analyse_resume
from app.models.schemas import ResumeAnalysisResponse
import uuid, os, shutil
from app.config import settings

router = APIRouter()


@router.post("/analyse", response_model=ResumeAnalysisResponse)
async def analyse_resume_endpoint(
    file: UploadFile = File(...),
    job_role: str = Form(...),
):
    """
    Upload a resume (PDF or DOCX) and receive a structured analysis
    along with a new session_id to carry through the interview.
    """
    # Validate file type
    if not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    # Save temp file
    session_id = str(uuid.uuid4())
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    temp_path = os.path.join(settings.UPLOADS_DIR, f"{session_id}{ext}")

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        resume_text = parse_resume(temp_path)
        analysis = await analyse_resume(resume_text, job_role, session_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analysing resume: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return analysis
