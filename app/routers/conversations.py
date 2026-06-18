from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext, get_current_user
from app.db.base import get_db
from app.db.repositories.conversation_repo import ConversationRepository
from app.schemas.conversation import ConversationDetailOut, ConversationOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista conversas do usuário autenticado.
    Ordenadas pela mais recente (updated_at desc).
    """
    repo = ConversationRepository(db)
    return await repo.list_by_user(user.franquia_id)


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: int,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna conversa com todas as mensagens.
    Permite ao frontend reconstruir qualquer chat salvo.
    """
    repo = ConversationRepository(db)
    conv = await repo.get_with_messages(conversation_id)

    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    if conv.franquia_id != user.franquia_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    return conv
