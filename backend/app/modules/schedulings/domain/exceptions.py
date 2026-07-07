from app.core.exceptions import ConflictError


class SchedulingOverlapUserError(ConflictError):
    code = "scheduling_overlap_user"
    message = "Profissional já tem agendamento neste horário."


class SchedulingOverlapClientError(ConflictError):
    code = "scheduling_overlap_client"
    message = "Cliente já tem agendamento neste horário."
