from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─────────────────────────────────────────────
# Resume Analysis
# ─────────────────────────────────────────────

class ResumeAnalysisResponse(BaseModel):
    session_id: str
    job_role: str
    skills_found: List[str] = []
    experience_summary: str = ""
    strengths: List[str] = []
    gaps: List[str] = []
    overall_fit_score: float = Field(0.0, ge=0, le=100)
    suggested_focus_areas: List[str] = []


# ─────────────────────────────────────────────
# Interview / Questions
# ─────────────────────────────────────────────

class NextQuestionRequest(BaseModel):
    session_id: str
    question_number: int = 1
    last_answer_transcript: Optional[str] = None
    duration_seconds: Optional[float] = None


class NextQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    question: str
    question_type: str = ""   # e.g. "behavioural", "technical", "situational"
    hint: Optional[str] = None


# ─────────────────────────────────────────────
# Feedback / Scoring
# ─────────────────────────────────────────────

class ContentScore(BaseModel):
    overall_score: float = Field(0.0, ge=0, le=100)
    relevance_score: float = Field(0.0, ge=0, le=100)
    depth_score: float = Field(0.0, ge=0, le=100)
    star_score: float = Field(0.0, ge=0, le=100)
    feedback: str = ""
    suggestions: List[str] = []


class DeliveryScore(BaseModel):
    filler_count: int = 0
    filler_words_found: Dict[str, int] = {}
    wpm: Optional[float] = None
    word_count: int = 0
    star_signals: Dict[str, bool] = {}
    delivery_score: float = Field(0.0, ge=0, le=100)


class FeedbackRequest(BaseModel):
    session_id: str
    question_number: int
    question: str
    transcript: str
    duration_seconds: Optional[float] = None


class FeedbackResponse(BaseModel):
    session_id: str
    question_number: int
    content_score: ContentScore
    delivery_score: DeliveryScore


# ─────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────

class ReportRequest(BaseModel):
    session_id: str


class ReportResponse(BaseModel):
    session_id: str
    job_role: str
    completed_at: str
    total_questions: int
    average_content_score: float
    average_delivery_score: float
    overall_score: float
    ai_summary: Dict[str, Any] = {}
    answers: List[Dict[str, Any]] = []


# ─────────────────────────────────────────────
# Sessions
# ─────────────────────────────────────────────

class SessionSummary(BaseModel):
    session_id: str
    job_role: Optional[str] = None
    status: str = "active"
    overall_score: Optional[float] = None
    completed_at: Optional[str] = None
