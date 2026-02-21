from pydantic import BaseModel
from typing import List, Optional, Union


class Education(BaseModel):
    degree: str
    institution: str
    location: Optional[str] = ""
    gpa: Optional[Union[str, float]] = ""
    graduation_date: Optional[str] = ""
    duration: Optional[str] = ""


class PreviousRole(BaseModel):
    role: str
    company: str
    duration: Optional[str] = ""


class CandidateExtraction(BaseModel):
    candidate_name: str
    email: str
    phone: str
    years_of_experience: float
    skills: List[str]
    education: List[Education]
    previous_roles: List[PreviousRole]
    extraction_confidence: float


class MatchResult(BaseModel):
    match_score: float
    critical_skills_missing: List[str]
    experience_gap: bool
    recommendation: str
    review_reason: Optional[str] = ""