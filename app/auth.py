import jwt
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

AUTH_KEY_HEADER = APIKeyHeader(name="Authorization")


def require_auth(auth_header: str = Security(AUTH_KEY_HEADER)) -> str:
    if not auth_header:
        raise HTTPException(detail="Token inválido", status_code=401)
    scheme, token = auth_header.split()
    if scheme.lower() != "bearer":
        raise HTTPException(detail="Token inválido", status_code=401)
    data = jwt.decode(token, algorithms=["RS256"], options={"verify_signature": False})
    franchise = data["custom:id_col"]
    return franchise
