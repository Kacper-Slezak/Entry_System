from pydantic import BaseModel

from datetime import datetime

from app.db.models import AccessLogStatus

# React's sending info
class AdminLogin(BaseModel):
    username: str
    password: str

# Answear to React
class Token(BaseModel):
    access_token: str
    token_type: str

class AccessLogReport(BaseModel):
    id: int
    timestamp: datetime
    status: AccessLogStatus
    reason: str

    class Config:
        from_attributes = True
