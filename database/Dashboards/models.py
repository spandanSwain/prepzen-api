from pydantic import BaseModel

class UserDashboard(BaseModel):
    employee_id: str