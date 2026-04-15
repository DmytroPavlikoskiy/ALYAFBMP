from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.moderation.deps import verify_bot_secret
from apps.moderation.schemas import ModerationDecisionBody
from common.database import get_db
from common.models import Notification, Product, User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/decision")
async def moderation_decision(
    body: ModerationDecisionBody,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_bot_secret),
):
    """
    POST /api/v1/moderation/decision — canonical moderation endpoint (bot-only).

    APPROVE: sets product.status = "APPROVE" and notifies the seller.
    REJECT:  sets product.status = "REJECTED", optionally bans the seller
             for body.ban_days days, and notifies the seller.

    Header X-Bot-Secret is required.
    """
    product = await db.get(Product, body.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    seller = await db.get(User, product.seller_id)
    now = datetime.now(timezone.utc)

    if body.action == "APPROVE":
        product.status = "APPROVE"
        product.updated_at = now
        notification_text = f"Your listing «{product.title}» has been approved."
        notification_type = "MODERATION_APPROVED"

    else:  # REJECT
        product.status = "REJECTED"
        product.updated_at = now
        notification_text = (
            f"Your listing «{product.title}» was rejected."
            + (f" Reason: {body.reason}" if body.reason else "")
        )
        notification_type = "MODERATION_REJECTED"

        if body.ban_user and seller:
            unban_date = now + timedelta(days=body.ban_days)
            seller.is_banned = True
            seller.banned_until = unban_date
            seller.ban_reason = body.reason or "Moderation violation"
            notification_text += f" Account suspended until {unban_date.date()}."

    if seller:
        db.add(
            Notification(
                user_id=seller.id,
                text_notification=notification_text,
                type=notification_type,
            )
        )

    try:
        await db.commit()
        logger.info("Moderation decision %s applied to product %s", body.action, body.product_id)
        return {"ok": True, "action": body.action, "product_id": body.product_id}
    except Exception as exc:
        await db.rollback()
        logger.exception("moderation_decision error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to apply decision")
