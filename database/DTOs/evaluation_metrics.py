from pydantic import BaseModel
from enum import Enum

class PerformanceRating(str, Enum):
    GOOD = "Good"
    AVERAGE = "Average"
    BAD = "Bad"

class EvaluationMetrics(BaseModel):
    communication_skills: int
    technical_knowledge: int
    problem_solving: int
    cultural_role_fit: int
    confidence_clarity: int
    detailed_feedback: PerformanceRating
    areas_for_improvement: list[str]