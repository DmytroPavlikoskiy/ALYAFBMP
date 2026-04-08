from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.moderation.deps import verify_bot_secret
from apps.moderation.schemas import ModerationDecisionBody
from common.database import get_db

router = APIRouter()


@router.post("/decision")
async def moderation_decision(
    body: ModerationDecisionBody,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_bot_secret),
):
    """
    POST /api/v1/moderation/decision

    1. Знайди Product за product_id.
    2. APPROVE -> онови status; REJECT -> відхилення / бан за правилами курсу.

    Заголовок X-Bot-Secret обов'язковий.
    """
    raise HTTPException(status_code=501, detail="Група 5: реалізуйте рішення модерації.")
