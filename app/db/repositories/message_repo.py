from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, conversation_id: int, role: str, content: str
    ) -> Message:
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    async def list_by_conversation(self, conversation_id: int) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def get_as_history(self, conversation_id: int) -> list[dict]:
        """
        Retorna mensagens no formato da API do Claude.
        Exclui role=system — o system prompt é gerenciado pelo AIService.
        """
        messages = await self.list_by_conversation(conversation_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role != "system"
        ]
