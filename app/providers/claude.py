from collections.abc import AsyncGenerator

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.exceptions import AIServiceError


class ClaudeProvider:
    """
    Provedor Claude — usa Haiku por padrão (menor custo).
    Troque CLAUDE_MODEL no .env para usar Sonnet ou Opus.
    """

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def stream(self, system: str, messages: list[dict]) -> AsyncGenerator[str, None]:
        try:
            async with self._client.messages.stream(
                model=self._model,
                max_tokens=2048,
                system=system,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except anthropic.APIError as e:
            raise AIServiceError(f"Claude API error: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def complete(self, system: str, messages: list[dict]) -> tuple[str, int]:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=system,
                messages=messages,
            )
            content = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens
            return content, tokens
        except anthropic.APIError as e:
            raise AIServiceError(f"Claude API error: {e}") from e
