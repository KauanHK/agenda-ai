"""
Erros do agendamento pelo canal automático.

São mais específicos que os genéricos de `app.core.exceptions` porque cada um vira um
`error_code` estável no envelope entregue ao agente de IA — é por ele que o agente
decide o que dizer ao cliente (oferecer outro horário, avisar que está fechado, etc.).
"""

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError


class ServiceUnavailableError(NotFoundError):
    code = "service_unavailable"
    message = "Serviço não encontrado ou indisponível."


class SchedulingNotFoundError(NotFoundError):
    code = "scheduling_not_found"
    message = "Agendamento não encontrado."


class PastDateTimeError(ValidationAppError):
    code = "past_datetime"
    message = "O horário escolhido já passou."


class ClosedOnWeekdayError(ValidationAppError):
    code = "closed_on_weekday"
    message = "O estabelecimento não funciona neste dia da semana."


class OutsideOperatingHoursError(ValidationAppError):
    code = "outside_operating_hours"
    message = "O horário escolhido está fora do funcionamento do estabelecimento."


class EstablishmentUnavailableError(ValidationAppError):
    code = "establishment_unavailable"
    message = "O estabelecimento está indisponível neste horário."


class NoProfessionalAvailableError(ConflictError):
    code = "no_professional_available"
    message = "Nenhum profissional disponível neste horário."


class NoProfessionalsError(ConflictError):
    code = "no_professionals"
    message = "O estabelecimento não tem profissionais cadastrados."


class SchedulingNotChangeableError(ConflictError):
    code = "scheduling_not_changeable"
    message = "Este agendamento não pode mais ser alterado."
