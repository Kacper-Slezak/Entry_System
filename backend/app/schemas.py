from pydantic import BaseModel

# React's sending info
class AdminLogin(BaseModel):
    username: str
    password: str

# Answear to React
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
    