from collections.abc import AsyncGenerator

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.exceptions import AIServiceError


def _to_gemini_messages(messages: list[dict]) -> list[dict]:
    """Converte formato Claude (role/content) para Gemini (role/parts)."""
    result = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else msg["role"]
        content = msg["content"]
        parts = [{"text": c["text"] if isinstance(c, dict) else c} for c in (content if isinstance(content, list) else [content])]
        result.append({"role": role, "parts": parts})
    return result


class GeminiProvider:
    """
    Provedor Google Gemini.
    Configure AI_PROVIDER=gemini e GEMINI_API_KEY no .env.
    Modelo padrão: gemini-2.0-flash (rápido e econômico).
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def stream(self, system: str, messages: list[dict]) -> AsyncGenerator[str, None]:
        from google.genai import types

        try:
            contents = _to_gemini_messages(messages)
            async for chunk in self._client.aio.models.generate_content_stream(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system),
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise AIServiceError(f"Gemini API error: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def complete(self, system: str, messages: list[dict]) -> tuple[str, int]:
        from google.genai import types

        try:
            contents = _to_gemini_messages(messages)
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system),
            )
            text = response.text or ""
            tokens = response.usage_metadata.total_token_count or 0
            return text, tokens
        except Exception as e:
            raise AIServiceError(f"Gemini API error: {e}") from e
