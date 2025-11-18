"""
os_o_reference_implementation.py

Minimal reference implementation of the OS_O v1.4 scoring logic and OS mode
classification.

This is intentionally simple and heuristic:
- No external libraries
- Tiny word lists
- All functions are easy to read, modify, and extend

Core outputs:
- threat_score ∈ [0, 1]
- opportunity_score ∈ [0, 1]
- OS_mode ∈ {"OS_L", "OS_E", "mixed"}
"""

# -----------------------------
# Term Dictionaries
# -----------------------------

RISK_TERMS = [
    "crisis", "threat", "danger", "terrorism", "collapse",
    "instability", "security", "emergency", "war", "attack",
    "risk", "catastrophe", "panic"
]

OPPORTUNITY_TERMS = [
    "opportunity", "growth", "innovation", "potential",
    "frontier", "expansion", "prosperity", "progress",
    "breakthrough", "advantage", "benefit"
]

UNCERTAINTY_MARKERS = [
    "maybe", "uncertain", "not sure", "unclear",
    "probably", "possibly", "it seems", "appears to"
]

NEGATIVE_WORDS = [
    "bad", "worse", "worst", "dangerous", "terrible",
    "horrible", "catastrophic", "awful", "fear", "anxiety",
    "loss", "collapse", "crisis", "problem", "threat"
]

POSITIVE_WORDS = [
    "good", "better", "best", "great", "excellent",
    "promising", "hopeful", "opportunity", "progress",
    "improve", "growth", "success", "benefit"
]


# -----------------------------
# Helper Functions
# -----------------------------

def _normalize_text(text: str) -> str:
    return text.lower()


def freq(text: str, term_list: list[str]) -> float:
    """
    Very simple normalized frequency:
    - Count how often any of the terms appears
    - Normalize by text length (approx. 'per 50 tokens'), capped at 1.0
    """
    t = _normalize_text(text)
    tokens = t.split()
    token_len = max(1, len(tokens))
    count = 0
    for term in term_list:
        count += t.count(term)
    # naive normalization: count per ~50 tokens
    value = count / max(1, token_len / 50.0)
    return min(1.0, max(0.0, value))


def count_uncertainty_markers(text: str) -> int:
    t = _normalize_text(text)
    return sum(t.count(m) for m in UNCERTAINTY_MARKERS)


def sentiment_negative(text: str) -> float:
    """
    Naive 'sentiment':
    Returns a value in [-1, 1] where:
    -1 = strongly negative, 0 = neutral, +1 = strongly positive

    Here we use only word counts:
    - negative_score = (#negative_words / tokens)
    - positive_score = (#positive_words / tokens)

    Then:
    sentiment = positive_score - negative_score  ∈ [-1,1] (roughly)
    """
    t = _normalize_text(text)
    tokens = t.split()
    token_len = max(1, len(tokens))

    neg_count = sum(t.count(w) for w in NEGATIVE_WORDS)
    pos_count = sum(t.count(w) for w in POSITIVE_WORDS)

    neg_score = neg_count / token_len
    pos_score = pos_count / token_len

    # crude difference, clipped to [-1,1]
    sentiment = pos_score - neg_score
    return max(-1.0, min(1.0, sentiment))


def sentiment_positive(text: str) -> float:
    """
    Same as sentiment_negative, but returns the same value.
    The mapping to [0,1] is done later.
    We expose a separate function to mirror the spec, but they share logic.
    """
    return sentiment_negative(text)


# -----------------------------
# Core Scoring Logic
# -----------------------------

def compute_scores(text: str) -> tuple[float, float]:
    """
    Compute threat_score and opportunity_score ∈ [0,1].

    threat_score:
        0.5 * risk_term_frequency
      + 0.3 * negative_sentiment_mapped
      + 0.2 * uncertainty_markers_mapped

    opportunity_score:
        0.6 * opportunity_term_frequency
      + 0.4 * positive_sentiment_mapped

    All mappings are heuristic and intentionally simple.
    """
    # term frequencies
    risk = freq(text, RISK_TERMS)
    opp = freq(text, OPPORTUNITY_TERMS)

    # sentiment in [-1,1]
    raw_sent = sentiment_negative(text)  # symmetric by design

    # map sentiment to [0,1]
    neg = (max(-1.0, min(1.0, raw_sent * -1)))  # invert: more negative → larger
    neg = (neg + 1) / 2.0

    pos = (max(-1.0, min(1.0, raw_sent)))       # positive side
    pos = (pos + 1) / 2.0

    # uncertainty markers: count, then crude mapping
    uncert_raw = count_uncertainty_markers(text)
    uncert = max(0.0, min(1.0, uncert_raw / 10.0))

    threat_score = (
        0.5 * risk +
        0.3 * neg +
        0.2 * uncert
    )
    opportunity_score = (
        0.6 * opp +
        0.4 * pos
    )

    # clip to [0,1]
    threat_score = max(0.0, min(1.0, threat_score))
    opportunity_score = max(0.0, min(1.0, opportunity_score))

    return threat_score, opportunity_score


def classify_OS_mode(threat_score: float, opportunity_score: float, epsilon: float = 0.1) -> str:
    """
    Classify OS mode based on scores:

    - if threat_score > opportunity_score + epsilon → OS_L
    - if opportunity_score > threat_score + epsilon → OS_E
    - else → mixed
    """
    if threat_score > opportunity_score + epsilon:
        return "OS_L"
    elif opportunity_score > threat_score + epsilon:
        return "OS_E"
    else:
        return "mixed"


# -----------------------------
# OML Helper (optional)
# -----------------------------

def oml_analysis_stub(text: str) -> dict:
    """
    Very simple OML stub.
    In einer echten Implementierung würdest Du hier:
    - mechanic: aus Funktionen/Policies ableiten
    - narrative: aus rhetorischen Frames ableiten

    Hier geben wir nur die Scores und Mode zurück – als Beispiel.
    """
    t, o = compute_scores(text)
    mode = classify_OS_mode(t, o)
    return {
        "threat_score": t,
        "opportunity_score": o,
        "OS_mode": mode,
        "mechanic": "heuristic-only placeholder (derive from domain logic).",
        "narrative": "heuristic-only placeholder (derive from rhetorical framing)."
    }


# -----------------------------
# Manual Test
# -----------------------------

if __name__ == "__main__":
    sample = (
        "AI brings enormous opportunities for growth, but also serious risks "
        "to jobs and democracy. We must innovate boldly while implementing "
        "robust safeguards."
    )

    t_score, o_score = compute_scores(sample)
    mode = classify_OS_mode(t_score, o_score)

    print("Text:", sample)
    print("Threat Score:     ", round(t_score, 3))
    print("Opportunity Score:", round(o_score, 3))
    print("OS Mode:          ", mode)
