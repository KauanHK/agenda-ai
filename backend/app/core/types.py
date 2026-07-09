import dataclasses
from typing import Any, ClassVar, Protocol


class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Any]]


class _UnsetType:
    """Sentinel para indicar que um valor não foi fornecido."""

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET = _UnsetType()
Unset = _UnsetType


def is_unset(value: object) -> bool:
    """Verifica se um valor é o sentinel UNSET."""
    return isinstance(value, _UnsetType)


@dataclasses.dataclass(frozen=True, slots=True)
class BaseCommand:
    """Base para comandos."""

    def to_dict(self) -> dict[str, Any]:
        """Converte o comando para um dicionário, ignorando campos UNSET."""
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True, slots=True)
class BaseUpdateCommand(BaseCommand):
    """
    Base para comandos de atualização que utilizam o sentinel UNSET para campos
    opcionais.
    """

    def defined_values(self) -> dict[str, Any]:
        """
        Retorna um dicionário dos campos que foram definidos (não UNSET) neste comando.
        """

        return {
            field.name: getattr(self, field.name)
            for field in dataclasses.fields(self)
            if not isinstance(getattr(self, field.name), _UnsetType)
        }

    def has_changes(self) -> bool:
        """
        Retorna `True` se pelo menos um campo foi definido (não UNSET) neste comando.
        """

        return bool(self.defined_values())


@dataclasses.dataclass(frozen=True, slots=True)
class BaseCreateCommand(BaseCommand):
    """Base para comandos de criação."""
