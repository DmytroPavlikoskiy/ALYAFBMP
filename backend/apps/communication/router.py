"""
Маршрути комунікації: список чатів, WebSocket.
Префікс /api/v1 задається в main.py.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.botkeyboard import router
from apps.communication.ws_manager import manager
from common.database import get_db
from common.deps import get_current_user_id
import uuid
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends


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
async def chat_websocket(
    websocket: WebSocket,
    chat_id: uuid.UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    user_id = await get_current_user_id(token, db)
    if not user_id:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, chat_id)

    try:
        while True:
            data = await websocket.receive_json()

            response = {
                "sender_id": str(user_id),
                "text": data.get("text"),
                "sent_at": datetime.utcnow().isoformat()
            }

            await manager.broadcast(response, chat_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)