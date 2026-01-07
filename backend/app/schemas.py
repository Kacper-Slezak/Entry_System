from pydantic import BaseModel

# React's sending info
class AdminLogin(BaseModel):
    username: str
    password: str

# Answear to React
class Token(BaseModel):
    access_token: str
    token_type: str
