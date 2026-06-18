import json

import structlog
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.auth import UserContext, get_ws_user
from app.db.base import get_db
from app.services.chat_service import ChatService

logger = structlog.get_logger()
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    user: UserContext = Depends(get_ws_user),
    db=Depends(get_db),
):
    """
    WebSocket principal. Recebe mensagens e transmite resposta em streaming.

    Payload esperado:
      {"conversation_id": null | int, "module": "mentor", "message": "texto"}

    Eventos emitidos:
      {"type": "conversation_created", "conversation_id": N, "title": "..."}
      {"type": "chunk",  "content": "fragmento..."}
      {"type": "done",   "conversation_id": N, "message_id": N}
      {"type": "error",  "error": "mensagem de erro"}
    """
    await websocket.accept()
    ai_service = websocket.app.state.ai_service
    service = ChatService(db=db, ai_service=ai_service)

    logger.info("ws_connected", franquia_id=user.franquia_id, user_id=user.user_id)

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "error": "Payload JSON inválido"}
                )
                continue

            conversation_id = data.get("conversation_id")
            module = data.get("module", "mentor")
            message = data.get("message", "").strip()

            if not message:
                await websocket.send_json({"type": "error", "error": "Mensagem vazia"})
                continue

            async for event in service.stream_chat(
                user=user,
                conversation_id=conversation_id,
                module=module,
                message=message,
            ):
                await websocket.send_json(event)

    except WebSocketDisconnect:
        logger.info("ws_disconnected", franquia_id=user.franquia_id)
    except Exception as e:
        logger.error("ws_unexpected_error", franquia_id=user.franquia_id, error=str(e))
        try:
            await websocket.send_json({"type": "error", "error": "Erro interno"})
        except Exception:
            pass
