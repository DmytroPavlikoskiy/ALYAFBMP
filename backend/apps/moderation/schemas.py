from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ModerationDecisionBody(BaseModel):
    product_id: int
    action: Literal["APPROVE", "REJECT"]
    reason: str | None = None
    ban_user: bool = False
    ban_days: int = Field(default=3, ge=1, le=365)
