from pydantic import BaseModel

class NotificationToAdmin(BaseModel):
    employee_id: str
    admin_id: str
    message: str
    type: str