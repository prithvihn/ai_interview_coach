"""
Delivery Analyser — Deep sentence-level analysis of spoken answer transcripts.

Analyses: pace, filler words (in context), hedging language, confidence markers,
repetition, vocabulary richness, sentence structure, STAR signals, and overall
delivery quality. Every metric is pinned to the specific sentence or phrase
it was found in, not just counted as a total.
"""

import re
import math
from typing import Optional
from collections import Counter


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

FILLER_WORDS = [
    "um", "uh", "erm", "ah",
    "like", "you know", "basically", "literally",
    "actually", "so", "right", "okay",
    "kind of", "sort of", "i mean", "you see", "well",
]

HEDGING_PHRASES = [
    "i think", "i guess", "i suppose", "maybe", "probably",
    "perhaps", "kind of", "sort of", "a little bit",
    "not sure", "i'm not sure", "i don't know",
    "it might be", "it could be", "possibly",
    "to be honest", "honestly", "i feel like",
]

STRONG_CONFIDENCE = [
    "i led", "i built", "i created", "i designed", "i implemented",
    "i managed", "i delivered", "i achieved", "i improved",
    "i increased", "i reduced", "i drove", "i launched",
    "i spearheaded", "i initiated", "i resolved", "i ensured",
    "i decided", "i took ownership", "i was responsible",
    "my approach was", "i chose to", "i made sure",
]

