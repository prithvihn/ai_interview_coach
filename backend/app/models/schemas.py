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
    preferred_category: Optional[str] = None  # hr, communication, technical, behavioural, situational, motivational


class NextQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    question: str
    question_type: str = ""   # hr, communication, behavioural, technical, situational, motivational
    hint: Optional[str] = None


# ─────────────────────────────────────────────
# Feedback / Scoring — Content (AI-scored)
# ─────────────────────────────────────────────

class MomentAnnotation(BaseModel):
    """A piece of feedback pinned to an exact quote from the transcript."""
    quote: str = ""                 # exact words from the transcript
    type: str = ""                  # "strength" | "weakness" | "filler" | "vague" | "off-topic" | "good-example"
    issue: str = ""                 # what the problem or strength is
    suggestion: str = ""            # actionable fix (for weaknesses) or reinforcement (for strengths)


class ContentScore(BaseModel):
    overall_score: float = Field(0.0, ge=0, le=100)
    relevance_score: float = Field(0.0, ge=0, le=100)
    depth_score: float = Field(0.0, ge=0, le=100)
    star_score: float = Field(0.0, ge=0, le=100)
    clarity_score: float = Field(0.0, ge=0, le=100)        # how clear & structured the answer is
    confidence_score: float = Field(0.0, ge=0, le=100)      # confidence conveyed through language
    feedback: str = ""                                       # 3-4 sentence honest assessment
    critical_mistakes: List[str] = []                        # things that would hurt in a real interview
    moment_annotations: List[MomentAnnotation] = []          # feedback pinned to transcript quotes
    suggestions: List[str] = []                              # actionable improvement tips


# ─────────────────────────────────────────────
# Feedback / Scoring — Delivery (algorithmically analysed)
# ─────────────────────────────────────────────

class FillerAnnotation(BaseModel):
    """A filler word pinned to the sentence it appears in."""
    word: str = ""
    sentence: str = ""              # the full sentence containing the filler
    position: int = 0               # which sentence number (1-indexed)


class DeliveryScore(BaseModel):
    # ── Filler analysis ──
    filler_count: int = 0
    filler_words_found: Dict[str, int] = {}
    filler_annotations: List[FillerAnnotation] = []         # filler words in context

    # ── Pace ──
    wpm: Optional[float] = None
    word_count: int = 0
    pace_assessment: str = ""       # "too_brief" | "too_slow" | "good" | "too_fast" | "rambling"

    # ── Sentence-level metrics ──
    sentence_count: int = 0
    avg_sentence_length: float = 0.0
    longest_sentence: str = ""
    shortest_sentence: str = ""

    # ── Confidence & hedging ──
    hedging_phrases: List[str] = []                         # "I think", "maybe", "kind of" found
    hedging_count: int = 0
    confidence_markers: Dict[str, List[str]] = {}           # {"strong": [...], "weak": [...]}
    confidence_ratio: float = 0.0                           # strong / (strong+weak), 0-1

    # ── Repetition ──
    repetition_flags: List[str] = []                        # repeated words/phrases flagged

    # ── Vocabulary ──
    vocabulary_richness: float = 0.0                        # type-token ratio (unique/total), 0-1

    # ── Structure ──
    star_signals: Dict[str, bool] = {}
    structure_score: float = Field(0.0, ge=0, le=100)       # opening / body / conclusion
    structure_notes: str = ""                                # explanation of structure assessment

    # ── Composite ──
    delivery_score: float = Field(0.0, ge=0, le=100)


# ─────────────────────────────────────────────
# Improvement Tracking — Cross-session trends
# ─────────────────────────────────────────────

class ImprovementTrends(BaseModel):
    sessions_compared: int = 0
    filler_rate_trend: str = "no_data"      # "improving" | "stable" | "worsening" | "no_data"
    content_score_trend: str = "no_data"
    delivery_score_trend: str = "no_data"
    confidence_trend: str = "no_data"
    biggest_improvement: Optional[str] = None
    biggest_regression: Optional[str] = None
    filler_rate_history: List[float] = []   # per-answer filler rates (newest last)
    content_score_history: List[float] = [] # per-answer content scores
    delivery_score_history: List[float] = []
    confidence_history: List[float] = []


# ─────────────────────────────────────────────
# Feedback Request / Response
# ─────────────────────────────────────────────

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
    improvement_trends: Optional[ImprovementTrends] = None


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
    improvement_trends: Optional[ImprovementTrends] = None


# ─────────────────────────────────────────────
# Sessions
# ─────────────────────────────────────────────

class SessionSummary(BaseModel):
    session_id: str
    job_role: Optional[str] = None
    status: str = "active"
    overall_score: Optional[float] = None
    completed_at: Optional[str] = None
