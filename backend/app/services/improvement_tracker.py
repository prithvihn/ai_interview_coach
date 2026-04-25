"""
Improvement Tracker — Analyse trends across multiple sessions and within
a single session to show the candidate how they're improving (or not).

Computes per-metric trends: filler rate, content scores, delivery scores,
confidence ratio. Identifies biggest improvements and regressions.
"""

from app.services.session_store import list_all_sessions, load_session


def compute_improvement_trends(current_session_id: str) -> dict | None:
    """
    Compare the current session's performance against all past sessions.

    Returns an ImprovementTrends-shaped dict with:
    - sessions_compared: number of past sessions analysed
    - per-metric trends: improving / stable / worsening
    - metric histories: lists of scores for charting
    - biggest improvement/regression
    """
    all_sessions = list_all_sessions()

    # Collect per-answer metrics from ALL sessions (including current)
    all_metrics = []
    for session in all_sessions:
        answers = session.get("answers", [])
        for answer in answers:
            scores = answer.get("scores", {})
            delivery = answer.get("delivery_metrics", {})
            word_count = delivery.get("word_count", 0)

            metric = {
                "session_id": session.get("session_id"),
                "content_score": scores.get("overall_score", 0),
                "delivery_score": delivery.get("delivery_score", 0),
                "filler_count": delivery.get("filler_count", 0),
                "word_count": word_count,
                "filler_rate": (
                    delivery.get("filler_count", 0) / max(word_count, 1)
                ),
                "confidence_ratio": delivery.get("confidence_ratio", 0),
                "hedging_count": delivery.get("hedging_count", 0),
                "vocabulary_richness": delivery.get("vocabulary_richness", 0),
                "structure_score": delivery.get("structure_score", 0),
            }
            all_metrics.append(metric)

    if len(all_metrics) < 2:
        return None  # Not enough data for trends

    # Separate current session metrics from historical
    current_metrics = [m for m in all_metrics if m["session_id"] == current_session_id]
    past_metrics = [m for m in all_metrics if m["session_id"] != current_session_id]

    # Build histories (oldest first)
    filler_rate_history = [m["filler_rate"] for m in all_metrics]
    content_score_history = [m["content_score"] for m in all_metrics]
    delivery_score_history = [m["delivery_score"] for m in all_metrics]
    confidence_history = [m["confidence_ratio"] for m in all_metrics]

    # Count unique past sessions
    past_session_ids = set(m["session_id"] for m in past_metrics)
    sessions_compared = len(past_session_ids)

    # Compute trends
    filler_rate_trend = _compute_trend(filler_rate_history, lower_is_better=True)
    content_score_trend = _compute_trend(content_score_history, lower_is_better=False)
    delivery_score_trend = _compute_trend(delivery_score_history, lower_is_better=False)
    confidence_trend = _compute_trend(confidence_history, lower_is_better=False)

    # Find biggest improvement and regression
    biggest_improvement, biggest_regression = _find_extremes(
        current_metrics, past_metrics
    )

    return {
        "sessions_compared": sessions_compared,
        "filler_rate_trend": filler_rate_trend,
        "content_score_trend": content_score_trend,
        "delivery_score_trend": delivery_score_trend,
        "confidence_trend": confidence_trend,
        "biggest_improvement": biggest_improvement,
        "biggest_regression": biggest_regression,
        "filler_rate_history": [round(x, 4) for x in filler_rate_history],
        "content_score_history": [round(x, 1) for x in content_score_history],
        "delivery_score_history": [round(x, 1) for x in delivery_score_history],
        "confidence_history": [round(x, 2) for x in confidence_history],
    }


