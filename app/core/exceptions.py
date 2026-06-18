from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(status.HTTP_404_NOT_FOUND, f"{resource} not found")


class UnauthorizedError(AppException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Not authenticated")


class ForbiddenError(AppException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "Not enough permissions")


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status.HTTP_409_CONFLICT, detail)


class UploadError(AppException):
    def __init__(self, detail: str = "Upload failed"):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


class AIServiceError(AppException):
    def __init__(self, detail: str = "AI service error"):
        super().__init__(status.HTTP_502_BAD_GATEWAY, detail)
