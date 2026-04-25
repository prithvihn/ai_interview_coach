from openai import AsyncOpenAI
from app.config import settings
from app.services.session_store import load_session, save_session
import json
import os


def _get_client() -> AsyncOpenAI:
    """
    Return an OpenAI-compatible client for GitHub Models.
    GitHub Models uses the standard OpenAI SDK with a custom base_url.
    """
    if not settings.GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN is not set. Add it to your .env file."
        )
    return AsyncOpenAI(
        api_key=settings.GITHUB_TOKEN,
        base_url=settings.GITHUB_MODELS_ENDPOINT,
    )


def _load_prompt(name: str) -> str:
    """Load a system prompt from the prompts directory."""
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", f"{name}.txt"
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _build_previous_answers_summary(session: dict) -> str:
    """
    Build a brief summary of previous answers in this session so the AI
    can compare and track improvement within the session.
    """
    answers = session.get("answers", [])
    if not answers:
        return "No previous answers in this session."

    summaries = []
    for i, a in enumerate(answers, 1):
        scores = a.get("scores", {})
        delivery = a.get("delivery_metrics", {})
        summary = (
            f"Q{i}: content_score={scores.get('overall_score', '?')}/100, "
            f"delivery_score={delivery.get('delivery_score', '?')}/100, "
            f"fillers={delivery.get('filler_count', '?')}, "
            f"confidence_ratio={delivery.get('confidence_ratio', '?')}, "
            f"hedging_count={delivery.get('hedging_count', '?')}"
        )
        summaries.append(summary)

    return " | ".join(summaries)


async def analyse_resume(resume_text: str, job_role: str, session_id: str) -> dict:
    """
    Use gpt-4o to analyse a resume against a target job role.
    Persists analysis result to session store.
    """
    client = _get_client()
    system_prompt = _load_prompt("analyse_resume")
    user_message = f"Job Role: {job_role}\n\nResume:\n{resume_text}"

    response = await client.chat.completions.create(
        model=settings.GPT4O_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    result = json.loads(response.choices[0].message.content)
    result["session_id"] = session_id
    result["job_role"] = job_role

    # Persist to session store
    save_session(session_id, {
        "session_id": session_id,
        "job_role": job_role,
        "resume_analysis": result,
        "questions": [],
        "answers": [],
        "status": "active",
    })

    return result


async def generate_next_question(
    session_id: str,
    question_number: int,
    delivery_metrics: dict | None = None,
    preferred_category: str | None = None,
) -> dict:
    """
    Use gpt-4o-mini to generate the next interview question
    based on the session context.
    """
    session = load_session(session_id)
    if not session:
        return None  # Let the route handle 404

    client = _get_client()
    system_prompt = _load_prompt("generate_questions")

    context = {
        "job_role": session.get("job_role"),
        "resume_analysis": session.get("resume_analysis"),
        "previous_questions": session.get("questions", []),
        "question_number": question_number,
        "last_delivery_metrics": delivery_metrics,
        "preferred_category": preferred_category,
    }

    response = await client.chat.completions.create(
        model=settings.GPT4O_MINI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    result = json.loads(response.choices[0].message.content)
    result["session_id"] = session_id
    result["question_number"] = question_number

    # Append question to session
    session.setdefault("questions", []).append(result.get("question"))
    save_session(session_id, session)

    return result


async def generate_batch_questions(
    session_id: str,
    category: str | None = None,
    count: int = 5,
) -> dict:
    """
    Generate a batch of interview questions at once for a specific category.
    Returns a dict with 'questions' list matching BatchQuestionResponse schema.
    """
    session = load_session(session_id)
    if not session:
        return None

    client = _get_client()
    system_prompt = _load_prompt("generate_batch_questions")

    context = {
        "job_role": session.get("job_role"),
        "resume_analysis": session.get("resume_analysis"),
        "previous_questions": session.get("questions", []),
        "category": category,
        "count": count,
    }

    response = await client.chat.completions.create(
        model=settings.GPT4O_MINI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    result = json.loads(response.choices[0].message.content)

    # Append all generated questions to the session
    questions_list = result.get("questions", [])
    for q in questions_list:
        session.setdefault("questions", []).append(q.get("question"))
    save_session(session_id, session)

    return {
        "session_id": session_id,
        "category": category,
        "questions": questions_list,
    }


async def score_answer_with_ai(
    session_id: str,
    question: str,
    answer: str,
    delivery_data: dict | None = None,
) -> dict:
    """
    Use gpt-4o to score a candidate's answer holistically — content AND delivery together.

    The AI receives:
    - The question and answer transcript
    - Algorithmic delivery analysis (fillers, hedging, confidence, structure)
    - Summary of previous answers for trend comparison

    This produces moment-specific, quote-based, honest feedback.
    """
    client = _get_client()
    system_prompt = _load_prompt("score_answer")

    session = load_session(session_id)
    job_role = session.get("job_role", "Unknown") if session else "Unknown"

    # Build previous answers summary for trend tracking
    previous_summary = _build_previous_answers_summary(session) if session else "No previous answers."

    # Build the comprehensive user message
    user_payload = {
        "job_role": job_role,
        "question": question,
        "answer": answer,
        "delivery_data": _sanitize_delivery_for_ai(delivery_data) if delivery_data else None,
        "previous_answers_summary": previous_summary,
    }

    response = await client.chat.completions.create(
        model=settings.GPT4O_MODEL,  # Use gpt-4o for better analysis quality
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    return json.loads(response.choices[0].message.content)


def _sanitize_delivery_for_ai(delivery_data: dict) -> dict:
    """
    Prepare delivery data for the AI prompt. Include the most useful fields
    without overwhelming the context window.
    """
    if not delivery_data:
        return {}

    return {
        "filler_count": delivery_data.get("filler_count", 0),
        "filler_words_found": delivery_data.get("filler_words_found", {}),
        "filler_annotations": delivery_data.get("filler_annotations", [])[:5],  # cap at 5
        "wpm": delivery_data.get("wpm"),
        "word_count": delivery_data.get("word_count", 0),
        "pace_assessment": delivery_data.get("pace_assessment", ""),
        "sentence_count": delivery_data.get("sentence_count", 0),
        "hedging_phrases": delivery_data.get("hedging_phrases", []),
        "hedging_count": delivery_data.get("hedging_count", 0),
        "confidence_markers": delivery_data.get("confidence_markers", {}),
        "confidence_ratio": delivery_data.get("confidence_ratio", 0),
        "repetition_flags": delivery_data.get("repetition_flags", []),
        "vocabulary_richness": delivery_data.get("vocabulary_richness", 0),
        "structure_score": delivery_data.get("structure_score", 0),
        "structure_notes": delivery_data.get("structure_notes", ""),
        "star_signals": delivery_data.get("star_signals", {}),
        "delivery_score": delivery_data.get("delivery_score", 0),
    }


async def generate_session_report(session_id: str) -> dict:
    """
    Use gpt-4o to produce a final session report summary.
    """
    session = load_session(session_id)
    if not session:
        return None  # Let the route handle 404

    client = _get_client()
    system_prompt = _load_prompt("session_report")

    response = await client.chat.completions.create(
        model=settings.GPT4O_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(session)},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    return json.loads(response.choices[0].message.content)
