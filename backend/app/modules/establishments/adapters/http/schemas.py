from datetime import datetime
from typing import Annotated, Self

from pydantic import UUID7, Field, model_validator

from app.core.schemas import BaseSchema
from app.core.validators import CnpjOrCpf, Timezone, validate_cnpj, validate_cpf
from app.modules.establishments.domain.enums import DocumentType

Name = Annotated[str, Field(max_length=255)]
Number = Annotated[str, Field(max_length=20)]
Complement = Annotated[str, Field(max_length=255)]
Neighborhood = Annotated[str, Field(max_length=255)]
City = Annotated[str, Field(max_length=255)]
State = Annotated[str, Field(max_length=255)]
ZipCode = Annotated[str, Field(max_length=20)]


class EstablishmentBase(BaseSchema):
    name: Name
    document: str
    document_type: DocumentType
    is_active: bool
    timezone: Timezone
    street: Name
    number: Number
    complement: Complement
    neighborhood: Neighborhood
    city: City
    state: State
    zip_code: ZipCode

    @model_validator(mode="after")
    def validate_document(self) -> Self:

        validators = {
            DocumentType.CNPJ: validate_cnpj,
            DocumentType.CPF: validate_cpf,
        }

        validators[self.document_type](self.document)
        return self


class EstablishmentRead(EstablishmentBase):
    id: UUID7
    created_at: datetime
    updated_at: datetime


class EstablishmentCreate(EstablishmentBase):
    pass


class EstablishmentUpdate(BaseSchema):
    name: Name | None = None
    document: CnpjOrCpf | None = None
    timezone: Timezone | None = None
    street: Name | None = None
    number: Number | None = None
    complement: Complement | None = None
    neighborhood: Neighborhood | None = None
    city: City | None = None
    state: State | None = None
    zip_code: ZipCode | None = None
