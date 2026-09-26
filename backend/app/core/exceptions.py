from typing import Any


class AppError(Exception):
    """Base class para erros da aplicação."""

    status_code = 400
    code = "app_error"
    message = "An application error occurred."

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> None:

        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "Resource not found."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "Resource conflict."


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    message = "Invalid credentials."


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"
    message = "You do not have permission to perform this action."


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"
    message = "Validation error."


class ExternalServiceError(AppError):
    status_code = 502
    code = "external_service_error"
    message = "An external service failed to respond."
