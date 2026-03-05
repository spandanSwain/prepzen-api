from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

class Users(BaseModel):
    email: str
    password: str
    username: str
    employee_id: str
    role: str = "student"
    createdAt: datetime
    updatedAt: datetime

class LoginUsers(BaseModel):
    employee_id: str
    password: str