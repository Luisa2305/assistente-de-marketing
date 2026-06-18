from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import UserContext
from app.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: UserContext, module: str, title: str) -> Conversation:
        conv = Conversation(
            user_id=user.user_id,
            franquia_id=user.franquia_id,
            nome_usuario=user.nome_usuario,
            module=module,
            title=title,
        )
        self.db.add(conv)
        await self.db.flush()
        await self.db.refresh(conv)
        return conv

    async def get_by_id(self, conversation_id: int) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_with_messages(self, conversation_id: int) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, franquia_id: int, limit: int = 100
    ) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.franquia_id == franquia_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_timestamp(self, conversation_id: int) -> None:
        """Atualiza updated_at após nova mensagem — mantém ordenação por atividade."""
        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
