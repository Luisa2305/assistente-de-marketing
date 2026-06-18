import uuid
from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable


@dataclass
class AICallContext:
    """
    Contexto de uma chamada à IA. Passado ao tracer em cada operação.
    Inclui dados suficientes para correlação em LangSmith e OTEL.
    """

    module: str
    conversation_id: int
    franquia_id: int
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[int] = None


@runtime_checkable
class AITracer(Protocol):
    """
    Ponto de extensão para observabilidade de chamadas à IA.

    Implementações previstas:
      NoOpTracer      → padrão (apenas logs estruturados)
      LangSmithTracer → rastreamento de chains e prompts
      OTELTracer      → spans OpenTelemetry para APMs (Datadog, Jaeger, etc.)

    Como adicionar uma nova implementação:
      1. Criar app/observability/{nome}.py implementando esta interface
      2. Instanciar em main.py._build_ai_service() e injetar no AIService
    """

    async def on_start(
        self, ctx: AICallContext, system: str, messages: list[dict]
    ) -> None: ...

    async def on_chunk(self, ctx: AICallContext, chunk: str) -> None: ...

    async def on_end(
        self, ctx: AICallContext, response: str, tokens: int | None
    ) -> None: ...

    async def on_error(self, ctx: AICallContext, error: Exception) -> None: ...
