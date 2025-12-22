from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None
    role: Optional[str] = None


class Login(BaseModel):
    email: EmailStr
    password: str


class Register(BaseModel):
    email: EmailStr
    password: str
