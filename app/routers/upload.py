import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.auth import UserContext, get_current_user
from app.core.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])

_UPLOAD_DIR = Path("uploads")
_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"}
_MAX_BYTES = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024


@router.post("/file")
async def upload_file(
    file: UploadFile,
    user: UserContext = Depends(get_current_user),
):
    """
    Upload local de arquivo.
    Arquivos servidos em GET /uploads/{user_id}/{filename}
    TODO: migrar para S3 quando sair do hackathon.
    """
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=422, detail=f"Tipo não suportado: {file.content_type}"
        )

    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=422, detail=f"Arquivo excede {settings.UPLOAD_MAX_SIZE_MB}MB"
        )

    ext = Path(file.filename).suffix if file.filename else ""
    filename = f"{uuid.uuid4()}{ext}"
    dest = _UPLOAD_DIR / str(user.user_id)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / filename).write_bytes(content)

    return {
        "url": f"/uploads/{user.user_id}/{filename}",
        "filename": filename,
        "size_bytes": len(content),
        "content_type": file.content_type,
    }
