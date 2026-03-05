from pydantic import BaseModel
from typing import List

class UserQuiz(BaseModel):
    employee_id: str

class QuizItem(BaseModel):
    id: int
    question: str
    options: List[str]
    correct: int

class QuizResponse(BaseModel):
    quiz: List[QuizItem]

class QuizScore(BaseModel):
    employee_id: str
    score: str