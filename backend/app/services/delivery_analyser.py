import re
from typing import Optional


# Common filler words to detect
FILLER_WORDS = [
    "um", "uh", "like", "you know", "basically", "literally",
    "actually", "so", "right", "okay", "kind of", "sort of",
    "i mean", "you see", "well",
]


def analyse_delivery(transcript: str, duration_seconds: Optional[float] = None) -> dict:
    """
    Analyse the delivery quality of a spoken answer transcript.

    Returns a dict with:
    - filler_count: total filler word occurrences
    - filler_words_found: dict mapping filler → count
    - wpm: words per minute (if duration provided)
    - word_count: total words
    - star_signals: detected STAR method signals
    - delivery_score: 0–100 composite score
    """
    text = transcript.lower()
    words = text.split()
    word_count = len(words)

    # --- Filler word analysis ---
    filler_found: dict[str, int] = {}
    for filler in FILLER_WORDS:
        pattern = r"\b" + re.escape(filler) + r"\b"
        matches = re.findall(pattern, text)
        if matches:
            filler_found[filler] = len(matches)

    filler_count = sum(filler_found.values())

    # --- WPM ---
    wpm = None
    if duration_seconds and duration_seconds > 0:
        wpm = round((word_count / duration_seconds) * 60, 1)

    # --- STAR method signal detection ---
    star_signals = _detect_star_signals(text)

    # --- Composite delivery score (0–100) ---
    delivery_score = _calculate_delivery_score(
        filler_count=filler_count,
        word_count=word_count,
        wpm=wpm,
        star_signals=star_signals,
    )

    return {
        "filler_count": filler_count,
        "filler_words_found": filler_found,
        "wpm": wpm,
        "word_count": word_count,
        "star_signals": star_signals,
        "delivery_score": delivery_score,
    }


def _detect_star_signals(text: str) -> dict:
    """Check for STAR method keywords in the answer."""
    signals = {
        "situation": bool(re.search(r"\b(situation|context|background|when i|at the time)\b", text)),
        "task": bool(re.search(r"\b(task|responsible|role|my job|needed to|had to)\b", text)),
        "action": bool(re.search(r"\b(i did|i decided|i implemented|i took|i created|i led|i built)\b", text)),
        "result": bool(re.search(r"\b(result|outcome|achieved|improved|increased|reduced|successfully)\b", text)),
    }
    return signals


def _calculate_delivery_score(
    filler_count: int,
    word_count: int,
    wpm: Optional[float],
    star_signals: dict,
) -> int:
    """
    Simple heuristic scoring:
    - Start at 100
    - Deduct for high filler ratio
    - Deduct for WPM outside optimal range (120–160)
    - Add bonus for each STAR signal detected
    """
    score = 60  # base

    # Filler penalty (max -30)
    if word_count > 0:
        filler_ratio = filler_count / word_count
        filler_penalty = min(30, int(filler_ratio * 200))
        score -= filler_penalty

    # WPM scoring (max +20)
    if wpm is not None:
        if 120 <= wpm <= 160:
            score += 20
        elif 100 <= wpm < 120 or 160 < wpm <= 180:
            score += 10

    # STAR bonus (max +20)
    star_count = sum(star_signals.values())
    score += star_count * 5

    return max(0, min(100, score))
