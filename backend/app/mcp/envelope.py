"""
Envelope de resposta das tools.

Toda tool devolve a mesma forma, com sucesso ou erro, para que o agente de IA possa
ramificar pelo `error_code` — um código estável — em vez de tentar interpretar texto
livre. Erros de domínio viram códigos descritivos (`no_professional_available`,
`outside_operating_hours`, ...); qualquer outra exceção vira `internal_error`, sem
vazar detalhes de implementação para o LLM.
"""

import functools
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = "Tive um problema aqui. Tente de novo em instantes."


def ok(data: Any) -> dict[str, Any]:
    """Monta o envelope de sucesso."""

    return {"success": True, "data": data}


def fail(
    error_code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    """Monta o envelope de erro."""

    return {
        "success": False,
        "error_code": error_code,
        "message": message,
        "details": details or {},
    }


def enveloped[**P, T](
    tool: Callable[P, Awaitable[T]],
) -> Callable[P, Awaitable[dict[str, Any]]]:
    """
    Envolve uma tool no envelope padrão, convertendo exceções em erros descritos.

    Preserva os parâmetros da assinatura original — é deles que o FastMCP deriva tanto
    o schema de entrada quanto as dependências declaradas como `Depends(...)` — mas
    reescreve a anotação de retorno para o envelope, que é o que a tool de fato
    devolve. Sem isso o FastMCP publicaria um `output_schema` do tipo interno e
    recusaria a própria resposta.

    Args:
        tool (Callable): A função da tool, que retorna apenas o dado útil.

    Returns:
        Callable: A função equivalente, retornando o envelope.
    """

    @functools.wraps(tool)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
        try:
            return ok(await tool(*args, **kwargs))
        except AppError as exc:
            return fail(
                error_code=exc.code,
                message=exc.message,
                details=exc.details,
            )
        except Exception:
            logger.exception("Erro inesperado na tool %s.", tool.__name__)
            return fail(
                error_code="internal_error",
                message=INTERNAL_ERROR_MESSAGE,
            )

    wrapper.__signature__ = inspect.signature(tool).replace(  # type: ignore[attr-defined]
        return_annotation=dict[str, Any]
    )
    wrapper.__annotations__ = {**tool.__annotations__, "return": dict[str, Any]}

    return wrapper
