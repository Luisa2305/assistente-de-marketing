from collections.abc import AsyncGenerator

from app.observability.base import AICallContext, AITracer
from app.providers.base import AIProvider

# Prompt temporário — substituir por prompts de módulo na próxima fase
_DEFAULT_SYSTEM = (
    "Você é um assistente de marca prestativo. "
    "Responda sempre em português brasileiro de forma clara e objetiva."
)


class AIService:
    """
    Serviço central de IA. Orquestra provider + tracer.

    Extensão para módulos (próxima fase):
      Passar `system=module.system_prompt` em stream() e complete()
      sem alterar nada nesta classe.

    Extensão para observabilidade:
      Substituir NoOpTracer por LangSmithTracer ou OTELTracer
      sem alterar nada nesta classe.
    """

    def __init__(self, provider: AIProvider, tracer: AITracer):
        self._provider = provider
        self._tracer = tracer

    async def stream(
        self,
        messages: list[dict],
        ctx: AICallContext,
        system: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming de resposta com tracing integrado."""
        system = system or _DEFAULT_SYSTEM
        await self._tracer.on_start(ctx, system, messages)
        full: list[str] = []
        try:
            async for chunk in self._provider.stream(system, messages):
                full.append(chunk)
                await self._tracer.on_chunk(ctx, chunk)
                yield chunk
            await self._tracer.on_end(ctx, "".join(full), None)
        except Exception as e:
            await self._tracer.on_error(ctx, e)
            raise

    async def complete(
        self,
        messages: list[dict],
        ctx: AICallContext,
        system: str | None = None,
    ) -> tuple[str, int]:
        """Resposta completa (não streaming) com tracing."""
        system = system or _DEFAULT_SYSTEM
        await self._tracer.on_start(ctx, system, messages)
        try:
            response, tokens = await self._provider.complete(system, messages)
            await self._tracer.on_end(ctx, response, tokens)
            return response, tokens
        except Exception as e:
            await self._tracer.on_error(ctx, e)
            raise
