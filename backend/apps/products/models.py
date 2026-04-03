from common.database import Base
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from common.database import db

class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", on_delete="CASCADE"), 
        primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", on_delete="CASCADE"), 
        primary_key=True
    )

    def create(self, user_id, category_id):
        self.user_id = user_id
        self.category_id = category_id
        db.add(self)
        db.commit()
        return self




class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    interested_users: Mapped[List["User"]] = relationship(
        secondary="user_preferences", 
        back_populates="preferences"
    )