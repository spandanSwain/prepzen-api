from pydantic import BaseModel

class UserDomain(BaseModel):
    employee_id: str
    domain_id: str