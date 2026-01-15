from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
