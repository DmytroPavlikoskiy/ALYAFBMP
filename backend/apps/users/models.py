import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, ForeignKey, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.database import Base
from products.models import Category

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), server_default="USER")
    
    # Зв'язки
    preferences: Mapped[List["Category"]] = relationship(
        secondary="user_preferences", 
        back_populates="interested_users"
    )
    bans: Mapped[List["BanList"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class BanList(Base):
    __tablename__ = "ban_list"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", on_delete="CASCADE"))
    start_ban_date: Mapped[datetime] = mapped_column(default=datetime.now)
    
    user: Mapped["User"] = relationship(back_populates="bans")