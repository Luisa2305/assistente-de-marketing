from dataclasses import dataclass

from fastapi import Header, Query


@dataclass
class UserContext:
    """
    Contexto do usuário autenticado.
    Populado via JWT da empresa — por enquanto mockado.
    """

    user_id: int
    franquia_id: int
    nome_usuario: str


async def get_current_user(
    x_user_id: int = Header(default=1),
    x_franquia_id: int = Header(default=100),
    x_nome_usuario: str = Header(default="Usuário Demo"),
) -> UserContext:
    return UserContext(
        user_id=x_user_id,
        franquia_id=x_franquia_id,
        nome_usuario=x_nome_usuario,
    )


# ── Dependência WebSocket ─────────────────────────────────────────────────────
# Browser não suporta headers customizados em WS — usa query params
# TODO: substituir por ?token=<JWT> quando auth for implementada
async def get_ws_user(
    user_id: int = Query(default=1),
    franquia_id: int = Query(default=100),
    nome_usuario: str = Query(default="Usuário Demo"),
) -> UserContext:
    return UserContext(
        user_id=user_id,
        franquia_id=franquia_id,
        nome_usuario=nome_usuario,
    )
