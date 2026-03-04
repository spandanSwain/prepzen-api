from pydantic import BaseModel
from typing import Dict, Any

class Interviews(BaseModel):
    user_id: str
    proficiency: str
    topic: str
    numQuestions: str

class InterviewComplete(BaseModel):
    interview_id: str
    user_id: str
    response: Dict[str, Any]

    communication: float
    technicalKnowledge: float
    problemSolving: float
    culturalFit: float
    confidence: float

    finalRemark: str