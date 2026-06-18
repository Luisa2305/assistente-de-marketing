from datetime import datetime

from pydantic import BaseModel


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    """Usado na listagem — sem mensagens para manter response leve."""
    id: int
    module: str
    title: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailOut(BaseModel):
    """Usado na recuperação de histórico — inclui todas as mensagens."""
    id: int
    module: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}
