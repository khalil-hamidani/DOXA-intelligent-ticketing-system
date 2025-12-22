import enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum, BigInteger, Text
from sqlalchemy.sql import func
from app.db.base import Base


class UserRole(str, enum.Enum):
    CLIENT = "CLIENT"
    AGENT = "AGENT"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    language = Column(String(5), default="en")
    profile_picture_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
