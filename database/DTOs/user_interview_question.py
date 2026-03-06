from typing import List, Optional, Union
from pydantic import BaseModel

class UserInterviewDTO(BaseModel):
    proficiency: str
    topic: str
    numQuestions: int
    
    domain: str
    performanceLevel: str
    username: str
    topic: Union[str, List[str]]
    level: int
    weaknesses: Optional[List[str]]
