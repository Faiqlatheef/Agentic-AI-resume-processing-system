from typing import List
from app.schemas import CandidateExtraction, MatchResult


def compute_match(candidate: CandidateExtraction,
                  required_skills: List[str],
                  min_experience: float):

    required_skills_lower = [s.lower() for s in required_skills]
    candidate_skills_lower = [s.lower() for s in candidate.skills]

    overlap = set(required_skills_lower) & set(candidate_skills_lower)

    skill_score = len(overlap) / max(len(required_skills_lower), 1)

    experience_gap = candidate.years_of_experience < min_experience
    experience_score = 0 if experience_gap else 1

    match_score = (skill_score * 0.7) + (experience_score * 0.3)

    missing = [
        skill for skill in required_skills
        if skill.lower() not in candidate_skills_lower
    ]

    return MatchResult(
        match_score=round(match_score, 2),
        critical_skills_missing=missing,
        experience_gap=experience_gap,
        recommendation="Pending"
    )