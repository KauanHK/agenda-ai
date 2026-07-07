from app.core.exceptions import (
    AppError,
    ConflictError,
    NotFoundError,
    ValidationAppError,
)
from app.modules.schedulings.domain.exceptions import (
    SchedulingOverlapClientError,
    SchedulingOverlapUserError,
)

_ERROR_MAP: dict[type[AppError], tuple[str, str]] = {
    SchedulingOverlapUserError: (
        "OVERLAP",
        "Profissional já tem agendamento neste horário.",
    ),
    SchedulingOverlapClientError: (
        "OVERLAP",
        "Cliente já tem agendamento neste horário.",
    ),
    NotFoundError: ("NOT_FOUND", "Recurso não encontrado."),
    ConflictError: (
        "CONFLICT",
        "Operação não permitida para o estado atual do agendamento.",
    ),
    ValidationAppError: (
        "SLOT_UNAVAILABLE",
        "Horário inválido ou fora do funcionamento.",
    ),
}


def to_envelope(exception: AppError | Exception) -> dict:
    entry = _ERROR_MAP.get(type(exception))
    if entry:
        code, default_message = entry
    else:
        code, default_message = (
            "INTERNAL_ERROR",
            "Tive um probleminha aqui, tente novamente.",
        )

    message = getattr(exception, "message", None) or default_message
    return {
        "success": False,
        "error_code": code,
        "message": message,
        "details": getattr(exception, "details", {}) or {},
    }
