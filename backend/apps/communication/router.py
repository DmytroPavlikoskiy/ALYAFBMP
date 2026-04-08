"""
Маршрути комунікації: список чатів, WebSocket.
Префікс /api/v1 задається в main.py.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from common.deps import get_current_user_id

router = APIRouter()


@router.get("/chats")
async def list_chats(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    GET /api/v1/chats

    1. select(Chat).where((Chat.buyer_id == user_id) | (Chat.seller_id == user_id)).
    2. Для кожного чату підвантаж останнє повідомлення (subquery або join).
    3. Поверни список з chat_id, last_message, opponent name.
    """
    raise HTTPException(status_code=501, detail="Група 6: реалізуйте список чатів.")


@router.websocket("/ws/chat/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: uuid.UUID):
    """
    WS /api/v1/ws/chat/{chat_id}

    1. await websocket.accept().
    2. Авторизуй користувача (токен у query ?token= або підпротокол — узгодьте).
    3. Перевір, що user має доступ до цього chat_id.
    4. Цикл while True: data = await websocket.receive_json(); збережи Message в БД; розішли іншим клієнтам.
    5. Оброби WebSocketDisconnect.

    Зараз: мінімальна заглушка.
    """
    await websocket.accept()
    try:
        await websocket.send_json({"detail": "Група 6: реалізуйте протокол повідомлень."})
    finally:
        await websocket.close()
