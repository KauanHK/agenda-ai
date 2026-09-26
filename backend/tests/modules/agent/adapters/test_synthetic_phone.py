"""Testes de `SyntheticPhoneResolver`: determinismo e uso do prefixo."""

from app.modules.agent.adapters.identity.synthetic_phone import SyntheticPhoneResolver
from app.modules.agent.domain.entities import Channel


def test_e_deterministico() -> None:
    resolver = SyntheticPhoneResolver("5547999")
    assert resolver.resolve(Channel.TELEGRAM, "123") == resolver.resolve(Channel.TELEGRAM, "123")


def test_usa_o_prefixo_configurado() -> None:
    assert SyntheticPhoneResolver("5547999").resolve(Channel.TELEGRAM, "x").startswith("5547999")
    assert SyntheticPhoneResolver("5511888").resolve(Channel.TELEGRAM, "x").startswith("5511888")


def test_gera_um_e164_de_13_digitos() -> None:
    phone = SyntheticPhoneResolver("5547999").resolve(Channel.TELEGRAM, "123")
    assert len(phone) == 13
    assert phone.isdigit()


def test_ids_diferentes_geram_telefones_diferentes() -> None:
    resolver = SyntheticPhoneResolver("5547999")
    assert resolver.resolve(Channel.TELEGRAM, "1") != resolver.resolve(Channel.TELEGRAM, "2")
