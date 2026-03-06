from pydantic import BaseModel

class UserReport(BaseModel):
    employee_id: str