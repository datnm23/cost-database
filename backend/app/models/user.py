from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, func
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    viewer = "viewer"
    editor = "editor" 
    admin = "admin"
    super_admin = "super_admin"


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.viewer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)
    
    def __repr__(self):
        return f"<User {self.username}>"
