"""
Identificação do cliente pelo telefone.

É a fronteira de autenticação do canal automático: o orquestrador (que recebe o webhook
do WhatsApp) troca um telefone por um token de sessão, e é esse token — não o telefone —
que o agente de IA carrega dali em diante. O LLM nunca vê o número nem o `client_id`.
"""

import uuid

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.phone import normalize_phone
from app.core.security.mcp_tokens import create_client_mcp_session_token
from app.modules.booking.application.ports.unit_of_work import BookingUnitOfWorkProtocol
from app.modules.booking.domain.entities import CustomerSession
from app.modules.clients.domain.entities import NewClient


class CustomerSessionIssuer:
    def __init__(self, uow: BookingUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def issue(
        self,
        *,
        establishment_id: uuid.UUID,
        phone: str,
        name: str | None = None,
    ) -> CustomerSession:
        """
        Identifica o cliente pelo telefone e emite o token de sessão dele.

        O cliente é criado na primeira mensagem, com o nome que o WhatsApp informa (ou
        o próprio número, se não vier nenhum) — assim uma conversa nova não esbarra em
        cadastro.

        Args:
            establishment_id (uuid.UUID): O estabelecimento dono da conversa.
            phone (str): O telefone do cliente, em qualquer formato.
            name (str | None): Nome a usar caso o cliente ainda não exista.

        Returns:
            CustomerSession: O token e a identidade resolvida.

        Raises:
            NotFoundError: Se o estabelecimento não existe ou está inativo.
            ForbiddenError: Se o cliente existe mas está inativo.
            ConflictError: Se o cliente foi criado concorrentemente.
            ValueError: Se o telefone não tiver dígitos suficientes.
        """

        canonical_phone = normalize_phone(phone)

        async with self._uow as uow:
            establishment = await uow.establishments.get_by_id_or_none(establishment_id)
            if establishment is None or not establishment.is_active:
                raise NotFoundError("Estabelecimento não encontrado.")

            client = await uow.clients.get_by_establishment_and_phone(
                establishment_id=establishment_id,
                phone=canonical_phone,
            )
            is_new_client = client is None

            if client is None:
                try:
                    client = await uow.clients.create(
                        create_command=NewClient(
                            establishment_id=establishment_id,
                            name=name or canonical_phone,
                            phone=canonical_phone,
                            email=None,
                        )
                    )
                except IntegrityError as exc:
                    raise ConflictError(
                        "Cliente já cadastrado neste estabelecimento."
                    ) from exc
            elif not client.is_active:
                raise ForbiddenError("Cliente inativo neste estabelecimento.")

            token = create_client_mcp_session_token(
                client_id=client.id,
                establishment_id=establishment_id,
                phone=canonical_phone,
            )

            return CustomerSession(
                token=token,
                client_id=client.id,
                client_name=client.name,
                is_new_client=is_new_client,
            )
