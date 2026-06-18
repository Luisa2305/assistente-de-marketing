import structlog

from app.observability.base import AICallContext

logger = structlog.get_logger()


class NoOpTracer:
    """
    Tracer padrão: sem integração externa, apenas logs estruturados.
    Substitua por LangSmithTracer ou OTELTracer quando necessário.
    """

    async def on_start(
        self, ctx: AICallContext, system: str, messages: list[dict]
    ) -> None:
        logger.info(
            "ai_call_start",
            trace_id=ctx.trace_id,
            module=ctx.module,
            conversation_id=ctx.conversation_id,
            user_id=ctx.user_id,
            message_count=len(messages),
        )

    async def on_chunk(self, ctx: AICallContext, chunk: str) -> None:
        pass  # sem overhead por chunk — ativo apenas em tracers de debug

    async def on_end(
        self, ctx: AICallContext, response: str, tokens: int | None
    ) -> None:
        logger.info(
            "ai_call_end",
            trace_id=ctx.trace_id,
            module=ctx.module,
            response_chars=len(response),
            tokens=tokens,
        )

    async def on_error(self, ctx: AICallContext, error: Exception) -> None:
        logger.error(
            "ai_call_error",
            trace_id=ctx.trace_id,
            module=ctx.module,
            error=str(error),
        )
