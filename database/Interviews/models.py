from pydantic import BaseModel
from typing import Dict, Any

class Interviews(BaseModel):
    user_id: str
    proficiency: str
    topic: int
    numQuestions: str

class InterviewComplete(BaseModel):
    interview_id: str
    transcribe: Dict[str, Any]

class InterviewFinalComplete(BaseModel):
    transcribe: Dict[str, Any]