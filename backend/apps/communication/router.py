"""
Маршрути комунікації: список чатів, WebSocket.
Префікс /api/v1 задається в main.py.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from apps.communication.ws_manager import manager
from common.database import AsyncSessionLocal, get_db
from common.deps import get_current_user_id, get_user_id_from_ws_token
from common.models import Chat, Message, Product, User

router = APIRouter()

#Давид, Женя

# ---------------------------------------------------------------------------
# Schemas (inline — keep communication self-contained)
# ---------------------------------------------------------------------------

class ChatCreateBody(BaseModel):
    product_id: int


class ChatOut(BaseModel):
    id: uuid.UUID
    product_id: int
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    created_at: datetime | None
    last_message: str | None = None
    opponent_name: str | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    sender_id: uuid.UUID
    # ORM attribute is text_msg; keep the JSON key as "text" for frontend compatibility
    text: str = Field(validation_alias="text_msg")
    sent_at: datetime | None


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@router.post("/chats", response_model=ChatOut, status_code=201)
async def create_chat(
    body: ChatCreateBody,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    POST /api/v1/chats — start a conversation about a product.
    The calling user is the buyer; the product seller is auto-detected.
    Idempotent: returns the existing chat if one already exists for
    (product_id, buyer_id).
    """
    product = await db.get(Product, body.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.seller_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot open a chat with yourself")

    existing = await db.execute(
        select(Chat).where(
            Chat.product_id == body.product_id,
            Chat.buyer_id == user_id,
        )
    )
    chat = existing.scalar_one_or_none()

    if chat is None:
        chat = Chat(
            product_id=body.product_id,
            buyer_id=user_id,
            seller_id=product.seller_id,
        )
        db.add(chat)
        await db.commit()
        await db.refresh(chat)

    return ChatOut(
        id=chat.id,
        product_id=chat.product_id,
        buyer_id=chat.buyer_id,
        seller_id=chat.seller_id,
        created_at=chat.created_at,
    )


@router.get("/chats", response_model=list[ChatOut])
async def list_chats(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """GET /api/v1/chats — all chats for the current user, with last message."""
    result = await db.execute(
        select(Chat)
        .where(or_(Chat.buyer_id == user_id, Chat.seller_id == user_id))
        .options(selectinload(Chat.messages))
        .order_by(Chat.created_at.desc())
    )
    chats = result.scalars().unique().all()

    out = []
    for chat in chats:
        opponent_id = chat.seller_id if chat.buyer_id == user_id else chat.buyer_id
        opponent = await db.get(User, opponent_id)
        opponent_name = (
            f"{opponent.first_name} {opponent.last_name or ''}".strip()
            if opponent
            else None
        )
        last_msg = (
            sorted(chat.messages, key=lambda m: m.sent_at or datetime.min)[-1].text_msg
            if chat.messages
            else None
        )
        out.append(
            ChatOut(
                id=chat.id,
                product_id=chat.product_id,
                buyer_id=chat.buyer_id,
                seller_id=chat.seller_id,
                created_at=chat.created_at,
                last_message=last_msg,
                opponent_name=opponent_name,
            )
        )
    return out


@router.get("/chats/{chat_id}/messages", response_model=list[MessageOut])
async def list_messages(
    chat_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """GET /api/v1/chats/{chat_id}/messages — paginated message history."""
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if user_id not in {chat.buyer_id, chat.seller_id}:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.sent_at.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@router.websocket("/ws/chat/{chat_id}")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: uuid.UUID,
    token: str = Query(...),
):
    """
    WS /api/v1/ws/chat/{chat_id}?token=<access_jwt>

    Authentication: JWT passed as query param.
    Authorization: only chat participants may connect.
    Persistence: every message is saved to the messages table.

    Не використовуємо Depends(get_db) на весь час з’єднання — інакше одна сесія БД
    «висить» на кожному відкритому WebSocket і вичерпує QueuePool.
    """
    async with AsyncSessionLocal() as db:
        try:
            user_id = await get_user_id_from_ws_token(token, db)
        except Exception:
            await websocket.close(code=1008)
            return

        chat = await db.get(Chat, chat_id)
        if not chat or user_id not in {chat.buyer_id, chat.seller_id}:
            await websocket.close(code=1008)
            return

    await manager.connect(websocket, chat_id)

    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text", "").strip()
            if not text:
                continue

            async with AsyncSessionLocal() as db:
                msg = Message(chat_id=chat_id, sender_id=user_id, text_msg=text)
                db.add(msg)
                await db.commit()
                await db.refresh(msg)

                response = {
                    "id": msg.id,
                    "sender_id": str(user_id),
                    "text": text,
                    "sent_at": (msg.sent_at or datetime.now(timezone.utc)).isoformat(),
                }
            await manager.broadcast(response, chat_id)

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, chat_id)