def compute_within_session_trends(session_id: str) -> dict:
    """
    Analyse trends WITHIN a single session — how did the candidate's
    performance change from question 1 to the last question?

    Useful for seeing if they warmed up, got nervous, or stayed consistent.
    """
    session = load_session(session_id)
    if not session:
        return {}

    answers = session.get("answers", [])
    if len(answers) < 2:
        return {"note": "Need at least 2 answers for within-session trends."}

    per_q = []
    for i, a in enumerate(answers, 1):
        scores = a.get("scores", {})
        delivery = a.get("delivery_metrics", {})
        word_count = delivery.get("word_count", 0)

        per_q.append({
            "question_number": i,
            "content_score": scores.get("overall_score", 0),
            "delivery_score": delivery.get("delivery_score", 0),
            "filler_rate": delivery.get("filler_count", 0) / max(word_count, 1),
            "confidence_ratio": delivery.get("confidence_ratio", 0),
            "hedging_count": delivery.get("hedging_count", 0),
            "word_count": word_count,
        })

    # Compute per-question trends
    content_scores = [q["content_score"] for q in per_q]
    delivery_scores = [q["delivery_score"] for q in per_q]
    filler_rates = [q["filler_rate"] for q in per_q]
    confidence_ratios = [q["confidence_ratio"] for q in per_q]

    return {
        "per_question": per_q,
        "content_trend": _compute_trend(content_scores, lower_is_better=False),
        "delivery_trend": _compute_trend(delivery_scores, lower_is_better=False),
        "filler_trend": _compute_trend(filler_rates, lower_is_better=True),
        "confidence_trend": _compute_trend(confidence_ratios, lower_is_better=False),
        "warmup_effect": _detect_warmup(per_q),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _compute_trend(values: list, lower_is_better: bool = False) -> str:
    """
    Compute trend direction from a list of values.
    Uses a simple linear comparison of first half vs second half averages.
    """
    if len(values) < 2:
        return "no_data"

    mid = len(values) // 2
    first_half = values[:mid] if mid > 0 else values[:1]
    second_half = values[mid:]

    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)

    diff = avg_second - avg_first

    # Apply a threshold — small changes are "stable"
    threshold = max(abs(avg_first) * 0.1, 0.01)  # 10% change or 0.01 minimum

    if abs(diff) < threshold:
        return "stable"

    if lower_is_better:
        return "improving" if diff < 0 else "worsening"
    else:
        return "improving" if diff > 0 else "worsening"


def _find_extremes(current_metrics: list, past_metrics: list) -> tuple:
    """
    Find the single biggest improvement and biggest regression between
    past performance and current session.
    """
    if not current_metrics or not past_metrics:
        return None, None

    metrics_to_compare = {
        "content_score": False,       # higher is better
        "delivery_score": False,
        "filler_rate": True,          # lower is better
        "confidence_ratio": False,
        "vocabulary_richness": False,
    }

    def avg(lst, key):
        vals = [m[key] for m in lst if key in m]
        return sum(vals) / max(len(vals), 1)

    best_improvement = None
    best_improvement_delta = 0
    worst_regression = None
    worst_regression_delta = 0

    for metric, lower_is_better in metrics_to_compare.items():
        past_avg = avg(past_metrics, metric)
        current_avg = avg(current_metrics, metric)
        delta = current_avg - past_avg

        # Normalize so positive = improvement
        if lower_is_better:
            delta = -delta

        if delta > best_improvement_delta:
            best_improvement_delta = delta
            best_improvement = f"{metric.replace('_', ' ').title()}: improved by {abs(delta):.1f}"

        if delta < worst_regression_delta:
            worst_regression_delta = delta
            worst_regression = f"{metric.replace('_', ' ').title()}: regressed by {abs(delta):.1f}"

    return best_improvement, worst_regression


def _detect_warmup(per_q: list) -> str:
    """
    Detect if there's a warmup effect — first 1-2 answers worse than later ones.
    """
    if len(per_q) < 3:
        return "Not enough questions to detect warmup pattern."

    first_scores = [per_q[0]["content_score"], per_q[0]["delivery_score"]]
    later_scores = []
    for q in per_q[2:]:
        later_scores.extend([q["content_score"], q["delivery_score"]])

    avg_first = sum(first_scores) / len(first_scores)
    avg_later = sum(later_scores) / max(len(later_scores), 1)

    if avg_later > avg_first + 10:
        return "Clear warmup effect detected — performance improved significantly after the first couple of questions."
    elif avg_later > avg_first + 3:
        return "Slight warmup effect — performance improved modestly after initial questions."
    elif avg_first > avg_later + 10:
        return "Reverse pattern — performance dropped after initial questions, possibly fatigue or increasing difficulty."
    else:
        return "Consistent performance across all questions — no significant warmup effect."
