class AppException(Exception):
    status_code: int = 500
    detail: str = "Internal Server Error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundException(AppException):
    status_code = 404
    detail = "Resource not found"


class ConflictException(AppException):
    status_code = 409
    detail = "Resource already exists"


class UnauthorizedException(AppException):
    status_code = 401
    detail = "Authentication required"


class ForbiddenException(AppException):
    status_code = 403
    detail = "Access denied"


class BadRequestException(AppException):
    status_code = 400
    detail = "Bad request"
