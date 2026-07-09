import dataclasses

import pytest

from app.core.types import (
    UNSET,
    BaseCommand,
    BaseCreateCommand,
    BaseUpdateCommand,
    Unset,
    _UnsetType,
    is_unset,
)


@dataclasses.dataclass(frozen=True, slots=True)
class _SampleCommand(BaseCommand):
    name: str
    value: int


@dataclasses.dataclass(frozen=True, slots=True)
class _SampleCreateCommand(BaseCreateCommand):
    name: str


@dataclasses.dataclass(frozen=True, slots=True)
class _SampleUpdateCommand(BaseUpdateCommand):
    name: str | Unset = UNSET
    value: int | None | Unset = UNSET


class TestUnsetType:
    def test_repr_is_unset(self):
        assert repr(UNSET) == "UNSET"

    def test_is_falsy(self):
        assert bool(UNSET) is False

    def test_unset_sentinel_is_instance_of_unset_type(self):
        assert isinstance(UNSET, _UnsetType)

    def test_unset_alias_is_unset_type_class(self):
        assert Unset is _UnsetType

    def test_unset_is_not_none(self):
        assert UNSET is not None


class TestIsUnset:
    def test_returns_true_for_unset_sentinel(self):
        assert is_unset(UNSET) is True

    def test_returns_true_for_any_unset_type_instance(self):
        assert is_unset(_UnsetType()) is True

    def test_returns_false_for_none(self):
        assert is_unset(None) is False

    def test_returns_false_for_falsy_values(self):
        assert is_unset(0) is False
        assert is_unset("") is False
        assert is_unset(False) is False
        assert is_unset({}) is False

    def test_returns_false_for_regular_value(self):
        assert is_unset("valor") is False


class TestBaseCommand:
    def test_to_dict_contains_all_fields(self):
        cmd = _SampleCommand(name="test", value=42)

        assert cmd.to_dict() == {"name": "test", "value": 42}

    def test_is_frozen(self):
        cmd = _SampleCommand(name="test", value=1)

        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            cmd.name = "outro"  # type: ignore[misc]

    def test_is_dataclass(self):
        assert dataclasses.is_dataclass(BaseCommand)


class TestBaseCreateCommand:
    def test_is_base_command_subclass(self):
        assert issubclass(BaseCreateCommand, BaseCommand)

    def test_to_dict_inherited(self):
        cmd = _SampleCreateCommand(name="produto")

        assert cmd.to_dict() == {"name": "produto"}


class TestBaseUpdateCommand:
    def test_is_base_command_subclass(self):
        assert issubclass(BaseUpdateCommand, BaseCommand)

    def test_defined_values_excludes_unset_fields(self):
        cmd = _SampleUpdateCommand(name="novo nome")

        result = cmd.defined_values()

        assert result == {"name": "novo nome"}
        assert "value" not in result

    def test_defined_values_keeps_explicit_none(self):
        cmd = _SampleUpdateCommand(value=None)

        assert cmd.defined_values() == {"value": None}

    def test_defined_values_returns_all_when_none_are_unset(self):
        cmd = _SampleUpdateCommand(name="nome", value=10)

        assert cmd.defined_values() == {"name": "nome", "value": 10}

    def test_defined_values_returns_empty_when_all_unset(self):
        cmd = _SampleUpdateCommand()

        assert cmd.defined_values() == {}

    def test_has_changes_true_when_at_least_one_defined(self):
        cmd = _SampleUpdateCommand(name="nome")

        assert cmd.has_changes() is True

    def test_has_changes_false_when_all_unset(self):
        cmd = _SampleUpdateCommand()

        assert cmd.has_changes() is False


class TestDataclassInstance:
    def test_dataclass_satisfies_protocol(self):
        @dataclasses.dataclass
        class Sample:
            x: int

        assert hasattr(Sample, "__dataclass_fields__")

    def test_plain_class_does_not_satisfy_protocol(self):
        class NotADataclass:
            pass

        assert not hasattr(NotADataclass, "__dataclass_fields__")
