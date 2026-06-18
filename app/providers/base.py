from collections.abc import AsyncGenerator
from typing import Protocol


class AIProvider(Protocol):
    """
    Interface para provedores de IA.

    stream()    → async generator de chunks de texto (para streaming WS)
    complete()  → texto completo + total de tokens (para respostas estruturadas)

    Implementações:
      MockProvider   → respostas simuladas, sem API (padrão em desenvolvimento)
      ClaudeProvider → Anthropic Claude API
      GeminiProvider → Google Gemini API
    """

    def stream(
        self, system: str, messages: list[dict]
    ) -> AsyncGenerator[str, None]: ...

    async def complete(
        self, system: str, messages: list[dict]
    ) -> tuple[str, int]: ...
