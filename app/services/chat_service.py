import uuid
from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.message_repo import MessageRepository
from app.observability.base import AICallContext
from app.services.ai_service import AIService

logger = structlog.get_logger()


class ChatService:
    """
    Orquestrador central. Coordena persistência e IA.

    Fluxo:
      1. Obter ou criar conversa
      2. Salvar mensagem do usuário
      3. Carregar histórico
      4. Chamar AIService (streaming)
      5. Salvar resposta da IA
      6. Atualizar timestamp da conversa
      7. Emitir evento done

    Extensão para módulos (próxima fase):
      Adicionar `system: str | None = None` e repassar ao AIService.
      Nenhuma outra mudança necessária nesta classe.
    """

    def __init__(self, db: AsyncSession, ai_service: AIService):
        self.conv_repo = ConversationRepository(db)
        self.msg_repo = MessageRepository(db)
        self.ai_service = ai_service

    async def stream_chat(
        self,
        user: UserContext,
        conversation_id: int | None,
        module: str,
        message: str,
    ) -> AsyncGenerator[dict, None]:
        """
        Yields dicts prontos para envio via WebSocket.

        Eventos emitidos (type):
          conversation_created  → nova conversa criada (apenas no primeiro turno)
          chunk                 → fragmento de texto da IA
          done                  → conclusão com IDs persistidos
          error                 → falha durante o processamento
        """
        # 1. Obter ou criar conversa
        if conversation_id is None:
            title = _generate_title(message)
            conv = await self.conv_repo.create(user, module, title)
            yield {
                "type": "conversation_created",
                "conversation_id": conv.id,
                "title": conv.title,
            }
            logger.info("conversation_created", conversation_id=conv.id, module=module)
        else:
            conv = await self.conv_repo.get_by_id(conversation_id)
            if not conv:
                yield {"type": "error", "error": "Conversa não encontrada"}
                return

        # 2. Salvar mensagem do usuário
        await self.msg_repo.create(conv.id, "user", message)

        logger.info("user_message_saved", conversation_id=conv.id, user_id=user.user_id)

        # 3. Carregar histórico para a IA
        history = await self.msg_repo.get_as_history(conv.id)

        # 4. Contexto de tracing (correlaciona logs, LangSmith e OTEL futuramente)
        ctx = AICallContext(
            module=module,
            conversation_id=conv.id,
            franquia_id=user.franquia_id,
            user_id=user.user_id,
            trace_id=str(uuid.uuid4()),
        )

        # 5. Streaming da IA
        full: list[str] = []
        try:
            async for chunk in self.ai_service.stream(history, ctx):
                full.append(chunk)
                yield {"type": "chunk", "content": chunk}
        except Exception as e:
            logger.error("ai_stream_error", conversation_id=conv.id, error=str(e))
            yield {"type": "error", "error": "Falha na geração de resposta"}
            return

        # 6. Salvar resposta da IA
        full_response = "".join(full)
        msg = await self.msg_repo.create(conv.id, "assistant", full_response)

        # 7. Atualizar timestamp (mantém conversa no topo da lista)
        await self.conv_repo.update_timestamp(conv.id)

        # 8. Sinalizar conclusão
        yield {
            "type": "done",
            "conversation_id": conv.id,
            "message_id": msg.id,
        }


def _generate_title(message: str) -> str:
    """Gera título truncando a primeira mensagem em 60 caracteres."""
    clean = message.strip()
    if len(clean) <= 60:
        return clean
    return clean[:57].rsplit(" ", 1)[0] + "..."
