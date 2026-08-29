import pytest

from app.core.phone import normalize_phone, only_digits, phone_lookup_keys


class TestOnlyDigits:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("(47) 99999-8888", "47999998888"),
            ("+55 47 99999-8888", "5547999998888"),
            ("47999998888", "47999998888"),
            ("sem numero", ""),
        ],
    )
    def test_remove_tudo_que_nao_e_digito(self, raw: str, expected: str) -> None:
        assert only_digits(raw) == expected


class TestNormalizePhone:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("(47) 99999-8888", "+5547999998888"),
            ("47999998888", "+5547999998888"),
            ("5547999998888", "+5547999998888"),
            ("+5547999998888", "+5547999998888"),
            ("4733334444", "+554733334444"),
        ],
    )
    def test_converte_para_e164(self, raw: str, expected: str) -> None:
        assert normalize_phone(raw) == expected

    @pytest.mark.parametrize("raw", ["", "abc", "123"])
    def test_rejeita_numero_sem_digitos_suficientes(self, raw: str) -> None:
        with pytest.raises(ValueError):
            normalize_phone(raw)


class TestPhoneLookupKeys:
    def test_inclui_variantes_com_e_sem_codigo_do_pais(self) -> None:
        keys = phone_lookup_keys("+5547999998888")

        assert "5547999998888" in keys
        assert "47999998888" in keys

    def test_celular_com_nove_tambem_procura_a_forma_antiga(self) -> None:
        keys = phone_lookup_keys("47999998888")

        assert "4799998888" in keys
        assert "554799998888" in keys

    def test_numero_de_oito_digitos_tambem_procura_a_forma_com_nove(self) -> None:
        keys = phone_lookup_keys("4799998888")

        assert "47999998888" in keys

    def test_formatos_diferentes_do_mesmo_numero_geram_as_mesmas_chaves(self) -> None:
        assert phone_lookup_keys("(47) 99999-8888") == phone_lookup_keys(
            "+55 47 99999 8888"
        )

    def test_sem_digitos_nao_gera_chave(self) -> None:
        assert phone_lookup_keys("sem numero") == []
