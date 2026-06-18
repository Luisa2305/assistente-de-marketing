import asyncio
from collections.abc import AsyncGenerator


class MockProvider:
    """
    Provedor simulado — sem chamadas de API.
    Simula streaming com delay para validar a arquitetura WS end-to-end.
    Troque AI_PROVIDER=claude no .env para usar a API real.
    """

    _RESPONSE = (
        "Olá! Sou o assistente de marca da Seguralta. "
        "Esta resposta confirma que WebSocket, persistência e streaming "
        "estão funcionando corretamente. "
        "Pronto para integrar os módulos Mentor, Studio, Guide e Radar."
    )

    async def stream(self, system: str, messages: list[dict]) -> AsyncGenerator[str, None]:
        for word in self._RESPONSE.split():
            yield word + " "
            await asyncio.sleep(0.04)

    async def complete(self, system: str, messages: list[dict]) -> tuple[str, int]:
        return self._RESPONSE, 0
