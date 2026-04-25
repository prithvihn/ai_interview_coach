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


async def score_answer_with_ai(
    session_id: str,
    question: str,
    answer: str,
) -> dict:
    """
    Use gpt-4o-mini to score a candidate's answer for content quality.
    """
    client = _get_client()
    system_prompt = _load_prompt("score_answer")

    session = load_session(session_id)
    user_message = json.dumps({
        "job_role": session.get("job_role") if session else "Unknown",
        "question": question,
        "answer": answer,
    })

    response = await client.chat.completions.create(
        model=settings.GPT4O_MINI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    return json.loads(response.choices[0].message.content)


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
