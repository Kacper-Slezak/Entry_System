from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

# React's sending info
class AdminLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str

class LogEntry(BaseModel):
    id: int
    timestamp: str
    employee_name: str
    status: str
    reason: str | None = None
    employee_email: str | None = None
    debug_distance: float | None = None

class EmployeeStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    expiration_date: Optional[str] = None


class EmployeeResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    email: str
    is_active: bool
    expires_at: Optional[datetime]  # Added to allow frontend to see the expiration date

    class Config:
        from_attributes = True

class EmployeeStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    expiration_date: Optional[str] = None
