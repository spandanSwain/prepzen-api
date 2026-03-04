from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

class Users(BaseModel):
    email: str
    password: str
    name: str
    isVerified: bool = True
    lastLogin: datetime | None = None
    createdAt: datetime
    updatedAt: datetime
    interviews_attended: [ObjectId] # type: ignore