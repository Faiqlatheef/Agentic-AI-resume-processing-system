from app.config import MATCH_THRESHOLD_SHORTLIST, MATCH_THRESHOLD_REVIEW
from app.schemas import MatchResult


def route_candidate(result: MatchResult,
                    extraction_confidence: float):

    review_reason = ""

    if extraction_confidence < 0.75:
        status = "Human Review"
        review_reason = "Low extraction confidence"

    elif result.match_score >= MATCH_THRESHOLD_SHORTLIST and not result.experience_gap:
        status = "Shortlisted"

    elif result.match_score >= MATCH_THRESHOLD_REVIEW:
        status = "Human Review"
        review_reason = "Partial skill match"

    else:
        status = "Rejected"
        review_reason = "Insufficient skill match"

    result.recommendation = status
    result.review_reason = review_reason

    return result