WEAK_CONFIDENCE = [
    "i tried", "i attempted", "i sort of", "i kind of",
    "i was just", "i was only", "they told me to",
    "i was asked to", "i had to", "someone else",
    "we did", "it was done", "things happened",
    "i'm not great at", "i struggle with",
]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def analyse_delivery(transcript: str, duration_seconds: Optional[float] = None) -> dict:
    """
    Perform comprehensive delivery analysis on a spoken answer transcript.

    Returns a rich dict matching the DeliveryScore schema with sentence-level
    annotations for every metric.
    """
    if not transcript or not transcript.strip():
        return _empty_result()

    text = transcript.strip()
    text_lower = text.lower()

    # ── Split into sentences ──────────────────────────────────────────────
    sentences = _split_sentences(text)
    sentences_lower = [s.lower() for s in sentences]
    words = text_lower.split()
    word_count = len(words)
    sentence_count = len(sentences)

    # ── Filler analysis (with sentence context) ──────────────────────────
    filler_found, filler_annotations = _analyse_fillers(sentences, sentences_lower)
    filler_count = sum(filler_found.values())

    # ── WPM & pace assessment ─────────────────────────────────────────────
    wpm = None
    if duration_seconds and duration_seconds > 0:
        wpm = round((word_count / duration_seconds) * 60, 1)
    pace_assessment = _assess_pace(word_count, wpm, duration_seconds)

    # ── Sentence-level metrics ────────────────────────────────────────────
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_sentence_length = round(sum(sentence_lengths) / max(len(sentence_lengths), 1), 1)
    longest_sentence = sentences[sentence_lengths.index(max(sentence_lengths))] if sentences else ""
    shortest_sentence = sentences[sentence_lengths.index(min(sentence_lengths))] if sentences else ""

    # ── Hedging language ──────────────────────────────────────────────────
    hedging_found = _detect_patterns(text_lower, HEDGING_PHRASES)

    # ── Confidence markers ────────────────────────────────────────────────
    strong_found = _detect_patterns(text_lower, STRONG_CONFIDENCE)
    weak_found = _detect_patterns(text_lower, WEAK_CONFIDENCE)
    total_conf = len(strong_found) + len(weak_found)
    confidence_ratio = round(len(strong_found) / max(total_conf, 1), 2)

    # ── Repetition detection ──────────────────────────────────────────────
    repetition_flags = _detect_repetitions(words)

    # ── Vocabulary richness (type-token ratio) ────────────────────────────
    unique_words = set(w for w in words if len(w) > 2)  # ignore tiny words
    meaningful_words = [w for w in words if len(w) > 2]
    vocabulary_richness = round(len(unique_words) / max(len(meaningful_words), 1), 2)

    # ── STAR method signal detection ──────────────────────────────────────
    star_signals = _detect_star_signals(text_lower)

    # ── Structure assessment ──────────────────────────────────────────────
    structure_score, structure_notes = _assess_structure(
        sentences, sentences_lower, word_count, star_signals
    )

    # ── Composite delivery score ──────────────────────────────────────────
    delivery_score = _calculate_delivery_score(
        filler_count=filler_count,
        word_count=word_count,
        wpm=wpm,
        star_signals=star_signals,
        hedging_count=len(hedging_found),
        confidence_ratio=confidence_ratio,
        vocabulary_richness=vocabulary_richness,
        structure_score=structure_score,
        repetition_count=len(repetition_flags),
        sentence_count=sentence_count,
    )

    return {
        # Fillers
        "filler_count": filler_count,
        "filler_words_found": filler_found,
        "filler_annotations": filler_annotations,
        # Pace
        "wpm": wpm,
        "word_count": word_count,
        "pace_assessment": pace_assessment,
        # Sentences
        "sentence_count": sentence_count,
        "avg_sentence_length": avg_sentence_length,
        "longest_sentence": longest_sentence[:200],  # cap for response size
        "shortest_sentence": shortest_sentence[:200],
        # Confidence & hedging
        "hedging_phrases": hedging_found,
        "hedging_count": len(hedging_found),
        "confidence_markers": {"strong": strong_found, "weak": weak_found},
        "confidence_ratio": confidence_ratio,
        # Repetition
        "repetition_flags": repetition_flags,
        # Vocabulary
        "vocabulary_richness": vocabulary_richness,
        # Structure
        "star_signals": star_signals,
        "structure_score": structure_score,
        "structure_notes": structure_notes,
        # Composite
        "delivery_score": delivery_score,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _empty_result() -> dict:
    """Return a zeroed-out result for empty transcripts."""
    return {
        "filler_count": 0, "filler_words_found": {}, "filler_annotations": [],
        "wpm": None, "word_count": 0, "pace_assessment": "too_brief",
        "sentence_count": 0, "avg_sentence_length": 0.0,
        "longest_sentence": "", "shortest_sentence": "",
        "hedging_phrases": [], "hedging_count": 0,
        "confidence_markers": {"strong": [], "weak": []},
        "confidence_ratio": 0.0, "repetition_flags": [],
        "vocabulary_richness": 0.0,
        "star_signals": {"situation": False, "task": False, "action": False, "result": False},
        "structure_score": 0.0, "structure_notes": "No transcript provided.",
        "delivery_score": 0.0,
    }


def _split_sentences(text: str) -> list[str]:
    """
    Split transcript into sentences. Handles typical speech patterns
    where punctuation is often missing from speech-to-text output.
    """
    # First try splitting on sentence-ending punctuation
    raw = re.split(r'(?<=[.!?])\s+', text.strip())

    # If we only got 1 chunk (no punctuation), split on common speech pauses
    if len(raw) <= 1 and len(text.split()) > 15:
        # Split on conjunctions and transitions that signal new clauses
        raw = re.split(
            r'\s*(?:,\s+(?:and|but|so|then|because|however|also|actually)\s+|'
            r'\.\s+|\?\s+|!\s+|;\s+)',
            text.strip()
        )

    # Filter out empty strings and very short fragments
    sentences = [s.strip() for s in raw if s.strip() and len(s.strip()) > 3]

    # If still just one big blob, split by word count (every ~15-20 words)
    if len(sentences) <= 1 and len(text.split()) > 20:
        words = text.split()
        sentences = []
        for i in range(0, len(words), 18):
            chunk = " ".join(words[i:i + 18])
            if chunk.strip():
                sentences.append(chunk.strip())

    return sentences if sentences else [text.strip()]


def _analyse_fillers(sentences: list[str], sentences_lower: list[str]) -> tuple[dict, list]:
    """
    Find filler words and annotate them with the sentence they appear in.
    Returns (filler_counts_dict, filler_annotations_list).
    """
    filler_found: dict[str, int] = {}
    annotations = []

    for idx, (original, lower) in enumerate(zip(sentences, sentences_lower)):
        for filler in FILLER_WORDS:
            pattern = r"\b" + re.escape(filler) + r"\b"
            matches = re.findall(pattern, lower)
            if matches:
                filler_found[filler] = filler_found.get(filler, 0) + len(matches)
                annotations.append({
                    "word": filler,
                    "sentence": original[:150],  # cap length
                    "position": idx + 1,
                })

    return filler_found, annotations


def _detect_patterns(text_lower: str, patterns: list[str]) -> list[str]:
    """Return list of patterns that were found in the text."""
    found = []
    for phrase in patterns:
        if re.search(r"\b" + re.escape(phrase) + r"\b", text_lower):
            found.append(phrase)
    return found


def _detect_repetitions(words: list[str]) -> list[str]:
    """
    Flag words or short phrases that are repeated excessively.
    Ignore common stop words and look for meaningful word repetition.
    """
    STOP_WORDS = {
        "the", "a", "an", "is", "was", "are", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "during", "before", "after", "above", "below", "between", "and",
        "but", "or", "nor", "not", "so", "very", "just", "about", "up",
        "out", "if", "than", "then", "that", "this", "it", "its", "my",
        "we", "our", "you", "your", "they", "their", "he", "she", "him",
        "her", "his", "i", "me", "what", "which", "who", "when", "where",
        "how", "all", "each", "every", "both", "few", "more", "most",
        "other", "some", "such", "no", "only", "same", "too",
    }

    meaningful = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    counts = Counter(meaningful)
    total = len(meaningful) if meaningful else 1

    flags = []
    for word, count in counts.most_common(10):
        # Flag if a meaningful word appears more than 3 times
        # and represents more than 3% of meaningful words
        if count >= 3 and (count / total) > 0.03:
            flags.append(f'"{word}" repeated {count} times')

    # Also check for repeated 2-word phrases (bigrams)
    if len(meaningful) >= 4:
        bigrams = [f"{meaningful[i]} {meaningful[i+1]}" for i in range(len(meaningful) - 1)]
        bigram_counts = Counter(bigrams)
        for bigram, count in bigram_counts.most_common(5):
            if count >= 2:
                flags.append(f'phrase "{bigram}" repeated {count} times')

    return flags[:8]  # cap at 8 flags


def _detect_star_signals(text_lower: str) -> dict:
    """Detect STAR (Situation-Task-Action-Result) method signals."""
    return {
        "situation": bool(re.search(
            r"\b(situation|context|background|when i was|at the time|"
            r"there was a|we were facing|the challenge was|the problem was)\b",
            text_lower
        )),
        "task": bool(re.search(
            r"\b(task|responsible for|my role was|my job was|needed to|"
            r"had to|was assigned|was tasked|objective was|goal was)\b",
            text_lower
        )),
        "action": bool(re.search(
            r"\b(i did|i decided|i implemented|i took|i created|i led|"
            r"i built|i developed|i designed|i initiated|i organized|"
            r"my approach|i chose to|i made sure|i set up|i coordinated)\b",
            text_lower
        )),
        "result": bool(re.search(
            r"\b(result|outcome|achieved|improved|increased|reduced|"
            r"successfully|delivered|completed|led to|resulted in|"
            r"impact was|we saved|grew by|decreased)\b",
            text_lower
        )),
    }


def _assess_pace(word_count: int, wpm: Optional[float], duration_seconds: Optional[float]) -> str:
    """Assess speaking pace based on word count and WPM."""
    if word_count < 15:
        return "too_brief"
    if word_count > 400:
        return "rambling"

    if wpm is not None:
        if wpm < 90:
            return "too_slow"
        if wpm > 180:
            return "too_fast"
        return "good"

    # Without duration, assess by word count alone
    if word_count < 40:
        return "too_brief"
    if word_count > 300:
        return "rambling"
    return "good"


def _assess_structure(
    sentences: list[str],
    sentences_lower: list[str],
    word_count: int,
    star_signals: dict,
) -> tuple[float, str]:
    """
    Assess whether the answer has clear structure:
    opening (context), body (details), conclusion (result/summary).
    Returns (score 0-100, explanation string).
    """
    if not sentences or word_count < 10:
        return 0.0, "Answer too short to assess structure."

    notes = []
    score = 30.0  # base

    # ── Opening: does the first sentence set context? ─────────────────────
    first = sentences_lower[0] if sentences_lower else ""
    opening_signals = ["so", "well", "the situation", "when i", "at my", "in my",
                       "there was", "we had", "i was working", "back when"]
    has_opening = any(first.startswith(s) or s in first for s in opening_signals)
    if has_opening:
        score += 15
        notes.append("Good: Answer opens with context.")
    else:
        notes.append("Missing: No clear opening/context setting.")

    # ── Body: does the middle have specific details? ──────────────────────
    mid_text = " ".join(sentences_lower[1:-1]) if len(sentences_lower) > 2 else ""
    detail_signals = ["specifically", "for example", "in particular", "percent",
                      "million", "team of", "over the course", "step", "first", "then", "next"]
    detail_count = sum(1 for s in detail_signals if s in mid_text)
    if detail_count >= 2:
        score += 20
        notes.append("Good: Body contains specific details and examples.")
    elif detail_count == 1:
        score += 10
        notes.append("Partial: Body has some detail but could be more specific.")
    else:
        notes.append("Missing: Body lacks specific details or examples.")

    # ── Conclusion: does the last sentence summarize/show results? ────────
    last = sentences_lower[-1] if sentences_lower else ""
    conclusion_signals = ["result", "outcome", "learned", "takeaway", "overall",
                          "in the end", "ultimately", "that experience", "since then",
                          "which led to", "improved", "successfully"]
    has_conclusion = any(s in last for s in conclusion_signals)
    if has_conclusion:
        score += 15
        notes.append("Good: Answer ends with a clear outcome or takeaway.")
    else:
        notes.append("Missing: No clear conclusion or result statement.")

    # ── STAR bonus ────────────────────────────────────────────────────────
    star_count = sum(star_signals.values())
    if star_count == 4:
        score += 20
        notes.append("Excellent: All four STAR elements (Situation, Task, Action, Result) present.")
    elif star_count >= 3:
        score += 12
        missing = [k for k, v in star_signals.items() if not v]
        notes.append(f"Good: STAR partially present. Missing: {', '.join(missing)}.")
    elif star_count >= 2:
        score += 5
        missing = [k for k, v in star_signals.items() if not v]
        notes.append(f"Partial: Only {star_count}/4 STAR elements. Missing: {', '.join(missing)}.")
    else:
        notes.append("Missing: No STAR structure detected. Use Situation→Task→Action→Result for behavioural questions.")

    return min(100.0, round(score, 1)), " ".join(notes)


def _calculate_delivery_score(
    filler_count: int,
    word_count: int,
    wpm: Optional[float],
    star_signals: dict,
    hedging_count: int,
    confidence_ratio: float,
    vocabulary_richness: float,
    structure_score: float,
    repetition_count: int,
    sentence_count: int,
) -> float:
    """
    Compute a weighted composite delivery score (0–100).

    Weights:
    - Filler penalty:     20%
    - Pace:               10%
    - Confidence:         20%
    - Hedging penalty:    10%
    - Vocabulary:         10%
    - Structure:          20%
    - Repetition penalty: 10%
    """
    score = 0.0

    # ── Filler score (20%) — fewer is better ──────────────────────────────
    if word_count > 0:
        filler_ratio = filler_count / word_count
        # 0 fillers = 100, 5%+ fillers = 0
        filler_score = max(0, 100 - (filler_ratio * 2000))
    else:
        filler_score = 0
    score += filler_score * 0.20

    # ── Pace score (10%) — 120-160 WPM ideal ──────────────────────────────
    if wpm is not None:
        if 120 <= wpm <= 160:
            pace_score = 100
        elif 100 <= wpm < 120 or 160 < wpm <= 180:
            pace_score = 70
        elif 80 <= wpm < 100 or 180 < wpm <= 200:
            pace_score = 40
        else:
            pace_score = 15
    else:
        pace_score = 50  # neutral when no duration data
    score += pace_score * 0.10

    # ── Confidence score (20%) ────────────────────────────────────────────
    conf_score = confidence_ratio * 100
    score += conf_score * 0.20

    # ── Hedging penalty (10%) ─────────────────────────────────────────────
    # 0 hedging phrases = 100, 5+ = 0
    hedging_score = max(0, 100 - (hedging_count * 20))
    score += hedging_score * 0.10

    # ── Vocabulary richness (10%) ─────────────────────────────────────────
    # TTR of 0.6+ is good, below 0.3 is repetitive
    vocab_score = min(100, vocabulary_richness * 150)
    score += vocab_score * 0.10

    # ── Structure (20%) — directly use structure_score ────────────────────
    score += structure_score * 0.20

    # ── Repetition penalty (10%) ──────────────────────────────────────────
    rep_score = max(0, 100 - (repetition_count * 25))
    score += rep_score * 0.10

    return round(max(0, min(100, score)), 1)
