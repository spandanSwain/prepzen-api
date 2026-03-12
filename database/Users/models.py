from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from typing import Optional, List

class Users(BaseModel):
    email: str
    password: str
    username: str
    employee_id: str
    role: str = "student"
    createdAt:datetime = Field(default_factory=datetime.now)
    updatedAt:datetime = Field(default_factory=datetime.now)

class LoginUsers(BaseModel):
    employee_id: str
    password: str
    role: str

class DeleteUsers(BaseModel):
    employee_id: str

class FinalUsers(BaseModel):
    employee_id: str
    numQuestions: str