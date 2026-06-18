import jwt

from fastapi import WebSocket, WebSocketException, status


def require_auth(websocket: WebSocket) -> str:
    auth_header = websocket.headers.get("authorization")
    if not auth_header:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        scheme, token = auth_header.split(" ", 1)
    except ValueError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    if scheme.lower() != "bearer":
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        data = jwt.decode(
            token,
            algorithms=["RS256"],
            options={"verify_signature": False},
        )
    except jwt.PyJWTError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    franchise = data.get("custom:id_col")

    if not franchise:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    return franchise
