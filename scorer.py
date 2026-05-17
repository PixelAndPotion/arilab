"""
Scoring engine for ARI'Lab.

Scores a user's review comment against the challenge's keyword lists.
The matching logic mirrors how a senior developer actually evaluates
a junior's review comment.

Each challenge has a keywords list of lists. Each inner list represents
one concept that needs to be identified. The user needs to hit at least
one term from each inner list to score full marks.

Grading:
    FULL    — user hit at least one keyword from every required concept
    PARTIAL — user hit at least one concept but not all of them
    WRONG   — user hit no keywords at all

Points:
    FULL    — full points for the challenge
    PARTIAL — half points, rounded up
    WRONG   — zero points
"""

import math


def score_answer(user_answer: str, challenge: dict) -> dict:
    """
    Scores the user's answer against the challenge keyword lists.

    Lowercases both the answer and keywords before matching so
    capitalisation doesn't penalise a correct answer.

    Parameters:
        user_answer — the raw text from the answer input box
        challenge   — the full challenge dict from the bank

    Returns:
        {
            "grade":        "FULL" / "PARTIAL" / "WRONG",
            "points_earned": int,
            "matched":      list of concept indices that were matched,
            "missed":       list of concept indices that were not matched,
        }
    """
    answer_lower    = user_answer.lower()
    keyword_groups  = challenge["keywords"]
    matched_groups  = []
    missed_groups   = []

    for i, group in enumerate(keyword_groups):
        hit = any(kw.lower() in answer_lower for kw in group)
        if hit:
            matched_groups.append(i)
        else:
            missed_groups.append(i)

    total_groups = len(keyword_groups)
    matched_count = len(matched_groups)

    if matched_count == total_groups:
        grade         = "FULL"
        points_earned = challenge["points"]
    elif matched_count > 0:
        grade         = "PARTIAL"
        points_earned = math.ceil(challenge["points"] / 2)
    else:
        grade         = "WRONG"
        points_earned = 0

    return {
        "grade":         grade,
        "points_earned": points_earned,
        "matched":       matched_groups,
        "missed":        missed_groups,
    }